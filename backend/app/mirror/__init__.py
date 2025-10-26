"""Mirror loop package exposing singleton loop."""
from __future__ import annotations

from .loop import MirrorLoop
from .repository import MirrorRepository
from .learner import MirrorPolicyLearner
from .tables import metadata
from ..db import get_engine

_loop: MirrorLoop | None = None


def get_mirror_loop() -> MirrorLoop:
    global _loop
    if _loop is None:
        engine = get_engine()
        repository = MirrorRepository(engine)
        learner = MirrorPolicyLearner(repository)
        _loop = MirrorLoop(repository, learner)
    return _loop


__all__ = ["get_mirror_loop", "MirrorLoop", "MirrorRepository", "MirrorPolicyLearner", "metadata"]
