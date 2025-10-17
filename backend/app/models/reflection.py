from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field, field_validator


class Reflection(BaseModel):
    id: str
    author: str
    content: str = Field(..., description="Text of the reflection")
    emotion: str = Field(..., description="Emotion tag associated with the reflection")
    pad: List[float] | None = Field(
        default=None,
        description="Optional PAD vector [Pleasure, Arousal, Dominance]",
    )


class ReflectionCreate(BaseModel):
    from_node: str
    to_user: str
    message: str
    emotion: str
    pad: List[float] | None = Field(
        default=None,
        description="Optional PAD vector [Pleasure, Arousal, Dominance]",
    )

    @field_validator("pad")
    @classmethod
    def _validate_pad(cls, value: List[float] | None) -> List[float] | None:
        if value is None:
            return None
        if len(value) != 3:
            raise ValueError("PAD vector must contain exactly three values")
        return value
