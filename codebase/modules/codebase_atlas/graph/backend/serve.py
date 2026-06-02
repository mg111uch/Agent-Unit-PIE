from pathlib import Path
from flask import (
    Flask,
    jsonify,
    render_template,
    send_from_directory,
)

from renderers.interactive_renderer import InteractiveRenderer

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