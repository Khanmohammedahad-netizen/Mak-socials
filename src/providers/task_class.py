"""Task classes the LLM router dispatches on. Blueprint §10/Task D names
SCORING/CAPTION/HOOK explicitly (Phase 2's clip engine); SCRIPT and TITLE
are added here because Phase 1 migrates the two LLM call sites that
already exist today (engine/script_generator.py, engine/lib/title_optimizer.py)
onto this router, and both need a task class to route on.
"""

from __future__ import annotations

from enum import Enum


class TaskClass(str, Enum):
    SCRIPT = "SCRIPT"
    TITLE = "TITLE"
    SCORING = "SCORING"
    CAPTION = "CAPTION"
    HOOK = "HOOK"
