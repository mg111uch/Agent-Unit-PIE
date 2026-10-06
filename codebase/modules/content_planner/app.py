"""Standalone planner server — stdlib only. Run: conda run -n myenv python codebase/modules/content_planner/app.py"""
from __future__ import annotations
import html
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import store as _s  # fallback
try:
    from codebase.modules.content_planner import store
except ImportError:
    store = _s

E = html.escape
PORT = 8765


import html
import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import store as _s  # fallback
try:
    from codebase.modules.content_planner import store
except ImportError:
    store = _s

E = html.escape
PORT = 8765
TS = "%Y-%m-%d %H:%M"


def fmt_ts(s):
    """-> (compact label, full label). Unknown time renders as an em dash."""
    if not s:
        return "—", ""
    try:
        d = datetime.strptime(s, TS)
    except ValueError:
        return E(s), ""
    n = datetime.now()
    if d.date() == n.date():
        short = d.strftime("%H:%M")
    elif d.year == n.year:
        short = d.strftime("%d %b")
    else:
        short = d.strftime("%d %b %Y")
    return short, d.strftime("%d %b %Y, %H:%M")


def item_html(it):
    return (f'<li class="it" data-id="{it["id"]}" title="click to load in editor">'
            f'<span class="body">{E(it["body"])}</span>'
            f'</li>')


def dot_html(t):
    """Green dot: the one topic holding the newest Done entry across all topics."""
    if not t.get("latest_done"):
        return ""
    _, full = fmt_ts(t.get("last_done_at", ""))
    tip = "last Done entry: " + (full or "time unknown")
    return f'<span class="dot on" title="{E(tip)}"></span>'


def sec_html(t, status):
    """Collapsible section whose <ul> is a 5-row scroll viewport; the rest lazy-load."""
    total, rows = t[f"{status}_total"], t[status]
    lis = "\n".join(item_html(i) for i in rows)
    more = "" if total <= len(rows) else f'<div class="more" title="click to load the next 5">scroll for more · {total - len(rows)} left</div>'
    o = " open" if status == "planned" else ""
    return (f'<details data-sec="{status}"{o}><summary>{status.capitalize()} ({total})</summary>'
            f'<ul class="lst" data-status="{status}" data-topic="{t["id"]}" '
            f'data-offset="{len(rows)}" data-total="{total}">{lis}</ul>{more}</details>')


def topic_body(t):
    """Editor + sections. Only ever rendered for the open topic (see /api/topic/<id>)."""
    return f"""<div class="tbody">
<div class="addbox"><textarea class="addinput" rows="3" placeholder="New script — Enter adds to Planned. Click a list item to load it here"></textarea><span class="count">0</span></div>
<div class="ibar"><button type="button" data-ib="add">Add</button><button type="button" data-ib="save" disabled>Save</button><button type="button" data-ib="del" disabled>Del</button><button type="button" data-ib="flip" disabled>Move ⇄</button><button type="button" data-ib="clear" disabled>Clear</button><span class="sel"></span></div>
{sec_html(t, "planned")}
{sec_html(t, "done")}
</div>"""


def topic_html(t, open_=False):
    o = " open" if open_ else ""
    return (f'<details class="topic"{o} data-topic="{t["id"]}">'
            f'<summary class="tsum" title="click to load in topic box">'
            f'<span class="tname">{E(t["name"])}</span>{dot_html(t)}'
            f'<span class="tcounts">{t["planned_total"]} | {t["done_total"]}</span></summary>'
            + (topic_body(t) if open_ else "")
            + "</details>")


def page(open_tid=None):
    tids = [t["id"] for t in store.list_topics()]
    if open_tid not in tids:
        open_tid = tids[0] if tids else None
    st = store.full_state({open_tid} if open_tid else set())
    topics = "\n".join(topic_html(t, t["id"] == open_tid) for t in st["topics"])
    tp = sum(t["planned_total"] for t in st["topics"])
    td = sum(t["done_total"] for t in st["topics"])
    return f"""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Content Planner</title>
<style>:root{{color-scheme:dark}}.topbar{{display:flex;gap:12px;align-items:center;justify-content:space-between;margin-bottom:8px}}.topbar strong{{font-size:1.1em;color:#4da3ff}}.topbar span{{font-weight:700}}#newtopic{{display:flex;gap:6px;align-items:center;flex-wrap:wrap}}#newtopic input{{flex:1;min-width:140px}}#newtopic .tsel{{font-size:11px;opacity:.65}}.topic.tsel{{outline:1px solid #555}}body{{font-family:system-ui;max-width:760px;margin:auto;padding:12px;background:#121214;color:#e8e8ea}}.topic{{border:1px solid #333;background:#1b1b1f;border-radius:8px;padding:8px;margin:10px 0}}.tsum{{font-size:1.2em;font-weight:700;cursor:pointer;display:flex;gap:8px;align-items:center;justify-content:space-between}}.tsum .tcounts{{margin-left:auto;font-size:.8em;font-weight:400;opacity:.75;white-space:nowrap}}.dot{{width:8px;height:8px;flex:0 0 auto;border-radius:50%}}.dot.on{{background:#33d17a;box-shadow:0 0 6px rgba(51,209,122,.6)}}.topic>details,.tbody>details{{margin-top:12px}}.lst{{box-sizing:border-box;min-height:30px;padding:8px;margin:8px 0 2px;border:1px dashed #444;background:#141417;border-radius:6px;list-style:none}}.lst.scroll{{overflow-y:auto;overscroll-behavior:contain;scrollbar-width:thin;scrollbar-color:#3a3a42 #141417}}.lst.scroll::-webkit-scrollbar{{width:8px}}.lst.scroll::-webkit-scrollbar-thumb{{background:#3a3a42;border-radius:4px}}.more{{font-size:11px;opacity:.55;text-align:center;padding:2px 0 4px;cursor:pointer;user-select:none}}.more:hover{{opacity:.9;text-decoration:underline}}
.it{{display:flex;gap:6px;padding:4px;border-bottom:1px solid #2a2a2e;align-items:flex-start;cursor:pointer}}.it.sel{{background:#2c2c38;outline:1px solid #555;border-radius:4px}}.ibar{{display:flex;gap:6px;align-items:center;margin:0 0 10px;flex-wrap:wrap}}.ibar .sel{{font-size:11px;opacity:.65}}button:disabled{{opacity:.4}}.it .body{{flex:1;white-space:pre-wrap}}input,button,textarea{{background:#26262b;color:#e8e8ea;border:1px solid #444;border-radius:6px;padding:4px 8px}}summary{{cursor:pointer}}.addbox{{position:relative;margin:6px 0 10px}}.addinput{{width:100%;box-sizing:border-box;resize:vertical}}.count{{position:absolute;right:10px;bottom:8px;font-size:11px;opacity:.6;pointer-events:none}}.ebox{{width:100%;box-sizing:border-box}}</style>
<div class="topbar"><strong>Content Planner</strong><span>Planned: {tp} | Done: {td}</span></div>
<form id="newtopic"><input name="name" placeholder="New topic — click a topic to load it here" required><button type="submit">Add</button><button type="button" data-tt="save" disabled>Save</button><button type="button" data-tt="del" disabled>Del</button><button type="button" data-tt="clear" disabled>Clear</button><span class="tsel"></span></form>
<div id=topics>{topics}</div>
<script src="/static/planner.js"></script>"""


class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def _send(self, body, ct="text/html", code=200):
        b = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ct)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/static/planner.js":
            import pathlib
            p = pathlib.Path(__file__).parent / "static" / "planner.js"
            return self._send(p.read_bytes(), "text/javascript")
        if u.path == "/api/state":
            return self._send(json.dumps(store.full_state()), "application/json")
        if u.path == "/api/items":  # lazy slice: ?topic=&status=&offset=&limit=
            q = parse_qs(u.query)
            try:
                tid = int(q.get("topic", ["0"])[0]); off = int(q.get("offset", ["0"])[0])
                lim = int(q.get("limit", [store.PAGE])[0])
            except ValueError:
                return self._send('{"error":"bad args"}', "application/json", 400)
            status = q.get("status", ["planned"])[0]
            if status not in ("planned", "done"):
                status = "planned"
            d = store.items_page(tid, status, off, lim)
            return self._send(json.dumps(d), "application/json")
        if u.path.startswith("/api/topic/"):  # body fragment for a topic the user just opened
            try:
                tid = int(u.path.split("/")[3])
            except ValueError:
                return self._send("bad id", code=400)
            t = next((x for x in store.full_state({tid})["topics"] if x["id"] == tid), None)
            return self._send(topic_body(t) if t else "nf", code=200 if t else 404)
        if u.path in ("/", "/planner"):
            try:
                want = int(parse_qs(u.query).get("topic", ["0"])[0])
            except ValueError:
                want = 0
            return self._send(page(want or None))
        return self._send("nf", code=404)

    def body(self):
        n = int(self.headers.get("Content-Length", 0))
        return parse_qs(self.rfile.read(n).decode())

    def do_POST(self):
        u = urlparse(self.path)
        f = self.body()
        g = lambda k, d="": (f.get(k, [d])[0] or "").strip()
        p = u.path
        if p == "/topics" and g("name"):
            store.create_topic(g("name"))
        elif p.startswith("/topics/") and p.endswith("/delete"):
            store.delete_topic(int(p.split("/")[2]))
        elif p.startswith("/topics/") and p.endswith("/rename"):
            store.rename_topic(int(p.split("/")[2]), g("name"))
        elif p == "/items" and g("body"):
            store.add_item(int(g("topic_id")), g("body"), g("status", "planned"))
        elif p.startswith("/items/") and p.endswith("/delete"):
            store.delete_item(int(p.split("/")[2]))
        elif p.startswith("/items/") and p.endswith("/edit"):
            store.edit_item(int(p.split("/")[2]), g("body"))
        elif p.startswith("/items/") and p.endswith("/move"):
            store.move_item(int(p.split("/")[2]), g("status"))
        return self._send("ok")


def _serve():
    store.init_db()
    print(f"planner on http://localhost:{PORT}  db={store.DB_PATH}")
    HTTPServer(("127.0.0.1", PORT), H).serve_forever()


if __name__ == "__main__":
    import sys
    if "--serve" in sys.argv or "--no-reload" in sys.argv:
        _serve()
    else:  # dev supervisor: restart child server when .py/.js changes
        import subprocess
        import time
        from pathlib import Path
        here = Path(__file__).parent
        watch = [here / "app.py", here / "store.py", here / "__init__.py",
                 here / "static" / "planner.js"]
        print("planner dev auto-reload on  (browser still needs one manual refresh)")
        proc = subprocess.Popen([sys.executable, __file__, "--serve"])
        mtimes = {str(p): p.stat().st_mtime if p.exists() else 0 for p in watch}
        try:
            while True:
                time.sleep(0.5)
                restart = False
                for p in watch:
                    m = p.stat().st_mtime if p.exists() else 0
                    if m != mtimes.get(str(p), 0):
                        mtimes[str(p)] = m
                        restart = True
                if restart:
                    print("change detected — restarting server…")
                    proc.terminate()
                    try:
                        proc.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                    proc = subprocess.Popen([sys.executable, __file__, "--serve"])
        except KeyboardInterrupt:
            proc.terminate()
