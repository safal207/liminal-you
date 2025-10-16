from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from ..models.reflection import Reflection, ReflectionCreate
from ..services import storage
from ..services.auth import get_current_user_optional
from ..resonance import resonance_hub

router = APIRouter()


@router.post("/reflection", response_model=Reflection, status_code=status.HTTP_201_CREATED)
async def create_reflection(
    payload: ReflectionCreate,
    user: str | None = Depends(get_current_user_optional),
) -> Reflection:
    """Create a new reflection addressed to a user."""
    if payload.message.strip() == "":
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    reflection = storage.add_reflection(payload, author=user or payload.from_node)

    await resonance_hub.publish(
        {"event": "new_reflection", "data": reflection.model_dump()}
    )

    return reflection


@router.get("/reflection", response_model=List[Reflection])
def list_reflections(_: str | None = Depends(get_current_user_optional)) -> List[Reflection]:
    """Return all stored reflections."""
    return storage.list_reflections()
