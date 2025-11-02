"""Analytics history tracking for astro field."""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from typing import Deque, List, Dict, Any


@dataclass
class FieldSnapshot:
    """Snapshot of astro field state at a point in time."""

    timestamp: float
    pad: List[float]  # [Pleasure, Arousal, Dominance]
    entropy: float
    coherence: float
    samples: int
    tone: str  # "warm", "cool", "neutral"


class AnalyticsHistory:
    """Track astro field history for analytics."""

    def __init__(self, max_snapshots: int = 1000, max_age_seconds: int = 86400):
        """Initialize analytics history.

        Args:
            max_snapshots: Maximum number of snapshots to keep
            max_age_seconds: Maximum age of snapshots in seconds (default: 24 hours)
        """
        self._snapshots: Deque[FieldSnapshot] = deque(maxlen=max_snapshots)
        self._max_age_seconds = max_age_seconds
        self._last_cleanup = time.time()

    def add_snapshot(
        self,
        pad: List[float],
        entropy: float,
        coherence: float,
        samples: int,
        tone: str = "neutral",
    ) -> None:
        """Add field snapshot to history.

        Args:
            pad: PAD vector
            entropy: Entropy value
            coherence: Coherence value
            samples: Number of samples
            tone: Field tone
        """
        snapshot = FieldSnapshot(
            timestamp=time.time(),
            pad=pad,
            entropy=entropy,
            coherence=coherence,
            samples=samples,
            tone=tone,
        )

        self._snapshots.append(snapshot)

        # Cleanup old snapshots periodically
        now = time.time()
        if now - self._last_cleanup > 3600:  # Clean up once per hour
            self._cleanup_old_snapshots()
            self._last_cleanup = now

    def _cleanup_old_snapshots(self) -> None:
        """Remove snapshots older than max_age_seconds."""
        now = time.time()
        cutoff = now - self._max_age_seconds

        # Remove from left while timestamps are too old
        while self._snapshots and self._snapshots[0].timestamp < cutoff:
            self._snapshots.popleft()

    def get_recent_snapshots(self, count: int = 100) -> List[FieldSnapshot]:
        """Get most recent snapshots.

        Args:
            count: Number of snapshots to return

        Returns:
            List of recent snapshots
        """
        return list(self._snapshots)[-count:]

    def get_time_range(self, start_time: float, end_time: float) -> List[FieldSnapshot]:
        """Get snapshots within time range.

        Args:
            start_time: Start timestamp
            end_time: End timestamp

        Returns:
            List of snapshots in range
        """
        return [s for s in self._snapshots if start_time <= s.timestamp <= end_time]

    def get_statistics(self, window_seconds: int | None = None) -> Dict[str, Any]:
        """Calculate statistics over time window.

        Args:
            window_seconds: Time window in seconds (None for all history)

        Returns:
            Statistics dict
        """
        if window_seconds:
            cutoff = time.time() - window_seconds
            snapshots = [s for s in self._snapshots if s.timestamp >= cutoff]
        else:
            snapshots = list(self._snapshots)

        if not snapshots:
            return {
                "count": 0,
                "avg_entropy": 0.0,
                "avg_coherence": 0.0,
                "avg_pad": [0.5, 0.35, 0.45],
                "tone_distribution": {},
                "time_span_seconds": 0.0,
            }

        # Calculate averages
        avg_entropy = sum(s.entropy for s in snapshots) / len(snapshots)
        avg_coherence = sum(s.coherence for s in snapshots) / len(snapshots)

        avg_pad = [
            sum(s.pad[0] for s in snapshots) / len(snapshots),
            sum(s.pad[1] for s in snapshots) / len(snapshots),
            sum(s.pad[2] for s in snapshots) / len(snapshots),
        ]

        # Tone distribution
        tone_counts: Dict[str, int] = {}
        for snapshot in snapshots:
            tone_counts[snapshot.tone] = tone_counts.get(snapshot.tone, 0) + 1

        tone_distribution = {
            tone: count / len(snapshots) for tone, count in tone_counts.items()
        }

        return {
            "count": len(snapshots),
            "avg_entropy": round(avg_entropy, 3),
            "avg_coherence": round(avg_coherence, 3),
            "avg_pad": [round(p, 3) for p in avg_pad],
            "tone_distribution": tone_distribution,
            "time_span_seconds": snapshots[-1].timestamp - snapshots[0].timestamp if len(snapshots) > 1 else 0,
        }

    def get_trends(self, window_seconds: int = 3600) -> Dict[str, Any]:
        """Analyze trends over time window.

        Args:
            window_seconds: Time window for trend analysis (default: 1 hour)

        Returns:
            Trend analysis dict
        """
        cutoff = time.time() - window_seconds
        snapshots = [s for s in self._snapshots if s.timestamp >= cutoff]

        if len(snapshots) < 2:
            return {
                "entropy_trend": "stable",
                "coherence_trend": "stable",
                "overall_mood": "neutral",
            }

        # Calculate trends using first and last quartile
        q1_size = max(1, len(snapshots) // 4)
        first_quarter = snapshots[:q1_size]
        last_quarter = snapshots[-q1_size:]

        avg_entropy_first = sum(s.entropy for s in first_quarter) / len(first_quarter)
        avg_entropy_last = sum(s.entropy for s in last_quarter) / len(last_quarter)

        avg_coherence_first = sum(s.coherence for s in first_quarter) / len(first_quarter)
        avg_coherence_last = sum(s.coherence for s in last_quarter) / len(last_quarter)

        # Determine trends
        entropy_diff = avg_entropy_last - avg_entropy_first
        coherence_diff = avg_coherence_last - avg_coherence_first

        if abs(entropy_diff) < 0.1:
            entropy_trend = "stable"
        elif entropy_diff > 0:
            entropy_trend = "increasing"
        else:
            entropy_trend = "decreasing"

        if abs(coherence_diff) < 0.1:
            coherence_trend = "stable"
        elif coherence_diff > 0:
            coherence_trend = "increasing"
        else:
            coherence_trend = "decreasing"

        # Overall mood from PAD
        avg_pleasure = sum(s.pad[0] for s in last_quarter) / len(last_quarter)
        if avg_pleasure >= 0.65:
            overall_mood = "positive"
        elif avg_pleasure <= 0.35:
            overall_mood = "negative"
        else:
            overall_mood = "neutral"

        return {
            "entropy_trend": entropy_trend,
            "coherence_trend": coherence_trend,
            "overall_mood": overall_mood,
            "entropy_change": round(entropy_diff, 3),
            "coherence_change": round(coherence_diff, 3),
        }

    def get_peaks_and_valleys(self, count: int = 10) -> Dict[str, List[FieldSnapshot]]:
        """Find peaks and valleys in entropy/coherence.

        Args:
            count: Number of peaks/valleys to return for each metric

        Returns:
            Dict with highest/lowest snapshots
        """
        if not self._snapshots:
            return {
                "highest_entropy": [],
                "lowest_entropy": [],
                "highest_coherence": [],
                "lowest_coherence": [],
            }

        snapshots = list(self._snapshots)

        highest_entropy = sorted(snapshots, key=lambda s: s.entropy, reverse=True)[:count]
        lowest_entropy = sorted(snapshots, key=lambda s: s.entropy)[:count]
        highest_coherence = sorted(snapshots, key=lambda s: s.coherence, reverse=True)[:count]
        lowest_coherence = sorted(snapshots, key=lambda s: s.coherence)[:count]

        return {
            "highest_entropy": highest_entropy,
            "lowest_entropy": lowest_entropy,
            "highest_coherence": highest_coherence,
            "lowest_coherence": lowest_coherence,
        }


# Global analytics history instance
_history: AnalyticsHistory | None = None


def get_analytics_history() -> AnalyticsHistory:
    """Get global analytics history instance."""
    global _history
    if _history is None:
        _history = AnalyticsHistory()
    return _history
