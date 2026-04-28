"""
briefing.py  —  Morning BD Briefing
Reads from data/bd_agent.db, writes briefing.html, opens it in the browser.

Run every morning:
    python briefing.py
"""

import sqlite3
import json
import os
import sys
import webbrowser
from datetime import date, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'bd_agent.db')
OUT_PATH = os.path.join(os.path.dirname(__file__), 'briefing.html')

# ── Queries ───────────────────────────────────────────────────────────────────

def fetch_data():
    today = date.today()
    week_start = today - timedelta(days=today.weekday())   # Monday
    week_end   = week_start + timedelta(days=6)            # Sunday

    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    def rows(q, *args):
        cur.execute(q, *args)
        return [dict(r) for r in cur.fetchall()]

    # 1. ETA this week — Shipped orders whose ETA falls in Mon–Sun this week
    eta_this_week = rows("""
        SELECT order_id, customer_name, territory, total_amount, order_date, eta
        FROM orders
        WHERE status = 'Shipped'
          AND eta BETWEEN ? AND ?
        ORDER BY eta
    """, (str(week_start), str(week_end)))

    # 2. Late orders — ETA already passed, not yet delivered
    late = rows("""
        SELECT order_id, customer_name, territory, total_amount, order_date,
               eta, status,
               CAST(julianday('now') - julianday(eta) AS INTEGER) AS days_late
        FROM orders
        WHERE status NOT IN ('Delivered', 'Cancelled')
          AND eta < date('now')
        ORDER BY days_late DESC
    """)

    # 3. Delivered this week — delivered_date falls in Mon–Sun this week
    delivered_this_week = rows("""
        SELECT order_id, customer_name, territory, total_amount,
               order_date, delivered_date
        FROM orders
        WHERE status = 'Delivered'
          AND delivered_date BETWEEN ? AND ?
        ORDER BY delivered_date
    """, (str(week_start), str(week_end)))

    con.close()
    return {
        'today': str(today),
        'week_start': str(week_start),
        'week_end': str(week_end),
        'eta_this_week': eta_this_week,
        'late': late,
        'delivered_this_week': delivered_this_week,
    }

# ── HTML Template ─────────────────────────────────────────────────────────────

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Morning Briefing — {today}</title>
<style>
:root {{
  --bg:#0d1117; --surface:#161b22; --surface2:#1e2530;
  --border:#30363d; --text:#e6edf3; --muted:#8b949e;
  --green:#3fb950; --yellow:#d29922; --red:#f85149;
  --accent:#58a6ff; --orange:#ffa657; --radius:12px;
}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
      background:var(--bg);color:var(--text);min-height:100vh;padding:32px 24px;font-size:14px}}
.page{{max-width:900px;margin:0 auto}}

/* Header */
.header{{margin-bottom:32px}}
.header-top{{display:flex;align-items:flex-end;justify-content:space-between;flex-wrap:wrap;gap:12px}}
.greeting{{font-size:24px;font-weight:800;letter-spacing:-.4px}}
.dateline{{font-size:13px;color:var(--muted)}}
.summary-pills{{display:flex;gap:8px;margin-top:14px;flex-wrap:wrap}}
.pill{{display:inline-flex;align-items:center;gap:6px;padding:5px 12px;border-radius:20px;
       font-size:12px;font-weight:700;border:1px solid}}
.pill-red{{background:rgba(248,81,73,.12);border-color:rgba(248,81,73,.3);color:var(--red)}}
.pill-yellow{{background:rgba(210,153,34,.12);border-color:rgba(210,153,34,.3);color:var(--yellow)}}
.pill-green{{background:rgba(63,185,80,.12);border-color:rgba(63,185,80,.3);color:var(--green)}}
.pill-dot{{width:7px;height:7px;border-radius:50%;background:currentColor}}

/* Sections */
.section{{margin-bottom:28px}}
.section-hdr{{display:flex;align-items:center;gap:10px;margin-bottom:14px}}
.section-icon{{font-size:18px}}
.section-title{{font-size:15px;font-weight:700}}
.section-count{{font-size:12px;font-weight:700;padding:2px 9px;border-radius:20px}}
.count-red   {{background:rgba(248,81,73,.15);color:var(--red)}}
.count-yellow{{background:rgba(210,153,34,.15);color:var(--yellow)}}
.count-green {{background:rgba(63,185,80,.15);color:var(--green)}}
.action-hint{{font-size:12px;color:var(--muted);margin-left:auto;font-style:italic}}

/* Cards */
.card-list{{display:flex;flex-direction:column;gap:10px}}
.card{{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);
       padding:16px 18px;display:flex;align-items:center;gap:16px;transition:.15s}}
.card:hover{{border-color:var(--accent);background:var(--surface2)}}
.card-left{{flex:1;min-width:0}}
.card-id{{font-size:11px;color:var(--muted);font-weight:700;font-family:monospace;
          letter-spacing:.3px;margin-bottom:3px}}
.card-client{{font-size:15px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.card-meta{{font-size:12px;color:var(--muted);margin-top:3px;display:flex;gap:12px;flex-wrap:wrap}}
.card-right{{text-align:right;flex-shrink:0}}
.card-amount{{font-size:16px;font-weight:800}}
.card-date{{font-size:12px;margin-top:3px}}
.card-date.late{{color:var(--red);font-weight:700}}
.card-date.ok{{color:var(--yellow)}}
.card-date.good{{color:var(--green);font-weight:700}}
.badge{{display:inline-block;font-size:11px;font-weight:700;padding:2px 8px;
        border-radius:6px;margin-top:6px}}
.badge-red{{background:rgba(248,81,73,.15);color:var(--red)}}
.badge-yellow{{background:rgba(210,153,34,.15);color:var(--yellow)}}
.badge-green{{background:rgba(63,185,80,.15);color:var(--green)}}
.badge-blue{{background:rgba(88,166,255,.15);color:var(--accent)}}
.left-bar-red   {{border-left:3px solid var(--red)}}
.left-bar-yellow{{border-left:3px solid var(--yellow)}}
.left-bar-green {{border-left:3px solid var(--green)}}

/* Empty state */
.empty{{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);
        padding:24px;text-align:center;color:var(--muted);font-size:13px}}

/* Footer */
.footer{{margin-top:40px;padding-top:20px;border-top:1px solid var(--border);
         font-size:12px;color:var(--muted);text-align:center}}
</style>
</head>
<body>
<div class="page">

  <!-- Header -->
  <div class="header">
    <div class="header-top">
      <div>
        <div class="greeting">Good morning 👋</div>
        <div class="dateline">Morning Briefing &nbsp;·&nbsp; {today_fmt} &nbsp;·&nbsp; Week of {week_start} – {week_end}</div>
      </div>
    </div>
    <div class="summary-pills" id="summaryPills"></div>
  </div>

  <!-- Section 1: ETA This Week -->
  <div class="section">
    <div class="section-hdr">
      <span class="section-icon">📦</span>
      <span class="section-title">ETA This Week</span>
      <span class="section-count count-yellow" id="etaCount">0</span>
      <span class="action-hint">Send client update</span>
    </div>
    <div class="card-list" id="etaList"></div>
  </div>

  <!-- Section 2: Late Orders -->
  <div class="section">
    <div class="section-hdr">
      <span class="section-icon">🚨</span>
      <span class="section-title">Late Orders</span>
      <span class="section-count count-red" id="lateCount">0</span>
      <span class="action-hint">Need attention today</span>
    </div>
    <div class="card-list" id="lateList"></div>
  </div>

  <!-- Section 3: Delivered This Week -->
  <div class="section">
    <div class="section-hdr">
      <span class="section-icon">✅</span>
      <span class="section-title">Delivered This Week</span>
      <span class="section-count count-green" id="delivCount">0</span>
      <span class="action-hint">Send confirmation to client</span>
    </div>
    <div class="card-list" id="delivList"></div>
  </div>

  <div class="footer">BD Agent &nbsp;·&nbsp; data/bd_agent.db &nbsp;·&nbsp; Generated {today}</div>
</div>

<script>
const DATA = __DATA__;

function fmt(dateStr) {{
  if (!dateStr) return '—';
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('en-GB', {{day:'numeric',month:'short',year:'numeric'}});
}}

function usd(n) {{
  return '$' + Number(n).toLocaleString('en-US', {{minimumFractionDigits:2, maximumFractionDigits:2}});
}}

function flag(territory) {{
  return {{Japan:'🇯🇵', Canada:'🇨🇦', Taiwan:'🇹🇼'}}[territory] || '🌐';
}}

// -- ETA this week
const etaList = document.getElementById('etaList');
document.getElementById('etaCount').textContent = DATA.eta_this_week.length;
if (DATA.eta_this_week.length === 0) {{
  etaList.innerHTML = '<div class="empty">No shipments arriving this week.</div>';
}} else {{
  DATA.eta_this_week.forEach(o => {{
    etaList.innerHTML += `
      <div class="card left-bar-yellow">
        <div class="card-left">
          <div class="card-id">${{o.order_id}}</div>
          <div class="card-client">${{flag(o.territory)}} ${{o.customer_name}}</div>
          <div class="card-meta">
            <span>${{o.territory}}</span>
            <span>Ordered ${{fmt(o.order_date)}}</span>
          </div>
        </div>
        <div class="card-right">
          <div class="card-amount">${{usd(o.total_amount)}}</div>
          <div class="card-date ok">ETA ${{fmt(o.eta)}}</div>
          <div><span class="badge badge-yellow">Shipped</span></div>
        </div>
      </div>`;
  }});
}}

// -- Late orders
const lateList = document.getElementById('lateList');
document.getElementById('lateCount').textContent = DATA.late.length;
if (DATA.late.length === 0) {{
  lateList.innerHTML = '<div class="empty">No late orders. Great!</div>';
}} else {{
  DATA.late.forEach(o => {{
    const daysLabel = o.days_late === 1 ? '1 day late' : `${{o.days_late}} days late`;
    lateList.innerHTML += `
      <div class="card left-bar-red">
        <div class="card-left">
          <div class="card-id">${{o.order_id}}</div>
          <div class="card-client">${{flag(o.territory)}} ${{o.customer_name}}</div>
          <div class="card-meta">
            <span>${{o.territory}}</span>
            <span>Status: ${{o.status}}</span>
            <span>Ordered ${{fmt(o.order_date)}}</span>
          </div>
        </div>
        <div class="card-right">
          <div class="card-amount">${{usd(o.total_amount)}}</div>
          <div class="card-date late">ETA was ${{fmt(o.eta)}}</div>
          <div><span class="badge badge-red">${{daysLabel}}</span></div>
        </div>
      </div>`;
  }});
}}

// -- Delivered this week
const delivList = document.getElementById('delivList');
document.getElementById('delivCount').textContent = DATA.delivered_this_week.length;
if (DATA.delivered_this_week.length === 0) {{
  delivList.innerHTML = '<div class="empty">No deliveries confirmed this week yet.</div>';
}} else {{
  DATA.delivered_this_week.forEach(o => {{
    delivList.innerHTML += `
      <div class="card left-bar-green">
        <div class="card-left">
          <div class="card-id">${{o.order_id}}</div>
          <div class="card-client">${{flag(o.territory)}} ${{o.customer_name}}</div>
          <div class="card-meta">
            <span>${{o.territory}}</span>
            <span>Ordered ${{fmt(o.order_date)}}</span>
          </div>
        </div>
        <div class="card-right">
          <div class="card-amount">${{usd(o.total_amount)}}</div>
          <div class="card-date good">Delivered ${{fmt(o.delivered_date)}}</div>
          <div><span class="badge badge-green">Delivered</span></div>
        </div>
      </div>`;
  }});
}}

// -- Summary pills
const pills = document.getElementById('summaryPills');
pills.innerHTML = `
  <span class="pill pill-yellow"><span class="pill-dot"></span>${{DATA.eta_this_week.length}} arriving this week</span>
  <span class="pill pill-red"><span class="pill-dot"></span>${{DATA.late.length}} late ${{DATA.late.length === 1 ? 'order' : 'orders'}}</span>
  <span class="pill pill-green"><span class="pill-dot"></span>${{DATA.delivered_this_week.length}} delivered this week</span>
`;
</script>
</body>
</html>
"""

# ── Generate ──────────────────────────────────────────────────────────────────

def generate():
    data = fetch_data()

    today_obj = date.fromisoformat(data['today'])
    today_fmt = today_obj.strftime('%A, %d %B %Y')

    html = HTML.format(
        today=data['today'],
        today_fmt=today_fmt,
        week_start=data['week_start'],
        week_end=data['week_end'],
    ).replace('__DATA__', json.dumps(data))

    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Briefing written to: {OUT_PATH}")
    print(f"  ETA this week : {len(data['eta_this_week'])}")
    print(f"  Late orders   : {len(data['late'])}")
    print(f"  Delivered     : {len(data['delivered_this_week'])}")

    webbrowser.open('file:///' + OUT_PATH.replace('\\', '/'))


if __name__ == '__main__':
    generate()
