"""
Single-file HTML dashboard for MandateX. Served at /dashboard by main.py.
No build step, no frontend framework — plain HTML/CSS/JS polling the API
that already exists. Kept as one string so there's nothing extra to wire up.
"""

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MandateX \u2014 Commerce Mandate &amp; Audit Trail</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #f7f7f5;
    --ink: #1c1f26;
    --muted: #6b7280;
    --line: #d8d8d3;
    --ok: #1e6b4f;
    --ok-bg: #e7f1ec;
    --blocked: #a6402f;
    --blocked-bg: #f5e9e6;
    --accent: #2b3a55;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    background: var(--bg);
    color: var(--ink);
    font-family: 'IBM Plex Sans', sans-serif;
    line-height: 1.5;
  }
  .wrap { max-width: 880px; margin: 0 auto; padding: 48px 24px 80px; }

  header { margin-bottom: 40px; }
  .brand { font-size: 22px; font-weight: 600; letter-spacing: -0.01em; }
  .subhead { color: var(--muted); font-size: 14px; margin-top: 4px; }
  .status {
    display: inline-flex; align-items: center; gap: 8px;
    margin-top: 16px; font-size: 13px; color: var(--muted);
    font-family: 'IBM Plex Mono', monospace;
  }
  .dot {
    width: 7px; height: 7px; border-radius: 50%; background: var(--ok);
    animation: pulse 2s ease-in-out infinite;
  }
  @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.35; } }

  section { margin-bottom: 48px; }
  h2 {
    font-size: 15px; font-weight: 600; margin: 0 0 16px;
    padding-bottom: 8px; border-bottom: 1px solid var(--line);
  }

  .mandate-row {
    display: flex; justify-content: space-between; gap: 24px;
    padding: 10px 0; border-bottom: 1px solid var(--line);
    font-size: 14px;
  }
  .mandate-row:last-child { border-bottom: none; }
  .mandate-label { color: var(--muted); flex-shrink: 0; }
  .mandate-value {
    text-align: right; font-family: 'IBM Plex Mono', monospace; font-size: 13px;
  }
  .tag-list { display: flex; flex-wrap: wrap; gap: 6px; justify-content: flex-end; }
  .tag {
    font-family: 'IBM Plex Mono', monospace; font-size: 12px;
    padding: 2px 8px; border: 1px solid var(--line); border-radius: 3px;
  }
  .tag.deny { color: var(--blocked); border-color: var(--blocked-bg); background: var(--blocked-bg); }
  .tag.allow { color: var(--ok); border-color: var(--ok-bg); background: var(--ok-bg); }

  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  thead th {
    text-align: left; font-weight: 500; color: var(--muted);
    padding: 8px 12px; border-bottom: 1px solid var(--line);
  }
  tbody td {
    padding: 10px 12px; border-bottom: 1px solid var(--line);
    vertical-align: top; font-family: 'IBM Plex Mono', monospace;
  }
  tbody tr:last-child td { border-bottom: none; }
  td.time { color: var(--muted); white-space: nowrap; }
  td.reason { font-family: 'IBM Plex Sans', sans-serif; color: var(--ink); }
  .badge {
    display: inline-block; padding: 2px 8px; border-radius: 3px;
    font-size: 12px; font-family: 'IBM Plex Mono', monospace;
  }
  .badge.ok { color: var(--ok); background: var(--ok-bg); }
  .badge.blocked { color: var(--blocked); background: var(--blocked-bg); }
  .badge.neutral { color: var(--muted); }

  .log-scroll { max-height: 480px; overflow-y: auto; border: 1px solid var(--line); }
  .log-scroll table { margin: 0; }
  .log-scroll thead th { position: sticky; top: 0; background: var(--bg); }
  .empty { padding: 24px 12px; color: var(--muted); font-size: 13px; text-align: center; }

  footer { color: var(--muted); font-size: 12px; font-family: 'IBM Plex Mono', monospace; }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="brand">MandateX</div>
    <div class="subhead">Commerce mandate &amp; live audit trail \u2014 TechBazaar (Razorpay test mode)</div>
    <div class="status"><span class="dot"></span> polling every 2s</div>
  </header>

  <section>
    <h2>Commerce mandate</h2>
    <div id="mandate"><div class="empty">Loading\u2026</div></div>
  </section>

  <section>
    <h2>Audit trail</h2>
    <div class="log-scroll">
      <table>
        <thead>
          <tr><th style="width:90px">Time</th><th style="width:110px">Action</th><th style="width:80px">Amount</th><th style="width:90px">Result</th><th>Reason</th></tr>
        </thead>
        <tbody id="log-body">
          <tr><td colspan="5" class="empty">Waiting for agent activity\u2026</td></tr>
        </tbody>
      </table>
    </div>
  </section>

  <footer>MandateX \u2014 agent permission infrastructure. All payments are Razorpay test mode; no real money moves.</footer>
</div>

<script>
async function loadMandate() {
  try {
    const res = await fetch('/mandate');
    const m = await res.json();
    const el = document.getElementById('mandate');
    el.innerHTML = `
      <div class="mandate-row"><span class="mandate-label">Merchant</span><span class="mandate-value">${m.merchant}</span></div>
      <div class="mandate-row"><span class="mandate-label">Per-order limit</span><span class="mandate-value">\u20b9${m.max_per_order.toLocaleString('en-IN')}</span></div>
      <div class="mandate-row"><span class="mandate-label">Daily limit</span><span class="mandate-value">\u20b9${m.max_per_day.toLocaleString('en-IN')}</span></div>
      <div class="mandate-row"><span class="mandate-label">Confirmation required above</span><span class="mandate-value">\u20b9${m.confirmation_required_above.toLocaleString('en-IN')}</span></div>
      <div class="mandate-row"><span class="mandate-label">Allowed actions</span><span class="mandate-value tag-list">${m.allowed_actions.map(a => `<span class="tag allow">${a}</span>`).join('')}</span></div>
      <div class="mandate-row"><span class="mandate-label">Forbidden actions</span><span class="mandate-value tag-list">${m.forbidden_actions.map(a => `<span class="tag deny">${a}</span>`).join('')}</span></div>
    `;
  } catch (e) { /* server not reachable yet \u2014 stay on loading state */ }
}

function fmtTime(iso) {
  return iso.split('T')[1] || iso;
}

function rowFor(entry) {
  const d = entry.detail;
  let action = entry.event, amount = '\u2014', result = '\u2014', resultClass = 'neutral', reason = '';

  if (entry.event === 'catalog_lookup') {
    action = 'Search';
    reason = `"${d.query}" \u2192 ${d.results_count} match(es)`;
  } else if (entry.event === 'authorization_check' && 'product' in d) {
    action = 'Purchase';
    amount = d.price != null ? `\u20b9${d.price}` : '\u2014';
    result = d.result === 'APPROVED' ? 'Approved' : 'Blocked';
    resultClass = d.result === 'APPROVED' ? 'ok' : 'blocked';
    reason = d.reason;
  } else if (entry.event === 'authorization_check' && 'action' in d) {
    action = d.action.charAt(0).toUpperCase() + d.action.slice(1);
    result = d.result === 'APPROVED' ? 'Approved' : 'Blocked';
    resultClass = d.result === 'APPROVED' ? 'ok' : 'blocked';
    reason = d.reason;
  } else if (entry.event === 'payment') {
    action = 'Payment';
    amount = `\u20b9${d.amount}`;
    if (d.status === 'PAYMENT_FAILED') {
      result = 'Failed'; resultClass = 'blocked'; reason = d.reason;
    } else {
      result = 'Created'; resultClass = 'ok'; reason = `Razorpay order ${d.razorpay_order_id}`;
    }
  } else if (entry.event === 'payment_error') {
    action = 'Payment error'; result = 'Error'; resultClass = 'blocked'; reason = d.error;
  } else if (entry.event === 'agent_intent') {
    action = 'Agent intent';
    reason = `requested "${d.requested_action}" \u2014 ${d.context}`;
  } else if (entry.event === 'user_confirmation') {
    action = 'Confirmation'; result = 'Granted'; resultClass = 'ok'; reason = d.status || '';
  }

  return `<tr>
    <td class="time">${fmtTime(entry.timestamp)}</td>
    <td>${action}</td>
    <td>${amount}</td>
    <td><span class="badge ${resultClass}">${result}</span></td>
    <td class="reason">${reason}</td>
  </tr>`;
}

async function loadLog() {
  try {
    const res = await fetch('/audit-log');
    const entries = await res.json();
    const body = document.getElementById('log-body');
    if (entries.length === 0) {
      body.innerHTML = '<tr><td colspan="5" class="empty">Waiting for agent activity\u2026</td></tr>';
      return;
    }
    body.innerHTML = entries.map(rowFor).join('');
    const scroller = document.querySelector('.log-scroll');
    scroller.scrollTop = scroller.scrollHeight;
  } catch (e) { /* server not reachable yet */ }
}

loadMandate();
loadLog();
setInterval(loadLog, 2000);
</script>
</body>
</html>
"""