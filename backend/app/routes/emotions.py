"""Emotions API routes."""
from __future__ import annotations

from typing import Dict, List

from fastapi import APIRouter
from pydantic import BaseModel

from ..astro import _PAD_LABELS

router = APIRouter()


class EmotionInfo(BaseModel):
    """Emotion information with PAD values."""

    name: str
    pad: List[float]  # [Pleasure, Arousal, Dominance]
    category: str  # "positive", "negative", "neutral"


class EmotionsResponse(BaseModel):
    """Response with all available emotions."""

    total: int
    emotions: List[EmotionInfo]
    categories: Dict[str, int]


def categorize_emotion(pad: List[float]) -> str:
    """Categorize emotion by PAD values.

    Args:
        pad: [Pleasure, Arousal, Dominance]

    Returns:
        Category: "positive", "negative", or "neutral"
    """
    pleasure = pad[0]

    if pleasure >= 0.65:
        return "positive"
    elif pleasure <= 0.35:
        return "negative"
    else:
        return "neutral"


@router.get("/emotions", response_model=EmotionsResponse)
def list_emotions() -> EmotionsResponse:
    """Get all available emotions with PAD values.

    Returns:
        List of emotions with metadata
    """
    emotions: List[EmotionInfo] = []
    categories_count: Dict[str, int] = {"positive": 0, "negative": 0, "neutral": 0}

    for name, pad in _PAD_LABELS.items():
        category = categorize_emotion(pad)
        emotions.append(
            EmotionInfo(
                name=name,
                pad=pad,
                category=category,
            )
        )
        categories_count[category] += 1

    # Sort by category, then by pleasure (descending)
    emotions.sort(key=lambda e: (e.category != "positive", -e.pad[0]))

    return EmotionsResponse(
        total=len(emotions),
        emotions=emotions,
        categories=categories_count,
    )


@router.get("/emotions/{emotion_name}")
def get_emotion(emotion_name: str) -> EmotionInfo:
    """Get specific emotion by name.

    Args:
        emotion_name: Emotion name in Russian

    Returns:
        Emotion information

    Raises:
        404: If emotion not found
    """
    from fastapi import HTTPException, status

    emotion_name_lower = emotion_name.strip().lower()
    pad = _PAD_LABELS.get(emotion_name_lower)

    if not pad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Emotion '{emotion_name}' not found",
        )

    return EmotionInfo(
        name=emotion_name_lower,
        pad=pad,
        category=categorize_emotion(pad),
    )


@router.get("/emotions/suggest/{query}")
def suggest_emotions(query: str, limit: int = 5) -> List[EmotionInfo]:
    """Suggest emotions based on partial query.

    Args:
        query: Partial emotion name
        limit: Maximum number of suggestions

    Returns:
        List of matching emotions
    """
    query_lower = query.strip().lower()
    suggestions: List[EmotionInfo] = []

    for name, pad in _PAD_LABELS.items():
        if query_lower in name:
            suggestions.append(
                EmotionInfo(
                    name=name,
                    pad=pad,
                    category=categorize_emotion(pad),
                )
            )

    # Sort by relevance (exact match first, then by name length)
    suggestions.sort(key=lambda e: (e.name != query_lower, len(e.name)))

    return suggestions[:limit]
