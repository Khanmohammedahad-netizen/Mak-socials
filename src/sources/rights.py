"""Create and validate rights records — evidence for why a source may
legally be clipped. This is the input side of the rights gate
(src/clips/rights_gate.py checks what this module writes).

Evidence files are copied/written to data/rights/<source_id>/ and are
never deleted by this module or any other code path: per the blueprint,
"if a payout or takedown is ever disputed, that folder is your entire
defence." (§14 Security)
"""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from src.core.models import RightsRecord

VALID_BASES = {"CAMPAIGN", "OWNED", "LICENSED_CC", "LICENSED_PAID", "WRITTEN_PERMISSION"}

RIGHTS_DIR = Path("data") / "rights"


class InvalidRightsBasisError(ValueError):
    pass


def _evidence_dir(source_id: str) -> Path:
    d = RIGHTS_DIR / source_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def create_rights_record(
    session: Session,
    *,
    source_id: str,
    basis: str,
    evidence_text: str | None = None,
    evidence_file_path: str | None = None,
    granted_by: str | None = None,
    valid_from: datetime | None = None,
    valid_until: datetime | None = None,
    restrictions: dict | None = None,
) -> RightsRecord:
    """Write one rights_records row + its evidence file. Exactly one of
    evidence_text (written out as a new file) or evidence_file_path (an
    existing file, copied in) must be given — a rights claim with no
    evidence on file is not a rights claim.
    """
    if basis not in VALID_BASES:
        raise InvalidRightsBasisError(
            f"basis must be one of {sorted(VALID_BASES)}, got {basis!r}"
        )
    if bool(evidence_text) == bool(evidence_file_path):
        raise ValueError(
            "exactly one of evidence_text or evidence_file_path is required"
        )

    dest_dir = _evidence_dir(source_id)

    if evidence_text is not None:
        evidence_path = dest_dir / "evidence.md"
        evidence_path.write_text(evidence_text, encoding="utf-8")
    else:
        src_path = Path(evidence_file_path)  # type: ignore[arg-type]
        if not src_path.exists():
            raise FileNotFoundError(f"evidence file not found: {src_path}")
        evidence_path = dest_dir / src_path.name
        shutil.copy2(src_path, evidence_path)

    record = RightsRecord(
        source_id=source_id,
        basis=basis,
        evidence_path=str(evidence_path),
        granted_by=granted_by,
        valid_from=valid_from or datetime.now(timezone.utc),
        valid_until=valid_until,
        restrictions=restrictions,
    )
    session.add(record)
    session.flush()
    return record
