import pytest

from src.core.config import Settings, load_settings


def test_settings_load_with_token(monkeypatch):
    monkeypatch.setenv("MAK_DASHBOARD_TOKEN", "abc123")
    s = Settings()  # type: ignore[call-arg]
    assert s.mak_dashboard_token == "abc123"


def test_flags_default_false(monkeypatch):
    monkeypatch.setenv("MAK_DASHBOARD_TOKEN", "abc123")
    monkeypatch.delenv("ENABLE_LEGACY_AUTOPUBLISH", raising=False)
    monkeypatch.delenv("ENABLE_REDDIT_PIPELINE", raising=False)
    s = Settings(_env_file=None)  # type: ignore[call-arg]
    assert s.enable_legacy_autopublish is False
    assert s.enable_reddit_pipeline is False


def test_missing_required_token_raises_clear_error(monkeypatch, tmp_path):
    monkeypatch.delenv("MAK_DASHBOARD_TOKEN", raising=False)
    monkeypatch.chdir(tmp_path)  # no .env here to fall back on
    with pytest.raises(RuntimeError) as exc_info:
        load_settings()
    msg = str(exc_info.value)
    assert "mak_dashboard_token" in msg.lower()
    assert ".env.example" in msg
