"""Log redaction. Wired into the root logger so it also catches records
from third-party libraries (urllib3, google-auth, etc.), not just this
project's own `logging.getLogger("engine")` instance.
"""

from __future__ import annotations

import logging
import re

_SECRET_PATTERN = re.compile(
    r"(?i)(api[_-]?key|token|secret|password|bearer)\s*[=:]\s*\S+"
)
_REDACTED = r"\1=***REDACTED***"


class RedactingFilter(logging.Filter):
    """Scrubs key=value / key: value secret-looking substrings from log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = _SECRET_PATTERN.sub(_REDACTED, record.msg)
        if record.args:
            record.args = tuple(
                _SECRET_PATTERN.sub(_REDACTED, arg) if isinstance(arg, str) else arg
                for arg in record.args
            )
        return True


def install_redaction_filter(logger: logging.Logger | None = None) -> None:
    """Attach the redaction filter to a logger AND every handler on it.

    A Filter attached only to a Logger object is bypassed for records that
    reach output through a *different* logger's handlers during
    propagation (Python's logging module runs Logger.filters only at the
    logger the call was made on, not at each ancestor). Since this
    project's engine logger owns its own console/file handlers, wiring
    the filter onto the root logger alone would silently do nothing —
    so we also attach it to every handler on the target logger.
    Idempotent: safe to call more than once on the same logger.
    """
    target = logger or logging.getLogger()

    def _already_has(filterable: logging.Logger | logging.Handler) -> bool:
        return any(isinstance(f, RedactingFilter) for f in filterable.filters)

    if not _already_has(target):
        target.addFilter(RedactingFilter())
    for handler in target.handlers:
        if not _already_has(handler):
            handler.addFilter(RedactingFilter())
