"""Causal hint generation utilities for neuro-feedback."""
from __future__ import annotations

from typing import Mapping, MutableMapping

__all__ = ["generate_hint"]


def _extract_metric(payload: Mapping[str, object] | None, *keys: str) -> float:
    for key in keys:
        if not payload or key not in payload:
            continue
        value = payload[key]
        try:
            return float(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            continue
    return 0.0


def generate_hint(
    pre: Mapping[str, object] | None,
    action: Mapping[str, object] | None,
    post: Mapping[str, object] | None,
    policy: Mapping[str, object] | None,
) -> MutableMapping[str, object]:
    """Build a short causal explanation for the chosen neuro-feedback action."""

    delta_coherence = _extract_metric(post, "coh", "coherence") - _extract_metric(pre, "coh", "coherence")
    delta_entropy = _extract_metric(post, "ent", "entropy") - _extract_metric(pre, "ent", "entropy")

    trend = "повышался" if delta_coherence > 0 else "понижался"

    if delta_entropy > 0.3 and delta_coherence < 0:
        reason = "поле перегрелось, нужно успокоение"
    elif delta_coherence > 0.2:
        reason = "появилось согласование, можно расширить тон"
    else:
        reason = "нейтральный отклик, поле стабильно"

    source_bucket = None
    if policy and isinstance(policy, Mapping):
        candidate = policy.get("bucket_key")
        if isinstance(candidate, str) and candidate:
            source_bucket = candidate

    return {
        "cause": reason,
        "trend": f"coherence {trend}",
        "source_bucket": source_bucket,
        "delta_coherence": delta_coherence,
        "delta_entropy": delta_entropy,
        "tone": action.get("tone") if action else None,
        "intensity": action.get("intensity") if action else None,
    }
