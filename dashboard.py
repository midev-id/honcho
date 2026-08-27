"""Ringkas read-only dashboard for the local Honcho instance.

Run with: uv run python dashboard.py
Then open http://localhost:8899

Proxies to the local Honcho API (localhost:8000) using an admin JWT minted
from this project's own AUTH_JWT_SECRET, so no separate token management is
needed. Browser never talks to :8000 directly (avoids CORS entirely).
"""

import json
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from src.security import create_admin_jwt

API_BASE = "http://localhost:8000/v3"
DASH_PORT = 8899
ADMIN_JWT = create_admin_jwt()


def api(method: str, path: str, query: str = "", body: dict | None = None) -> tuple[int, bytes]:
    url = f"{API_BASE}{path}"
    if query:
        url += f"?{query}"
    data = json.dumps(body).encode() if method == "POST" else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {ADMIN_JWT}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><title>Honcho Dashboard</title>
<style>
body{font:14px/1.4 system-ui,sans-serif;margin:0;background:#0f1115;color:#e6e6e6}
header{padding:12px 20px;background:#171a21;border-bottom:1px solid #2a2e38;display:flex;gap:16px;align-items:center}
header b{font-size:16px}
main{padding:20px;max-width:1100px;margin:0 auto}
select,button{background:#1c2029;color:#e6e6e6;border:1px solid #2a2e38;border-radius:6px;padding:6px 10px}
button{cursor:pointer}
button.tab{margin-right:6px}
button.tab.active{background:#3a5bd9;border-color:#3a5bd9}
table{width:100%;border-collapse:collapse;margin-top:12px}
th,td{text-align:left;padding:6px 8px;border-bottom:1px solid #23262f;vertical-align:top}
th{color:#9aa3b2;font-weight:600;font-size:12px;text-transform:uppercase}
tr:hover{background:#161920}
pre{white-space:pre-wrap;word-break:break-word;margin:0;font-size:12px;color:#b7c0cf}
.muted{color:#7d8593}
.err{color:#e06666}
.section{margin-top:18px}
code{background:#1c2029;padding:1px 5px;border-radius:4px}
</style></head>
<body>
<header>
  <b>Honcho Dashboard</b>
  <span class="muted">workspace:</span>
  <select id="wsSelect"></select>
  <span id="status" class="muted"></span>
</header>
<main>
  <div id="tabs" class="section" style="display:none">
    <button class="tab active" data-tab="peers">Peers</button>
    <button class="tab" data-tab="sessions">Sessions</button>
    <button class="tab" data-tab="conclusions">Conclusions</button>
    <button class="tab" data-tab="queue">Queue</button>
  </div>
  <div id="content" class="section"></div>
</main>
<script>
let wsId = null, tab = "peers";

async function jget(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

function esc(s) { return String(s).replace(/[&<>]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;"}[c])); }
function fmtMeta(m) { return m && Object.keys(m).length ? `<pre>${esc(JSON.stringify(m, null, 1))}</pre>` : '<span class="muted">-</span>'; }

async function loadWorkspaces() {
  const data = await jget('/api/workspaces');
  const sel = document.getElementById('wsSelect');
  sel.innerHTML = data.items.map(w => `<option value="${esc(w.id)}">${esc(w.id)}</option>`).join('');
  if (data.items.length) {
    wsId = data.items[0].id;
    document.getElementById('tabs').style.display = '';
    render();
  } else {
    document.getElementById('content').innerHTML = '<p class="muted">Belum ada workspace.</p>';
  }
}

document.getElementById('wsSelect').addEventListener('change', e => { wsId = e.target.value; render(); });
document.querySelectorAll('.tab').forEach(b => b.addEventListener('click', () => {
  document.querySelectorAll('.tab').forEach(x => x.classList.remove('active'));
  b.classList.add('active');
  tab = b.dataset.tab;
  render();
}));

async function render() {
  const el = document.getElementById('content');
  el.innerHTML = '<p class="muted">Memuat...</p>';
  try {
    if (tab === 'peers') {
      const d = await jget(`/api/workspaces/${wsId}/peers`);
      el.innerHTML = `<table><tr><th>ID</th><th>Metadata</th><th>Dibuat</th></tr>` +
        d.items.map(p => `<tr><td><code>${esc(p.id)}</code></td><td>${fmtMeta(p.metadata)}</td><td class="muted">${esc(p.created_at)}</td></tr>`).join('') +
        `</table><p class="muted">${d.total} peer</p>`;
    } else if (tab === 'sessions') {
      const d = await jget(`/api/workspaces/${wsId}/sessions`);
      el.innerHTML = `<table><tr><th>ID</th><th>Aktif</th><th>Metadata</th><th>Dibuat</th></tr>` +
        d.items.map(s => `<tr><td><code>${esc(s.id)}</code></td><td>${s.is_active ? 'ya' : 'tidak'}</td><td>${fmtMeta(s.metadata)}</td><td class="muted">${esc(s.created_at)}</td></tr>`).join('') +
        `</table><p class="muted">${d.total} session</p>`;
    } else if (tab === 'conclusions') {
      const d = await jget(`/api/workspaces/${wsId}/conclusions`);
      el.innerHTML = `<table><tr><th>Observer -> Observed</th><th>Level</th><th>Content</th><th>Dibuat</th></tr>` +
        d.items.map(c => `<tr><td><code>${esc(c.observer_id)}</code> -> <code>${esc(c.observed_id)}</code></td><td>${esc(c.level)}</td><td>${esc(c.content)}</td><td class="muted">${esc(c.created_at)}</td></tr>`).join('') +
        `</table><p class="muted">${d.total} conclusion</p>`;
    } else if (tab === 'queue') {
      const d = await jget(`/api/workspaces/${wsId}/queue`);
      el.innerHTML = `<pre>${esc(JSON.stringify(d, null, 2))}</pre>`;
    }
  } catch (e) {
    el.innerHTML = `<p class="err">Gagal load: ${esc(e.message)}</p>`;
  }
}

loadWorkspaces();
</script>
</body></html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _send(self, status: int, body: bytes, content_type: str = "application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        parts = [p for p in parsed.path.split("/") if p]
        qs = parse_qs(parsed.query)
        page = qs.get("page", ["1"])[0]
        size = qs.get("size", ["50"])[0]

        if parsed.path == "/":
            self._send(200, PAGE.encode(), "text/html; charset=utf-8")
            return

        if parts[:2] == ["api", "workspaces"] and len(parts) == 2:
            status, body = api("POST", "/workspaces/list", f"page={page}&size={size}", {})
            self._send(status, body)
            return

        if parts[:2] == ["api", "workspaces"] and len(parts) == 4 and parts[3] == "peers":
            ws = parts[2]
            status, body = api("POST", f"/workspaces/{ws}/peers/list", f"page={page}&size={size}", {})
            self._send(status, body)
            return

        if parts[:2] == ["api", "workspaces"] and len(parts) == 4 and parts[3] == "sessions":
            ws = parts[2]
            status, body = api("POST", f"/workspaces/{ws}/sessions/list", f"page={page}&size={size}", {})
            self._send(status, body)
            return

        if parts[:2] == ["api", "workspaces"] and len(parts) == 4 and parts[3] == "conclusions":
            ws = parts[2]
            status, body = api("POST", f"/workspaces/{ws}/conclusions/list", f"page={page}&size={size}", {})
            self._send(status, body)
            return

        if parts[:2] == ["api", "workspaces"] and len(parts) == 4 and parts[3] == "queue":
            ws = parts[2]
            status, body = api("GET", f"/workspaces/{ws}/queue/status")
            self._send(status, body)
            return

        self._send(404, b'{"error":"not found"}')


if __name__ == "__main__":
    print(f"Honcho API: {API_BASE}")
    print(f"Dashboard:  http://localhost:{DASH_PORT}")
    HTTPServer(("localhost", DASH_PORT), Handler).serve_forever()
