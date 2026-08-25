import logging

from src.core.logging import RedactingFilter, install_redaction_filter


def _log_and_capture(logger, msg):
    import io

    buf = io.StringIO()
    handler = logging.StreamHandler(buf)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.error(msg)
    logger.removeHandler(handler)
    return buf.getvalue()


def test_filter_redacts_key_value_secrets():
    logger = logging.getLogger("test.redaction.filter")
    logger.setLevel(logging.DEBUG)
    logger.addFilter(RedactingFilter())

    out = _log_and_capture(logger, "leaked api_key=SUPERSECRET123 ok")
    assert "SUPERSECRET123" not in out
    assert "REDACTED" in out


def test_filter_leaves_non_secret_text_alone():
    logger = logging.getLogger("test.redaction.filter.clean")
    logger.setLevel(logging.DEBUG)
    logger.addFilter(RedactingFilter())

    out = _log_and_capture(logger, "pipeline run completed successfully")
    assert "pipeline run completed successfully" in out


def test_install_is_idempotent_and_covers_handlers():
    logger = logging.getLogger("test.redaction.install")
    logger.addHandler(logging.NullHandler())

    install_redaction_filter(logger)
    install_redaction_filter(logger)  # must not double-attach

    assert sum(isinstance(f, RedactingFilter) for f in logger.filters) == 1
    for handler in logger.handlers:
        assert sum(isinstance(f, RedactingFilter) for f in handler.filters) == 1
