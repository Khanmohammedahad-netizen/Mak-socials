"""/money and /campaigns — deliberately minimal. Blueprint §13/risk #13:
"over-building the dashboard... capped at 10% of each phase." These are
two small pages over the ledger and campaign-scorer tables Phase 1 just
built, nothing more.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify
from sqlalchemy import func

from src.core.config import settings
from src.core.db import SessionLocal
from src.core.models import ApiCost, Campaign, ProductionCost, RevenueEvent
from src.dashboard.auth import require_bearer_token

money_campaigns_bp = Blueprint("money_campaigns", __name__)

_PALETTE_CSS = """
  :root { --bg:#0A1511; --accent:#C9A84C; --text:#F1ECDF; --border:#22332c; }
  body { background:var(--bg); color:var(--text); font-family:'DM Sans',system-ui,sans-serif;
         margin:0; padding:32px; }
  h1 { font-family:'Cormorant Garamond',serif; font-size:32px; color:var(--accent);
       margin:0 0 24px; font-weight:600; }
  table { width:100%; border-collapse:collapse; margin-top:16px; }
  th, td { text-align:left; padding:10px 12px; border-bottom:1px solid var(--border); font-size:13px; }
  th { color:var(--accent); font-weight:600; text-transform:uppercase; font-size:11px; letter-spacing:0.05em; }
  .stat-row { display:flex; gap:16px; flex-wrap:wrap; }
  .stat { background:#0e1b16; border:1px solid var(--border); border-radius:10px; padding:16px 20px; min-width:160px; }
  .stat .label { font-size:11px; color:#8a998f; text-transform:uppercase; letter-spacing:0.05em; }
  .stat .value { font-size:24px; color:var(--accent); font-family:'Cormorant Garamond',serif; margin-top:4px; }
  .empty { color:#8a998f; font-size:13px; padding:24px 0; }
  .badge { padding:2px 8px; border-radius:6px; font-size:11px; }
  .badge-ACTIVE { background:#1c3324; color:#7fd99a; }
  .badge-REJECTED, .badge-BLACKLISTED { background:#3a1c1c; color:#e08080; }
  .badge-LOW_VALUE { background:#3a331c; color:#e0c080; }
"""


def _page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>MAK Socials — {title}</title>
<style>{_PALETTE_CSS}</style></head>
<body>
<h1>{title}</h1>
{body}
<script>
window.MAK_TOKEN = "{settings.mak_dashboard_token}";
function authFetch(url) {{
  return fetch(url, {{ headers: {{ 'Authorization': 'Bearer ' + window.MAK_TOKEN }} }});
}}
</script>
</body></html>"""


@money_campaigns_bp.route("/api/money", methods=["GET"])
@require_bearer_token
def api_money():
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        thirty_days_ago = now - timedelta(days=30)

        def totals(since=None):
            rev_q = db.query(func.coalesce(func.sum(RevenueEvent.amount_inr), 0.0))
            prod_q = db.query(func.coalesce(func.sum(ProductionCost.amount_inr), 0.0))
            api_q = db.query(func.coalesce(func.sum(ApiCost.cost_inr), 0.0))
            if since is not None:
                rev_q = rev_q.filter(RevenueEvent.occurred_at >= since)
                prod_q = prod_q.filter(ProductionCost.occurred_at >= since)
                api_q = api_q.filter(ApiCost.occurred_at >= since)
            revenue = float(rev_q.scalar())
            production = float(prod_q.scalar())
            api_cost = float(api_q.scalar())
            return {
                "revenue_inr": revenue,
                "production_cost_inr": production,
                "api_cost_inr": api_cost,
                "profit_inr": revenue - production - api_cost,
            }

        return jsonify({"all_time": totals(), "last_30_days": totals(thirty_days_ago)})
    finally:
        db.close()


@money_campaigns_bp.route("/money")
def money_page():
    body = """
<div class="stat-row" id="stats"><div class="empty">Loading…</div></div>
<script>
authFetch('/api/money').then(r => r.json()).then(data => {
  const el = document.getElementById('stats');
  const fmt = n => '₹' + Math.round(n).toLocaleString('en-IN');
  el.innerHTML = ['all_time', 'last_30_days'].map(period => `
    <div class="stat"><div class="label">${period === 'all_time' ? 'Revenue (all time)' : 'Revenue (30d)'}</div>
      <div class="value">${fmt(data[period].revenue_inr)}</div></div>
    <div class="stat"><div class="label">Cost (${period === 'all_time' ? 'all time' : '30d'})</div>
      <div class="value">${fmt(data[period].production_cost_inr + data[period].api_cost_inr)}</div></div>
    <div class="stat"><div class="label">Profit (${period === 'all_time' ? 'all time' : '30d'})</div>
      <div class="value">${fmt(data[period].profit_inr)}</div></div>
  `).join('');
}).catch(() => {
  document.getElementById('stats').innerHTML = '<div class="empty">Could not reach /api/money</div>';
});
</script>
"""
    return _page("Money", body)


@money_campaigns_bp.route("/api/campaigns", methods=["GET"])
@require_bearer_token
def api_campaigns():
    db = SessionLocal()
    try:
        campaigns = db.query(Campaign).order_by(Campaign.score.desc().nullslast()).all()
        return jsonify([
            {
                "id": c.id,
                "brand": c.brand,
                "platform": c.platform,
                "rate_per_1k": c.rate_per_1k,
                "pool_remaining": c.pool_remaining,
                "pool_size": c.pool_size,
                "effective_rate": c.effective_rate,
                "score": c.score,
                "status": c.status,
                "launched_at": c.launched_at.isoformat() if c.launched_at else None,
            }
            for c in campaigns
        ])
    finally:
        db.close()


@money_campaigns_bp.route("/campaigns")
def campaigns_page():
    body = """
<table id="campaigns-table">
  <thead><tr><th>Brand</th><th>Rate/1k</th><th>Pool remaining</th><th>Effective rate</th><th>Score</th><th>Status</th></tr></thead>
  <tbody><tr><td colspan="6" class="empty">Loading…</td></tr></tbody>
</table>
<script>
authFetch('/api/campaigns').then(r => r.json()).then(rows => {
  const tbody = document.querySelector('#campaigns-table tbody');
  if (!rows.length) { tbody.innerHTML = '<tr><td colspan="6" class="empty">No campaigns yet — intake one via src/clipping/campaigns.py</td></tr>'; return; }
  tbody.innerHTML = rows.map(c => `
    <tr>
      <td>${c.brand}</td>
      <td>$${c.rate_per_1k}</td>
      <td>$${Math.round(c.pool_remaining).toLocaleString()} / $${Math.round(c.pool_size).toLocaleString()}</td>
      <td>$${c.effective_rate != null ? c.effective_rate.toFixed(2) : '—'}</td>
      <td>${c.score != null ? c.score.toFixed(2) : '—'}</td>
      <td><span class="badge badge-${c.status}">${c.status}</span></td>
    </tr>`).join('');
}).catch(() => {
  document.querySelector('#campaigns-table tbody').innerHTML = '<tr><td colspan="6" class="empty">Could not reach /api/campaigns</td></tr>';
});
</script>
"""
    return _page("Campaigns", body)
