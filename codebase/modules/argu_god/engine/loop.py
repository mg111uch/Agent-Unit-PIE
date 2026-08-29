from .topic_store import TopicStoreError, export_graph, hydrate


def load_graph(topic: str):
    """Topic graph view from kernel semantic memory (SQLite is canonical)."""
    try:
        hydrate()
        graph = export_graph(topic)
    except TopicStoreError:
        return None
    return graph if graph["nodes"] else None


def get_next_argument(topic, graph, state, beliefs):
    nodes = graph.get("nodes", [])

    # prioritize arguments user disagrees or unsure
    for node in nodes:
        name = node["name"]

        if name in state["seen_arguments"]:
            continue

        if name in beliefs["arguments"]:
            stance = beliefs["arguments"][name]["stance"]
            if stance in ["disagree", "neutral"]:
                return node

    # fallback
    for node in nodes:
        if node["name"] not in state["seen_arguments"]:
            return node

    return None
