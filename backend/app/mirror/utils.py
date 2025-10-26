from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Sequence


@dataclass(slots=True)
class MirrorEpisode:
    ts: datetime
    user_count: int
    tone: str
    intensity: float
    intensity_bin: int
    reward: float
    pre_coh: float
    pre_ent: float
    post_coh: float
    post_ent: float
    pre_pad: Sequence[float]
    post_pad: Sequence[float]
    dt_ms: int
    bucket_key: str
    id: int | None = None


@dataclass(slots=True)
class PolicyRecord:
    bucket_key: str
    tone: str
    intensity_bin: int
    reward_avg: float
    n: int
    updated_at: datetime


def clamp(value: float, min_value: float = 0.0, max_value: float = 1.0) -> float:
    return max(min_value, min(max_value, value))


def intensity_to_bin(value: float) -> int:
    return int(round(clamp(value) * 10))


def bin_to_intensity(value: int) -> float:
    return clamp(value / 10.0)


def compute_reward(pre: dict[str, float], post: dict[str, float]) -> float:
    return (post["coherence"] - pre["coherence"]) - (post["entropy"] - pre["entropy"])


def dominant_pad_letter(pad: Iterable[float]) -> str:
    values = list(pad)[:3]
    if not values:
        return "P"
    max_index = max(range(len(values)), key=lambda idx: values[idx])
    return "PAD"[max_index]


def build_bucket_key(ts: int, user_count: int, pad: Sequence[float]) -> str:
    moment = datetime.fromtimestamp(ts, tz=timezone.utc)
    hour = moment.hour
    load_bin = "L" if user_count < 20 else "M" if user_count < 60 else "H"
    dominant = dominant_pad_letter(pad or [0.0, 0.0, 0.0])
    return f"{hour:02d}-{load_bin}-{dominant}"
