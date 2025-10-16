from fastapi import APIRouter, Depends, HTTPException

from ..models.profile import Profile
from ..services.auth import get_current_user_optional

router = APIRouter()


_SAMPLE_PROFILE = Profile(
    id="user-001",
    name="Liminal Explorer",
    bio="Исследователь тонких состояний и резонансов",
    nodes=[
        {"id": "node-1", "label": "Созерцание"},
        {"id": "node-2", "label": "Синхронизация"},
    ],
    reflections_count=3,
    emotions={
        "радость": 5,
        "свет": 3,
        "спокойствие": 4,
    },
)


@router.get("/profile/{profile_id}", response_model=Profile)
def get_profile(profile_id: str, user: str | None = Depends(get_current_user_optional)) -> Profile:
    if user and user != profile_id:
        # Simple bootstrap access rule; real impl would query DB with authz.
        raise HTTPException(status_code=403, detail="Accessing another profile is restricted in MVP")

    if profile_id != _SAMPLE_PROFILE.id:
        raise HTTPException(status_code=404, detail="Profile not found")

    return _SAMPLE_PROFILE
