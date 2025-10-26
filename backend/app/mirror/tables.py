from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    JSON,
    MetaData,
    String,
    Table,
)

metadata = MetaData()

mirror_events = Table(
    "mirror_events",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("ts", DateTime(timezone=True), default=datetime.utcnow, nullable=False),
    Column("user_count", Integer, nullable=False, default=0),
    Column("tone", String(16), nullable=False),
    Column("intensity", Float, nullable=False),
    Column("intensity_bin", Integer, nullable=False),
    Column("reward", Float, nullable=False),
    Column("pre_coh", Float, nullable=False),
    Column("pre_ent", Float, nullable=False),
    Column("post_coh", Float, nullable=False),
    Column("post_ent", Float, nullable=False),
    Column("pre_pad", JSON, nullable=False),
    Column("post_pad", JSON, nullable=False),
    Column("dt_ms", Integer, nullable=False),
    Column("bucket_key", String(32), nullable=False),
)

policy_table = Table(
    "policy_table",
    metadata,
    Column("bucket_key", String(32), primary_key=True),
    Column("tone", String(16), primary_key=True),
    Column("intensity_bin", Integer, primary_key=True),
    Column("reward_avg", Float, nullable=False),
    Column("n", Integer, nullable=False),
    Column("updated_at", DateTime(timezone=True), default=datetime.utcnow, nullable=False),
)

Index("idx_mirror_ts", mirror_events.c.ts)
Index("idx_mirror_bucket", mirror_events.c.bucket_key)
Index("idx_policy_bucket", policy_table.c.bucket_key)
