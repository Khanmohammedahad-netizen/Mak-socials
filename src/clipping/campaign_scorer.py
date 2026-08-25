"""Campaign scorer — blueprint §4.1. Deterministic weighted formula, no
LLM involved (that's Phase 2's clip_scorer, a different thing entirely).

Three of the eight factors — clippability, brief_clarity,
payout_reliability — are human-scored 0-10 at manual intake time; the
blueprint describes them in terms only a person reading the brief can
judge. See config/scoring/campaign_weights.yaml for why.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import yaml

WEIGHTS_PATH = Path("config") / "scoring" / "campaign_weights.yaml"


def _load_weights() -> dict:
    with open(WEIGHTS_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@dataclass
class CampaignScoreInput:
    rate_per_1k: float
    pool_size: float
    pool_remaining: float
    launched_at: datetime
    platforms: list[str]
    per_clip_cap: float | None = None
    # human-judged at intake, each 0-10
    clippability_score: float = 5.0
    brief_clarity_score: float = 5.0
    payout_reliability_score: float = 5.0
    expected_approval_rate: float | None = None  # defaults from config if None
    required_claims_substantiable: bool = True
    entry_fee: bool = False
    projected_earnings_per_hour_inr: float | None = None  # None = gate not evaluated
    now: datetime | None = None


@dataclass
class CampaignScoreResult:
    total_score: float
    effective_rate: float
    factor_scores: dict[str, float]
    gates: dict[str, bool]
    verdict: str  # OK | REJECT | BLACKLIST | LOW_VALUE
    reasons: list[str] = field(default_factory=list)


def _linear_score(value: float, low: float, high: float) -> float:
    """0 at/below `low`, 10 at/above `high`, linear between. Handles a
    degenerate low==high by treating it as a step function."""
    if high <= low:
        return 10.0 if value >= high else 0.0
    frac = (value - low) / (high - low)
    return max(0.0, min(10.0, frac * 10.0))


def score_campaign(inp: CampaignScoreInput, weights: dict | None = None) -> CampaignScoreResult:
    w = weights or _load_weights()
    now = inp.now or datetime.now(timezone.utc)
    approval_rate = (
        inp.expected_approval_rate
        if inp.expected_approval_rate is not None
        else w["default_expected_approval_rate"]
    )

    effective_rate = inp.rate_per_1k * approval_rate * (1 - w["fee_rate"])
    effective_rate_score = _linear_score(effective_rate, 0.30, 3.00)

    launched_at = inp.launched_at
    if launched_at.tzinfo is None:
        launched_at = launched_at.replace(tzinfo=timezone.utc)
    age_days = (now - launched_at).total_seconds() / 86400.0
    pool_freshness_score = max(0.0, min(10.0, 10.0 * (1 - age_days / 30.0)))

    pool_remaining_score = _linear_score(inp.pool_remaining, 500, 20000)

    our_platforms = set(w["our_platforms"])
    campaign_platforms = set(inp.platforms)
    overlap = campaign_platforms & our_platforms
    platform_overlap_score = (
        10.0 * len(overlap) / len(campaign_platforms) if campaign_platforms else 10.0
    )

    cap_headroom_score = (
        10.0 if inp.per_clip_cap is None else _linear_score(inp.per_clip_cap, 50, 500)
    )

    factor_scores = {
        "effective_rate": effective_rate_score,
        "pool_freshness": pool_freshness_score,
        "pool_remaining": pool_remaining_score,
        "clippability": inp.clippability_score,
        "brief_clarity": inp.brief_clarity_score,
        "platform_overlap": platform_overlap_score,
        "cap_headroom": cap_headroom_score,
        "payout_reliability": inp.payout_reliability_score,
    }

    total_score = sum(w[name] * score for name, score in factor_scores.items())

    gates = {
        "unsubstantiable_claims": not inp.required_claims_substantiable,
        "no_platform_overlap": len(overlap) == 0,
        "entry_fee": inp.entry_fee,
        "low_value": (
            inp.projected_earnings_per_hour_inr is not None
            and inp.projected_earnings_per_hour_inr < w["low_value_earnings_per_hour_inr"]
        ),
    }

    reasons = []
    verdict = "OK"
    if gates["entry_fee"]:
        verdict = "BLACKLIST"
        reasons.append("charges an entry fee — free-to-join is non-negotiable, blacklist the brand")
    elif gates["unsubstantiable_claims"]:
        verdict = "REJECT"
        reasons.append("brief requires claims that cannot be substantiated")
    elif gates["no_platform_overlap"]:
        verdict = "REJECT"
        reasons.append(f"campaign platforms {sorted(campaign_platforms)} don't overlap our platforms {sorted(our_platforms)}")
    elif gates["low_value"]:
        verdict = "LOW_VALUE"
        reasons.append(
            f"projected {inp.projected_earnings_per_hour_inr:.0f} INR/hr < "
            f"{w['low_value_earnings_per_hour_inr']} INR/hr floor"
        )

    return CampaignScoreResult(
        total_score=round(total_score, 4),
        effective_rate=round(effective_rate, 4),
        factor_scores=factor_scores,
        gates=gates,
        verdict=verdict,
        reasons=reasons,
    )
