from typing import List

from fastapi import APIRouter, Depends

from ..models.reflection import Reflection
from ..services import storage
from ..services.auth import get_current_user_optional

router = APIRouter()


@router.get("/feed", response_model=List[Reflection])
def get_feed(_: str | None = Depends(get_current_user_optional)) -> List[Reflection]:
    """Return the latest reflections from the collective feed."""
    return storage.list_reflections()
