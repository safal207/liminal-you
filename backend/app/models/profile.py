from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel

from .node import Node
from .user import User


class Profile(BaseModel):
    id: str
    name: str
    bio: str | None = None
    nodes: List[Dict[str, str]]
    reflections_count: int
    emotions: Dict[str, int]
    astro_opt_out: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "id": "user-001",
                "name": "Liminal Explorer",
                "bio": "Исследователь тонких состояний",
                "nodes": [{"id": "node-1", "label": "Созерцание"}],
                "reflections_count": 3,
                "emotions": {"радость": 5, "свет": 3},
                "astro_opt_out": False,
            }
        }


class ProfileSummary(BaseModel):
    user: User
    recent_nodes: List[Node]
    dominant_emotion: str
