from __future__ import annotations

from typing import List

from ..models.reflection import Reflection, ReflectionCreate

_REFLECTIONS: List[Reflection] = [
    Reflection(
        id="r1",
        author="node-alpha",
        content="Здесь пересекаются ветви твоей сети",
        emotion="вдохновение",
    )
]


def add_reflection(payload: ReflectionCreate, author: str | None = None) -> Reflection:
    new_reflection = Reflection(
        id=f"r{len(_REFLECTIONS) + 1}",
        author=author or payload.from_node,
        content=payload.message,
        emotion=payload.emotion,
        pad=payload.pad,
    )
    _REFLECTIONS.append(new_reflection)
    return new_reflection


def list_reflections() -> List[Reflection]:
    return list(_REFLECTIONS)
