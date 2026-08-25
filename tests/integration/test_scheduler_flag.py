"""Phase 0 acceptance: with ENABLE_LEGACY_AUTOPUBLISH off, the scheduler
must register ZERO publish jobs — from either entry point.

Settings load once at process start (src.core.config.settings is a module
singleton), so monkeypatching the environment after import has no effect
on it — pydantic-settings reads env only at instantiation. We monkeypatch
the already-loaded settings object's attribute directly instead, which is
what start_scheduler() actually reads.
"""

from apscheduler.schedulers.background import BackgroundScheduler

import engine.scheduler as scheduler_module


def test_start_scheduler_registers_no_jobs_when_flag_off(monkeypatch):
    monkeypatch.setattr(scheduler_module.settings, "enable_legacy_autopublish", False)

    created = []
    original_init = BackgroundScheduler.__init__

    def spy_init(self, *a, **kw):
        created.append(self)
        return original_init(self, *a, **kw)

    monkeypatch.setattr(BackgroundScheduler, "__init__", spy_init)

    result = scheduler_module.start_scheduler()

    assert result is None
    assert created == [], "a BackgroundScheduler was constructed despite the flag being off"
