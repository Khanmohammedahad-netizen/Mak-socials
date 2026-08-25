"""SQLAlchemy models for the Phase 1+ schema (blueprint §12).

None of this is read by the existing engine/*.py pipeline yet — that
pipeline has no database (docs/AUDIT.md §7). These tables exist so the
rights gate, campaign scorer, and cost/revenue ledgers have somewhere
real to write, ahead of the clip engine (Phase 2) that will actually
populate `clips`.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Identity(Base):
    __tablename__ = "identities"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String, nullable=False)
    niche: Mapped[str | None] = mapped_column(String)
    caption_style_set: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    cover_layout: Mapped[str | None] = mapped_column(String)
    voice_id: Mapped[str | None] = mapped_column(String)
    music_bed_set: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    posting_rhythm: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String, default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class PlatformAccount(Base):
    __tablename__ = "platform_accounts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    identity_id: Mapped[str] = mapped_column(ForeignKey("identities.id"), nullable=False)
    platform: Mapped[str] = mapped_column(String, nullable=False)  # youtube|instagram|facebook
    external_id: Mapped[str | None] = mapped_column(String)
    page_id: Mapped[str | None] = mapped_column(String)
    token_ref: Mapped[str | None] = mapped_column(String)  # reference only, never the token
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    follower_count: Mapped[int | None] = mapped_column(Integer)
    monetization_status: Mapped[str | None] = mapped_column(String)


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    platform: Mapped[str] = mapped_column(String, nullable=False)
    brand: Mapped[str] = mapped_column(String, nullable=False)
    rate_per_1k: Mapped[float] = mapped_column(Float, nullable=False)
    pool_size: Mapped[float] = mapped_column(Float, nullable=False)
    pool_remaining: Mapped[float] = mapped_column(Float, nullable=False)
    launched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    platforms: Mapped[list[Any] | None] = mapped_column(JSON)
    brief_url: Mapped[str | None] = mapped_column(String)
    brief_text: Mapped[str | None] = mapped_column(Text)
    required_tags: Mapped[list[Any] | None] = mapped_column(JSON)
    banned_claims: Mapped[list[Any] | None] = mapped_column(JSON)
    per_clip_cap: Mapped[float | None] = mapped_column(Float)
    score: Mapped[float | None] = mapped_column(Float)
    effective_rate: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String, default="ACTIVE")
    # BLACKLISTED brands (entry-fee scam gate) — status carries this; brand
    # name is what future intake checks against, not campaign id.

    __table_args__ = (Index("ix_campaigns_status_pool_remaining", "status", "pool_remaining"),)


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    identity_id: Mapped[str | None] = mapped_column(ForeignKey("identities.id"))
    kind: Mapped[str] = mapped_column(String, nullable=False)  # CAMPAIGN|OWNED_RECORDING|LICENSED
    title: Mapped[str | None] = mapped_column(String)
    path: Mapped[str | None] = mapped_column(String)
    duration_s: Mapped[float | None] = mapped_column(Float)
    campaign_id: Mapped[str | None] = mapped_column(ForeignKey("campaigns.id"))
    transcript_cached: Mapped[bool] = mapped_column(Boolean, default=False)
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class RightsRecord(Base):
    __tablename__ = "rights_records"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    source_id: Mapped[str] = mapped_column(ForeignKey("sources.id"), nullable=False)
    # CAMPAIGN|OWNED|LICENSED_CC|LICENSED_PAID|WRITTEN_PERMISSION
    basis: Mapped[str] = mapped_column(String, nullable=False)
    evidence_path: Mapped[str] = mapped_column(String, nullable=False)
    granted_by: Mapped[str | None] = mapped_column(String)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    restrictions: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class RevenueEvent(Base):
    __tablename__ = "revenue_events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    # CAMPAIGN_PAYOUT|FB_CMP|YT_SHORTS|AFFILIATE|PRODUCT|LEAD
    kind: Mapped[str] = mapped_column(String, nullable=False)
    publication_id: Mapped[str | None] = mapped_column(String)
    clip_id: Mapped[str | None] = mapped_column(String)
    source_id: Mapped[str | None] = mapped_column(ForeignKey("sources.id"))
    amount_inr: Mapped[float] = mapped_column(Float, nullable=False)
    currency_orig: Mapped[str | None] = mapped_column(String)
    amount_orig: Mapped[float | None] = mapped_column(Float)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    __table_args__ = (Index("ix_revenue_events_clip_id_occurred_at", "clip_id", "occurred_at"),)


class ProductionCost(Base):
    __tablename__ = "production_costs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    source_id: Mapped[str | None] = mapped_column(ForeignKey("sources.id"))
    kind: Mapped[str] = mapped_column(String, nullable=False)
    amount_inr: Mapped[float] = mapped_column(Float, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class ApiCost(Base):
    __tablename__ = "api_costs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    task_class: Mapped[str] = mapped_column(String, nullable=False)
    source_id: Mapped[str | None] = mapped_column(String)
    clip_id: Mapped[str | None] = mapped_column(String)
    tokens_in: Mapped[int | None] = mapped_column(Integer)
    tokens_out: Mapped[int | None] = mapped_column(Integer)
    cost_inr: Mapped[float] = mapped_column(Float, default=0.0)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class AffiliateLink(Base):
    __tablename__ = "affiliate_links"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    clip_id: Mapped[str | None] = mapped_column(String)
    program: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    short_url: Mapped[str | None] = mapped_column(String)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    conversions: Mapped[int] = mapped_column(Integer, default=0)
    commission_inr: Mapped[float] = mapped_column(Float, default=0.0)


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    source_publication_id: Mapped[str | None] = mapped_column(String)
    source_id: Mapped[str | None] = mapped_column(ForeignKey("sources.id"))
    channel_source: Mapped[str | None] = mapped_column(String)
    contact_ref: Mapped[str | None] = mapped_column(String)
    stage: Mapped[str] = mapped_column(String, default="NEW")
    deal_value_inr: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
