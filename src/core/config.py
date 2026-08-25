"""Centralized settings, loaded from environment / .env.

Existing engine/*.py modules still read config/config.yaml directly for
pipeline parameters (voice, duration, platforms, etc.) — that is unchanged
in this phase. This module is the new home for *secrets and feature flags*
only: the things Phase 0 (security hardening) and later phases need, and
the single place future modules should read them from instead of calling
os.environ directly.
"""

from __future__ import annotations

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Dashboard auth — required. There is no safe default for a bearer
    # token; an empty/missing value must fail startup, not silently open
    # every /api/* route (see dashboard_api.py's history of an
    # unauthenticated /api/run-now route that triggers real YouTube uploads).
    mak_dashboard_token: str

    # Feature flags — both default OFF. Phase 0 requirement: no scheduler
    # may register an unattended publish job unless explicitly re-enabled.
    enable_legacy_autopublish: bool = False
    enable_reddit_pipeline: bool = False

    # YouTube OAuth (env-var path). Currently unused in practice — the live
    # pipeline authenticates via config/credentials/youtube_client_secret.json
    # and youtube_token.json instead (see docs/AUDIT.md §5) — kept optional
    # so a blank .env does not block startup.
    youtube_client_id: str | None = None
    youtube_client_secret: str | None = None

    # Instagram Graph API
    ig_user_id: str | None = None
    ig_access_token: str | None = None

    # Snapchat hand-off email
    email_address: str | None = None
    email_app_password: str | None = None
    snapchat_email: str | None = None


def load_settings() -> Settings:
    """Load and validate settings, failing fast with a clear message."""
    try:
        return Settings()  # type: ignore[call-arg]  # fields sourced from env at runtime
    except ValidationError as exc:
        missing = [
            str(err["loc"][0])
            for err in exc.errors()
            if err["type"] == "missing"
        ]
        if missing:
            raise RuntimeError(
                "Missing required environment variable(s): "
                f"{', '.join(sorted(set(missing)))}. "
                "Set them in .env (see .env.example)."
            ) from exc
        raise


settings = load_settings()
