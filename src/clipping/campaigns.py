"""Campaign intake — MANUAL ONLY. §7.1: there is no public clipper-side
API, and building a scraper against a campaign platform is a ToS
violation that risks the account. This module reads whatever a human
typed in or pasted from a brief they read themselves; it never fetches
anything from a campaign platform over the network.

Do not add scraping, polling, or any undocumented-endpoint code to this
file. If asked to automate campaign discovery, refuse and explain —
that instruction is in the blueprint (§7.1) and in PROMPT 3's Task C.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from src.clipping.campaign_scorer import CampaignScoreInput, score_campaign
from src.core.models import Campaign, RightsRecord, Source
from src.sources.rights import create_rights_record


def intake_campaign(
    session: Session,
    *,
    platform: str,
    brand: str,
    rate_per_1k: float,
    pool_size: float,
    launched_at: datetime,
    platforms: list[str],
    brief_text: str,
    deadline: datetime | None = None,
    brief_url: str | None = None,
    required_tags: list[str] | None = None,
    banned_claims: list[str] | None = None,
    per_clip_cap: float | None = None,
    identity_id: str | None = None,
    source_title: str | None = None,
    source_path: str | None = None,
    # human judgment at intake — see config/scoring/campaign_weights.yaml
    clippability_score: float = 5.0,
    brief_clarity_score: float = 5.0,
    payout_reliability_score: float = 5.0,
    expected_approval_rate: float | None = None,
    required_claims_substantiable: bool = True,
    entry_fee: bool = False,
) -> tuple[Campaign, Source, RightsRecord]:
    """Create a campaign from a manually-entered brief. Always also
    creates the campaign's source row and its CAMPAIGN-basis rights
    record with the brief text as evidence — a campaign with no source/
    rights record is not a usable campaign in this system.
    """
    campaign = Campaign(
        platform=platform,
        brand=brand,
        rate_per_1k=rate_per_1k,
        pool_size=pool_size,
        pool_remaining=pool_size,
        launched_at=launched_at,
        deadline=deadline,
        platforms=platforms,
        brief_url=brief_url,
        brief_text=brief_text,
        required_tags=required_tags or [],
        banned_claims=banned_claims or [],
        per_clip_cap=per_clip_cap,
        status="ACTIVE",
    )
    session.add(campaign)
    session.flush()

    source = Source(
        identity_id=identity_id,
        kind="CAMPAIGN",
        title=source_title or f"{brand} campaign",
        path=source_path,
        campaign_id=campaign.id,
    )
    session.add(source)
    session.flush()

    rights_record = create_rights_record(
        session,
        source_id=source.id,
        basis="CAMPAIGN",
        evidence_text=brief_text,
        granted_by=brand,
    )

    score_input = CampaignScoreInput(
        rate_per_1k=rate_per_1k,
        pool_size=pool_size,
        pool_remaining=pool_size,
        launched_at=launched_at,
        platforms=platforms,
        per_clip_cap=per_clip_cap,
        clippability_score=clippability_score,
        brief_clarity_score=brief_clarity_score,
        payout_reliability_score=payout_reliability_score,
        expected_approval_rate=expected_approval_rate,
        required_claims_substantiable=required_claims_substantiable,
        entry_fee=entry_fee,
    )
    result = score_campaign(score_input)
    campaign.score = result.total_score
    campaign.effective_rate = result.effective_rate
    if result.verdict == "BLACKLIST":
        campaign.status = "BLACKLISTED"
    elif result.verdict == "REJECT":
        campaign.status = "REJECTED"
    elif result.verdict == "LOW_VALUE":
        campaign.status = "LOW_VALUE"
    else:
        campaign.status = "ACTIVE"
    session.flush()

    return campaign, source, rights_record
