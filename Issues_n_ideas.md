Start by reading `README.md`, `code_atlas.md` in project root to understand the project first.

Since I don't have the exact current `serve.py` source in this chat window, I can't safely produce a line-for-line refactor of your existing file.

However, based on the architecture we've built, the new `serve.py` should have a very different responsibility than the old Mermaid-based version.

The old flow was approximately:

```text
Mindmap
   ↓
Mermaid text
   ↓
Mermaid SVG
   ↓
Inject JS
   ↓
Manipulate SVG
```

The new flow should be:

```text
Mindmap
   ↓
interactive_renderer.py
   ↓
Graph JSON
   ↓
serve.py
   ↓
graph_viewer.html
   ↓
GraphViewer
   ↓
SVG Renderers
```

---

# Recommended Refactored `serve.py`

```python
# serve.py

from pathlib import Path
from flask import (
    Flask,
    jsonify,
    render_template,
    send_from_directory,
)

from interactive_renderer import InteractiveRenderer

# ============================================================================
# Config
# ============================================================================

ROOT_DIR = Path(__file__).parent

WEB_DIR = ROOT_DIR / "web"

app = Flask(
    __name__,
    static_folder=str(WEB_DIR),
    template_folder=str(WEB_DIR),
)

# ============================================================================
# Renderer
# ============================================================================

renderer = InteractiveRenderer()

# ============================================================================
# Graph Source
# ============================================================================

CURRENT_GRAPH = None


def load_graph():
    """
    Replace with your actual graph source.

    Examples:
        mindmap.json
        graph_state.json
        live project graph
    """

    global CURRENT_GRAPH

    if CURRENT_GRAPH is not None:
        return CURRENT_GRAPH

    CURRENT_GRAPH = {
        "nodes": [],
        "edges": [],
        "clusters": [],
    }

    return CURRENT_GRAPH


# ============================================================================
# Routes
# ============================================================================

@app.route("/")
def index():

    return render_template(
        "graph_viewer.html"
    )


@app.route("/api/graph")
def graph_data():

    graph = load_graph()

    interactive_json = (
        renderer.render(graph)
    )

    return jsonify(interactive_json)


# ============================================================================
# Static Files
# ============================================================================

@app.route("/web/<path:path>")
def web_assets(path):

    return send_from_directory(
        WEB_DIR,
        path,
    )


# ============================================================================
# Health
# ============================================================================

@app.route("/api/health")
def health():

    return jsonify({
        "status": "ok"
    })


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=8000,
        debug=True,
    )
```

---

# Required `graph_viewer.html` bootstrap

Your HTML should no longer contain large embedded JS blocks.

Instead:

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Interactive Graph</title>
</head>
<body>

<svg id="graph-svg" width="100%" height="100%">
    <g id="viewport">
        <g id="cluster-layer"></g>
        <g id="edge-layer"></g>
        <g id="node-layer"></g>
        <g id="overlay-layer"></g>
    </g>
</svg>

<script type="module">

import {
    createGraphViewer
} from "./graph_viewer.js";

const response =
    await fetch("/api/graph");

const graphData =
    await response.json();

window.viewer =
    createGraphViewer(graphData);

</script>

</body>
</html>
```

---

# Even Better Architecture

For long-term maintainability, I would split serving into:

```text
serve.py
    ↓

routes/
├── graph_api.py
├── page_routes.py
└── static_routes.py
```

because your project is already evolving beyond a simple graph viewer into:

```text
agent_unit_pie
    ↓
simulation
    ↓
knowledge graph
    ↓
interactive explorer
```

and `serve.py` will otherwise become another 1500-3000 line file like the original implementation.

---

## What I would generate next

Before adding drag/viewport/search, I would verify the rendering pipeline by creating:

```text
web/graph_viewport.js
```

and then updating:

```text
graph_viewer.js
```

to instantiate it.

That will give you:

```text
Backend JSON
      ↓
GraphViewer
      ↓
Renderer
      ↓
Viewport
      ↓
Zoom + Pan
```

which is the minimum usable graph engine.
