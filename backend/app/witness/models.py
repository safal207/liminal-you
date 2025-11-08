"""Data models for witness tracking."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class WitnessState(str, Enum):
    """The state of presence/awareness."""

    SCATTERED = "scattered"  # Рассеянное внимание, автопилот
    PRESENT = "present"      # Присутствие, осознанность
    WITNESSING = "witnessing"  # Чистое наблюдение, метаосознанность


@dataclass
class WitnessSnapshot:
    """A snapshot of witness metrics at a point in time.

    Represents the quality of presence and attention for a user
    at a specific moment.

    Attributes:
        timestamp: When this snapshot was taken
        user_id: User identifier
        presence_score: Overall presence quality (0.0-1.0)
        attention_quality: Quality of attention/focus (0.0-1.0)
        state: Current witness state (scattered/present/witnessing)
        action_interval: Seconds since last action (reflection/interaction)
        emotional_variance: Stability of emotions in recent window (0.0-1.0)
        coherence: Field coherence at this moment (0.0-1.0)
        entropy: Field entropy at this moment (0.0-1.0)
        metadata: Additional context (optional)
    """

    timestamp: datetime
    user_id: str
    presence_score: float
    attention_quality: float
    state: WitnessState
    action_interval: float
    emotional_variance: float
    coherence: float
    entropy: float
    metadata: Optional[dict] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "presence_score": round(self.presence_score, 3),
            "attention_quality": round(self.attention_quality, 3),
            "state": self.state.value,
            "action_interval": round(self.action_interval, 2),
            "emotional_variance": round(self.emotional_variance, 3),
            "coherence": round(self.coherence, 3),
            "entropy": round(self.entropy, 3),
            "metadata": self.metadata or {},
        }


@dataclass
class WitnessInsight:
    """Insights derived from witness history.

    Provides meaningful patterns and recommendations based on
    observed presence patterns.
    """

    user_id: str
    avg_presence_score: float
    dominant_state: WitnessState
    scattered_ratio: float  # Percentage of time in scattered state
    present_ratio: float
    witnessing_ratio: float
    trend: str  # "improving" | "declining" | "stable"
    recommendation: str  # Human-readable insight
    generated_at: datetime

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "user_id": self.user_id,
            "avg_presence_score": round(self.avg_presence_score, 3),
            "dominant_state": self.dominant_state.value,
            "state_distribution": {
                "scattered": round(self.scattered_ratio, 3),
                "present": round(self.present_ratio, 3),
                "witnessing": round(self.witnessing_ratio, 3),
            },
            "trend": self.trend,
            "recommendation": self.recommendation,
            "generated_at": self.generated_at.isoformat(),
        }
