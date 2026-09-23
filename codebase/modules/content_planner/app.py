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


def item_html(it, tag):
    return (f'<li class="it" data-id="{it["id"]}" title="click to load in editor">'
            f'<span class="grip">⠿</span>'
            f'<span class="body">{E(it["body"])}</span>'
            f'</li>')


def topic_html(t):
    p = "\n".join(item_html(i, "ul") for i in t["planned"])
    d = "\n".join(item_html(i, "ul") for i in t["done"])
    return f"""
<details class="topic" open data-topic="{t['id']}">
<summary class="tsum" title="click to load in topic box"><span class="tname">{E(t['name'])}</span><span class="tcounts">{len(t['planned'])} | {len(t['done'])}</span></summary>
<div class="addbox"><textarea class="addinput" rows="3" placeholder="New script — Enter adds to Planned. Click a list item to load it here"></textarea><span class="count">0</span></div>
<div class="ibar"><button type="button" data-ib="add">Add</button><button type="button" data-ib="save" disabled>Save</button><button type="button" data-ib="del" disabled>Del</button><button type="button" data-ib="flip" disabled>Move ⇄</button><button type="button" data-ib="clear" disabled>Clear</button><span class="sel"></span></div>
<details data-sec="planned" open><summary>Planned ({len(t['planned'])})</summary>
<ul class="lst" data-status="planned" data-topic="{t['id']}">{p}</ul></details>
<details data-sec="done"><summary>Done ({len(t['done'])})</summary>
<ul class="lst" data-status="done" data-topic="{t['id']}">{d}</ul></details>
</details>"""


def page():
    st = store.full_state()
    topics = "\n".join(topic_html(t) for t in st["topics"])
    tp = sum(len(t["planned"]) for t in st["topics"])
    td = sum(len(t["done"]) for t in st["topics"])
    return f"""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Content Planner</title>
<script src="https://unpkg.com/htmx.org@1.9.10"></script>
<script src="https://unpkg.com/sortablejs@1.15.2/Sortable.min.js"></script>
<style>:root{{color-scheme:dark}}.topbar{{display:flex;gap:12px;align-items:center;justify-content:space-between;margin-bottom:8px}}.topbar strong{{font-size:1.1em;color:#4da3ff}}.topbar span{{font-weight:700}}#newtopic{{display:flex;gap:6px;align-items:center;flex-wrap:wrap}}#newtopic input{{flex:1;min-width:140px}}#newtopic .tsel{{font-size:11px;opacity:.65}}.topic.tsel{{outline:1px solid #555}}body{{font-family:system-ui;max-width:760px;margin:auto;padding:12px;background:#121214;color:#e8e8ea}}.topic{{border:1px solid #333;background:#1b1b1f;border-radius:8px;padding:8px;margin:10px 0}}.tsum{{font-size:1.2em;font-weight:700;cursor:pointer;display:flex;gap:8px;align-items:center;justify-content:space-between}}.tsum .tcounts{{margin-left:auto;font-size:.8em;font-weight:400;opacity:.75;white-space:nowrap}}.topic>details{{margin-top:12px}}.lst{{min-height:30px;padding:8px;margin:8px 0 2px;border:1px dashed #444;background:#141417;border-radius:6px;list-style:none}}.it{{display:flex;gap:6px;padding:4px;border-bottom:1px solid #2a2a2e;align-items:flex-start;cursor:pointer}}.it.sel{{background:#2c2c38;outline:1px solid #555;border-radius:4px}}.ibar{{display:flex;gap:6px;align-items:center;margin:0 0 10px;flex-wrap:wrap}}.ibar .sel{{font-size:11px;opacity:.65}}button:disabled{{opacity:.4}}.it .body{{flex:1;white-space:pre-wrap}}.grip{{cursor:grab}}input,button,textarea{{background:#26262b;color:#e8e8ea;border:1px solid #444;border-radius:6px;padding:4px 8px}}summary{{cursor:pointer}}.addbox{{position:relative;margin:6px 0 10px}}.addinput{{width:100%;box-sizing:border-box;resize:vertical}}.count{{position:absolute;right:10px;bottom:8px;font-size:11px;opacity:.6;pointer-events:none}}.ebox{{width:100%;box-sizing:border-box}}</style>
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
        self.send_header("HX-Refresh", "true")
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
        if u.path in ("/", "/planner"):
            return self._send(page())
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
        elif p == "/api/move":
            try:
                d = json.loads(self.rfile.read(0) or b"") if False else None
            except Exception:
                pass
            # handled below via raw read fallback
            return self._send("ok")
        # JSON drag payloads
        if self.headers.get("Content-Type", "").startswith("application/json"):
            pass
        return self._send("ok")

    def do_PUT(self):  # JSON drag-drop: {"id":..,"status":..,"index":..}
        if urlparse(self.path).path == "/api/move":
            n = int(self.headers.get("Content-Length", 0))
            d = json.loads(self.rfile.read(n) or b"{}")
            store.move_item(int(d["id"]), d["status"], int(d.get("index", 0)))
            return self._send("ok")
        return self._send("nf", code=404)


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
