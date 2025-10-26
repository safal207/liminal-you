from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ..mirror import get_mirror_loop
from ..mirror.utils import bin_to_intensity
from ..services.auth import get_current_user_optional

router = APIRouter()


class MirrorEventModel(BaseModel):
    id: int | None = Field(default=None)
    ts: datetime
    tone: str
    intensity: float
    reward: float
    delta_coherence: float
    delta_entropy: float
    bucket_key: str
    intensity_bin: int
    user_count: int
    dt_ms: int


class MirrorSummaryModel(BaseModel):
    total_events: int
    avg_reward: float
    coverage: float


class MirrorActionModel(BaseModel):
    tone: str
    intensity: float


class MirrorContextModel(BaseModel):
    bucket_key: str | None = None
    policy_source: str | None = None
    action: MirrorActionModel | None = None


class MirrorStatsResponse(BaseModel):
    events: List[MirrorEventModel]
    summary: MirrorSummaryModel
    current: MirrorContextModel | None = None


class PolicyEntryModel(BaseModel):
    bucket_key: str
    tone: str
    intensity_bin: int
    reward_avg: float
    n: int
    updated_at: datetime
    intensity: float = Field(..., description="Representative intensity for the bin")


class MirrorPolicyResponse(BaseModel):
    bucket_key: str | None
    entries: List[PolicyEntryModel]
    best: PolicyEntryModel | None


@router.get("/mirror/stats", response_model=MirrorStatsResponse)
async def get_mirror_stats(
    from_dt: datetime | None = Query(None, alias="from"),
    to_dt: datetime | None = Query(None, alias="to"),
    limit: int = Query(200, ge=1, le=1000),
):
    loop = get_mirror_loop()
    repository = loop.repository
    episodes = await repository.fetch_events(start=from_dt, end=to_dt, limit=limit)

    events: List[MirrorEventModel] = []
    total_reward = 0.0
    for episode in episodes:
        delta_coh = episode.post_coh - episode.pre_coh
        delta_ent = episode.post_ent - episode.pre_ent
        total_reward += episode.reward
        events.append(
            MirrorEventModel(
                id=getattr(episode, "id", None),
                ts=episode.ts,
                tone=episode.tone,
                intensity=episode.intensity,
                reward=episode.reward,
                delta_coherence=delta_coh,
                delta_entropy=delta_ent,
                bucket_key=episode.bucket_key,
                intensity_bin=episode.intensity_bin,
                user_count=episode.user_count,
                dt_ms=episode.dt_ms,
            )
        )

    coverage_value = 0.0
    if events:
        bucket_count = await repository.count_distinct_buckets()
        coverage_value = min(1.0, (bucket_count or 0) / max(1, len(events)))

    summary = MirrorSummaryModel(
        total_events=len(events),
        avg_reward=total_reward / len(events) if events else 0.0,
        coverage=coverage_value,
    )

    raw_context = await loop.current_context()
    context = None
    if raw_context:
        action = raw_context.get("action")
        context = MirrorContextModel(
            bucket_key=raw_context.get("bucket_key"),
            policy_source=raw_context.get("policy_source"),
            action=MirrorActionModel(**action) if isinstance(action, dict) else None,
        )

    return MirrorStatsResponse(events=events, summary=summary, current=context)


@router.get("/mirror/policy", response_model=MirrorPolicyResponse)
async def get_mirror_policy(bucket_key: str | None = None) -> MirrorPolicyResponse:
    loop = get_mirror_loop()
    repository = loop.repository
    rows = await repository.fetch_policies(bucket_key)
    entries = [
        PolicyEntryModel(
            bucket_key=row.bucket_key,
            tone=row.tone,
            intensity_bin=row.intensity_bin,
            reward_avg=row.reward_avg,
            n=row.n,
            updated_at=row.updated_at,
            intensity=bin_to_intensity(row.intensity_bin),
        )
        for row in rows
    ]
    best = entries[0] if entries else None
    return MirrorPolicyResponse(bucket_key=bucket_key, entries=entries, best=best)


@router.post("/mirror/replay", status_code=status.HTTP_202_ACCEPTED)
async def trigger_mirror_replay(user: str | None = Depends(get_current_user_optional)) -> dict:
    if user != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Только администратор может перезапустить обучение")
    loop = get_mirror_loop()
    await loop.run_learning_cycle()
    return {"status": "replaying", "updated_at": datetime.now(timezone.utc)}
