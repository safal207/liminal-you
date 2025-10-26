from __future__ import annotations

import asyncio
import logging

from .repository import MirrorRepository

logger = logging.getLogger(__name__)


class MirrorPolicyLearner:
    """Periodic learner that refreshes the policy table from mirror events."""

    def __init__(self, repository: MirrorRepository, interval: float = 60.0) -> None:
        self._repository = repository
        self._interval = interval
        self._task: asyncio.Task[None] | None = None
        self._lock = asyncio.Lock()

    async def run_once(self) -> None:
        async with self._lock:
            try:
                await self._repository.rebuild_policy()
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.exception("Mirror policy rebuild failed: %%s", exc)

    async def _loop(self) -> None:
        while True:
            await asyncio.sleep(self._interval)
            await self.run_once()

    def ensure_running(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._loop())

    async def trigger_rebuild(self) -> None:
        await self.run_once()
