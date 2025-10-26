from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..models.profile import Profile
from ..services.auth import get_current_user_optional
from ..services.preferences import (
    get_astro_opt_out,
    get_feedback_enabled,
    get_mirror_enabled,
    set_astro_opt_out,
    set_feedback_enabled,
    set_mirror_enabled,
)

router = APIRouter()


_SAMPLE_PROFILE_DATA = {
    "id": "user-001",
    "name": "Liminal Explorer",
    "bio": "Исследователь тонких состояний и резонансов",
    "nodes": [
        {"id": "node-1", "label": "Созерцание"},
        {"id": "node-2", "label": "Синхронизация"},
    ],
    "reflections_count": 3,
    "emotions": {
        "радость": 5,
        "свет": 3,
        "спокойствие": 4,
    },
    "astro_opt_out": False,
    "feedback_enabled": True,
    "mirror_enabled": True,
}


class AstroOptPayload(BaseModel):
    astro_opt_out: bool


def _build_profile(profile_id: str) -> Profile:
    return Profile(
        **{
            **_SAMPLE_PROFILE_DATA,
            "astro_opt_out": get_astro_opt_out(profile_id),
            "feedback_enabled": get_feedback_enabled(profile_id),
            "mirror_enabled": get_mirror_enabled(profile_id),
        }
    )


class ProfileSettingsPayload(BaseModel):
    feedback_enabled: bool | None = None
    mirror_enabled: bool | None = None


@router.get("/profile/{profile_id}", response_model=Profile)
def get_profile(profile_id: str, user: str | None = Depends(get_current_user_optional)) -> Profile:
    if user and user != profile_id:
        # Simple bootstrap access rule; real impl would query DB with authz.
        raise HTTPException(status_code=403, detail="Accessing another profile is restricted in MVP")

    if profile_id != _SAMPLE_PROFILE_DATA["id"]:
        raise HTTPException(status_code=404, detail="Profile not found")

    return _build_profile(profile_id)


@router.patch("/profile/{profile_id}/astro", response_model=Profile)
def set_profile_astro_opt_out(
    profile_id: str,
    payload: AstroOptPayload,
    user: str | None = Depends(get_current_user_optional),
) -> Profile:
    if user and user != profile_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Измени настройки в своём профиле")

    if profile_id != _SAMPLE_PROFILE_DATA["id"]:
        raise HTTPException(status_code=404, detail="Profile not found")

    set_astro_opt_out(profile_id, payload.astro_opt_out)
    return _build_profile(profile_id)


@router.patch("/profile/{profile_id}/settings", response_model=Profile)
def update_profile_settings(
    profile_id: str,
    payload: ProfileSettingsPayload,
    user: str | None = Depends(get_current_user_optional),
) -> Profile:
    if user and user != profile_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Измени настройки в своём профиле",
        )

    if profile_id != _SAMPLE_PROFILE_DATA["id"]:
        raise HTTPException(status_code=404, detail="Profile not found")

    if payload.feedback_enabled is None and payload.mirror_enabled is None:
        raise HTTPException(status_code=400, detail="Нет обновляемых настроек")

    if payload.feedback_enabled is not None:
        set_feedback_enabled(profile_id, payload.feedback_enabled)

    if payload.mirror_enabled is not None:
        set_mirror_enabled(profile_id, payload.mirror_enabled)
    return _build_profile(profile_id)
