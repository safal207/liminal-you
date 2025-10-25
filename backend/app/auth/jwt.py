"""JWT authentication for liminal-you."""
from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Dict, Any

import jwt
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..config import settings

security = HTTPBearer()


def create_access_token(user_id: str, device_id: str | None = None, extra_claims: Dict[str, Any] | None = None) -> str:
    """Create JWT access token.

    Args:
        user_id: User identifier
        device_id: Device identifier (for Device Memory tracking)
        extra_claims: Additional claims to include in token

    Returns:
        Encoded JWT token
    """
    now = datetime.utcnow()
    expires = now + timedelta(hours=settings.jwt_expiration_hours)

    payload = {
        "sub": user_id,
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
        "type": "access",
    }

    if device_id:
        payload["device_id"] = device_id

    if extra_claims:
        payload.update(extra_claims)

    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate JWT access token.

    Args:
        token: JWT token string

    Returns:
        Decoded payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )

        # Validate token type
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
        )


async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict[str, Any]:
    """Get current authenticated user from JWT token.

    Args:
        credentials: HTTP authorization credentials

    Returns:
        User payload with user_id and device_id

    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user ID",
        )

    return {
        "user_id": user_id,
        "device_id": payload.get("device_id"),
        "iat": payload.get("iat"),
        "exp": payload.get("exp"),
    }


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Security(HTTPBearer(auto_error=False))
) -> Dict[str, Any] | None:
    """Get current user if authenticated, otherwise return None.

    Args:
        credentials: HTTP authorization credentials (optional)

    Returns:
        User payload or None
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
