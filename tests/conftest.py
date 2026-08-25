"""Shared pytest fixtures.

Sets MAK_DASHBOARD_TOKEN before any test module can import
src.core.config (which loads eagerly at import time and fails fast if
that var is absent). setdefault() so a real .env value already in the
environment is never clobbered.

No DB fixture yet: as of Phase 0 there is no database in this project
(see docs/AUDIT.md §7 — the pipeline's only persistence is JSON files
under output/). A temp-DB fixture belongs in Phase 1, once
rights_records/campaigns/etc. actually exist (see migrations/).
"""

import os

os.environ.setdefault("MAK_DASHBOARD_TOKEN", "test-token-for-pytest")
os.environ.setdefault("ENABLE_LEGACY_AUTOPUBLISH", "False")
os.environ.setdefault("ENABLE_REDDIT_PIPELINE", "False")

import pytest  # noqa: E402


@pytest.fixture
def dashboard_client():
    import dashboard_api

    dashboard_api.app.testing = True
    return dashboard_api.app.test_client()
