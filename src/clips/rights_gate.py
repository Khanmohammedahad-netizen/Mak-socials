"""The rights gate. Per blueprint §6.2: this is "the whole business" —
the difference between a legitimate clip factory and a terminated
account with forfeited pending earnings.

assert_rights() is called before ANY render, not before publish (once
the clip engine exists in Phase 2). There is deliberately no override
parameter, no force flag, and no config toggle here. If this ever needs
to be bypassed, that has to mean editing this function on a tired
evening and thinking better of it — not flipping a flag.

Do not add a bypass parameter to this file. That instruction is the
point of the file.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from engine.utils.logger import logger
from src.core.db import SessionLocal
from src.core.models import RightsRecord


class NoRightsError(Exception):
    """Raised when a source has no currently-valid rights record.
    Never caught-and-continued anywhere in this codebase — a source
    without rights must produce zero files, not a warning."""


def assert_rights(source_id: str, *, session: Session | None = None) -> RightsRecord:
    """Return the currently-valid RightsRecord for source_id, or raise
    NoRightsError. "Currently valid" means: a record exists, its
    valid_from is not in the future, and its valid_until (if set) is
    not in the past.
    """
    owns_session = session is None
    db = session or SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        records = (
            db.query(RightsRecord)
            .filter(RightsRecord.source_id == source_id)
            .order_by(RightsRecord.verified_at.desc())
            .all()
        )

        if not records:
            logger.error(f"rights_gate: BLOCKED source_id={source_id} — no rights record on file")
            raise NoRightsError(f"no rights record for source_id={source_id}")

        for record in records:
            valid_from = _as_aware(record.valid_from)
            valid_until = _as_aware(record.valid_until)
            if valid_from > now:
                continue
            if valid_until is not None and valid_until < now:
                continue
            logger.info(
                f"rights_gate: PASSED source_id={source_id} "
                f"basis={record.basis} record_id={record.id}"
            )
            return record

        reasons = [_describe(r, now) for r in records]
        logger.error(
            f"rights_gate: BLOCKED source_id={source_id} — "
            f"{len(records)} record(s) on file, none currently valid: {reasons}"
        )
        raise NoRightsError(
            f"no currently-valid rights record for source_id={source_id} "
            f"({len(records)} record(s) found, all expired or not-yet-valid)"
        )
    finally:
        if owns_session:
            db.close()


def _as_aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _describe(record: RightsRecord, now: datetime) -> str:
    valid_from = _as_aware(record.valid_from)
    if valid_from > now:
        return f"{record.id}:not-yet-valid(from={record.valid_from})"
    return f"{record.id}:expired(until={record.valid_until})"
