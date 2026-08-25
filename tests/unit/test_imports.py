"""Every previously-working import must still import cleanly after Phase 0's
changes (config.py/logging.py wiring, auth decorator, scheduler flag gate).
Importing must not execute the pipeline or hit the network — these modules
all guard their real work behind `if __name__ == "__main__":` (see
docs/AUDIT.md §3), except dashboard_api, which builds a ViralEngine() at
module scope and therefore loads the Whisper model on import (existing
behaviour, unchanged by this phase — noted as a REFACTOR item in the audit,
not fixed here).
"""

import importlib

import pytest

MODULES = [
    "main",
    "bulk_upload_backlog",
    "setup",
    "engine.scheduler",
    "engine.script_generator",
    "engine.tts_engine",
    "engine.subtitle_generator",
    "engine.video_composer",
    "engine.thumbnail_generator",
    "engine.lib.title_optimizer",
    "engine.utils.background_manager",
    "engine.utils.music_mixer",
    "engine.utils.logger",
    "engine.uploader.youtube_uploader",
    "engine.uploader.instagram_uploader",
    "engine.uploader.snapchat_emailer",
    "src.core.config",
    "src.core.logging",
]


@pytest.mark.parametrize("module_name", MODULES)
def test_module_imports_cleanly(module_name):
    importlib.import_module(module_name)


def test_dashboard_api_imports_cleanly():
    importlib.import_module("dashboard_api")
