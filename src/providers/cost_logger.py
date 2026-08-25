"""Every provider call writes an api_costs row. Non-negotiable (Task D).
Centralized here so routers call one function instead of each provider
re-implementing logging (and risking forgetting to)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from src.core.db import SessionLocal
from src.core.models import ApiCost


def log_api_cost(
    *,
    provider: str,
    task_class: str,
    source_id: str | None = None,
    clip_id: str | None = None,
    tokens_in: int | None = None,
    tokens_out: int | None = None,
    cost_inr: float = 0.0,
    session: Session | None = None,
) -> ApiCost:
    owns_session = session is None
    db = session or SessionLocal()
    try:
        row = ApiCost(
            provider=provider,
            task_class=task_class,
            source_id=source_id,
            clip_id=clip_id,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_inr=cost_inr,
        )
        db.add(row)
        db.flush()
        if owns_session:
            db.commit()
        return row
    finally:
        if owns_session:
            db.close()
