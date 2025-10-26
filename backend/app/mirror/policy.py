"""Adaptive policy selection for mirror loop."""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable, Optional

from .storage import MirrorRepository
from .utils import MirrorAction


@dataclass
class PolicyCandidate:
    tone: str
    intensity_bin: int
    reward_avg: float
    n: int


class MirrorPolicyService:
    def __init__(self, repository: MirrorRepository, *, epsilon: float = 0.1) -> None:
        self._repository = repository
        self._epsilon = epsilon

    async def choose_action(
        self,
        bucket_key: str,
        fallback: MirrorAction,
        *,
        candidate_intensity: Optional[float] = None,
    ) -> MirrorAction:
        """Choose action via epsilon-greedy policy."""

        if random.random() < self._epsilon:
            return fallback

        best = await self._repository.get_best_policy(bucket_key)
        if best is None or best.reward_avg <= 0:
            return fallback

        intensity = candidate_intensity if candidate_intensity is not None else fallback.intensity
        # Align intensity with learned bin to avoid abrupt jumps
        if best.intensity_bin >= 0:
            intensity = min(0.99, max(0.0, (best.intensity_bin + 0.5) / 10))

        return MirrorAction(tone=best.tone, intensity=float(intensity), message=fallback.message)

    async def list_policies(self, bucket_key: str | None = None) -> Iterable[PolicyCandidate]:
        entries = await self._repository.get_policy_entries(bucket_key)
        for entry in entries:
            yield PolicyCandidate(
                tone=entry.tone,
                intensity_bin=int(entry.intensity_bin),
                reward_avg=float(entry.reward_avg),
                n=int(entry.n),
            )
