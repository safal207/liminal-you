"""Analytics API routes."""
from __future__ import annotations

from typing import List, Dict, Any

from fastapi import APIRouter, Query
from pydantic import BaseModel

from ..analytics import get_analytics_history, FieldSnapshot

router = APIRouter()


class SnapshotResponse(BaseModel):
    """Field snapshot response."""

    timestamp: float
    pad: List[float]
    entropy: float
    coherence: float
    samples: int
    tone: str


class StatisticsResponse(BaseModel):
    """Statistics response."""

    count: int
    avg_entropy: float
    avg_coherence: float
    avg_pad: List[float]
    tone_distribution: Dict[str, float]
    time_span_seconds: float


class TrendsResponse(BaseModel):
    """Trends analysis response."""

    entropy_trend: str  # "increasing", "decreasing", "stable"
    coherence_trend: str
    overall_mood: str  # "positive", "negative", "neutral"
    entropy_change: float
    coherence_change: float


class PeaksValleysResponse(BaseModel):
    """Peaks and valleys response."""

    highest_entropy: List[SnapshotResponse]
    lowest_entropy: List[SnapshotResponse]
    highest_coherence: List[SnapshotResponse]
    lowest_coherence: List[SnapshotResponse]


def _snapshot_to_response(snapshot: FieldSnapshot) -> SnapshotResponse:
    """Convert FieldSnapshot to response model."""
    return SnapshotResponse(
        timestamp=snapshot.timestamp,
        pad=snapshot.pad,
        entropy=snapshot.entropy,
        coherence=snapshot.coherence,
        samples=snapshot.samples,
        tone=snapshot.tone,
    )


@router.get("/analytics/snapshots", response_model=List[SnapshotResponse])
def get_snapshots(
    count: int = Query(100, ge=1, le=1000, description="Number of recent snapshots")
) -> List[SnapshotResponse]:
    """Get recent field snapshots.

    Args:
        count: Number of snapshots to return

    Returns:
        List of recent snapshots
    """
    history = get_analytics_history()
    snapshots = history.get_recent_snapshots(count)
    return [_snapshot_to_response(s) for s in snapshots]


@router.get("/analytics/statistics", response_model=StatisticsResponse)
def get_statistics(
    window_seconds: int | None = Query(
        None,
        ge=60,
        le=604800,
        description="Time window in seconds (None for all history)",
    )
) -> StatisticsResponse:
    """Get field statistics over time window.

    Args:
        window_seconds: Time window for statistics

    Returns:
        Statistics summary
    """
    history = get_analytics_history()
    stats = history.get_statistics(window_seconds)

    return StatisticsResponse(**stats)


@router.get("/analytics/trends", response_model=TrendsResponse)
def get_trends(
    window_seconds: int = Query(3600, ge=300, le=86400, description="Time window for trend analysis")
) -> TrendsResponse:
    """Analyze field trends over time window.

    Args:
        window_seconds: Time window for trends (default: 1 hour)

    Returns:
        Trend analysis
    """
    history = get_analytics_history()
    trends = history.get_trends(window_seconds)

    return TrendsResponse(**trends)


@router.get("/analytics/peaks", response_model=PeaksValleysResponse)
def get_peaks_valleys(
    count: int = Query(10, ge=1, le=50, description="Number of peaks/valleys per metric")
) -> PeaksValleysResponse:
    """Get peaks and valleys in entropy/coherence.

    Args:
        count: Number of peaks/valleys to return

    Returns:
        Peaks and valleys analysis
    """
    history = get_analytics_history()
    peaks = history.get_peaks_and_valleys(count)

    return PeaksValleysResponse(
        highest_entropy=[_snapshot_to_response(s) for s in peaks["highest_entropy"]],
        lowest_entropy=[_snapshot_to_response(s) for s in peaks["lowest_entropy"]],
        highest_coherence=[_snapshot_to_response(s) for s in peaks["highest_coherence"]],
        lowest_coherence=[_snapshot_to_response(s) for s in peaks["lowest_coherence"]],
    )


@router.get("/analytics/time-range", response_model=List[SnapshotResponse])
def get_time_range(
    start_time: float = Query(..., description="Start timestamp (Unix time)"),
    end_time: float = Query(..., description="End timestamp (Unix time)"),
) -> List[SnapshotResponse]:
    """Get snapshots within time range.

    Args:
        start_time: Start timestamp
        end_time: End timestamp

    Returns:
        List of snapshots in range
    """
    history = get_analytics_history()
    snapshots = history.get_time_range(start_time, end_time)
    return [_snapshot_to_response(s) for s in snapshots]
