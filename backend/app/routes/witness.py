"""Witness API routes — presence and attention tracking.

Endpoints for accessing witness/metacognition metrics.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Query, HTTPException

from ..witness import WitnessTracker, get_witness_storage

router = APIRouter(prefix="/api/witness", tags=["witness"])

# Global tracker instance
_tracker: Optional[WitnessTracker] = None


def get_tracker() -> WitnessTracker:
    """Get the global witness tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = WitnessTracker()
    return _tracker


@router.get("/score")
async def get_current_score(user_id: str = Query(default="user-001", description="User identifier")):
    """Get current presence score for a user.

    Returns the most recent witness snapshot, including:
    - presence_score: Overall presence quality (0.0-1.0)
    - attention_quality: Focus/attention measure (0.0-1.0)
    - state: Current witness state (scattered/present/witnessing)
    - Recent intervals, emotional variance, coherence

    Args:
        user_id: User identifier

    Returns:
        {
            "timestamp": "2025-11-08T10:30:00Z",
            "presence_score": 0.75,
            "attention_quality": 0.80,
            "state": "present",
            "action_interval": 15.2,
            "emotional_variance": 0.25,
            "coherence": 0.78,
            "entropy": 0.22,
            "metadata": {...}
        }
    """
    tracker = get_tracker()
    snapshot = tracker.get_current_score(user_id)

    if not snapshot:
        raise HTTPException(
            status_code=404,
            detail=f"No witness data found for user {user_id}. Start by creating reflections."
        )

    return snapshot.to_dict()


@router.get("/history")
async def get_history(
    user_id: str = Query(default="user-001", description="User identifier"),
    limit: int = Query(default=100, ge=1, le=1000, description="Max snapshots to return"),
):
    """Get presence history for a user.

    Returns recent witness snapshots, most recent first.

    Args:
        user_id: User identifier
        limit: Maximum number of snapshots (1-1000)

    Returns:
        {
            "user_id": "user-001",
            "snapshots": [
                {...},  // Most recent
                {...},
                ...
            ],
            "count": 100
        }
    """
    tracker = get_tracker()
    snapshots = tracker.get_history(user_id, limit=limit)

    return {
        "user_id": user_id,
        "snapshots": [s.to_dict() for s in snapshots],
        "count": len(snapshots),
    }


@router.get("/insights")
async def get_insights(
    user_id: str = Query(default="user-001", description="User identifier"),
    window_hours: int = Query(default=24, ge=1, le=168, description="Hours of history to analyze"),
):
    """Get insights about presence patterns.

    Analyzes recent history to provide:
    - Average presence score
    - Dominant state (scattered/present/witnessing)
    - State distribution percentages
    - Trend (improving/declining/stable)
    - Personalized recommendation

    Args:
        user_id: User identifier
        window_hours: Hours of history to analyze (1-168)

    Returns:
        {
            "avg_presence_score": 0.65,
            "dominant_state": "present",
            "state_distribution": {
                "scattered": 0.20,
                "present": 0.65,
                "witnessing": 0.15
            },
            "trend": "improving",
            "recommendation": "Глубокое присутствие. Продолжай наблюдение. Присутствие растёт — отличная работа! 🌟"
        }
    """
    tracker = get_tracker()
    insights = tracker.get_insights(user_id, window_hours=window_hours)

    if not insights:
        raise HTTPException(
            status_code=404,
            detail=f"Insufficient data for insights. User {user_id} needs more activity."
        )

    return insights.to_dict()


@router.get("/stats")
async def get_storage_stats():
    """Get overall witness storage statistics.

    Returns:
        {
            "total_users": 42,
            "total_snapshots": 1337,
            "avg_snapshots_per_user": 31.8
        }
    """
    storage = get_witness_storage()
    return storage.get_stats()


@router.post("/reset")
async def reset_user(user_id: str = Query(..., description="User identifier")):
    """Reset witness data for a user.

    Clears all tracking history and snapshots.
    Use with caution - this is irreversible!

    Args:
        user_id: User identifier

    Returns:
        {"message": "Reset complete", "user_id": "user-001"}
    """
    tracker = get_tracker()
    tracker.reset_user(user_id)

    return {
        "message": f"Witness data reset for user {user_id}",
        "user_id": user_id,
    }
