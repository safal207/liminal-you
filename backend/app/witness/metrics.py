"""Metrics calculation for witness/presence tracking.

This module implements the core algorithm for measuring presence and
attention quality based on Buddhist principles of mindfulness.

Key concepts:
- Presence Score: Overall quality of "being here now" (0.0-1.0)
- Attention Quality: Focus vs scattered-ness (0.0-1.0)
- Witness State: scattered | present | witnessing

The algorithm considers:
1. Action intervals: Time between reflections/interactions
2. Emotional variance: Stability of emotional state
3. Coherence trend: Direction of field coherence
"""

from __future__ import annotations

import math
import statistics
from typing import Dict, List

from .models import WitnessState


class WitnessMetrics:
    """Calculates presence and attention quality metrics."""

    def __init__(
        self,
        scattered_threshold: float = 5.0,  # seconds
        witnessing_threshold: float = 30.0,  # seconds
    ):
        """Initialize metrics calculator.

        Args:
            scattered_threshold: Max interval (sec) before considered scattered
            witnessing_threshold: Min interval (sec) for witnessing state
        """
        self.scattered_threshold = scattered_threshold
        self.witnessing_threshold = witnessing_threshold

    def calculate_presence_score(
        self,
        action_intervals: List[float],
        emotional_variance: float,
        coherence_trend: float,
    ) -> Dict[str, any]:
        """Calculate overall presence score and state.

        Algorithm:
        1. Interval Score: Based on time between actions
           - Too quick (< 5s) = scattered (autopilot)
           - Moderate (5-30s) = present (mindful)
           - Long (> 30s) = witnessing (deep observation)

        2. Emotional Stability Score: Low variance = high presence
           - variance < 0.2 = stable (0.8-1.0)
           - variance > 0.5 = unstable (0.0-0.3)

        3. Coherence Contribution: Positive trend = improving presence
           - trend > 0.3 = strong positive (+0.2 bonus)
           - trend < -0.3 = strong negative (-0.2 penalty)

        4. Attention Quality: Focus measure
           - Based on interval consistency (low std = focused)

        Args:
            action_intervals: Recent intervals between actions (seconds)
            emotional_variance: Variance in PAD vector (0.0-1.0)
            coherence_trend: Change in coherence (-1.0 to 1.0)

        Returns:
            {
                'presence_score': float,  # 0.0-1.0
                'attention_quality': float,  # 0.0-1.0
                'state': WitnessState,  # scattered/present/witnessing
                'components': {
                    'interval_score': float,
                    'stability_score': float,
                    'coherence_bonus': float,
                }
            }
        """
        if not action_intervals:
            # No data yet - assume neutral
            return {
                "presence_score": 0.5,
                "attention_quality": 0.5,
                "state": WitnessState.PRESENT,
                "components": {
                    "interval_score": 0.5,
                    "stability_score": 0.5,
                    "coherence_bonus": 0.0,
                },
            }

        # 1. Interval Score
        avg_interval = statistics.mean(action_intervals)
        interval_score = self._score_from_interval(avg_interval)

        # 2. Emotional Stability Score
        stability_score = self._score_from_variance(emotional_variance)

        # 3. Coherence Contribution
        coherence_bonus = self._coherence_adjustment(coherence_trend)

        # 4. Attention Quality (from interval consistency)
        attention_quality = self._calculate_attention_quality(action_intervals)

        # Combined Presence Score
        base_score = (interval_score * 0.5) + (stability_score * 0.5)
        presence_score = max(0.0, min(1.0, base_score + coherence_bonus))

        # Determine State
        state = self._determine_state(avg_interval, presence_score)

        return {
            "presence_score": round(presence_score, 3),
            "attention_quality": round(attention_quality, 3),
            "state": state,
            "components": {
                "interval_score": round(interval_score, 3),
                "stability_score": round(stability_score, 3),
                "coherence_bonus": round(coherence_bonus, 3),
            },
        }

    def _score_from_interval(self, interval: float) -> float:
        """Convert interval to score (0.0-1.0).

        Interval zones:
        - 0-5s: Scattered (score 0.0-0.3)
        - 5-30s: Present (score 0.4-0.8)
        - 30+s: Witnessing (score 0.8-1.0)
        """
        if interval < self.scattered_threshold:
            # Scattered: autopilot mode
            # Linear: 0s=0.0, 5s=0.3
            return 0.3 * (interval / self.scattered_threshold)

        elif interval < self.witnessing_threshold:
            # Present: mindful engagement
            # Peak around 15-20 seconds
            normalized = (interval - self.scattered_threshold) / (
                self.witnessing_threshold - self.scattered_threshold
            )
            # Use sine curve for smooth transition
            return 0.3 + 0.5 * math.sin(normalized * math.pi / 2)

        else:
            # Witnessing: deep observation
            # Asymptotic approach to 1.0
            excess = interval - self.witnessing_threshold
            return 0.8 + 0.2 * (1.0 - math.exp(-excess / 60.0))

    def _score_from_variance(self, variance: float) -> float:
        """Convert emotional variance to stability score.

        Low variance = stable emotions = high presence
        High variance = chaotic emotions = low presence
        """
        # Invert: variance 0.0 -> score 1.0
        # variance 1.0 -> score 0.0
        return max(0.0, min(1.0, 1.0 - variance))

    def _coherence_adjustment(self, trend: float) -> float:
        """Calculate coherence-based bonus/penalty.

        Positive trend = presence improving
        Negative trend = presence declining
        """
        if trend > 0.3:
            # Strong positive: +0.2 bonus
            return 0.2 * min(1.0, trend / 0.5)
        elif trend < -0.3:
            # Strong negative: -0.2 penalty
            return -0.2 * min(1.0, abs(trend) / 0.5)
        else:
            # Neutral
            return 0.0

    def _calculate_attention_quality(self, intervals: List[float]) -> float:
        """Calculate attention quality from interval consistency.

        Low standard deviation = focused attention
        High standard deviation = scattered attention
        """
        if len(intervals) < 2:
            return 0.5  # Neutral

        std_dev = statistics.stdev(intervals)
        mean = statistics.mean(intervals)

        if mean == 0:
            return 0.5

        # Coefficient of variation
        cv = std_dev / mean

        # Low CV (< 0.3) = high quality
        # High CV (> 1.0) = low quality
        if cv < 0.3:
            return 0.8 + 0.2 * (1.0 - cv / 0.3)
        elif cv > 1.0:
            return max(0.0, 0.5 - 0.5 * ((cv - 1.0) / 2.0))
        else:
            # Linear interpolation
            return 0.5 + 0.3 * (1.0 - (cv - 0.3) / 0.7)

    def _determine_state(self, avg_interval: float, presence_score: float) -> WitnessState:
        """Determine witness state from interval and score.

        State decision matrix:
        - interval < 5s OR score < 0.3: SCATTERED
        - interval > 30s AND score > 0.7: WITNESSING
        - else: PRESENT
        """
        if avg_interval < self.scattered_threshold or presence_score < 0.3:
            return WitnessState.SCATTERED

        if avg_interval > self.witnessing_threshold and presence_score > 0.7:
            return WitnessState.WITNESSING

        return WitnessState.PRESENT
