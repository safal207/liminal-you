"""High-level tracking logic for witness metrics.

The tracker coordinates between metrics calculation and storage,
providing a clean interface for the rest of the application.
"""

from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime
from typing import Dict, List, Optional

from .metrics import WitnessMetrics
from .models import WitnessSnapshot, WitnessInsight
from .storage import WitnessStorage, get_witness_storage


class WitnessTracker:
    """High-level tracker for witness/presence metrics.

    Tracks user actions and calculates presence scores over time.
    """

    def __init__(
        self,
        storage: Optional[WitnessStorage] = None,
        metrics: Optional[WitnessMetrics] = None,
        window_size: int = 10,  # Track last N intervals
    ):
        """Initialize tracker.

        Args:
            storage: Storage backend (uses global if None)
            metrics: Metrics calculator (creates new if None)
            window_size: Number of recent intervals to track
        """
        self.storage = storage or get_witness_storage()
        self.metrics = metrics or WitnessMetrics()
        self.window_size = window_size

        # Track recent intervals per user
        self._intervals: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))

        # Track recent PAD vectors for variance calculation
        self._pad_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))

        # Track recent coherence values for trend
        self._coherence_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))

        # Last action timestamp per user
        self._last_action: Dict[str, datetime] = {}

    def track_action(
        self,
        user_id: str,
        pad_vec: List[float],
        coherence: float,
        entropy: float,
    ) -> WitnessSnapshot:
        """Track a user action (reflection/interaction) and calculate metrics.

        Args:
            user_id: User identifier
            pad_vec: Current PAD vector [pleasure, arousal, dominance]
            coherence: Current field coherence (0.0-1.0)
            entropy: Current field entropy (0.0-1.0)

        Returns:
            WitnessSnapshot with calculated metrics
        """
        now = datetime.utcnow()

        # Calculate interval since last action
        interval = 0.0
        if user_id in self._last_action:
            interval = (now - self._last_action[user_id]).total_seconds()
        self._last_action[user_id] = now

        # Update histories
        if interval > 0:  # Skip first action
            self._intervals[user_id].append(interval)
        self._pad_history[user_id].append(pad_vec)
        self._coherence_history[user_id].append(coherence)

        # Calculate metrics
        action_intervals = list(self._intervals[user_id])
        emotional_variance = self._calculate_emotional_variance(user_id)
        coherence_trend = self._calculate_coherence_trend(user_id)

        result = self.metrics.calculate_presence_score(
            action_intervals=action_intervals,
            emotional_variance=emotional_variance,
            coherence_trend=coherence_trend,
        )

        # Create snapshot
        snapshot = WitnessSnapshot(
            timestamp=now,
            user_id=user_id,
            presence_score=result["presence_score"],
            attention_quality=result["attention_quality"],
            state=result["state"],
            action_interval=interval,
            emotional_variance=emotional_variance,
            coherence=coherence,
            entropy=entropy,
            metadata={
                "components": result.get("components", {}),
                "coherence_trend": coherence_trend,
            },
        )

        # Store snapshot
        self.storage.add_snapshot(snapshot)

        return snapshot

    def get_current_score(self, user_id: str) -> Optional[WitnessSnapshot]:
        """Get the most recent presence score for a user.

        Args:
            user_id: User identifier

        Returns:
            Latest snapshot or None
        """
        return self.storage.get_latest(user_id)

    def get_history(
        self, user_id: str, limit: int = 100
    ) -> List[WitnessSnapshot]:
        """Get recent presence history for a user.

        Args:
            user_id: User identifier
            limit: Max snapshots to return

        Returns:
            List of snapshots (most recent first)
        """
        return self.storage.get_recent(user_id, limit=limit)

    def get_insights(
        self, user_id: str, window_hours: int = 24
    ) -> Optional[WitnessInsight]:
        """Get insights about a user's presence patterns.

        Args:
            user_id: User identifier
            window_hours: Hours of history to analyze

        Returns:
            WitnessInsight or None if insufficient data
        """
        return self.storage.calculate_insights(user_id, window_hours=window_hours)

    def _calculate_emotional_variance(self, user_id: str) -> float:
        """Calculate variance in PAD vectors.

        Low variance = stable emotions
        High variance = chaotic emotions

        Args:
            user_id: User identifier

        Returns:
            Variance score (0.0-1.0)
        """
        pad_history = list(self._pad_history[user_id])

        if len(pad_history) < 2:
            return 0.0  # Not enough data

        # Calculate standard deviation for each dimension
        variances = []
        for dim in range(3):  # P, A, D
            values = [pad[dim] for pad in pad_history if len(pad) > dim]
            if len(values) < 2:
                continue

            mean = sum(values) / len(values)
            variance = sum((x - mean) ** 2 for x in values) / len(values)
            variances.append(variance ** 0.5)  # std dev

        if not variances:
            return 0.0

        # Average variance across dimensions
        avg_variance = sum(variances) / len(variances)

        # Normalize to 0-1 range (empirically, std > 0.3 is high variance)
        return min(1.0, avg_variance / 0.3)

    def _calculate_coherence_trend(self, user_id: str) -> float:
        """Calculate trend in coherence (rising/falling).

        Args:
            user_id: User identifier

        Returns:
            Trend score (-1.0 to 1.0)
            - Positive = coherence increasing
            - Negative = coherence decreasing
            - Zero = stable
        """
        coherence_history = list(self._coherence_history[user_id])

        if len(coherence_history) < 3:
            return 0.0  # Not enough data

        # Simple linear regression
        n = len(coherence_history)
        x_vals = list(range(n))
        y_vals = coherence_history

        # Calculate slope
        x_mean = sum(x_vals) / n
        y_mean = sum(y_vals) / n

        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_vals, y_vals))
        denominator = sum((x - x_mean) ** 2 for x in x_vals)

        if denominator == 0:
            return 0.0

        slope = numerator / denominator

        # Normalize slope to -1 to 1 range
        # Empirically, slope of ±0.1 per step is significant
        normalized = max(-1.0, min(1.0, slope / 0.1))

        return normalized

    def reset_user(self, user_id: str) -> None:
        """Reset tracking data for a user.

        Args:
            user_id: User identifier
        """
        if user_id in self._intervals:
            del self._intervals[user_id]
        if user_id in self._pad_history:
            del self._pad_history[user_id]
        if user_id in self._coherence_history:
            del self._coherence_history[user_id]
        if user_id in self._last_action:
            del self._last_action[user_id]

        self.storage.clear_user(user_id)
