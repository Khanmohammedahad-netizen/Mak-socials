from src.core.config import settings


def test_html_route_open_no_auth(dashboard_client):
    resp = dashboard_client.get("/")
    assert resp.status_code == 200


def test_api_route_rejects_no_auth(dashboard_client):
    resp = dashboard_client.get("/api/status")
    assert resp.status_code == 401


def test_api_route_rejects_wrong_token(dashboard_client):
    resp = dashboard_client.get(
        "/api/status", headers={"Authorization": "Bearer not-the-token"}
    )
    assert resp.status_code == 401


def test_api_route_accepts_correct_token(dashboard_client):
    resp = dashboard_client.get(
        "/api/status",
        headers={"Authorization": f"Bearer {settings.mak_dashboard_token}"},
    )
    assert resp.status_code == 200


def test_run_now_rejects_no_auth(dashboard_client):
    """The route audit flagged as risk #3: any unauthenticated caller could
    trigger a real pipeline run + YouTube upload. Must be 401, and since the
    guard runs before the handler, no background thread should be spawned."""
    resp = dashboard_client.post("/api/run-now")
    assert resp.status_code == 401
