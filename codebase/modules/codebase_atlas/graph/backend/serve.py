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
from .graph_models import GraphData


ROOT_DIR = Path(__file__).parent.parent

WEB_DIR = ROOT_DIR / "web"

_POS_FILE = {
    "dependency": "node_pos_dep.json",
    "call": "node_pos_call.json",
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
) -> tuple[str | None, dict | None]:

    pos_file = output_dir / _POS_FILE[graph_type]

    if not pos_file.exists():
        return None, None

    try:
        data = json.loads(
            pos_file.read_text(encoding="utf-8")
        )
    except Exception:
        return None, None

    if not isinstance(data, dict):
        return None, None

    if "positions" in data:
        return data.get("project_id"), data.get("positions")

    return "legacy", data


def _merge_positions(
    graph: GraphData,
    output_dir: Path,
    graph_type: str,
) -> None:
    """Overwrite node.x / node.y from saved positions file if it exists."""

    current_project_id = _read_project_id(output_dir)

    if current_project_id is None:
        return

    file_project_id, positions = _load_positions_with_meta(
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
) -> None:

    payload = {
        "project_id": project_id,
        "positions": positions,
    }

    pos_file = (
        Path(output_dir) /
        _POS_FILE[graph_type]
    )

    pos_file.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )


def create_app(
    dep_graph: GraphData,
    call_graph: GraphData,
    output_dir: str | Path | None = None,
    project_id: str | None = None,
) -> Flask:
    """Create app from GraphData objects (renders at startup)."""

    if output_dir is not None:
        output_dir = Path(output_dir)
        _merge_positions(dep_graph, output_dir, "dependency")
        _merge_positions(call_graph, output_dir, "call")

    interactive_renderer = InteractiveRenderer()

    dep_json = json.dumps(interactive_renderer.render(dep_graph))
    call_json = json.dumps(interactive_renderer.render(call_graph))

    return _build_app(
        dep_json,
        call_json,
        output_dir=output_dir,
        project_id=project_id,
    )


def _build_app(
    dep_json: str,
    call_json: str,
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
            dep_json=dep_json,
            call_json=call_json,
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

        if project_id is None:
            return jsonify(
                {"error": "project_id not configured"}
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

        _write_positions(
            output_dir,
            graph_type,
            rounded,
            project_id,
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
