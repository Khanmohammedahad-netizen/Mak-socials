from datetime import datetime, timedelta, timezone

from src.core.models import ApiCost, ProductionCost, RevenueEvent, Source
from src.monetization.roi import cost_per_clip, identity_pnl, revenue_per_clip, revenue_per_source


def test_cost_per_clip_sums_api_costs_for_that_clip(db_session):
    db_session.add_all([
        ApiCost(provider="ollama", task_class="SCRIPT", clip_id="clip-1", cost_inr=0.0),
        ApiCost(provider="anthropic", task_class="SCORING", clip_id="clip-1", cost_inr=12.5),
        ApiCost(provider="anthropic", task_class="SCORING", clip_id="clip-2", cost_inr=99.0),
    ])
    db_session.flush()

    assert cost_per_clip("clip-1", session=db_session) == 12.5
    assert cost_per_clip("clip-nonexistent", session=db_session) == 0.0


def test_revenue_per_clip_sums_revenue_events(db_session):
    db_session.add_all([
        RevenueEvent(kind="CAMPAIGN_PAYOUT", clip_id="clip-1", amount_inr=1000),
        RevenueEvent(kind="FB_CMP", clip_id="clip-1", amount_inr=500),
        RevenueEvent(kind="YT_SHORTS", clip_id="clip-2", amount_inr=1),
    ])
    db_session.flush()

    assert revenue_per_clip("clip-1", session=db_session) == 1500
    assert revenue_per_clip("clip-2", session=db_session) == 1


def test_revenue_per_source_rolls_up_all_descendant_platforms(db_session):
    """A clip that flops on one platform but earns elsewhere is a
    winner at the source level — blueprint §9.2."""
    db_session.add_all([
        RevenueEvent(kind="CAMPAIGN_PAYOUT", source_id="src-1", amount_inr=2000),
        RevenueEvent(kind="LEAD", source_id="src-1", amount_inr=50000),
        RevenueEvent(kind="YT_SHORTS", source_id="src-1", amount_inr=0),
    ])
    db_session.flush()

    assert revenue_per_source("src-1", session=db_session) == 52000


def test_identity_pnl_computes_profit_within_period(db_session):
    identity_id = "id-1"
    source = Source(id="src-1", identity_id=identity_id, kind="OWNED_RECORDING")
    db_session.add(source)
    db_session.flush()

    now = datetime.now(timezone.utc)
    in_period = now - timedelta(days=1)
    out_of_period = now - timedelta(days=40)

    db_session.add_all([
        RevenueEvent(kind="FB_CMP", source_id="src-1", amount_inr=10000, occurred_at=in_period),
        RevenueEvent(kind="FB_CMP", source_id="src-1", amount_inr=99999, occurred_at=out_of_period),
        ProductionCost(source_id="src-1", kind="music", amount_inr=500, occurred_at=in_period),
        ApiCost(provider="ollama", task_class="SCRIPT", source_id="src-1", cost_inr=200, occurred_at=in_period),
    ])
    db_session.flush()

    result = identity_pnl(
        identity_id, now - timedelta(days=30), now, session=db_session
    )

    assert result["revenue_inr"] == 10000
    assert result["production_cost_inr"] == 500
    assert result["api_cost_inr"] == 200
    assert result["profit_inr"] == 10000 - 500 - 200


def test_identity_pnl_with_no_sources_returns_zeros(db_session):
    now = datetime.now(timezone.utc)
    result = identity_pnl("nonexistent-identity", now - timedelta(days=30), now, session=db_session)
    assert result["revenue_inr"] == 0.0
    assert result["profit_inr"] == 0.0
