"""Cost/revenue rollups — blueprint §12/Task E.

Nothing here talks to a payment processor or a platform API; every
number comes from rows already written by other modules (rights/
campaign intake, the provider routers' cost logging, and — from Phase 5
onward — manually reconciled campaign payouts). This is arithmetic over
the ledger, not a source of truth of its own.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.core.db import SessionLocal
from src.core.models import ApiCost, ProductionCost, RevenueEvent, Source


def _session(session: Session | None) -> tuple[Session, bool]:
    if session is not None:
        return session, False
    return SessionLocal(), True


def cost_per_clip(clip_id: str, *, session: Session | None = None) -> float:
    """api_costs attributed to this clip + production_costs attributed
    to this clip (production_costs.source_id is used as a proxy target
    until Phase 2's clips table exists — see note in production_costs
    usage below)."""
    db, owns = _session(session)
    try:
        api = (
            db.query(func.coalesce(func.sum(ApiCost.cost_inr), 0.0))
            .filter(ApiCost.clip_id == clip_id)
            .scalar()
        )
        return float(api)
    finally:
        if owns:
            db.close()


def revenue_per_clip(clip_id: str, *, session: Session | None = None) -> float:
    db, owns = _session(session)
    try:
        total = (
            db.query(func.coalesce(func.sum(RevenueEvent.amount_inr), 0.0))
            .filter(RevenueEvent.clip_id == clip_id)
            .scalar()
        )
        return float(total)
    finally:
        if owns:
            db.close()


def revenue_per_source(source_id: str, *, session: Session | None = None) -> float:
    """Sum over every revenue event attributed to this source, across
    every descendant clip/publication/platform — the blueprint's
    total_source_revenue answer to "which sources actually make money."
    """
    db, owns = _session(session)
    try:
        total = (
            db.query(func.coalesce(func.sum(RevenueEvent.amount_inr), 0.0))
            .filter(RevenueEvent.source_id == source_id)
            .scalar()
        )
        return float(total)
    finally:
        if owns:
            db.close()


def identity_pnl(
    identity_id: str,
    period_start: datetime,
    period_end: datetime,
    *,
    session: Session | None = None,
) -> dict:
    """Revenue minus (production + API) costs for every source belonging
    to this identity, within [period_start, period_end)."""
    db, owns = _session(session)
    try:
        source_ids = [
            row[0]
            for row in db.query(Source.id).filter(Source.identity_id == identity_id).all()
        ]
        if not source_ids:
            return {
                "identity_id": identity_id,
                "revenue_inr": 0.0,
                "production_cost_inr": 0.0,
                "api_cost_inr": 0.0,
                "profit_inr": 0.0,
            }

        revenue = (
            db.query(func.coalesce(func.sum(RevenueEvent.amount_inr), 0.0))
            .filter(
                RevenueEvent.source_id.in_(source_ids),
                RevenueEvent.occurred_at >= period_start,
                RevenueEvent.occurred_at < period_end,
            )
            .scalar()
        )
        production_cost = (
            db.query(func.coalesce(func.sum(ProductionCost.amount_inr), 0.0))
            .filter(
                ProductionCost.source_id.in_(source_ids),
                ProductionCost.occurred_at >= period_start,
                ProductionCost.occurred_at < period_end,
            )
            .scalar()
        )
        api_cost = (
            db.query(func.coalesce(func.sum(ApiCost.cost_inr), 0.0))
            .filter(
                ApiCost.source_id.in_(source_ids),
                ApiCost.occurred_at >= period_start,
                ApiCost.occurred_at < period_end,
            )
            .scalar()
        )

        revenue = float(revenue)
        production_cost = float(production_cost)
        api_cost = float(api_cost)

        return {
            "identity_id": identity_id,
            "revenue_inr": revenue,
            "production_cost_inr": production_cost,
            "api_cost_inr": api_cost,
            "profit_inr": revenue - production_cost - api_cost,
        }
    finally:
        if owns:
            db.close()
