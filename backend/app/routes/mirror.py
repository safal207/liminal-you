from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, Field

from ..config import settings
from ..services.auth import get_current_user_optional
from ..mirror import mirror_manager
from ..mirror.storage import get_repository

router = APIRouter()


class PolicyEntry(BaseModel):
    bucket_key: str
    tone: str
    intensity_bin: int
    reward_avg: float
    n: int
    updated_at: datetime


class MirrorStatsResponse(BaseModel):
    total_events: int
    avg_reward: float
    bucket_coverage: float = Field(..., description="Fraction of explored buckets (0-1)")
    unique_buckets: int
    recent_events: List[dict]
    heatmap: List[dict]
    current_policy: Optional[PolicyEntry] = None


def _require_admin(token: Optional[str]) -> None:
    expected = settings.jwt_secret  # simple bootstrap safeguard
    if token and token == expected:
        return
    if expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недостаточно прав")


@router.post("/mirror/replay", status_code=202)
async def trigger_mirror_learning(
    token: Optional[str] = Header(default=None, alias="X-Mirror-Token"),
    user: str | None = Depends(get_current_user_optional),
) -> dict[str, str]:
    _require_admin(token)
    await mirror_manager.run_learning_cycle()
    return {"status": "ok"}


@router.get("/mirror/policy", response_model=List[PolicyEntry])
async def get_mirror_policy(bucket_key: Optional[str] = Query(default=None)) -> List[PolicyEntry]:
    entries = [
        PolicyEntry(
            bucket_key=entry.bucket_key,
            tone=entry.tone,
            intensity_bin=int(entry.intensity_bin),
            reward_avg=float(entry.reward_avg),
            n=int(entry.n),
            updated_at=entry.updated_at,
        )
        for entry in await get_repository().get_policy_entries(bucket_key)
    ]
    return entries


@router.get("/mirror/stats", response_model=MirrorStatsResponse)
async def get_mirror_stats() -> MirrorStatsResponse:
    repository = get_repository()
    stats = await repository.stats()
    heatmap = await repository.heatmap()
    snapshot = await mirror_manager.current_policy_snapshot()
    current_policy = (
        PolicyEntry(
            bucket_key=snapshot.bucket_key,
            tone=snapshot.tone,
            intensity_bin=snapshot.intensity_bin,
            reward_avg=snapshot.reward_avg,
            n=snapshot.n,
            updated_at=snapshot.updated_at,
        )
        if snapshot
        else None
    )
    return MirrorStatsResponse(
        total_events=stats["total_events"],
        avg_reward=float(stats["avg_reward"]),
        bucket_coverage=float(stats["bucket_coverage"]),
        unique_buckets=int(stats["unique_buckets"]),
        recent_events=stats["recent_events"],
        heatmap=heatmap,
        current_policy=current_policy,
    )
