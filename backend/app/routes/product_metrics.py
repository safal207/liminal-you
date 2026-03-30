"""Product metrics routes (North Star and funnel)."""

from fastapi import APIRouter
from pydantic import BaseModel

from ..product import get_product_metrics_tracker

router = APIRouter(prefix="/api/product", tags=["product"])


class PracticeCompletedRequest(BaseModel):
    user_id: str


@router.get("/wws")
def get_weekly_witnessed_sessions() -> dict:
    """Get current week North Star metric (Weekly Witnessed Sessions)."""
    tracker = get_product_metrics_tracker()
    return tracker.get_wws_summary()


@router.get("/funnel")
def get_product_funnel() -> dict:
    """Get simple product funnel from reflection to improved state."""
    tracker = get_product_metrics_tracker()
    return tracker.get_funnel()


@router.post("/practice-completed")
def mark_practice_completed(payload: PracticeCompletedRequest) -> dict:
    """Mark practice as completed for current user session."""
    tracker = get_product_metrics_tracker()
    completed = tracker.track_practice_completed(payload.user_id)
    return {"user_id": payload.user_id, "wws_completed": completed}
