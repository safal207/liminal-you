import time
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request, status

from ..models.reflection import Reflection, ReflectionCreate
from ..config import settings
from ..services.auth import get_current_user_optional
from ..feedback import feedback_hub
from ..services.preferences import get_astro_opt_out
from ..astro import map_label_to_pad

router = APIRouter()

_LAST_INTEGRATION: Dict[str, float] = {}
_RATE_LIMIT_SECONDS = 3.0


@router.post("/reflection", response_model=Reflection, status_code=status.HTTP_201_CREATED)
async def create_reflection(
    payload: ReflectionCreate,
    request: Request,
    user: str | None = Depends(get_current_user_optional),
) -> Reflection:
    """Create a new reflection addressed to a user."""
    if payload.message.strip() == "":
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Use LiminalDB storage if enabled, otherwise fallback to memory storage
    if settings.liminaldb_enabled and hasattr(request.app.state, "storage"):
        reflection = await request.app.state.storage.add_reflection(payload, author=user or payload.from_node)
    else:
        # Fallback to memory storage
        from ..services import storage
        reflection = storage.add_reflection(payload, author=user or payload.from_node)

    await feedback_hub.publish({"event": "new_reflection", "data": reflection.model_dump()})

    author = reflection.author
    now = time.time()
    rate_limited = now - _LAST_INTEGRATION.get(author, 0.0) < _RATE_LIMIT_SECONDS
    opted_out = get_astro_opt_out(author)

    if not rate_limited and not opted_out:
        pad_vec = payload.pad or map_label_to_pad(payload.emotion)
        await feedback_hub.integrate_field(pad_vec)
        _LAST_INTEGRATION[author] = now

    return reflection


@router.get("/reflection", response_model=List[Reflection])
async def list_reflections(
    request: Request,
    _: str | None = Depends(get_current_user_optional)
) -> List[Reflection]:
    """Return all stored reflections."""
    if settings.liminaldb_enabled and hasattr(request.app.state, "storage"):
        return await request.app.state.storage.list_reflections()
    else:
        from ..services import storage
        return storage.list_reflections()
