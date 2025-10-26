"""Stateful coordination of the mirror loop."""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from .policy import MirrorPolicyService
from .storage import MirrorRepository, get_repository
from .utils import EpisodeRecord, MirrorAction, MirrorState, derive_bucket_key

logger = logging.getLogger(__name__)


@dataclass
class CurrentPolicySnapshot:
    bucket_key: str
    tone: str
    intensity_bin: int
    reward_avg: float
    n: int
    updated_at: datetime


class MirrorManager:
    def __init__(self, repository: MirrorRepository | None = None) -> None:
        self._repository = repository or get_repository()
        self._policy = MirrorPolicyService(self._repository)
        self._pending: EpisodeRecord | None = None
        self._lock = asyncio.Lock()
        self._learner_task: asyncio.Task[None] | None = None
        self._last_bucket_key: str | None = None

    async def observe_post_state(self, state_payload: dict) -> None:
        async with self._lock:
            if not self._pending:
                return
            post = MirrorState.from_payload(state_payload)
            # Ensure timestamps progress monotonically
            if post.ts <= self._pending.pre.ts:
                post = MirrorState(
                    coherence=post.coherence,
                    entropy=post.entropy,
                    pad=post.pad,
                    ts=self._pending.pre.ts + 1,
                )
            await self._repository.record_episode(self._pending, post)
            logger.debug("mirror episode recorded for bucket %s", self._pending.bucket_key)
            self._pending = None

    async def choose_action(
        self,
        state_payload: dict,
        fallback: MirrorAction,
        *,
        user_count: int,
        mirror_allowed: bool,
    ) -> tuple[MirrorAction, str]:
        await self._ensure_learner()
        now = datetime.now(timezone.utc)
        state = MirrorState.from_payload(state_payload)
        bucket_key = derive_bucket_key(now, user_count, state.pad)
        self._last_bucket_key = bucket_key

        if not mirror_allowed:
            return fallback, bucket_key

        action = await self._policy.choose_action(
            bucket_key,
            fallback,
            candidate_intensity=fallback.intensity,
        )
        return action, bucket_key

    async def start_episode(
        self,
        state_payload: dict,
        action: MirrorAction,
        bucket_key: str,
        user_count: int,
    ) -> None:
        state = MirrorState.from_payload(state_payload)
        async with self._lock:
            self._pending = EpisodeRecord(
                pre=state,
                action=action,
                bucket_key=bucket_key,
                user_count=user_count,
                started_at=time.time(),
            )

    async def run_learning_cycle(self) -> None:
        await self._repository.recalculate_policies()

    async def _ensure_learner(self) -> None:
        if self._learner_task and not self._learner_task.done():
            return
        loop = asyncio.get_running_loop()
        self._learner_task = loop.create_task(self._periodic_learner())

    async def _periodic_learner(self) -> None:
        while True:
            await asyncio.sleep(60)
            try:
                await self._repository.recalculate_policies()
            except Exception:  # pragma: no cover - defensive logging
                logger.exception("mirror policy recalculation failed")

    async def current_policy_snapshot(self) -> Optional[CurrentPolicySnapshot]:
        if not self._last_bucket_key:
            return None
        best = await self._repository.get_best_policy(self._last_bucket_key)
        if not best:
            return None
        return CurrentPolicySnapshot(
            bucket_key=best.bucket_key,
            tone=best.tone,
            intensity_bin=int(best.intensity_bin),
            reward_avg=float(best.reward_avg),
            n=int(best.n),
            updated_at=best.updated_at,
        )


mirror_manager = MirrorManager()
