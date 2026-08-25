"""SQLAlchemy engine + declarative base for the new (Phase 1+) schema.

Not used by the existing engine/*.py pipeline — that pipeline has no SQL
database at all (see docs/AUDIT.md §7: persistence today is flat JSON
under output/). This module exists in Phase 0 purely so Alembic has a
real target to baseline against; the actual tables (identities, sources,
rights_records, campaigns, ...) are created in Phase 1.
"""

from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DB_PATH = os.path.join("data", "mak.db")

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass
