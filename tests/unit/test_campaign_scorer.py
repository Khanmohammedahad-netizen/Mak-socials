from datetime import datetime, timedelta, timezone

from src.clipping.campaign_scorer import CampaignScoreInput, score_campaign


def _base_input(**overrides):
    defaults = dict(
        rate_per_1k=1.5,
        pool_size=20000,
        pool_remaining=15000,
        launched_at=datetime.now(timezone.utc) - timedelta(days=3),
        platforms=["youtube", "instagram", "facebook"],
        per_clip_cap=300,
        clippability_score=7,
        brief_clarity_score=8,
        payout_reliability_score=6,
    )
    defaults.update(overrides)
    return CampaignScoreInput(**defaults)


def test_score_is_deterministic_across_repeated_runs():
    inp = _base_input()
    results = [score_campaign(inp) for _ in range(3)]
    scores = [r.total_score for r in results]
    assert scores[0] == scores[1] == scores[2]
    assert all(r.effective_rate == results[0].effective_rate for r in results)


def test_pool_freshness_decays_linearly_day_0_15_30():
    now = datetime.now(timezone.utc)

    day0 = score_campaign(_base_input(launched_at=now, now=now))
    day15 = score_campaign(_base_input(launched_at=now - timedelta(days=15), now=now))
    day30 = score_campaign(_base_input(launched_at=now - timedelta(days=30), now=now))
    day60 = score_campaign(_base_input(launched_at=now - timedelta(days=60), now=now))

    assert day0.factor_scores["pool_freshness"] == 10.0
    assert day15.factor_scores["pool_freshness"] == 5.0
    assert day30.factor_scores["pool_freshness"] == 0.0
    assert day60.factor_scores["pool_freshness"] == 0.0  # clipped, never negative


def test_effective_rate_matches_hand_calculation():
    inp = _base_input(rate_per_1k=2.0, expected_approval_rate=0.9)
    result = score_campaign(inp)
    expected = 2.0 * 0.9 * (1 - 0.09)  # rate * approval * (1 - fee)
    assert abs(result.effective_rate - round(expected, 4)) < 1e-9


def test_entry_fee_rejects_and_blacklists():
    inp = _base_input(entry_fee=True)
    result = score_campaign(inp)
    assert result.verdict == "BLACKLIST"
    assert result.gates["entry_fee"] is True


def test_unsubstantiable_claims_rejected():
    inp = _base_input(required_claims_substantiable=False)
    result = score_campaign(inp)
    assert result.verdict == "REJECT"
    assert result.gates["unsubstantiable_claims"] is True


def test_no_platform_overlap_rejected():
    inp = _base_input(platforms=["tiktok"])
    result = score_campaign(inp)
    assert result.verdict == "REJECT"
    assert result.gates["no_platform_overlap"] is True


def test_partial_platform_overlap_not_rejected_but_scored_lower():
    full = score_campaign(_base_input(platforms=["youtube", "instagram", "facebook"]))
    partial = score_campaign(_base_input(platforms=["youtube", "tiktok"]))
    assert partial.verdict == "OK"
    assert partial.factor_scores["platform_overlap"] < full.factor_scores["platform_overlap"]


def test_low_value_flag_only_when_projection_given():
    not_evaluated = score_campaign(_base_input())
    assert not_evaluated.gates["low_value"] is False

    below_floor = score_campaign(_base_input(projected_earnings_per_hour_inr=100))
    assert below_floor.verdict == "LOW_VALUE"

    above_floor = score_campaign(_base_input(projected_earnings_per_hour_inr=1000))
    assert above_floor.verdict == "OK"


def test_uncapped_clip_gets_full_cap_headroom_score():
    result = score_campaign(_base_input(per_clip_cap=None))
    assert result.factor_scores["cap_headroom"] == 10.0


def test_weights_sum_to_one():
    from src.clipping.campaign_scorer import _load_weights

    w = _load_weights()
    factor_keys = [
        "effective_rate", "pool_freshness", "pool_remaining", "clippability",
        "brief_clarity", "platform_overlap", "cap_headroom", "payout_reliability",
    ]
    assert abs(sum(w[k] for k in factor_keys) - 1.0) < 1e-9
