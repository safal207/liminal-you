from __future__ import annotations

from pydantic import BaseModel


class Node(BaseModel):
    id: str
    label: str
    description: str | None = None
