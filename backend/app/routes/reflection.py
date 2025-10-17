import time
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, status

from ..models.reflection import Reflection, ReflectionCreate
from ..services import storage
from ..services.auth import get_current_user_optional
from ..resonance import resonance_hub
from ..services.preferences import get_astro_opt_out
from ..astro import map_label_to_pad
from .astro import field, push_field

router = APIRouter()

_LAST_INTEGRATION: Dict[str, float] = {}
_RATE_LIMIT_SECONDS = 3.0


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

    author = reflection.author
    now = time.time()
    rate_limited = now - _LAST_INTEGRATION.get(author, 0.0) < _RATE_LIMIT_SECONDS
    opted_out = get_astro_opt_out(author)

    if not rate_limited and not opted_out:
        pad_vec = payload.pad or map_label_to_pad(payload.emotion)
        state = field.integrate(pad_vec)
        await push_field(state)
        _LAST_INTEGRATION[author] = now

    return reflection


@router.get("/reflection", response_model=List[Reflection])
def list_reflections(_: str | None = Depends(get_current_user_optional)) -> List[Reflection]:
    """Return all stored reflections."""
    return storage.list_reflections()
