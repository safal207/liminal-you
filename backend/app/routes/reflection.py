import time
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request, status

from ..models.reflection import Reflection, ReflectionCreate
from ..config import settings
from ..services.auth import get_current_user_optional
from ..feedback import feedback_hub
from ..services.preferences import get_astro_opt_out
from ..astro import map_label_to_pad
from ..witness import WitnessTracker

router = APIRouter()

_LAST_INTEGRATION: Dict[str, float] = {}
_RATE_LIMIT_SECONDS = 3.0

# Global witness tracker
_witness_tracker: WitnessTracker | None = None


def get_witness_tracker() -> WitnessTracker:
    """Get global witness tracker instance."""
    global _witness_tracker
    if _witness_tracker is None:
        _witness_tracker = WitnessTracker()
    return _witness_tracker


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
        state = await feedback_hub.integrate_field(pad_vec)
        _LAST_INTEGRATION[author] = now

        # Track witness metrics
        try:
            tracker = get_witness_tracker()
            witness_snapshot = tracker.track_action(
                user_id=author,
                pad_vec=pad_vec,
                coherence=state.get("coherence", 0.0),
                entropy=state.get("entropy", 0.0),
            )

            # Broadcast witness update via WebSocket
            await feedback_hub.publish({
                "event": "witness_update",
                "data": {
                    "user_id": author,
                    "presence_score": witness_snapshot.presence_score,
                    "attention_quality": witness_snapshot.attention_quality,
                    "state": witness_snapshot.state.value,
                    "message": _get_witness_message(witness_snapshot.state.value),
                }
            })
        except Exception as e:
            # Don't fail reflection creation if witness tracking fails
            import logging
            logging.getLogger(__name__).warning(f"Failed to track witness metrics: {e}")

    return reflection


def _get_witness_message(state: str) -> str:
    """Get human-readable message for witness state."""
    messages = {
        "scattered": "Внимание рассеяно. Возможно, время для паузы?",
        "present": "Присутствие ощущается. Продолжай наблюдение.",
        "witnessing": "Глубокое присутствие. Свидетель проявлен. 🌟",
    }
    return messages.get(state, "Наблюдаем...")


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
