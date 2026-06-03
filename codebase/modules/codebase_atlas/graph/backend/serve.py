from __future__ import annotations

import json
from pathlib import Path
from flask import (
    Flask,
    render_template,
    send_from_directory,
)

from .renderers.interactive_renderer import InteractiveRenderer
from .renderers.mermaid_renderer import MermaidRenderer
from .graph_models import GraphData


ROOT_DIR = Path(__file__).parent.parent

WEB_DIR = ROOT_DIR / "web"


def create_app(
    dep_graph: GraphData,
    call_graph: GraphData,
) -> Flask:

    app = Flask(
        __name__,
        static_folder=str(WEB_DIR),
        template_folder=str(WEB_DIR),
    )

    interactive_renderer = InteractiveRenderer()
    mermaid_renderer = MermaidRenderer()

    dep_json = json.dumps(interactive_renderer.render(dep_graph))
    call_json = json.dumps(interactive_renderer.render(call_graph))

    dep_mermaid = mermaid_renderer.render(dep_graph)
    call_mermaid = mermaid_renderer.render(call_graph)

    @app.route("/")
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
