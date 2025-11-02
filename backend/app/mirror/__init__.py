"""Mirror loop package exposing singleton loop."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from .loop import MirrorLoop as AsyncMirrorLoop
from .repository import MirrorRepository
from .learner import MirrorPolicyLearner
from .tables import metadata
from ..db import get_engine

_legacy_path = Path(__file__).resolve().parent.parent / "mirror.py"
_spec = importlib.util.spec_from_file_location("app._mirror_legacy", _legacy_path)
legacy_mirror = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
assert _spec and _spec.loader  # for mypy/static hints
sys.modules[_spec.name] = legacy_mirror  # type: ignore[index]
_spec.loader.exec_module(legacy_mirror)  # type: ignore[union-attr]

FieldSnapshot = legacy_mirror.FieldSnapshot
MirrorEvent = legacy_mirror.MirrorEvent
PolicyEntry = legacy_mirror.PolicyEntry
compute_bucket_key = legacy_mirror.compute_bucket_key
compute_reward = legacy_mirror.compute_reward
mirror_loop = legacy_mirror.mirror_loop
MirrorLoop = legacy_mirror.MirrorLoop

_loop: AsyncMirrorLoop | None = None


def get_mirror_loop() -> MirrorLoop:
    global _loop
    if _loop is None:
        engine = get_engine()
        repository = MirrorRepository(engine)
        learner = MirrorPolicyLearner(repository)
        _loop = AsyncMirrorLoop(repository, learner)
    return _loop


__all__ = [
    "FieldSnapshot",
    "MirrorEvent",
    "PolicyEntry",
    "compute_bucket_key",
    "compute_reward",
    "mirror_loop",
    "MirrorLoop",
    "get_mirror_loop",
    "MirrorRepository",
    "MirrorPolicyLearner",
    "metadata",
]
