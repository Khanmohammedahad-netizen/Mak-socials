from datetime import datetime, timezone
from pathlib import Path

from src.clipping.campaigns import intake_campaign
from src.clips.rights_gate import assert_rights
from src.core.models import Campaign, RightsRecord, Source


def test_intake_creates_campaign_source_and_rights_record(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr("src.sources.rights.RIGHTS_DIR", tmp_path / "rights")

    campaign, source, rights_record = intake_campaign(
        db_session,
        platform="whop",
        brand="Neon",
        rate_per_1k=1.5,
        pool_size=18400,
        launched_at=datetime.now(timezone.utc),
        platforms=["youtube", "instagram", "facebook"],
        brief_text="Cut clips 15-58s. Required tag: #neon. No health claims.",
        required_tags=["#neon"],
        banned_claims=["health claims"],
        per_clip_cap=500,
    )

    assert db_session.query(Campaign).count() == 1
    assert db_session.query(Source).count() == 1
    assert db_session.query(RightsRecord).count() == 1

    assert source.campaign_id == campaign.id
    assert source.kind == "CAMPAIGN"
    assert rights_record.source_id == source.id
    assert rights_record.basis == "CAMPAIGN"
    assert Path(rights_record.evidence_path).read_text(encoding="utf-8") == campaign.brief_text


def test_intake_creates_a_source_that_passes_the_rights_gate(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr("src.sources.rights.RIGHTS_DIR", tmp_path / "rights")
    campaign, source, _ = intake_campaign(
        db_session,
        platform="whop",
        brand="Neon",
        rate_per_1k=1.5,
        pool_size=18400,
        launched_at=datetime.now(timezone.utc),
        platforms=["youtube"],
        brief_text="brief",
    )
    record = assert_rights(source.id, session=db_session)
    assert record.basis == "CAMPAIGN"


def test_intake_scores_and_sets_status(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr("src.sources.rights.RIGHTS_DIR", tmp_path / "rights")
    campaign, _, _ = intake_campaign(
        db_session,
        platform="whop",
        brand="Good Brand",
        rate_per_1k=2.5,
        pool_size=20000,
        launched_at=datetime.now(timezone.utc),
        platforms=["youtube", "instagram", "facebook"],
        brief_text="brief",
        clippability_score=8,
        brief_clarity_score=9,
        payout_reliability_score=7,
    )
    assert campaign.score is not None
    assert campaign.effective_rate is not None
    assert campaign.status == "ACTIVE"


def test_intake_blacklists_entry_fee_campaigns(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr("src.sources.rights.RIGHTS_DIR", tmp_path / "rights")
    campaign, _, _ = intake_campaign(
        db_session,
        platform="scammy",
        brand="Pay To Join Inc",
        rate_per_1k=5.0,
        pool_size=99999,
        launched_at=datetime.now(timezone.utc),
        platforms=["youtube"],
        brief_text="brief",
        entry_fee=True,
    )
    assert campaign.status == "BLACKLISTED"


def test_intake_pool_remaining_starts_at_pool_size(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr("src.sources.rights.RIGHTS_DIR", tmp_path / "rights")
    campaign, _, _ = intake_campaign(
        db_session,
        platform="whop",
        brand="Neon",
        rate_per_1k=1.5,
        pool_size=18400,
        launched_at=datetime.now(timezone.utc),
        platforms=["youtube"],
        brief_text="brief",
    )
    assert campaign.pool_remaining == campaign.pool_size == 18400
