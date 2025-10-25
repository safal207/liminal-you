"""Configuration for liminal-you backend."""
from __future__ import annotations

import os
from typing import Literal

from pydantic import BaseModel


class Settings(BaseModel):
    """Application settings."""

    # Database
    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_user: str = os.getenv("POSTGRES_USER", "liminal")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "youpass")
    postgres_db: str = os.getenv("POSTGRES_DB", "liminal_you")

    # LiminalDB
    liminaldb_enabled: bool = os.getenv("LIMINALDB_ENABLED", "true").lower() == "true"
    liminaldb_url: str = os.getenv("LIMINALDB_URL", "ws://localhost:8001")

    # Storage backend
    storage_backend: Literal["memory", "postgres", "liminaldb"] = os.getenv(
        "STORAGE_BACKEND", "liminaldb"
    )

    # JWT
    jwt_secret: str = os.getenv("JWT_SECRET", "liminal-you-secret-change-in-production")
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # Feedback
    feedback_enabled: bool = os.getenv("FEEDBACK_ENABLED", "true").lower() == "true"

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]


settings = Settings()
