import json
import os

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_graph(topic: str):
    path = os.path.join(BASE_PATH, "topics", topic, "graph.json")
    
    if not os.path.exists(path):
        return None

    with open(path, "r") as f:
        return json.load(f)
    
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



