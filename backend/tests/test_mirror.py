from datetime import datetime, timedelta

import pytest

from app.mirror import FieldSnapshot, MirrorLoop, compute_reward


def test_compute_reward_prefers_coherence_and_low_entropy():
    pre = FieldSnapshot(coherence=0.4, entropy=0.6, pad=(0.5, 0.3, 0.2), ts=0.0)
    post = FieldSnapshot(coherence=0.6, entropy=0.4, pad=(0.5, 0.3, 0.2), ts=5.0)

    reward = compute_reward(pre, post)

    assert reward == pytest.approx((0.6 - 0.4) - (0.4 - 0.6))


def test_choose_action_uses_best_known_policy():
    loop = MirrorLoop(epsilon=0.0, rate_limit=0.0)

    base_time = datetime(2024, 1, 1, 10, 0, 0)
    pre_state = {
        "coherence": 0.4,
        "entropy": 0.6,
        "pad_avg": [0.8, 0.1, 0.1],
        "ts": 0.0,
    }
    weaker_post = {
        "coherence": 0.5,
        "entropy": 0.55,
        "pad_avg": [0.8, 0.1, 0.1],
        "ts": 1.0,
    }
    stronger_post = {
        "coherence": 0.65,
        "entropy": 0.4,
        "pad_avg": [0.8, 0.1, 0.1],
        "ts": 2.0,
    }

    event_one = loop.log_event(
        pre_state=pre_state,
        action={"tone": "neutral", "intensity": 0.3},
        post_state=weaker_post,
        user_count=12,
        timestamp=base_time,
    )
    assert event_one is not None

    event_two = loop.log_event(
        pre_state=pre_state,
        action={"tone": "warm", "intensity": 0.8},
        post_state=stronger_post,
        user_count=12,
        timestamp=base_time + timedelta(minutes=5),
    )
    assert event_two is not None

    tone, intensity = loop.choose_action(
        bucket_key=event_two.bucket_key,
        fallback_tone="neutral",
        fallback_intensity=0.4,
    )

    assert tone == "warm"
    assert intensity == pytest.approx(event_two.intensity)
