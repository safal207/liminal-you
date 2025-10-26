from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app.mirror.loop import MirrorLoop
from app.mirror.repository import MirrorRepository
from app.mirror.utils import MirrorEpisode, build_bucket_key, compute_reward, intensity_to_bin


class _DummyLearner:
    def ensure_running(self) -> None:  # pragma: no cover - hook for compatibility
        return

    async def trigger_rebuild(self) -> None:  # pragma: no cover - compatibility
        return


def test_compute_reward() -> None:
    pre = {"coherence": 0.4, "entropy": 0.6}
    post = {"coherence": 0.7, "entropy": 0.4}
    assert compute_reward(pre, post) == pytest.approx(0.5)


@pytest.mark.asyncio
async def test_choose_action_prefers_best_policy() -> None:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    repository = MirrorRepository(engine)
    learner = _DummyLearner()
    loop = MirrorLoop(repository, learner, epsilon=0.0)

    bucket_key = "12-M-D"
    now = datetime.now(timezone.utc)
    episode = MirrorEpisode(
        id=None,
        ts=now,
        user_count=25,
        tone="cool",
        intensity=0.8,
        intensity_bin=intensity_to_bin(0.8),
        reward=0.42,
        pre_coh=0.55,
        pre_ent=0.48,
        post_coh=0.75,
        post_ent=0.35,
        pre_pad=[0.4, 0.45, 0.9],
        post_pad=[0.5, 0.5, 0.85],
        dt_ms=3200,
        bucket_key=bucket_key,
    )
    await repository.insert_event(episode)
    await repository.rebuild_policy()

    pad = [0.3, 0.35, 0.82]
    ts_value = int(datetime(2024, 1, 1, 12, tzinfo=timezone.utc).timestamp())
    fallback = {
        "tone": "neutral",
        "message": "",
        "intensity": 0.45,
        "pad": pad,
        "entropy": 0.5,
        "coherence": 0.6,
        "ts": ts_value,
        "samples": 10,
    }
    state = {"entropy": 0.5, "coherence": 0.6, "pad_avg": pad, "ts": ts_value, "samples": 10}

    bucket = build_bucket_key(ts_value, 25, pad)
    assert bucket == bucket_key

    analysis = await loop.choose_action(state, fallback, user_count=25, mirror_active=True)

    assert analysis["tone"] == "cool"
    assert analysis["policy_source"] == "mirror"
    assert analysis["intensity"] == pytest.approx(0.8, abs=1e-6)
