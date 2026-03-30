"""Product metrics routes (North Star and funnel)."""

from fastapi import APIRouter

from ..product import get_product_metrics_tracker

router = APIRouter(prefix="/api/product", tags=["product"])


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
