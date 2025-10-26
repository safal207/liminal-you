from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import logging
from typing import List, Sequence

from sqlalchemy import Engine, func, select

from .tables import metadata, mirror_events, policy_table
from .utils import MirrorEpisode, PolicyRecord


logger = logging.getLogger(__name__)


class MirrorRepository:
    """Persistence helper for mirror loop artifacts."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._available = True
        try:
            metadata.create_all(self._engine, checkfirst=True)
        except Exception as exc:  # pragma: no cover - defensive path when DB unavailable
            logger.warning("Mirror repository unavailable: %s", exc)
            self._available = False

    async def insert_event(self, episode: MirrorEpisode) -> None:
        if not self._available:
            return
        await asyncio.to_thread(self._insert_event_sync, episode)

    def _insert_event_sync(self, episode: MirrorEpisode) -> None:
        payload = {
            "ts": episode.ts,
            "user_count": episode.user_count,
            "tone": episode.tone,
            "intensity": episode.intensity,
            "intensity_bin": episode.intensity_bin,
            "reward": episode.reward,
            "pre_coh": episode.pre_coh,
            "pre_ent": episode.pre_ent,
            "post_coh": episode.post_coh,
            "post_ent": episode.post_ent,
            "pre_pad": list(episode.pre_pad),
            "post_pad": list(episode.post_pad),
            "dt_ms": episode.dt_ms,
            "bucket_key": episode.bucket_key,
        }
        if not self._available:
            return
        with self._engine.begin() as connection:
            connection.execute(mirror_events.insert().values(**payload))

    async def rebuild_policy(self) -> None:
        if not self._available:
            return
        await asyncio.to_thread(self._rebuild_policy_sync)

    def _rebuild_policy_sync(self) -> None:
        if not self._available:
            return
        with self._engine.begin() as connection:
            result = connection.execute(
                select(
                    mirror_events.c.bucket_key,
                    mirror_events.c.tone,
                    mirror_events.c.intensity_bin,
                    func.avg(mirror_events.c.reward).label("reward_avg"),
                    func.count().label("n"),
                ).group_by(
                    mirror_events.c.bucket_key,
                    mirror_events.c.tone,
                    mirror_events.c.intensity_bin,
                )
            ).all()
            connection.execute(policy_table.delete())
            now = datetime.now(timezone.utc)
            if result:
                connection.execute(
                    policy_table.insert(),
                    [
                        {
                            "bucket_key": row.bucket_key,
                            "tone": row.tone,
                            "intensity_bin": row.intensity_bin,
                            "reward_avg": float(row.reward_avg or 0.0),
                            "n": int(row.n or 0),
                            "updated_at": now,
                        }
                        for row in result
                    ],
                )

    async def fetch_policies(self, bucket_key: str | None = None) -> List[PolicyRecord]:
        if not self._available:
            return []
        rows = await asyncio.to_thread(self._fetch_policies_sync, bucket_key)
        return [
            PolicyRecord(
                bucket_key=row.bucket_key,
                tone=row.tone,
                intensity_bin=row.intensity_bin,
                reward_avg=float(row.reward_avg),
                n=row.n,
                updated_at=row.updated_at,
            )
            for row in rows
        ]

    def _fetch_policies_sync(self, bucket_key: str | None) -> Sequence:
        if not self._available:
            return []
        with self._engine.begin() as connection:
            query = select(policy_table).order_by(policy_table.c.bucket_key, policy_table.c.reward_avg.desc())
            if bucket_key:
                query = query.where(policy_table.c.bucket_key == bucket_key)
            return connection.execute(query).all()

    async def get_best_policy(self, bucket_key: str) -> PolicyRecord | None:
        rows = await self.fetch_policies(bucket_key)
        return rows[0] if rows else None

    async def fetch_events(
        self,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = 200,
    ) -> List[MirrorEpisode]:
        if not self._available:
            return []
        rows = await asyncio.to_thread(self._fetch_events_sync, start, end, limit)
        return [
            MirrorEpisode(
                id=row.id,
                ts=row.ts,
                user_count=row.user_count,
                tone=row.tone,
                intensity=row.intensity,
                intensity_bin=row.intensity_bin,
                reward=row.reward,
                pre_coh=row.pre_coh,
                pre_ent=row.pre_ent,
                post_coh=row.post_coh,
                post_ent=row.post_ent,
                pre_pad=row.pre_pad,
                post_pad=row.post_pad,
                dt_ms=row.dt_ms,
                bucket_key=row.bucket_key,
            )
            for row in rows
        ]

    def _fetch_events_sync(
        self,
        start: datetime | None,
        end: datetime | None,
        limit: int,
    ) -> Sequence:
        if not self._available:
            return []
        with self._engine.begin() as connection:
            query = select(mirror_events).order_by(mirror_events.c.ts.desc()).limit(limit)
            if start:
                query = query.where(mirror_events.c.ts >= start)
            if end:
                query = query.where(mirror_events.c.ts <= end)
            return connection.execute(query).all()

    async def count_distinct_buckets(self) -> int:
        if not self._available:
            return 0
        return await asyncio.to_thread(self._count_distinct_buckets_sync)

    def _count_distinct_buckets_sync(self) -> int:
        if not self._available:
            return 0
        with self._engine.begin() as connection:
            result = connection.execute(select(func.count(func.distinct(mirror_events.c.bucket_key)))).scalar()
            return int(result or 0)
