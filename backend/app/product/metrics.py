"""Product metrics tracking (North Star: Weekly Witnessed Sessions)."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict


@dataclass
class SessionState:
    started_at: datetime
    reflection_count: int = 0
    has_improved_state: bool = False
    has_practice_completed: bool = False


class ProductMetricsTracker:
    """Tracks product-level funnel and WWS progress in memory."""

    def __init__(self) -> None:
        self._sessions: Dict[str, SessionState] = {}
        self._weekly_completed: Dict[str, set[str]] = defaultdict(set)
        self._funnel = {
            "reflection_users": set(),
            "practice_users": set(),
            "improved_users": set(),
        }

    def track_reflection(self, user_id: str) -> None:
        now = datetime.now(timezone.utc)
        session = self._sessions.get(user_id)

        if session is None or self._session_expired(session, now):
            session = SessionState(started_at=now)
            self._sessions[user_id] = session

        session.reflection_count += 1
        self._funnel["reflection_users"].add(user_id)


    def track_practice_completed(self, user_id: str) -> bool:
        """Track completed practice in current session.

        Returns True when WWS criteria are satisfied after this event.
        """
        session = self._sessions.get(user_id)
        if session is None:
            return False

        session.has_practice_completed = True
        self._funnel["practice_users"].add(user_id)

        return self._maybe_complete_wws(user_id, session)

    def track_state_change(self, user_id: str, coherence: float, entropy: float) -> bool:
        """Track outcome quality. Returns True when a WWS is completed."""
        session = self._sessions.get(user_id)
        if session is None:
            return False

        if coherence >= 0.65 and entropy <= 0.45:
            session.has_improved_state = True
            self._funnel["improved_users"].add(user_id)

        return self._maybe_complete_wws(user_id, session)


    def _maybe_complete_wws(self, user_id: str, session: SessionState) -> bool:
        if not session.has_practice_completed:
            return False

        if session.reflection_count >= 1 and session.has_improved_state:
            week_key = self._week_key(datetime.now(timezone.utc))
            self._weekly_completed[week_key].add(user_id)
            return True

        return False

    def get_wws_summary(self) -> dict:
        now = datetime.now(timezone.utc)
        week_key = self._week_key(now)
        completed_users = self._weekly_completed.get(week_key, set())

        return {
            "week": week_key,
            "weekly_witnessed_sessions": len(completed_users),
            "unique_completed_users": len(completed_users),
        }

    def get_funnel(self) -> dict:
        reflection_users = len(self._funnel["reflection_users"])
        practice_users = len(self._funnel["practice_users"])
        improved_users = len(self._funnel["improved_users"])

        reflection_to_practice = 0.0
        practice_to_improved = 0.0
        reflection_to_improved = 0.0

        if reflection_users > 0:
            reflection_to_practice = practice_users / reflection_users
            reflection_to_improved = improved_users / reflection_users
        if practice_users > 0:
            practice_to_improved = improved_users / practice_users

        return {
            "reflection_users": reflection_users,
            "practice_users": practice_users,
            "improved_users": improved_users,
            "reflection_to_practice": round(reflection_to_practice, 3),
            "practice_to_improved": round(practice_to_improved, 3),
            "reflection_to_improved": round(reflection_to_improved, 3),
        }

    @staticmethod
    def _week_key(ts: datetime) -> str:
        iso_year, iso_week, _ = ts.isocalendar()
        return f"{iso_year}-W{iso_week:02d}"

    @staticmethod
    def _session_expired(session: SessionState, now: datetime) -> bool:
        return now - session.started_at > timedelta(hours=24)


_tracker: ProductMetricsTracker | None = None


def get_product_metrics_tracker() -> ProductMetricsTracker:
    global _tracker
    if _tracker is None:
        _tracker = ProductMetricsTracker()
    return _tracker
