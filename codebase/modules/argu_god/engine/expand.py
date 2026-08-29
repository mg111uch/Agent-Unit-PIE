from .topic_store import TopicStoreError, add_edge, add_node, export_graph
from .topic_store import hydrate, write_export


def expand_topic(topic: str, new_nodes: list, new_edges: list) -> dict:
    """Add nodes/edges via topic_store; keeps strict duplicate-error contract."""
    try:
        hydrate()
        graph = export_graph(topic)
    except TopicStoreError:
        return {"status": "error", "message": f"Topic not found: {topic}"}

    existing_names = {n["name"] for n in graph.get("nodes", [])}
    for node in new_nodes:
        name = node.get("name", "")
        if not name:
            return {"status": "error", "message": "Each node must have a 'name' field"}
        if name in existing_names:
            return {"status": "error", "message": f"Node already exists: {name}"}

    for node in new_nodes:
        res = add_node(topic, node, write=False)
        if res.get("kind") == "blocked_contradiction":
            return {"status": "blocked", "reason": res["reason"], "conflicts": res["conflicts"], "blocked_node": node.get("name")}
    for edge in new_edges:
        try:
            res = add_edge(topic, edge.get("source", ""), edge.get("target", ""),
                     edge.get("relation", "related"), write=False,
                     allow_legacy_relation=True)
            if isinstance(res, dict) and res.get("kind") == "blocked_contradiction":
                return {"status": "blocked", "reason": res["reason"], "conflicts": res["conflicts"]}
        except TopicStoreError:
            pass

    graph = write_export(topic)

    from .vector_store import index_graph
    index_graph(graph)

    return {
        "status": "ok",
        "nodes_added": len(new_nodes),
        "edges_added": len(new_edges),
        "total_nodes": len(graph["nodes"]),
        "total_edges": len(graph["edges"]),
    }
