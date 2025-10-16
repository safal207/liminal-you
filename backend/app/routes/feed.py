from typing import List

from fastapi import APIRouter, Depends

from ..models.reflection import Reflection
from ..services.auth import get_current_user_optional

router = APIRouter()


# In-memory feed storage for bootstrap purposes.
_FEED: List[Reflection] = [
    Reflection(id="r1", author="user-001", content="Свет в тебе отражается во мне", emotion="радость"),
    Reflection(id="r2", author="user-002", content="Дыши синхронно с ночным небом", emotion="спокойствие"),
]


@router.get("/feed", response_model=List[Reflection])
def get_feed(_: str | None = Depends(get_current_user_optional)) -> List[Reflection]:
    """Return the latest reflections from the collective feed."""
    return _FEED
