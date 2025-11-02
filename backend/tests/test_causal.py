import pytest

from app.causal import generate_hint


def build_state(coh: float, ent: float) -> dict[str, float]:
    return {"coherence": coh, "entropy": ent}


def test_generate_hint_detects_overheated_field():
    pre = build_state(0.7, 0.3)
    post = build_state(0.6, 0.7)
    hint = generate_hint(pre, {"tone": "warm", "intensity": 0.2}, post, {"bucket_key": "10-L-P"})

    assert hint["cause"] == "поле перегрелось, нужно успокоение"
    assert hint["trend"].endswith("понижался")
    assert hint["source_bucket"] == "10-L-P"


def test_generate_hint_expands_when_coherence_rises():
    pre = build_state(0.4, 0.6)
    post = build_state(0.7, 0.55)
    hint = generate_hint(pre, {"tone": "cool", "intensity": 0.8}, post, {})

    assert hint["cause"] == "появилось согласование, можно расширить тон"
    assert hint["trend"].endswith("повышался")


def test_generate_hint_defaults_to_neutral_message():
    hint = generate_hint(build_state(0.5, 0.4), {"tone": "neutral"}, build_state(0.52, 0.45), None)

    assert hint["cause"] == "нейтральный отклик, поле стабильно"
    assert hint["trend"].startswith("coherence")
    assert hint["source_bucket"] is None
