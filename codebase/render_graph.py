"""render_graph.py — emit Agent_graph.html from the SQLite workflow graph.

Reads kernel.db (chain_specs / graph_nodes / graph_edges / graph_clusters /
graph_notes) and renders a dagre-d3 HTML with:
  - tool-chain steps as node chains inside colored cluster subgraphs,
  - mining candidates as dashed diamond shortcut edges,
  - observed-usage notes in the toggleable side panel.

Usage:  conda run -n myenv python scripts/render_graph.py [output.html]
"""

import json
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
KERNEL_DB = PROJECT_ROOT / "data" / "kernel.db"
DEFAULT_OUT = PROJECT_ROOT / "Agent_graph.html"

_ESC = str.maketrans({"\\": "\\\\", '"': '\\"', "\n": "\\n"})


def _esc(s):
    return str(s).translate(_ESC)


def _load():
    if not KERNEL_DB.exists():
        raise SystemExit(f"kernel.db not found at {KERNEL_DB}")
    conn = sqlite3.connect(KERNEL_DB)
    conn.row_factory = sqlite3.Row
    nodes = [dict(r) for r in conn.execute("SELECT * FROM graph_nodes").fetchall()]
    edges = [dict(r) for r in conn.execute("SELECT * FROM graph_edges").fetchall()]
    clusters = [dict(r) for r in conn.execute("SELECT * FROM graph_clusters").fetchall()]
    notes = [dict(r) for r in conn.execute(
        "SELECT section, text, tag FROM graph_notes ORDER BY ts DESC LIMIT 60").fetchall()]
    state = conn.execute("SELECT version FROM graph_state WHERE id=1").fetchone()
    conn.close()
    return {"nodes": nodes, "edges": edges, "clusters": clusters,
            "notes": notes, "version": state[0] if state else 0}


def _node_tuple(n):
    return [n["id"], n.get("label", n["id"]), n.get("shape", "rect"),
            n.get("color", "#ffffff"), n.get("cluster_id", "")]


def _edge_tuple(e):
    return [e["src"], e["dst"], e.get("label", "")]


def _cluster_label(c):
    return c.get("label", c["id"])


def _notes_html(notes, version):
    if not notes:
        return "<p>No notes yet — run workflow_status evolve after a session.</p>"
    parts = []
    for n in notes:
        tag = n.get("tag", "do")
        cls = "tag-avoid" if tag == "avoid" else "tag-do"
        parts.append(
            f'<li><span class="tag {cls}">{tag.upper()}</span>'
            f'<strong>{_esc(n["section"])}:</strong> {_esc(n["text"])}</li>')
    return (f"<p style='font-size:11px;color:#aaa;margin-top:-4px;'>"
            f"Graph v{version} — DO/AVOID rules learned from usage.</p>"
            f"<ul>{''.join(parts)}</ul>")


_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<title>Agentic Workflow Graph</title>
<script src="https://d3js.org/d3.v7.min.js"></script>
<script src="https://dagrejs.github.io/project/dagre-d3/latest/dagre-d3.js"></script>
<style>
  html,body {{ margin:0; height:100%; font-family:sans-serif; background:#2a2a2a; color:#fff; overflow:hidden; }}
  svg {{ display:block; width:100vw; height:100vh; background:#2a2a2a; }}
  .node rect, .node ellipse, .node polygon {{ stroke:#ccc; stroke-width:1.5; }}
  .label {{ font-size:12px; pointer-events:none; fill:#000; }}
  .edgePath path {{ stroke:#ccc; stroke-width:1.5; fill:none; }}
  .edgePath.dashed path {{ stroke-dasharray: 5 5; }}
  .edgeLabel {{ font-size:10px; fill:#fff; background:#2a2a2a; }}
  .cluster rect {{ fill:rgba(255,255,255,0.08); stroke:#888; stroke-width:1.5; }}
  .cluster text {{ fill:#ffd866; font-size:13px; font-weight:bold; }}
  #toggle-btn {{ position:fixed; top:12px; right:12px; z-index:100; background:#555; color:#fff;
    border:1px solid #888; padding:8px 14px; border-radius:4px; cursor:pointer; font-size:13px; }}
  #toggle-btn:hover {{ background:#777; }}
  #notes {{ position:fixed; top:52px; right:12px; z-index:100; width:440px; max-height:85vh;
    overflow-y:auto; background:rgba(40,40,40,0.95); border:1px solid #666; border-radius:6px;
    padding:16px; font-size:12px; display:none; line-height:1.5; }}
  #notes h2 {{ margin:0 0 8px 0; font-size:14px; color:#ffd866; }}
  #notes ul {{ margin:4px 0; padding-left:16px; }}
  #notes li {{ margin-bottom:4px; }}
  #notes .tag {{ display:inline-block; font-size:10px; padding:1px 6px; border-radius:3px; margin-right:4px; }}
  .tag-avoid {{ background:#a33; }}
  .tag-do {{ background:#2a6; }}
  code {{ background:#333; padding:1px 4px; border-radius:3px; font-size:11px; }}
</style>
</head>
<body>
<svg id="graph"></svg>
<button id="toggle-btn">☰ Workflow Details</button>
<div id="notes">
  <h2>Agent Workflow Details</h2>
  {notes}
</div>
<script>
// Notes panel must work even if graph rendering fails (e.g. CDN blocked).
document.addEventListener('DOMContentLoaded', () => {{
  document.getElementById('toggle-btn').addEventListener('click', () => {{
    const n = document.getElementById('notes');
    n.style.display = n.style.display === 'none' ? 'block' : 'none';
  }});
}});
const data = {{"nodes":{nodes},"edges":{edges},"clusters":{clusters}}};

try {{
const g = new dagreD3.graphlib.Graph({{compound:true}}).setGraph({{rankdir:'LR', splines:'ortho', nodesep:20, ranksep:30}});

// Cluster subgraphs first (dagre compound nodes).
data.clusters.forEach(([id, label]) => {{
  g.setNode(id, {{label, cluster:true, clusterLabelPos:'top',
    paddingTop:45, paddingBottom:10, paddingLeft:10, paddingRight:10,
    style:'fill:rgba(255,255,255,0.05)', labelStyle:'fill:#ffd866;font-weight:bold;font-size:13px'}});
}});

data.nodes.forEach(([id, label, shape, color, clusterId]) => {{
  const a = {{label, style:`fill:${{color}}`}};
  if (shape === 'ellipse') a.shape = 'ellipse';
  else if (shape === 'diamond') a.shape = 'diamond';
  else a.shape = 'rect';
  g.setNode(id, a);
  if (clusterId) g.setParent(id, clusterId);
}});

data.edges.forEach(([from, to, label, dashed]) => {{
  g.setEdge(from, to, {{label, curve:d3.curveBasis}});
  if (dashed) g.edge(from, to).dash = dashed;
}});

const svg = d3.select('#graph');
const zoomG = svg.append('g');
const inner = zoomG.append('g');
const render = new dagreD3.render();
render(inner, g);
inner.selectAll('.edgeLabel text').attr('fill', '#fff');

const pad = 60;
const gw = g.graph().width, gh = g.graph().height;
const s = Math.max(gw, gh) + pad * 2;
svg.attr('viewBox', `0 0 ${{s}} ${{s}}`).attr('preserveAspectRatio', 'xMidYMid meet');
inner.attr('transform', `translate(${{pad}},${{pad}})`);
svg.call(d3.zoom().on('zoom', (e) => zoomG.attr('transform', e.transform)));
}} catch (err) {{
  const msg = document.createElement('div');
  msg.style.cssText = 'position:fixed;top:12px;left:12px;z-index:200;background:#a33;color:#fff;padding:8px 14px;border-radius:4px;font-family:sans-serif;font-size:13px;';
  msg.textContent = 'Graph render error: ' + err.message;
  document.body.appendChild(msg);
}}
</script>
</body>
</html>
"""


def _render(data):
    nodes = [_node_tuple(n) for n in data["nodes"]]
    edges = [tuple(_edge_tuple(e)) + (False,) for e in data["edges"]]
    clusters = [[c["id"], _cluster_label(c)] for c in data["clusters"]]
    # Dashed edges mark mining candidates (diamond source nodes).
    dashed = {(e[0], e[1]) for e in edges if e[0].startswith("cand_")}
    edges = [list(e) for e in edges]
    for e in edges:
        e[3] = (e[0], e[1]) in dashed
    return _TEMPLATE.format(
        nodes=json.dumps(nodes),
        edges=json.dumps(edges),
        clusters=json.dumps(clusters),
        notes=_notes_html(data["notes"], data["version"]),
    )


def _serve(port: int, open_browser: bool):
    """Serve the rendered graph HTML over HTTP. Re-renders from SQLite per request
    so refreshing the page always shows the latest graph state."""
    import http.server
    import socketserver
    import threading
    import webbrowser

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            if self.path.split("?")[0] == "/graph.json":
                self._send_json()
            else:
                self._send_html()

        def _send_html(self):
            html = _render(_load()).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)

        def _send_json(self):
            payload = json.dumps(_load()).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args):
            pass  # keep the console quiet

    class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
        daemon_threads = True
        allow_reuse_address = True

    with Server(("127.0.0.1", port), Handler) as httpd:
        url = f"http://127.0.0.1:{port}"
        print(f"Serving workflow graph at {url}  (refresh to re-render from SQLite; Ctrl+C to stop)")
        if open_browser:
            threading.Timer(0.5, lambda: webbrowser.open(url)).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Render the workflow graph from SQLite.")
    parser.add_argument("--output", metavar="FILE",
                        help="Write the HTML to FILE (default: serve over HTTP instead)")
    parser.add_argument("--port", type=int, default=8123,
                        help="HTTP port when serving (default 8123)")
    parser.add_argument("--no-browser", action="store_true",
                        help="Do not auto-open the browser when serving")
    args = parser.parse_args()

    if args.output:
        out_path = Path(args.output)
        html = _render(_load())
        out_path.write_text(html)
        print(f"Wrote {out_path} ({len(html)} bytes)")
        return
    _serve(args.port, open_browser=not args.no_browser)


if __name__ == "__main__":
    main()
