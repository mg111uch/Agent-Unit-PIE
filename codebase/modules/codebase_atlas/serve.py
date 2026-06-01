"""Local HTTP server for interactive graph exploration.

Provides a standalone --serve CLI mode that starts a browser-based
Mermaid graph viewer for exploring dependency and call graphs.
"""

import json
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler

from .config import AtlasConfig
from .models import AtlasData
from .generators.mermaid_generator import MermaidGenerator


HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Codebase Atlas - Graph Explorer</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        svg, svg * {{ box-sizing: content-box; }}
        body {{ background: #1a1a2e; color: #e0e0e0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
        #toolbar {{ background: #16213e; padding: 12px 24px; display: flex; align-items: center; gap: 16px; border-bottom: 1px solid #0f3460; flex-wrap: wrap; }}
        #toolbar h1 {{ font-size: 18px; font-weight: 600; color: #e94560; }}
        #toolbar select, #toolbar button {{ background: #0f3460; color: #e0e0e0; border: 1px solid #1a1a4e; padding: 6px 12px; border-radius: 4px; font-size: 13px; cursor: pointer; outline: none; }}
        #toolbar select:hover, #toolbar button:hover {{ background: #1a1a4e; }}
        #toolbar .stats {{ font-size: 12px; color: #888; margin-left: auto; }}
        #graph-container {{ width: 100vw; height: calc(100vh - 52px); overflow: hidden; cursor: grab; user-select: none; position: relative; }}
        #graph-container.panning {{ cursor: grabbing; }}
        #graph-viewport {{ width: 100%; height: 100%; transform-origin: 0 0; }}
        .node {{ cursor: move; }}
        .node.dragging {{ cursor: grabbing; }}
        .graph-wrapper {{ display: none; }}
        .graph-wrapper.active {{ display: block; }}
        .graph-wrapper.active pre.mermaid {{ transition: none; overflow: visible; }}
        .graph-wrapper.active pre.mermaid {{ overflow: visible; }}
        .graph-wrapper.active pre.mermaid svg {{ max-width: none !important; overflow: visible; }}
        .graph-wrapper.active pre.mermaid svg foreignObject {{ overflow: visible !important; }}
        .legend {{ display: flex; gap: 16px; font-size: 12px; align-items: center; }}
        .legend-item {{ display: flex; align-items: center; gap: 4px; }}
        .legend-dot {{ width: 12px; height: 12px; border-radius: 2px; display: inline-block; }}
    </style>
</head>
<body>
    <div id="toolbar">
        <h1>&#x1F5FA;&#xFE0F; Codebase Atlas</h1>
        <select id="graph-type">
            <option value="dependency">Dependency Graph</option>
            <option value="call">Function Call Graph</option>
        </select>
        <div class="legend">
            <span class="legend-item"><span class="legend-dot" style="background:#4CAF50;"></span> Entry</span>
            <span class="legend-item"><span class="legend-dot" style="background:#f44336;"></span> High Risk</span>
            <span class="legend-item"><span class="legend-dot" style="background:#FF9800;"></span> Medium Risk</span>
            <span class="legend-item"><span class="legend-dot" style="background:#FFEB3B;"></span> Low Risk</span>
            <span class="legend-item"><span class="legend-dot" style="background:#9C27B0;border:1px dashed #6A1B9A;"></span> Circular Dep</span>
        </div>
        <button id="reset-zoom" onclick="resetZoom()" title="Reset zoom to 100%">⟲ Reset Zoom</button>
        <button id="reset-layout" onclick="resetLayout()" title="Reset node positions to default">⟳ Reset Layout</button>
        <span id="zoom-level" style="font-size:12px;color:#888;min-width:36px;">100%</span>
        <span class="stats">
            {files_count} files | {funcs_count} functions | {deps_count} dependencies
        </span>
    </div>
    <div id="graph-container">
        <div id="graph-viewport">
            <div id="graph-dependency" class="graph-wrapper"></div>
            <div id="graph-call" class="graph-wrapper"></div>
        </div>
    </div>
    <script>
        var MERMAID_SOURCES = {{
            dependency: {dependency_json},
            call: {call_json}
        }};

        var zoomLevel = 1.0;
        var panX = 0, panY = 0;
        var initialZoom = 1.0;
        var initialPanX = 0, initialPanY = 0;
        var ZOOM_STEP = 0.25;
        var MAX_ZOOM = 5.0;
        var MIN_ZOOM = 0.25;

        var container = document.getElementById('graph-container');
        var viewport = document.getElementById('graph-viewport');
        var currentType = 'dependency';

        // --- Node drag state ---
        var nodePositions = {{}};
        var dragNode = null;
        var dragNodeId = null;
        var dragStartX = 0, dragStartY = 0;
        var dragNodeBaseX = 0, dragNodeBaseY = 0;
        var isNodeDrag = false;
        var nodeEdges = {{}};

        function loadNodePositions() {{
            try {{ nodePositions = JSON.parse(localStorage.getItem('atlas-node-positions') || '{{}}'); }} catch(e) {{ nodePositions = {{}}; }}
        }}
        function saveNodePositions() {{
            localStorage.setItem('atlas-node-positions', JSON.stringify(nodePositions));
        }}
        function resetLayout() {{
            nodePositions = {{}};
            saveNodePositions();
            renderGraph(currentType);
        }}

        function findNodeEl(el) {{
            while (el && el !== container) {{
                if (el.classList && el.classList.contains('node')) return el;
                el = el.parentElement;
            }}
            return null;
        }}

        function getNodePos(g) {{
            var t = g.getAttribute('transform') || '';
            var m = t.match(/translate\\(([^,]+),([^)]+)\\)/);
            if (m) return {{x: parseFloat(m[1]), y: parseFloat(m[2])}};
            return {{x: 0, y: 0}};
        }}

        // --- Edge path helpers ---
        function parseCoords(d) {{
            var coords = [];
            var segs = d.match(/[MCQLTZ][^MCQLTZ]*/g) || [];
            segs.forEach(function(seg) {{
                var nums = seg.match(/[-+]?\\d*\\.?\\d+(?:[eE][-+]?\\d+)?/g);
                if (!nums) return;
                for (var i = 0; i + 1 < nums.length; i += 2) {{
                    coords.push({{x: parseFloat(nums[i]), y: parseFloat(nums[i+1])}});
                }}
            }});
            return coords;
        }}

        function rebuildPath(d, modifyFn) {{
            var parts = d.split(/([MCQLTZ])/);
            var total = 0;
            for (var i = 0; i < parts.length; i++) {{
                if (/^[MCQLTZ]$/.test(parts[i])) continue;
                var nums = parts[i].match(/[-+]?\\d*\\.?\\d+(?:[eE][-+]?\\d+)?/g);
                if (nums) total += Math.floor(nums.length / 2);
            }}
            var pairIdx = 0;
            for (var i = 0; i < parts.length; i++) {{
                var p = parts[i];
                if (/^[MCQLTZ]$/.test(p)) continue;
                var nums = p.match(/[-+]?\\d*\\.?\\d+(?:[eE][-+]?\\d+)?/g);
                if (!nums) continue;
                var newNums = [];
                for (var j = 0; j + 1 < nums.length; j += 2) {{
                    var x = parseFloat(nums[j]);
                    var y = parseFloat(nums[j+1]);
                    var r = modifyFn(x, y, pairIdx, total);
                    newNums.push(r.x + ',' + r.y);
                    pairIdx++;
                }}
                parts[i] = ' ' + newNums.join(' ');
            }}
            return parts.join('');
        }}

        function findClosestNode(pt, nodeMap, threshold) {{
            var best = null;
            var bestDist = threshold || 50;
            for (var id in nodeMap) {{
                var n = nodeMap[id];
                var d = Math.abs(pt.x - n.x) + Math.abs(pt.y - n.y);
                if (d < bestDist) {{ bestDist = d; best = id; }}
            }}
            return best;
        }}

        function buildNodeEdgeMap(type) {{
            nodeEdges = {{}};
            var svg = document.querySelector('#graph-' + type + ' .mermaid svg');
            if (!svg) return;
            var nps = {{}};
            svg.querySelectorAll('g.node').forEach(function(g) {{
                if (g.id) nps[g.id] = getNodePos(g);
            }});
            var edgeCount = 0;
            svg.querySelectorAll('path').forEach(function(p) {{
                if (p.closest('g.node')) return;
                var d = p.getAttribute('d') || '';
                if (!d.match(/^M\\s/i)) return;
                var c = parseCoords(d);
                if (c.length < 2) return;
                var src = findClosestNode(c[0], nps, 150);
                var dst = findClosestNode(c[c.length - 1], nps, 150);
                if (src && dst) {{
                    edgeCount++;
                    if (!nodeEdges[src]) nodeEdges[src] = [];
                    nodeEdges[src].push({{path: p, role: 'source'}});
                    if (dst !== src) {{
                        if (!nodeEdges[dst]) nodeEdges[dst] = [];
                        nodeEdges[dst].push({{path: p, role: 'target'}});
                    }}
                }}
            }});
        }}

        function applyNodePositions(type) {{
            var svg = document.querySelector('#graph-' + type + ' .mermaid svg');
            if (!svg) return;
            var mermaidPos = {{}};
            svg.querySelectorAll('g.node').forEach(function(g) {{
                if (g.id) mermaidPos[g.id] = getNodePos(g);
            }});
            svg.querySelectorAll('g.node').forEach(function(g) {{
                if (g.id && nodePositions[g.id]) {{
                    var mPos = mermaidPos[g.id];
                    var sPos = nodePositions[g.id];
                    var dx = sPos.x - (mPos ? mPos.x : 0);
                    var dy = sPos.y - (mPos ? mPos.y : 0);
                    g.setAttribute('transform', 'translate(' + sPos.x + ',' + sPos.y + ')');
                    if (dx !== 0 || dy !== 0) updateEdgePaths(g.id, dx, dy);
                }}
            }});
        }}

        function getSubgraphBounds(type) {{
            var svg = document.querySelector('#graph-' + type + ' .mermaid svg');
            if (!svg) return [];
            var clusters = [];
            svg.querySelectorAll('g.cluster').forEach(function(g) {{
                var rect = g.querySelector('rect');
                if (!rect) return;
                try {{
                    var b = rect.getBBox();
                    clusters.push({{x: b.x, y: b.y, w: b.width, h: b.height}});
                }} catch(e) {{}}
            }});
            return clusters;
        }}

        function clampInSubgraph(x, y, nodeId, clusters, padding) {{
            padding = padding || 10;
            for (var i = 0; i < clusters.length; i++) {{
                var c = clusters[i];
                if (x >= c.x && x <= c.x + c.w && y >= c.y && y <= c.y + c.h) {{
                    return {{
                        x: Math.max(c.x + padding, Math.min(c.x + c.w - padding, x)),
                        y: Math.max(c.y + padding, Math.min(c.y + c.h - padding, y))
                    }};
                }}
            }}
            return {{x: x, y: y}};
        }}

        function applyTransform() {{
            viewport.style.transform = 'translate(' + panX + 'px, ' + panY + 'px) scale(' + zoomLevel + ')';
            document.getElementById('zoom-level').textContent = Math.round(zoomLevel * 100) + '%';
        }}

        function resetZoom() {{
            zoomLevel = initialZoom;
            panX = initialPanX;
            panY = initialPanY;
            applyTransform();
        }}

        function renderGraph(type) {{
            currentType = type;
            document.querySelectorAll('.graph-wrapper').forEach(function(el) {{
                el.classList.remove('active');
                el.innerHTML = '';
            }});
            var wrapper = document.getElementById('graph-' + type);
            if (!wrapper) return;
            wrapper.innerHTML = '<pre class="mermaid">' + MERMAID_SOURCES[type] + '</pre>';
            wrapper.classList.add('active');
            mermaid.run({{ querySelector: '#graph-' + type + ' .mermaid' }}).then(function() {{
                fitGraph();
                buildNodeEdgeMap(type);
                applyNodePositions(type);
            }});
        }}

        function fitGraph() {{
            var svg = document.querySelector('.graph-wrapper.active .mermaid svg');
            if (!svg) return;
            var cw = container.clientWidth;
            var ch = container.clientHeight;
            var sw, sh;

            if (svg.viewBox && svg.viewBox.baseVal && svg.viewBox.baseVal.width) {{
                sw = svg.viewBox.baseVal.width;
                sh = svg.viewBox.baseVal.height;
            }} else {{
                sw = svg.scrollWidth || svg.getBoundingClientRect().width;
                sh = svg.scrollHeight || svg.getBoundingClientRect().height;
            }}
            if (!sw || !sh || sw === 0 || sh === 0) return;

            var scaleX = cw / sw;
            var scaleY = ch / sh;
            zoomLevel = Math.min(scaleX, scaleY) * 0.9;
            panX = (cw - sw * zoomLevel) / 2;
            panY = (ch - sh * zoomLevel) / 2;
            initialZoom = zoomLevel;
            initialPanX = panX;
            initialPanY = panY;
            applyTransform();
        }}

        function updateEdgePaths(nodeId, dx, dy) {{
            var edges = nodeEdges[nodeId];
            if (!edges) return;
            edges.forEach(function(e) {{
                var d = e.path.getAttribute('d') || '';
                if (e.role === 'source') {{
                    d = rebuildPath(d, function(x, y, idx) {{
                        if (idx <= 1) return {{x: x + dx, y: y + dy}};
                        return {{x: x, y: y}};
                    }});
                }} else {{
                    d = rebuildPath(d, function(x, y, idx, total) {{
                        if (idx >= total - 2) return {{x: x + dx, y: y + dy}};
                        return {{x: x, y: y}};
                    }});
                }}
                e.path.setAttribute('d', d);
            }});
        }}

        // Mouse down: node drag or canvas pan
        container.addEventListener('mousedown', function(e) {{
            if (e.button !== 0) return;

            var nodeEl = findNodeEl(e.target);
            if (nodeEl) {{
                // --- Node drag ---
                e.preventDefault();
                isNodeDrag = true;
                dragNode = nodeEl;
                dragNodeId = nodeEl.id || '';
                var pos = getNodePos(nodeEl);
                dragNodeBaseX = pos.x;
                dragNodeBaseY = pos.y;
                dragStartX = e.clientX;
                dragStartY = e.clientY;
                nodeEl.classList.add('dragging');

                var clusters = currentType === 'call' ? getSubgraphBounds(currentType) : [];
                var lastX = dragNodeBaseX, lastY = dragNodeBaseY;
                var onMove = function(me) {{
                    var dx = me.clientX - dragStartX;
                    var dy = me.clientY - dragStartY;
                    var newX = dragNodeBaseX + dx / zoomLevel;
                    var newY = dragNodeBaseY + dy / zoomLevel;
                    if (clusters.length > 0) {{
                        var clamped = clampInSubgraph(newX, newY, dragNodeId, clusters);
                        newX = clamped.x;
                        newY = clamped.y;
                    }}
                    var incX = newX - lastX;
                    var incY = newY - lastY;
                    dragNode.setAttribute('transform', 'translate(' + newX + ',' + newY + ')');
                    if (dragNodeId) updateEdgePaths(dragNodeId, incX, incY);
                    lastX = newX;
                    lastY = newY;
                }};
                var onUp = function(ue) {{
                    dragNode.classList.remove('dragging');
                    document.removeEventListener('mousemove', onMove);
                    document.removeEventListener('mouseup', onUp);
                    if (dragNodeId) {{
                        var finalPos = getNodePos(dragNode);
                        nodePositions[dragNodeId] = {{x: finalPos.x, y: finalPos.y}};
                        saveNodePositions();
                    }}
                    dragNode = null;
                    dragNodeId = null;
                    isNodeDrag = false;
                }};
                document.addEventListener('mousemove', onMove);
                document.addEventListener('mouseup', onUp);
                return;
            }}

            // --- Canvas pan (existing behavior) ---
            var panStartX = e.clientX, panStartY = e.clientY;
            var panStartPX = panX, panStartPY = panY;
            var wasDragged = false;
            container.classList.add('panning');

            var onMove = function(me) {{
                var dx = me.clientX - panStartX;
                var dy = me.clientY - panStartY;
                if (Math.abs(dx) > 5 || Math.abs(dy) > 5) {{
                    wasDragged = true;
                    panX = panStartPX + dx;
                    panY = panStartPY + dy;
                    applyTransform();
                }}
            }};
            var onUp = function(ue) {{
                container.classList.remove('panning');
                document.removeEventListener('mousemove', onMove);
                document.removeEventListener('mouseup', onUp);
                if (!wasDragged) {{
                    zoomAt(ue.clientX, ue.clientY);
                }}
            }};
            document.addEventListener('mousemove', onMove);
            document.addEventListener('mouseup', onUp);
        }});

        function zoomAt(cx, cy) {{
            if (zoomLevel >= MAX_ZOOM) return;
            var oldZoom = zoomLevel;
            zoomLevel = Math.min(zoomLevel + ZOOM_STEP, MAX_ZOOM);
            var rect = container.getBoundingClientRect();
            var mx = cx - rect.left;
            var my = cy - rect.top;
            panX = mx - (mx - panX) * (zoomLevel / oldZoom);
            panY = my - (my - panY) * (zoomLevel / oldZoom);
            applyTransform();
        }}

        // Ctrl+scroll to zoom in/out at mouse position
        container.addEventListener('wheel', function(e) {{
            if (!e.ctrlKey && !e.metaKey) return;
            e.preventDefault();
            var oldZoom = zoomLevel;
            var delta = e.deltaY > 0 ? -ZOOM_STEP : ZOOM_STEP;
            zoomLevel = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, zoomLevel + delta));
            var rect = container.getBoundingClientRect();
            var mx = e.clientX - rect.left;
            var my = e.clientY - rect.top;
            panX = mx - (mx - panX) * (zoomLevel / oldZoom);
            panY = my - (my - panY) * (zoomLevel / oldZoom);
            applyTransform();
        }});

        container.addEventListener('contextmenu', function(e) {{ e.preventDefault(); }});

        // Tab switch
        document.getElementById('graph-type').addEventListener('change', function() {{
            renderGraph(this.value);
        }});

        // Init
        loadNodePositions();
        mermaid.initialize({{
            theme: 'dark',
            startOnLoad: false,
            flowchart: {{ useMaxWidth: false, htmlLabels: true, nodeSpacing: 30, rankSpacing: 60 }},
            securityLevel: 'loose',
        }});
        renderGraph('dependency');
    </script>
</body>
</html>
"""


def build_graph_html(atlas_data: AtlasData, config: AtlasConfig) -> str:
    """Build HTML page with embedded Mermaid graphs."""
    generator = MermaidGenerator(config, atlas_data)
    dep_graph = generator.generate_dependency_graph()
    call_graph = generator.generate_call_graph()

    files_count = len(atlas_data.files)
    funcs_count = sum(len(f.get_all_functions()) for f in atlas_data.files)
    deps_count = len(atlas_data.dependency_graph.edges)

    return HTML_TEMPLATE.format(
        dependency_json=json.dumps(dep_graph),
        call_json=json.dumps(call_graph),
        files_count=files_count,
        funcs_count=funcs_count,
        deps_count=deps_count,
    )


class _GraphHandler(BaseHTTPRequestHandler):
    """HTTP handler serving the graph explorer HTML."""
    html_content = ""

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(self.html_content.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, fmt, *args):
        print(f"  [{self.address_string()}] {fmt % args}")


def serve_atlas(
    atlas_data: AtlasData,
    config: AtlasConfig,
    host: str = '127.0.0.1',
    port: int = 8080,
    open_browser: bool = True,
):
    """Start local HTTP server to explore dependency and call graphs.

    Args:
        atlas_data: Complete atlas analysis data
        config: Atlas configuration
        host: Host to bind the HTTP server to
        port: Port to bind the HTTP server to
        open_browser: Whether to open the browser automatically
    """
    html = build_graph_html(atlas_data, config)

    handler = type('Handler', (_GraphHandler,), {'html_content': html})
    server = HTTPServer((host, port), handler)

    print()
    print("=" * 60)
    print("  CODEBASE ATLAS - GRAPH EXPLORER")
    print("=" * 60)
    print(f"  Local URL:  http://{host}:{port}")
    print()
    print("  Views:")
    print("    - Dependency Graph: file-level dependencies")
    print("    - Call Graph:       function call relationships")
    print()
    print("  Press Ctrl+C to stop the server")
    print("=" * 60)
    print()

    if open_browser:
        webbrowser.open(f'http://{host}:{port}')

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down graph explorer...")
        server.shutdown()
