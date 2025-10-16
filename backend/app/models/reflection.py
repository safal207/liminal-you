from __future__ import annotations

from pydantic import BaseModel, Field


class Reflection(BaseModel):
    id: str
    author: str
    content: str = Field(..., description="Text of the reflection")
    emotion: str = Field(..., description="Emotion tag associated with the reflection")


class ReflectionCreate(BaseModel):
    from_node: str
    to_user: str
    message: str
    emotion: str
