from __future__ import annotations

import asyncio
import logging
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict

from .learner import MirrorPolicyLearner
from .repository import MirrorRepository
from .utils import (
    MirrorEpisode,
    bin_to_intensity,
    build_bucket_key,
    clamp,
    compute_reward,
    intensity_to_bin,
)

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class _PendingAction:
    pre_state: Dict[str, Any]
    tone: str
    intensity: float
    user_count: int
    bucket_key: str
    mirror_active: bool


class MirrorLoop:
    """Coordinates mirror logging and policy decisions."""

    def __init__(
        self,
        repository: MirrorRepository,
        learner: MirrorPolicyLearner,
        *,
        epsilon: float = 0.1,
    ) -> None:
        self._repository = repository
        self._learner = learner
        self._epsilon = epsilon
        self._pending: _PendingAction | None = None
        self._lock = asyncio.Lock()
        self._rng = random.Random()
        self._current_bucket: str | None = None
        self._current_source: str | None = None
        self._current_action: Dict[str, Any] | None = None

    async def observe_state(self, state: Dict[str, Any]) -> None:
        episode: MirrorEpisode | None = None
        async with self._lock:
            if self._pending and self._pending.mirror_active:
                episode = self._build_episode(self._pending, state)
            self._pending = None
        if episode:
            await self._repository.insert_event(episode)

    def _build_episode(self, pending: _PendingAction, post_state: Dict[str, Any]) -> MirrorEpisode | None:
        pre_pad = pending.pre_state.get("pad_avg") or [0.0, 0.0, 0.0]
        post_pad = post_state.get("pad_avg") or [0.0, 0.0, 0.0]
        pre = {
            "coherence": float(pending.pre_state.get("coherence", 0.0)),
            "entropy": float(pending.pre_state.get("entropy", 0.0)),
        }
        post = {
            "coherence": float(post_state.get("coherence", 0.0)),
            "entropy": float(post_state.get("entropy", 0.0)),
        }
        reward = compute_reward(pre, post)
        pre_ts = int(pending.pre_state.get("ts", datetime.now(tz=timezone.utc).timestamp()))
        post_ts = int(post_state.get("ts", pre_ts))
        dt_ms = max(0, (post_ts - pre_ts) * 1000)
        return MirrorEpisode(
            ts=datetime.now(tz=timezone.utc),
            user_count=pending.user_count,
            tone=pending.tone,
            intensity=pending.intensity,
            intensity_bin=intensity_to_bin(pending.intensity),
            reward=reward,
            pre_coh=pre["coherence"],
            pre_ent=pre["entropy"],
            post_coh=post["coherence"],
            post_ent=post["entropy"],
            pre_pad=pre_pad,
            post_pad=post_pad,
            dt_ms=dt_ms,
            bucket_key=pending.bucket_key,
        )

    async def choose_action(
        self,
        state: Dict[str, Any],
        fallback: Dict[str, Any],
        *,
        user_count: int,
        mirror_active: bool,
    ) -> Dict[str, Any]:
        async with self._lock:
            self._learner.ensure_running()
            pad = state.get("pad_avg") or [0.0, 0.0, 0.0]
            ts = int(state.get("ts", datetime.now(tz=timezone.utc).timestamp()))
            bucket_key = build_bucket_key(ts, user_count, pad)
            self._current_bucket = bucket_key

            if not mirror_active:
                self._pending = None
                self._current_source = "fallback"
                self._current_action = {
                    "tone": fallback["tone"],
                    "intensity": fallback["intensity"],
                }
                return {
                    **fallback,
                    "bucket_key": bucket_key,
                    "policy_source": "fallback",
                }

            chosen = None
            queried = False
            if self._rng.random() > self._epsilon:
                queried = True
                chosen = await self._repository.get_best_policy(bucket_key)

            if chosen:
                tone = chosen.tone
                intensity = bin_to_intensity(chosen.intensity_bin)
                source = "mirror"
            else:
                tone = fallback["tone"]
                intensity = fallback["intensity"]
                source = "fallback" if queried else "explore"

            intensity = clamp(float(intensity))
            result = {
                **fallback,
                "tone": tone,
                "intensity": intensity,
                "bucket_key": bucket_key,
                "policy_source": source,
            }

            self._current_source = source
            self._current_action = {"tone": tone, "intensity": intensity}
            self._pending = _PendingAction(
                pre_state=state,
                tone=tone,
                intensity=intensity,
                user_count=user_count,
                bucket_key=bucket_key,
                mirror_active=True,
            )
            return result

    async def register_action(
        self,
        state: Dict[str, Any],
        action: Dict[str, Any],
        *,
        user_count: int,
        mirror_active: bool,
    ) -> None:
        async with self._lock:
            if not mirror_active:
                self._pending = None
                self._current_action = None
                self._current_source = "fallback"
                return
            self._pending = _PendingAction(
                pre_state=state,
                tone=action["tone"],
                intensity=float(action["intensity"]),
                user_count=user_count,
                bucket_key=action.get("bucket_key")
                or build_bucket_key(int(state.get("ts", 0)), user_count, state.get("pad_avg") or [0.0, 0.0, 0.0]),
                mirror_active=True,
            )
            self._current_action = {"tone": action["tone"], "intensity": float(action["intensity"])}

    async def current_context(self) -> Dict[str, Any]:
        async with self._lock:
            return {
                "bucket_key": self._current_bucket,
                "policy_source": self._current_source,
                "action": self._current_action,
            }

    async def run_learning_cycle(self) -> None:
        await self._learner.trigger_rebuild()

    @property
    def repository(self) -> MirrorRepository:
        return self._repository
