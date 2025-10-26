"""Authentication routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from ..auth import create_access_token, get_device_memory
from ..auth.jwt import get_current_user as auth_dependency

router = APIRouter()


class LoginRequest(BaseModel):
    """Login request payload."""

    user_id: str
    password: str | None = None  # Optional for MVP


class LoginResponse(BaseModel):
    """Login response payload."""

    access_token: str
    token_type: str
    user_id: str
    device_id: str
    emotional_seed: list[float]


class DeviceInfoResponse(BaseModel):
    """Device information response."""

    device_id: str
    user_id: str
    interaction_count: int
    trust_level: float
    emotional_seed: list[float]
    resonance_map: dict[str, float] | None = None


@router.post("/auth/login", response_model=LoginResponse)
async def login(request: Request, payload: LoginRequest) -> LoginResponse:
    """Login and create JWT token with device tracking.

    Args:
        request: FastAPI request (for fingerprinting)
        payload: Login credentials

    Returns:
        Access token and device info
    """
    device_memory = get_device_memory()

    # Generate device ID from fingerprint
    user_agent = request.headers.get("user-agent", "unknown")
    client_ip = request.client.host if request.client else "0.0.0.0"

    device_id = device_memory.generate_device_id(
        user_agent=user_agent,
        ip=client_ip,
        user_id=payload.user_id,
    )

    # Register or update device
    device_profile = device_memory.register_device(
        device_id=device_id,
        user_id=payload.user_id,
        emotional_seed=[0.6, 0.4, 0.5],  # Initial calm state
        tags=["web", "liminal-you"],
    )

    # Create JWT token
    access_token = create_access_token(
        user_id=payload.user_id,
        device_id=device_id,
        extra_claims={
            "trust_level": device_profile.trust_level,
            "first_seen": device_profile.first_seen,
        },
    )

    return LoginResponse(
        access_token=access_token,
        token_type="Bearer",
        user_id=payload.user_id,
        device_id=device_id,
        emotional_seed=device_profile.emotional_seed,
    )


@router.get("/auth/device", response_model=DeviceInfoResponse)
async def get_device_info(user: dict = Depends(auth_dependency)) -> DeviceInfoResponse:
    """Get current device information.

    Args:
        user: Authenticated user from JWT

    Returns:
        Device profile with resonance map
    """
    device_memory = get_device_memory()
    device_id = user.get("device_id")

    if not device_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No device ID in token",
        )

    device_profile = device_memory.get_device(device_id)
    if not device_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    # Calculate resonance with other user's devices
    user_devices = device_memory.get_user_devices(device_profile.user_id)
    resonance_map = {}

    for other_device in user_devices:
        if other_device.device_id != device_id:
            resonance = device_memory.calculate_resonance(device_id, other_device.device_id)
            resonance_map[other_device.device_id] = round(resonance, 3)

    return DeviceInfoResponse(
        device_id=device_profile.device_id,
        user_id=device_profile.user_id,
        interaction_count=device_profile.interaction_count,
        trust_level=device_profile.trust_level,
        emotional_seed=device_profile.emotional_seed,
        resonance_map=resonance_map if resonance_map else None,
    )


@router.get("/auth/stats")
async def get_device_memory_stats() -> dict:
    """Get device memory statistics.

    Returns:
        Statistics about registered devices
    """
    device_memory = get_device_memory()
    return device_memory.get_stats()


@router.post("/auth/logout")
async def logout(user: dict = Depends(auth_dependency)) -> dict:
    """Logout (token blacklisting not implemented in MVP).

    Args:
        user: Authenticated user

    Returns:
        Success message
    """
    return {
        "message": "Logged out successfully",
        "user_id": user["user_id"],
    }
