import json
import os

from .loop import BASE_PATH, load_graph
from .vector_store import index_graph


def expand_topic(topic: str, new_nodes: list, new_edges: list) -> dict:
    graph = load_graph(topic)
    if graph is None:
        return {"status": "error", "message": f"Topic not found: {topic}"}

    existing_names = {n["name"] for n in graph.get("nodes", [])}
    for node in new_nodes:
        name = node.get("name", "")
        if not name:
            return {"status": "error", "message": "Each node must have a 'name' field"}
        if name in existing_names:
            return {"status": "error", "message": f"Node already exists: {name}"}

    graph.setdefault("nodes", []).extend(new_nodes)
    graph.setdefault("edges", []).extend(new_edges)

    path = os.path.join(BASE_PATH, "topics", topic, "graph.json")
    with open(path, "w") as f:
        json.dump(graph, f, indent=2)

    index_graph(graph)

    return {
        "status": "ok",
        "nodes_added": len(new_nodes),
        "edges_added": len(new_edges),
        "total_nodes": len(graph["nodes"]),
        "total_edges": len(graph["edges"]),
    }
