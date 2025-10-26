"""Utility helpers for mirror loop calculations."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List


@dataclass(slots=True)
class MirrorState:
    """Normalized snapshot of astro field metrics."""

    coherence: float
    entropy: float
    pad: List[float]
    ts: int

    @classmethod
    def from_payload(cls, payload: dict) -> "MirrorState":
        pad_values = payload.get("pad") or payload.get("pad_avg") or [0.0, 0.0, 0.0]
        pad = [float(value) for value in list(pad_values)[:3]]
        if len(pad) < 3:
            pad.extend([0.0] * (3 - len(pad)))

        return cls(
            coherence=float(payload.get("coherence", 0.0)),
            entropy=float(payload.get("entropy", 0.0)),
            pad=pad,
            ts=int(payload.get("ts", 0)),
        )


@dataclass(slots=True)
class MirrorAction:
    tone: str
    intensity: float
    message: str

    @property
    def intensity_bin(self) -> int:
        return max(0, min(9, int(self.intensity * 10)))


@dataclass(slots=True)
class EpisodeRecord:
    pre: MirrorState
    action: MirrorAction
    bucket_key: str
    user_count: int
    started_at: float


def calculate_reward(pre: MirrorState, post: MirrorState) -> float:
    """Reward positive changes in coherence and negative entropy drift."""

    delta_coherence = post.coherence - pre.coherence
    delta_entropy = post.entropy - pre.entropy
    return round(delta_coherence - delta_entropy, 6)


def derive_bucket_key(now: datetime, load: int, pad: Iterable[float]) -> str:
    """Compose a coarse context bucket key."""

    hour = now.hour
    if load < 20:
        load_bin = "L"
    elif load < 60:
        load_bin = "M"
    else:
        load_bin = "H"

    pad_list = [float(value) for value in list(pad)[:3]]
    if len(pad_list) < 3:
        pad_list.extend([0.0] * (3 - len(pad_list)))

    labels = ["P", "A", "D"]
    dominant_index = max(range(3), key=lambda idx: pad_list[idx])
    dominant = labels[dominant_index]

    return f"{hour:02d}-{load_bin}-{dominant}"
