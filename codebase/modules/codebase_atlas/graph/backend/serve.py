from __future__ import annotations

import json
from pathlib import Path
from flask import (
    Flask,
    render_template,
    send_from_directory,
    request,
    jsonify,
)

from .renderers.interactive_renderer import InteractiveRenderer
from .renderers.mermaid_renderer import MermaidRenderer
from .graph_models import GraphData


ROOT_DIR = Path(__file__).parent.parent

WEB_DIR = ROOT_DIR / "web"

_POS_FILE = {
    "dependency": "node_pos_dep.json",
    "call": "node_pos_call.json",
}


def _merge_positions(
    graph: GraphData,
    output_dir: Path,
    graph_type: str,
) -> None:
    """Overwrite node.x / node.y from saved positions file if it exists."""

    pos_file = output_dir / _POS_FILE[graph_type]

    if not pos_file.exists():
        return

    try:
        positions = json.loads(
            pos_file.read_text(encoding="utf-8")
        )
    except Exception:
        return

    for node in graph.nodes.values():

        pos = positions.get(node.id)

        if pos is None:
            continue

        node.x = pos.get("x", node.x)
        node.y = pos.get("y", node.y)


def create_app(
    dep_graph: GraphData,
    call_graph: GraphData,
    output_dir: str | Path | None = None,
) -> Flask:
    """Create app from GraphData objects (renders at startup)."""

    if output_dir is not None:
        output_dir = Path(output_dir)
        _merge_positions(dep_graph, output_dir, "dependency")
        _merge_positions(call_graph, output_dir, "call")

    interactive_renderer = InteractiveRenderer()
    mermaid_renderer = MermaidRenderer()

    dep_json = json.dumps(interactive_renderer.render(dep_graph))
    call_json = json.dumps(interactive_renderer.render(call_graph))
    dep_mermaid = mermaid_renderer.render(dep_graph)
    call_mermaid = mermaid_renderer.render(call_graph)

    return _build_app(
        dep_json,
        call_json,
        dep_mermaid,
        call_mermaid,
        output_dir=output_dir,
    )


def _merge_positions_into_json(
    json_str: str,
    output_dir: Path,
    graph_type: str,
) -> str:
    """Parse JSON, merge saved positions into each node, re-serialize."""

    pos_file = output_dir / _POS_FILE[graph_type]

    if not pos_file.exists():
        return json_str

    try:
        positions = json.loads(
            pos_file.read_text(encoding="utf-8")
        )
    except Exception:
        return json_str

    try:
        data = json.loads(json_str)
    except Exception:
        return json_str

    for node in data.get("nodes", []):

        pos = positions.get(node["id"])

        if pos is None:
            continue

        node["position"] = {
            "x": pos.get("x", node.get("position", {}).get("x")),
            "y": pos.get("y", node.get("position", {}).get("y")),
        }

    return json.dumps(data)


def create_app_from_dir(output_dir: str | Path) -> Flask:
    """Create app from pre-saved JSON/text files in output_dir.

    Expects these files:
        interactive_dep.json
        interactive_call.json
        mermaid_dep.txt
        mermaid_call.txt
    """

    output_dir = Path(output_dir)

    dep_json_path = output_dir / "interactive_dep.json"
    call_json_path = output_dir / "interactive_call.json"

    dep_json = dep_json_path.read_text(encoding="utf-8")
    call_json = call_json_path.read_text(encoding="utf-8")

    dep_json = _merge_positions_into_json(dep_json, output_dir, "dependency")
    call_json = _merge_positions_into_json(call_json, output_dir, "call")

    dep_mermaid = (
        output_dir / "mermaid_dep.txt"
    ).read_text(encoding="utf-8")

    call_mermaid = (
        output_dir / "mermaid_call.txt"
    ).read_text(encoding="utf-8")

    return _build_app(
        dep_json,
        call_json,
        dep_mermaid,
        call_mermaid,
        output_dir=output_dir,
    )


def _build_app(
    dep_json: str,
    call_json: str,
    dep_mermaid: str,
    call_mermaid: str,
    output_dir: str | Path | None = None,
) -> Flask:

    app = Flask(
        __name__,
        static_folder=str(WEB_DIR),
        template_folder=str(WEB_DIR),
    )

    @app.route("/view/interactive")
    def index():

        return render_template(
            "graph_viewer.html",
            dep_json=dep_json,
            call_json=call_json,
        )

    @app.route("/view/mermaid")
    @app.route("/view/mermaid/<graph_type>")
    def mermaid_view(graph_type: str = "dependency"):

        return render_template(
            "mermaid_view.html",
            graph_type=graph_type,
            dep_mermaid=dep_mermaid,
            call_mermaid=call_mermaid,
        )

    @app.route("/web/<path:path>")
    def web_assets(path: str):

        return send_from_directory(
            WEB_DIR,
            path,
        )

    @app.route("/api/save-positions", methods=["POST"])
    def save_positions():

        if output_dir is None:
            return jsonify(
                {"error": "output_dir not configured"}
            ), 400

        data = request.get_json(silent=True)

        if not data:
            return jsonify(
                {"error": "invalid JSON"}
            ), 400

        graph_type = data.get("graph_type")
        positions = data.get("positions")

        if graph_type not in ("dependency", "call"):
            return jsonify(
                {"error": "graph_type must be 'dependency' or 'call'"}
            ), 400

        if not isinstance(positions, dict):
            return jsonify(
                {"error": "positions must be an object"}
            ), 400

        rounded = {
            node_id: {
                "x": round(pos["x"]),
                "y": round(pos["y"]),
            }
            for node_id, pos in positions.items()
            if isinstance(pos, dict) and
               "x" in pos and "y" in pos
        }

        pos_file = (
            Path(output_dir) /
            _POS_FILE[graph_type]
        )

        pos_file.write_text(
            json.dumps(rounded, indent=2),
            encoding="utf-8",
        )

        return jsonify({"saved": True})

    return app


if __name__ == "__main__":

    dep_graph = GraphData()
    call_graph = GraphData()

    app = create_app(
        dep_graph,
        call_graph,
    )

    app.run(
        host="0.0.0.0",
        port=8000,
        debug=True,
    )
