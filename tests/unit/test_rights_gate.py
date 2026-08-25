from datetime import datetime, timedelta, timezone

import pytest

from src.clips.rights_gate import NoRightsError, assert_rights
from src.core.models import Source
from src.sources.rights import InvalidRightsBasisError, create_rights_record


def _make_source(session, source_id="src-1"):
    source = Source(id=source_id, kind="OWNED_RECORDING", title="test")
    session.add(source)
    session.flush()
    return source


def test_missing_record_raises(db_session):
    _make_source(db_session)
    with pytest.raises(NoRightsError):
        assert_rights("src-1", session=db_session)


def test_expired_record_raises(db_session):
    _make_source(db_session)
    now = datetime.now(timezone.utc)
    create_rights_record(
        db_session,
        source_id="src-1",
        basis="OWNED",
        evidence_text="I own this.",
        valid_from=now - timedelta(days=30),
        valid_until=now - timedelta(days=1),
    )
    with pytest.raises(NoRightsError):
        assert_rights("src-1", session=db_session)


def test_not_yet_valid_record_raises(db_session):
    _make_source(db_session)
    now = datetime.now(timezone.utc)
    create_rights_record(
        db_session,
        source_id="src-1",
        basis="OWNED",
        evidence_text="I will own this.",
        valid_from=now + timedelta(days=1),
    )
    with pytest.raises(NoRightsError):
        assert_rights("src-1", session=db_session)


def test_valid_record_passes(db_session):
    _make_source(db_session)
    create_rights_record(
        db_session,
        source_id="src-1",
        basis="OWNED",
        evidence_text="I own this.",
    )
    record = assert_rights("src-1", session=db_session)
    assert record.basis == "OWNED"
    assert record.source_id == "src-1"


def test_one_expired_one_valid_record_passes(db_session):
    """A source can accumulate multiple rights records over time (e.g. a
    campaign renewed, or licensing renegotiated). Any currently-valid one
    is enough."""
    _make_source(db_session)
    now = datetime.now(timezone.utc)
    create_rights_record(
        db_session,
        source_id="src-1",
        basis="LICENSED_CC",
        evidence_text="old licence, expired",
        valid_from=now - timedelta(days=60),
        valid_until=now - timedelta(days=30),
    )
    create_rights_record(
        db_session,
        source_id="src-1",
        basis="LICENSED_PAID",
        evidence_text="renewed licence",
        valid_from=now - timedelta(days=1),
    )
    record = assert_rights("src-1", session=db_session)
    assert record.basis == "LICENSED_PAID"


def test_invalid_basis_rejected(db_session):
    _make_source(db_session)
    with pytest.raises(InvalidRightsBasisError):
        create_rights_record(
            db_session,
            source_id="src-1",
            basis="I_PROMISE_ITS_FINE",
            evidence_text="trust me",
        )


def test_evidence_file_written_and_never_expected_to_be_deleted(db_session, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _make_source(db_session)
    record = create_rights_record(
        db_session,
        source_id="src-1",
        basis="OWNED",
        evidence_text="I own this, see attached.",
    )
    from pathlib import Path

    evidence = Path(record.evidence_path)
    assert evidence.exists()
    assert evidence.read_text(encoding="utf-8") == "I own this, see attached."


def test_no_evidence_no_record(db_session):
    """A rights claim with neither evidence_text nor evidence_file_path
    must be rejected outright — there is no such thing as an
    undocumented rights record in this system."""
    _make_source(db_session)
    with pytest.raises(ValueError):
        create_rights_record(db_session, source_id="src-1", basis="OWNED")
