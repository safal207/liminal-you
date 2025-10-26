"""SQL-backed repository for mirror loop events and policies."""
from __future__ import annotations

import asyncio
import os
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    MetaData,
    String,
    create_engine,
    func,
    select,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base

from .utils import EpisodeRecord, MirrorAction, calculate_reward

_DEFAULT_URL = os.getenv("MIRROR_DB_URL", "sqlite:///./mirror_loop.db")

metadata = MetaData()
Base = declarative_base(metadata=metadata)


class MirrorEvent(Base):
    __tablename__ = "mirror_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts = Column(Integer, nullable=False)
    user_count = Column(Integer, nullable=False)
    tone = Column(String(16), nullable=False)
    intensity = Column(Float, nullable=False)
    intensity_bin = Column(Integer, nullable=False)
    pre_coh = Column(Float, nullable=False)
    pre_ent = Column(Float, nullable=False)
    pre_pad = Column(String(64), nullable=False)
    post_coh = Column(Float, nullable=False)
    post_ent = Column(Float, nullable=False)
    post_pad = Column(String(64), nullable=False)
    dt_ms = Column(Integer, nullable=False)
    bucket_key = Column(String(32), nullable=False, index=True)
    reward = Column(Float, nullable=False)


class MirrorPolicy(Base):
    __tablename__ = "policy_table"

    bucket_key = Column(String(32), primary_key=True)
    tone = Column(String(16), primary_key=True)
    intensity_bin = Column(Integer, primary_key=True)
    reward_avg = Column(Float, nullable=False)
    n = Column(Integer, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class MirrorRepository:
    """Encapsulates mirror event persistence and aggregation logic."""

    def __init__(self, url: str | None = None) -> None:
        self._url = url or _DEFAULT_URL
        if self._url.startswith("sqlite"):
            db_path = self._url.split("///", 1)[-1]
            if db_path and db_path != ":memory:":
                Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._engine: Engine = create_engine(self._url, future=True)
        Base.metadata.create_all(self._engine)
        self._lock = asyncio.Lock()

    @contextmanager
    def _session(self) -> Iterable[Session]:
        with Session(self._engine) as session:
            yield session

    async def record_episode(self, episode: EpisodeRecord, post: MirrorState) -> None:
        reward = calculate_reward(episode.pre, post)
        dt_ms = max(0, int((post.ts - episode.pre.ts) * 1000))
        payload = MirrorEvent(
            ts=post.ts,
            user_count=episode.user_count,
            tone=episode.action.tone,
            intensity=float(episode.action.intensity),
            intensity_bin=episode.action.intensity_bin,
            pre_coh=episode.pre.coherence,
            pre_ent=episode.pre.entropy,
            pre_pad=",".join(f"{value:.4f}" for value in episode.pre.pad),
            post_coh=post.coherence,
            post_ent=post.entropy,
            post_pad=",".join(f"{value:.4f}" for value in post.pad),
            dt_ms=dt_ms,
            bucket_key=episode.bucket_key,
            reward=reward,
        )

        async with self._lock:
            await asyncio.to_thread(self._persist_event, payload, episode.action)

    def _persist_event(self, payload: MirrorEvent, action: MirrorAction) -> None:
        with self._session() as session:
            session.add(payload)
            self._upsert_policy(session, payload.bucket_key, action, payload.reward)
            session.commit()

    def _upsert_policy(
        self, session: Session, bucket_key: str, action: MirrorAction, reward: float
    ) -> None:
        record = session.get(
            MirrorPolicy,
            {
                "bucket_key": bucket_key,
                "tone": action.tone,
                "intensity_bin": action.intensity_bin,
            },
        )
        now = datetime.utcnow()
        if record is None:
            record = MirrorPolicy(
                bucket_key=bucket_key,
                tone=action.tone,
                intensity_bin=action.intensity_bin,
                reward_avg=reward,
                n=1,
                updated_at=now,
            )
            session.add(record)
        else:
            total = record.reward_avg * record.n + reward
            record.n += 1
            record.reward_avg = total / max(record.n, 1)
            record.updated_at = now

    async def recalculate_policies(self) -> None:
        async with self._lock:
            await asyncio.to_thread(self._recalculate_sync)

    def _recalculate_sync(self) -> None:
        with self._session() as session:
            aggregates = session.execute(
                select(
                    MirrorEvent.bucket_key,
                    MirrorEvent.tone,
                    MirrorEvent.intensity_bin,
                    func.avg(MirrorEvent.reward).label("reward_avg"),
                    func.count(MirrorEvent.id).label("n"),
                )
                .group_by(MirrorEvent.bucket_key, MirrorEvent.tone, MirrorEvent.intensity_bin)
            ).all()

            seen: set[tuple[str, str, int]] = set()
            for bucket_key, tone, intensity_bin, reward_avg, n in aggregates:
                key = (bucket_key, tone, int(intensity_bin))
                seen.add(key)
                record = session.get(
                    MirrorPolicy,
                    {
                        "bucket_key": bucket_key,
                        "tone": tone,
                        "intensity_bin": int(intensity_bin),
                    },
                )
                now = datetime.utcnow()
                if record is None:
                    record = MirrorPolicy(
                        bucket_key=bucket_key,
                        tone=tone,
                        intensity_bin=int(intensity_bin),
                        reward_avg=float(reward_avg or 0.0),
                        n=int(n or 0),
                        updated_at=now,
                    )
                    session.add(record)
                else:
                    record.reward_avg = float(reward_avg or 0.0)
                    record.n = int(n or 0)
                    record.updated_at = now

            session.commit()

    async def get_policy_entries(self, bucket_key: str | None = None) -> List[MirrorPolicy]:
        async with self._lock:
            return await asyncio.to_thread(self._get_policy_sync, bucket_key)

    def _get_policy_sync(self, bucket_key: str | None) -> List[MirrorPolicy]:
        with self._session() as session:
            stmt = select(MirrorPolicy)
            if bucket_key:
                stmt = stmt.where(MirrorPolicy.bucket_key == bucket_key)
            stmt = stmt.order_by(MirrorPolicy.reward_avg.desc())
            result = session.execute(stmt)
            return [row[0] for row in result]

    async def get_best_policy(self, bucket_key: str) -> Optional[MirrorPolicy]:
        entries = await self.get_policy_entries(bucket_key)
        return entries[0] if entries else None

    async def list_recent_events(self, limit: int = 120) -> List[MirrorEvent]:
        async with self._lock:
            return await asyncio.to_thread(self._list_recent_events_sync, limit)

    def _list_recent_events_sync(self, limit: int) -> List[MirrorEvent]:
        with self._session() as session:
            stmt = select(MirrorEvent).order_by(MirrorEvent.id.desc()).limit(limit)
            result = session.execute(stmt)
            return [row[0] for row in result]

    async def heatmap(self) -> List[dict]:
        async with self._lock:
            return await asyncio.to_thread(self._heatmap_sync)

    def _heatmap_sync(self) -> List[dict]:
        with self._session() as session:
            stmt = (
                select(
                    MirrorEvent.tone,
                    MirrorEvent.intensity_bin,
                    func.avg(MirrorEvent.reward).label("reward"),
                    func.count(MirrorEvent.id).label("n"),
                )
                .group_by(MirrorEvent.tone, MirrorEvent.intensity_bin)
                .order_by(MirrorEvent.tone)
            )
            rows = session.execute(stmt).all()
            return [
                {
                    "tone": tone,
                    "intensity_bin": int(intensity_bin or 0),
                    "reward": float(reward or 0.0),
                    "count": int(n or 0),
                }
                for tone, intensity_bin, reward, n in rows
            ]

    async def stats(self) -> dict:
        events = await self.list_recent_events(limit=500)
        total = len(events)
        if not total:
            return {
                "total_events": 0,
                "avg_reward": 0.0,
                "bucket_coverage": 0.0,
                "unique_buckets": 0,
                "recent_events": [],
            }

        rewards = [event.reward for event in events]
        unique_buckets = {event.bucket_key for event in events}
        coverage = len(unique_buckets) / 72.0
        return {
            "total_events": total,
            "avg_reward": sum(rewards) / total,
            "bucket_coverage": coverage,
            "unique_buckets": len(unique_buckets),
            "recent_events": [
                {
                    "id": event.id,
                    "ts": event.ts,
                    "bucket_key": event.bucket_key,
                    "tone": event.tone,
                    "intensity": event.intensity,
                    "delta_coherence": event.post_coh - event.pre_coh,
                    "delta_entropy": event.post_ent - event.pre_ent,
                    "reward": event.reward,
                }
                for event in events
            ],
        }


_mirror_repository: MirrorRepository | None = None


def get_repository() -> MirrorRepository:
    global _mirror_repository
    if _mirror_repository is None:
        _mirror_repository = MirrorRepository()
    return _mirror_repository
