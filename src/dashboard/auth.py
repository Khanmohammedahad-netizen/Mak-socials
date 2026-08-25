"""Shared bearer-token guard for every /api/* route, across
dashboard_api.py and any Blueprint registered onto it (src/dashboard/*)."""

from __future__ import annotations

from functools import wraps

from flask import jsonify, request

from src.core.config import settings


def require_bearer_token(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        expected = f"Bearer {settings.mak_dashboard_token}"
        if auth != expected:
            return jsonify({"error": "unauthorized"}), 401
        return view(*args, **kwargs)

    return wrapped
