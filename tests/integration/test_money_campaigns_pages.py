from src.core.config import settings


def _auth_headers():
    return {"Authorization": f"Bearer {settings.mak_dashboard_token}"}


def test_money_page_open_no_auth(dashboard_client):
    resp = dashboard_client.get("/money")
    assert resp.status_code == 200
    assert b"authFetch" in resp.data


def test_campaigns_page_open_no_auth(dashboard_client):
    resp = dashboard_client.get("/campaigns")
    assert resp.status_code == 200


def test_api_money_requires_auth(dashboard_client):
    resp = dashboard_client.get("/api/money")
    assert resp.status_code == 401


def test_api_money_returns_totals_shape(dashboard_client):
    resp = dashboard_client.get("/api/money", headers=_auth_headers())
    assert resp.status_code == 200
    data = resp.get_json()
    assert "all_time" in data and "last_30_days" in data
    assert "profit_inr" in data["all_time"]


def test_api_campaigns_requires_auth(dashboard_client):
    resp = dashboard_client.get("/api/campaigns")
    assert resp.status_code == 401


def test_api_campaigns_returns_list(dashboard_client):
    resp = dashboard_client.get("/api/campaigns", headers=_auth_headers())
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)
