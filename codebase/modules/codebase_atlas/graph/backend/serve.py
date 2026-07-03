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

from .graph_models import GraphData
from .graph_serializer import GraphSerializer


ROOT_DIR = Path(__file__).parent.parent

WEB_DIR = ROOT_DIR / "web"

_POS_FILE = {
    "unified": "node_positions.json",
}


def _read_project_id(output_dir: Path) -> str | None:

    meta_file = output_dir / "atlas_meta.json"

    if not meta_file.exists():
        return None

    try:
        return json.loads(
            meta_file.read_text(encoding="utf-8")
        ).get("project_id")
    except Exception:
        return None


def _load_positions_with_meta(
    output_dir: Path,
    graph_type: str,
) -> tuple[str | None, dict | None, dict | None]:

    pos_file = output_dir / _POS_FILE[graph_type]

    if not pos_file.exists():
        return None, None, None

    try:
        data = json.loads(
            pos_file.read_text(encoding="utf-8")
        )
    except Exception:
        return None, None, None

    if not isinstance(data, dict):
        return None, None, None

    if "positions" in data:
        return (
            data.get("project_id"),
            data.get("positions"),
            data.get("child_offsets"),
        )

    return "legacy", data, None


def _merge_positions(
    graph: GraphData,
    output_dir: Path,
    graph_type: str,
) -> None:
    """Overwrite node.x / node.y from saved positions file if it exists."""

    current_project_id = _read_project_id(output_dir)

    if current_project_id is None:
        return

    file_project_id, positions, _ = _load_positions_with_meta(
        output_dir,
        graph_type,
    )

    if positions is None:
        return

    if file_project_id == "legacy":
        pass
    elif file_project_id != current_project_id:
        return

    for node in graph.nodes.values():

        pos = positions.get(node.id)

        if pos is None:
            continue

        node.x = pos.get("x", node.x)
        node.y = pos.get("y", node.y)


def _write_positions(
    output_dir: Path,
    graph_type: str,
    positions: dict,
    project_id: str,
    child_offsets: dict | None = None,
) -> None:

    payload = {
        "project_id": project_id,
        "positions": positions,
    }

    if child_offsets is not None:

        if child_offsets:
            payload["child_offsets"] = child_offsets

    else:
        _, _, existing_offsets = _load_positions_with_meta(
            output_dir,
            graph_type,
        )

        if existing_offsets:
            payload["child_offsets"] = existing_offsets

    pos_file = (
        Path(output_dir) /
        _POS_FILE[graph_type]
    )

    pos_file.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )


def create_app(
    unified_graph: GraphData | None = None,
    output_dir: str | Path | None = None,
    project_id: str | None = None,
) -> Flask:
    """Create app from a unified GraphData object."""

    if unified_graph is None:
        raise ValueError("create_app requires unified_graph")

    if output_dir is not None:
        output_dir = Path(output_dir)
        _merge_positions(unified_graph, output_dir, "unified")

    graph_json = json.dumps(
        GraphSerializer.to_nested_dict(unified_graph)
    )

    return _build_app(
        graph_json=graph_json,
        output_dir=output_dir,
        project_id=project_id,
    )


def _build_app(
    graph_json: str | None = None,
    output_dir: str | Path | None = None,
    project_id: str | None = None,
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
            graph_json=graph_json,
        )

    @app.route("/web/<path:path>")
    def web_assets(path: str):

        return send_from_directory(
            WEB_DIR,
            path,
        )

    @app.route("/api/graph")
    def api_graph():

        if graph_json is None:
            return jsonify(
                {"error": "unified graph not configured"}
            ), 400

        return jsonify(
            json.loads(graph_json)
        )

    @app.route("/api/graph/children/<node_id>")
    def api_graph_children(node_id):

        if graph_json is None:
            return jsonify(
                {"error": "unified graph not configured"}
            ), 400

        try:

            data = json.loads(graph_json)

        except Exception:
            return jsonify(
                {"error": "invalid graph data"}
            ), 500

        children = data.get("children_by_parent", {}).get(
            node_id,
            {"nodes": [], "edges": []}
        )

        return jsonify(children)

    @app.route("/api/save-positions", methods=["POST"])
    def save_positions():

        if output_dir is None:
            return jsonify(
                {"error": "output_dir not configured"}
            ), 400

        if project_id is None:
            return jsonify(
                {"error": "project_id not configured"}
            ), 400

        data = request.get_json(silent=True)

        if not data:
            return jsonify(
                {"error": "invalid JSON"}
            ), 400

        graph_type = data.get("graph_type", "unified")
        positions = data.get("positions")
        child_offsets = data.get("child_offsets")

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

        _write_positions(
            output_dir,
            graph_type,
            rounded,
            project_id,
            child_offsets,
        )

        return jsonify({"saved": True})

    @app.route("/api/child-offsets")
    def api_child_offsets():

        if output_dir is None:
            return jsonify({}), 200

        _, _, child_offsets = _load_positions_with_meta(
            output_dir,
            "unified",
        )

        return jsonify(
            child_offsets or {}
        )

    return app


if __name__ == "__main__":

    unified_graph = GraphData()

    app = create_app(
        unified_graph=unified_graph,
    )

    app.run(
        host="0.0.0.0",
        port=8000,
        debug=True,
    )
