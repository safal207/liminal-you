"""AstroLayer field harmonizer utilities."""
from __future__ import annotations

from typing import Dict, Iterable, List

import math
import time

_PAD_LABELS: Dict[str, List[float]] = {
    "свет": [0.68, 0.42, 0.35],
    "радость": [0.85, 0.55, 0.6],
    "спокойствие": [0.6, 0.2, 0.7],
    "вдохновение": [0.78, 0.6, 0.58],
    "любовь": [0.82, 0.48, 0.5],
    "грусть": [0.2, 0.35, 0.25],
    "злость": [0.1, 0.65, 0.7],
    "тревога": [0.25, 0.72, 0.3],
    "интерес": [0.7, 0.5, 0.55],
}

_DEFAULT_PAD = [0.5, 0.35, 0.45]


def clamp_pad(values: Iterable[float]) -> List[float]:
    """Return a PAD vector constrained to the [0.0, 1.0] range."""

    clamped = [max(0.0, min(1.0, float(v))) for v in values][:3]
    if len(clamped) < 3:
        clamped.extend([0.0] * (3 - len(clamped)))
    return clamped


def map_label_to_pad(label: str) -> List[float]:
    """Map a textual emotion label onto a PAD vector."""

    normalized = label.strip().lower()
    pad = _PAD_LABELS.get(normalized, _DEFAULT_PAD)
    return list(pad)


class AstroField:
    """Maintains a decaying exponential moving average of the shared field."""

    def __init__(self, alpha: float = 0.15, decay: float = 0.98) -> None:
        self.pad: List[float] = [0.0, 0.0, 0.0]
        self.n = 0
        self.decay = decay
        self.alpha = alpha
        self.last = time.time()

    def _ema(self, vector: Iterable[float]) -> None:
        values = clamp_pad(vector)
        if self.n == 0:
            self.pad = values
            self.n = 1
            return

        self.pad = [p * (1 - self.alpha) + x * self.alpha for p, x in zip(self.pad, values)]
        self.n += 1

    def _entropy(self) -> float:
        magnitude = math.sqrt(sum(p * p for p in self.pad))
        return max(0.0, 1.0 - min(magnitude, 1.0))

    def _coherence(self) -> float:
        return max(0.0, min(1.0, 1.0 - self._entropy()))

    def integrate(self, pad_vec: Iterable[float]) -> Dict[str, object]:
        now = time.time()
        # time-based decay gently relaxes the field when no updates arrive
        elapsed = max(0.0, now - self.last)
        self.last = now
        decay_factor = self.decay ** max(1.0, elapsed)
        self.pad = [p * decay_factor for p in self.pad]
        self._ema(pad_vec)

        entropy = round(self._entropy(), 3)
        coherence = round(self._coherence(), 3)

        return {
            "field_id": "global",
            "pad_avg": [round(value, 4) for value in self.pad],
            "entropy": entropy,
            "coherence": coherence,
            "ts": int(now),
            "samples": self.n,
        }

    def snapshot(self) -> Dict[str, object]:
        now = int(time.time())
        entropy = round(self._entropy(), 3)
        coherence = round(self._coherence(), 3)
        return {
            "field_id": "global",
            "pad_avg": [round(value, 4) for value in self.pad],
            "entropy": entropy,
            "coherence": coherence,
            "ts": now,
            "samples": self.n,
        }
