"""In-memory storage for witness snapshots.

For v0.3, we use simple in-memory storage.
In v0.4, we'll migrate to database (PostgreSQL or LiminalDB).
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from .models import WitnessSnapshot, WitnessInsight, WitnessState


class WitnessStorage:
    """In-memory storage for witness metrics."""

    def __init__(self, max_snapshots_per_user: int = 1000):
        """Initialize storage.

        Args:
            max_snapshots_per_user: Max snapshots to keep per user
        """
        self._snapshots: Dict[str, List[WitnessSnapshot]] = defaultdict(list)
        self._max_snapshots = max_snapshots_per_user

    def add_snapshot(self, snapshot: WitnessSnapshot) -> None:
        """Add a witness snapshot for a user.

        Args:
            snapshot: The snapshot to store
        """
        snapshots = self._snapshots[snapshot.user_id]
        snapshots.append(snapshot)

        # Trim old snapshots if needed
        if len(snapshots) > self._max_snapshots:
            # Keep most recent
            snapshots[:] = snapshots[-self._max_snapshots :]

    def get_recent(
        self, user_id: str, limit: int = 100, since: Optional[datetime] = None
    ) -> List[WitnessSnapshot]:
        """Get recent snapshots for a user.

        Args:
            user_id: User identifier
            limit: Maximum number of snapshots to return
            since: Only return snapshots after this time

        Returns:
            List of snapshots, most recent first
        """
        snapshots = self._snapshots.get(user_id, [])

        if since:
            snapshots = [s for s in snapshots if s.timestamp >= since]

        # Return most recent first
        return sorted(snapshots, key=lambda s: s.timestamp, reverse=True)[:limit]

    def get_latest(self, user_id: str) -> Optional[WitnessSnapshot]:
        """Get the most recent snapshot for a user.

        Args:
            user_id: User identifier

        Returns:
            Latest snapshot or None if no data
        """
        snapshots = self._snapshots.get(user_id, [])
        return snapshots[-1] if snapshots else None

    def calculate_insights(
        self, user_id: str, window_hours: int = 24
    ) -> Optional[WitnessInsight]:
        """Calculate insights from recent witness history.

        Args:
            user_id: User identifier
            window_hours: Hours of history to analyze

        Returns:
            WitnessInsight or None if insufficient data
        """
        since = datetime.utcnow() - timedelta(hours=window_hours)
        snapshots = self.get_recent(user_id, limit=1000, since=since)

        if not snapshots:
            return None

        # Calculate averages
        avg_presence = sum(s.presence_score for s in snapshots) / len(snapshots)

        # Count states
        state_counts = {
            WitnessState.SCATTERED: 0,
            WitnessState.PRESENT: 0,
            WitnessState.WITNESSING: 0,
        }
        for snapshot in snapshots:
            state_counts[snapshot.state] += 1

        total = len(snapshots)
        scattered_ratio = state_counts[WitnessState.SCATTERED] / total
        present_ratio = state_counts[WitnessState.PRESENT] / total
        witnessing_ratio = state_counts[WitnessState.WITNESSING] / total

        # Dominant state
        dominant_state = max(state_counts.items(), key=lambda x: x[1])[0]

        # Trend analysis
        trend = self._calculate_trend(snapshots)

        # Generate recommendation
        recommendation = self._generate_recommendation(
            avg_presence, dominant_state, trend, scattered_ratio
        )

        return WitnessInsight(
            user_id=user_id,
            avg_presence_score=avg_presence,
            dominant_state=dominant_state,
            scattered_ratio=scattered_ratio,
            present_ratio=present_ratio,
            witnessing_ratio=witnessing_ratio,
            trend=trend,
            recommendation=recommendation,
            generated_at=datetime.utcnow(),
        )

    def _calculate_trend(self, snapshots: List[WitnessSnapshot]) -> str:
        """Calculate presence trend from snapshots.

        Args:
            snapshots: List of snapshots (recent first)

        Returns:
            "improving" | "declining" | "stable"
        """
        if len(snapshots) < 10:
            return "stable"

        # Split into first half and second half
        mid = len(snapshots) // 2
        first_half = snapshots[mid:]  # Older
        second_half = snapshots[:mid]  # Newer

        avg_first = sum(s.presence_score for s in first_half) / len(first_half)
        avg_second = sum(s.presence_score for s in second_half) / len(second_half)

        diff = avg_second - avg_first

        if diff > 0.1:
            return "improving"
        elif diff < -0.1:
            return "declining"
        else:
            return "stable"

    def _generate_recommendation(
        self,
        avg_presence: float,
        dominant_state: WitnessState,
        trend: str,
        scattered_ratio: float,
    ) -> str:
        """Generate human-readable recommendation.

        Args:
            avg_presence: Average presence score
            dominant_state: Most common state
            trend: Trend direction
            scattered_ratio: Percentage of scattered time

        Returns:
            Recommendation text
        """
        if avg_presence > 0.7:
            base = "Глубокое присутствие. Продолжай наблюдение."
        elif avg_presence > 0.4:
            base = "Качество присутствия умеренное. Практикуй дыхание."
        else:
            base = "Внимание рассеяно. Начни с коротких пауз."

        if trend == "improving":
            return f"{base} Присутствие растёт — отличная работа! 🌟"
        elif trend == "declining":
            return f"{base} Присутствие ослабевает. Время для практики? 🌿"
        else:
            if scattered_ratio > 0.5:
                return f"{base} Слишком много спешки. Замедлись. 🍃"
            else:
                return f"{base} Стабильная осознанность. 🧘"

    def clear_user(self, user_id: str) -> None:
        """Clear all snapshots for a user.

        Args:
            user_id: User identifier
        """
        if user_id in self._snapshots:
            del self._snapshots[user_id]

    def clear_all(self) -> None:
        """Clear all stored data."""
        self._snapshots.clear()

    def get_stats(self) -> Dict[str, any]:
        """Get storage statistics.

        Returns:
            {
                'total_users': int,
                'total_snapshots': int,
                'avg_snapshots_per_user': float
            }
        """
        total_users = len(self._snapshots)
        total_snapshots = sum(len(snapshots) for snapshots in self._snapshots.values())
        avg_per_user = total_snapshots / total_users if total_users > 0 else 0

        return {
            "total_users": total_users,
            "total_snapshots": total_snapshots,
            "avg_snapshots_per_user": round(avg_per_user, 1),
        }


# Global singleton instance
_storage: Optional[WitnessStorage] = None


def get_witness_storage() -> WitnessStorage:
    """Get the global witness storage instance.

    Returns:
        WitnessStorage instance
    """
    global _storage
    if _storage is None:
        _storage = WitnessStorage()
    return _storage
