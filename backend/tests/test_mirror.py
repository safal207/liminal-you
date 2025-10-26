import asyncio
from contextlib import suppress
from datetime import datetime

import pytest

from app.mirror.manager import MirrorManager
from app.mirror.storage import MirrorRepository
from app.mirror.utils import MirrorAction, MirrorState, calculate_reward, derive_bucket_key


def test_calculate_reward_positive_change():
    pre = MirrorState(coherence=0.4, entropy=0.6, pad=[0.5, 0.3, 0.4], ts=100)
    post = MirrorState(coherence=0.6, entropy=0.4, pad=[0.5, 0.3, 0.4], ts=110)
    reward = calculate_reward(pre, post)
    assert pytest.approx(reward, rel=1e-6) == 0.4


def test_bucket_key_bins_pad():
    key = derive_bucket_key(datetime(2024, 3, 20, 15, 0, 0), 42, [0.1, 0.7, 0.2])
    assert key == "15-M-A"


@pytest.mark.asyncio
async def test_policy_learning_cycle(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'mirror.db'}"
    repository = MirrorRepository(url=db_url)
    manager = MirrorManager(repository=repository)

    state = {"coherence": 0.5, "entropy": 0.6, "pad_avg": [0.2, 0.3, 0.4], "ts": 100}
    fallback = MirrorAction(tone="neutral", intensity=0.5, message="msg")

    action, bucket_key = await manager.choose_action(state, fallback, user_count=10, mirror_allowed=True)
    assert action.tone == "neutral"
    assert bucket_key.count("-") == 2

    await manager.start_episode(state, fallback, bucket_key, user_count=10)
    post_state = {"coherence": 0.7, "entropy": 0.3, "pad_avg": [0.3, 0.3, 0.4], "ts": 120}
    await manager.observe_post_state(post_state)

    stats = await repository.stats()
    assert stats["total_events"] == 1

    await manager.run_learning_cycle()
    policy = await repository.get_best_policy(bucket_key)
    assert policy is not None
    assert policy.tone == "neutral"
    assert policy.n == 1

    if manager._learner_task:  # cleanup background task
        manager._learner_task.cancel()
        with suppress(asyncio.CancelledError):
            await manager._learner_task
