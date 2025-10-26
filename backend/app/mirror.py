from __future__ import annotations

"""Mirror loop adaptive policy utilities."""

import random
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, List, MutableMapping, Optional, Sequence, Tuple

_BUCKET_RATE_LIMIT_SECONDS = 2.0
_EPSILON = 0.1


@dataclass
class FieldSnapshot:
    """Lightweight immutable state extracted from AstroLayer."""

    coherence: float
    entropy: float
    pad: Tuple[float, float, float]
    ts: float

    @classmethod
    def from_mapping(cls, payload: MutableMapping[str, object] | None) -> Optional["FieldSnapshot"]:
        if not payload:
            return None

        coherence = float(payload.get("coherence", 0.0))
        entropy = float(payload.get("entropy", 0.0))
        pad_values = payload.get("pad_avg") or payload.get("pad") or [0.0, 0.0, 0.0]
        pad_tuple = tuple(float(x) for x in list(pad_values)[:3])
        if len(pad_tuple) < 3:  # type: ignore[arg-type]
            pad_tuple = pad_tuple + (0.0,) * (3 - len(pad_tuple))  # type: ignore[operator]
        ts_raw = payload.get("ts")
        ts = float(ts_raw) if ts_raw is not None else time.time()
        return cls(coherence=coherence, entropy=entropy, pad=pad_tuple, ts=ts)


@dataclass
class MirrorEvent:
    """Recorded transition between two AstroLayer snapshots."""

    timestamp: datetime
    user_count: int
    tone: str
    intensity: float
    pre: FieldSnapshot
    post: FieldSnapshot
    dt_ms: float
    bucket_key: str
    reward: float


@dataclass
class PolicyEntry:
    """Aggregated reward statistics for a tone/intensity bin."""

    bucket_key: str
    tone: str
    intensity_bin: str
    reward_avg: float = 0.0
    n: int = 0
    avg_intensity: float = 0.0
    updated_at: datetime | None = None

    def update(self, reward: float, intensity: float, timestamp: datetime) -> None:
        self.n += 1
        delta_reward = reward - self.reward_avg
        self.reward_avg += delta_reward / float(self.n)
        delta_intensity = intensity - self.avg_intensity
        self.avg_intensity += delta_intensity / float(self.n)
        self.updated_at = timestamp


def _intensity_bin(value: float) -> str:
    if value < 0.33:
        return "low"
    if value < 0.66:
        return "medium"
    return "high"


def compute_reward(pre: FieldSnapshot, post: FieldSnapshot) -> float:
    """Reward encourages higher coherence and lower entropy."""

    delta_coherence = post.coherence - pre.coherence
    delta_entropy = post.entropy - pre.entropy
    return delta_coherence - delta_entropy


def compute_bucket_key(timestamp: datetime, load: int, pad: Sequence[float]) -> str:
    hour = timestamp.hour
    if load < 20:
        load_bin = "L"
    elif load < 60:
        load_bin = "M"
    else:
        load_bin = "H"

    if not pad:
        dominant = "P"
    else:
        dominant_index = max(range(min(3, len(pad))), key=lambda idx: pad[idx])
        dominant = ["P", "A", "D"][dominant_index]

    return f"{hour:02d}-{load_bin}-{dominant}"


class MirrorLoop:
    """Stores mirror events and maintains an adaptive policy."""

    def __init__(self, *, epsilon: float = _EPSILON, rate_limit: float = _BUCKET_RATE_LIMIT_SECONDS) -> None:
        self._events: List[MirrorEvent] = []
        self._policy: Dict[str, Dict[Tuple[str, str], PolicyEntry]] = {}
        self._last_logged_at: Dict[str, float] = {}
        self._epsilon = epsilon
        self._rate_limit = rate_limit

    # --- logging -----------------------------------------------------------------
    def log_event(
        self,
        *,
        pre_state: MutableMapping[str, object] | None,
        action: MutableMapping[str, object] | None,
        post_state: MutableMapping[str, object] | None,
        user_count: int,
        timestamp: datetime | None = None,
    ) -> Optional[MirrorEvent]:
        pre_snapshot = FieldSnapshot.from_mapping(pre_state)
        post_snapshot = FieldSnapshot.from_mapping(post_state)
        if not pre_snapshot or not post_snapshot or not action:
            return None

        tone = str(action.get("tone", "neutral"))
        intensity = float(action.get("intensity", 0.5))
        ts = timestamp or datetime.utcnow()
        dt_ms = max(0.0, (post_snapshot.ts - pre_snapshot.ts) * 1000.0)
        bucket_key = compute_bucket_key(ts, user_count, pre_snapshot.pad)

        last_logged = self._last_logged_at.get(bucket_key)
        now_sec = ts.timestamp()
        if last_logged is not None and now_sec - last_logged < self._rate_limit:
            return None

        reward = compute_reward(pre_snapshot, post_snapshot)
        event = MirrorEvent(
            timestamp=ts,
            user_count=user_count,
            tone=tone,
            intensity=intensity,
            pre=pre_snapshot,
            post=post_snapshot,
            dt_ms=dt_ms,
            bucket_key=bucket_key,
            reward=reward,
        )
        self._events.append(event)
        self._last_logged_at[bucket_key] = now_sec
        self._update_policy(event)
        return event

    def _update_policy(self, event: MirrorEvent) -> None:
        bucket = self._policy.setdefault(event.bucket_key, {})
        bin_name = _intensity_bin(event.intensity)
        entry = bucket.get((event.tone, bin_name))
        if entry is None:
            entry = PolicyEntry(
                bucket_key=event.bucket_key,
                tone=event.tone,
                intensity_bin=bin_name,
            )
            bucket[(event.tone, bin_name)] = entry
        entry.update(event.reward, event.intensity, event.timestamp)

    # --- policy ------------------------------------------------------------------
    def choose_action(
        self,
        *,
        bucket_key: str,
        fallback_tone: str,
        fallback_intensity: float,
    ) -> Tuple[str, float]:
        if not bucket_key:
            return fallback_tone, fallback_intensity

        if random.random() < self._epsilon:
            return fallback_tone, fallback_intensity

        bucket = self._policy.get(bucket_key)
        if not bucket:
            return fallback_tone, fallback_intensity

        # Select entry with highest reward_avg (ties broken by sample size)
        best_entry = max(bucket.values(), key=lambda item: (item.reward_avg, item.n))
        chosen_intensity = min(1.0, max(0.0, best_entry.avg_intensity or fallback_intensity))
        return best_entry.tone, chosen_intensity

    # --- inspection --------------------------------------------------------------
    def rebuild_policy(self) -> None:
        self._policy.clear()
        self._last_logged_at.clear()
        events = list(self._events)
        self._events.clear()
        for event in events:
            self._events.append(event)
            self._update_policy(event)
            self._last_logged_at[event.bucket_key] = event.timestamp.timestamp()

    def get_policy(self, bucket_key: str | None = None) -> List[PolicyEntry]:
        if bucket_key:
            bucket = self._policy.get(bucket_key, {})
            return sorted(bucket.values(), key=lambda entry: entry.reward_avg, reverse=True)

        entries: List[PolicyEntry] = []
        for bucket in self._policy.values():
            entries.extend(bucket.values())
        return sorted(entries, key=lambda entry: (entry.bucket_key, -entry.reward_avg))

    def get_stats(
        self,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> Dict[str, object]:
        events = self._events
        if start or end:
            events = [
                event
                for event in events
                if (start is None or event.timestamp >= start)
                and (end is None or event.timestamp <= end)
            ]

        if not events:
            return {
                "count": 0,
                "avg_reward": 0.0,
                "avg_delta_coherence": 0.0,
                "avg_delta_entropy": 0.0,
                "coverage": 0.0,
                "buckets": [],
                "events": [],
            }

        count = len(events)
        avg_reward = sum(event.reward for event in events) / count
        avg_delta_coherence = sum(event.post.coherence - event.pre.coherence for event in events) / count
        avg_delta_entropy = sum(event.post.entropy - event.pre.entropy for event in events) / count
        buckets = sorted({event.bucket_key for event in events})

        return {
            "count": count,
            "avg_reward": avg_reward,
            "avg_delta_coherence": avg_delta_coherence,
            "avg_delta_entropy": avg_delta_entropy,
            "coverage": len(buckets) / max(1, len(self._policy)) if self._policy else 1.0,
            "buckets": buckets,
            "events": [
                {
                    "timestamp": event.timestamp.isoformat(),
                    "bucket_key": event.bucket_key,
                    "delta_coherence": event.post.coherence - event.pre.coherence,
                    "delta_entropy": event.post.entropy - event.pre.entropy,
                    "reward": event.reward,
                    "tone": event.tone,
                    "intensity": event.intensity,
                }
                for event in events
            ],
        }


mirror_loop = MirrorLoop()

__all__ = [
    "FieldSnapshot",
    "MirrorEvent",
    "PolicyEntry",
    "MirrorLoop",
    "compute_bucket_key",
    "compute_reward",
    "mirror_loop",
]
