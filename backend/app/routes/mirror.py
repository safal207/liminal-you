from __future__ import annotations

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from ..mirror import PolicyEntry, mirror_loop
from ..services.auth import get_current_user_optional

router = APIRouter()


class MirrorPolicyEntryModel(BaseModel):
    bucket_key: str
    tone: str
    intensity_bin: str
    reward_avg: float
    n: int
    avg_intensity: float
    updated_at: datetime | None

    @classmethod
    def from_entry(cls, entry: PolicyEntry) -> "MirrorPolicyEntryModel":
        return cls(
            bucket_key=entry.bucket_key,
            tone=entry.tone,
            intensity_bin=entry.intensity_bin,
            reward_avg=entry.reward_avg,
            n=entry.n,
            avg_intensity=entry.avg_intensity,
            updated_at=entry.updated_at,
        )


class MirrorPolicyResponse(BaseModel):
    bucket_key: str | None
    entries: List[MirrorPolicyEntryModel]


class MirrorEventModel(BaseModel):
    timestamp: str
    bucket_key: str
    delta_coherence: float
    delta_entropy: float
    reward: float
    tone: str
    intensity: float
    cause_text: str | None = None


class CausalSummaryModel(BaseModel):
    bucket_key: str
    hint: str
    count: int


class HintMetricModel(BaseModel):
    hint: str
    avg_delta_coherence: float
    avg_delta_entropy: float
    count: int


class MirrorStatsResponse(BaseModel):
    count: int
    avg_reward: float
    avg_delta_coherence: float
    avg_delta_entropy: float
    coverage: float
    buckets: List[str]
    events: List[MirrorEventModel]
    causal_summary: List[CausalSummaryModel]
    hint_metrics: List[HintMetricModel]


@router.get("/mirror/policy", response_model=MirrorPolicyResponse)
def get_mirror_policy(
    bucket_key: str | None = Query(default=None, description="Composite bucket identifier"),
    _: str | None = Depends(get_current_user_optional),
) -> MirrorPolicyResponse:
    entries = [MirrorPolicyEntryModel.from_entry(entry) for entry in mirror_loop.get_policy(bucket_key)]
    return MirrorPolicyResponse(bucket_key=bucket_key, entries=entries)


@router.get("/mirror/stats", response_model=MirrorStatsResponse)
def get_mirror_stats(
    from_ts: str | None = Query(default=None, alias="from"),
    to_ts: str | None = Query(default=None, alias="to"),
    _: str | None = Depends(get_current_user_optional),
) -> MirrorStatsResponse:
    start = _parse_iso(from_ts)
    end = _parse_iso(to_ts)
    stats = mirror_loop.get_stats(start=start, end=end)
    events = [MirrorEventModel(**event) for event in stats["events"]]
    causal_summary = [CausalSummaryModel(**entry) for entry in stats.get("causal_summary", [])]
    hint_metrics = [HintMetricModel(**entry) for entry in stats.get("hint_metrics", [])]
    return MirrorStatsResponse(
        count=stats["count"],
        avg_reward=stats["avg_reward"],
        avg_delta_coherence=stats["avg_delta_coherence"],
        avg_delta_entropy=stats["avg_delta_entropy"],
        coverage=stats["coverage"],
        buckets=list(stats["buckets"]),
        events=events,
        causal_summary=causal_summary,
        hint_metrics=hint_metrics,
    )


@router.post("/mirror/replay", status_code=status.HTTP_202_ACCEPTED)
def trigger_mirror_replay(
    _: str | None = Depends(get_current_user_optional),
) -> dict[str, str]:
    mirror_loop.rebuild_policy()
    return {"status": "replaying"}


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid datetime format: {value}") from exc
