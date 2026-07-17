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

def map_choice_to_stance(choice):
    if choice == 1:
        return "agree", 0.7
    elif choice == 2:
        return "disagree", 0.7
    elif choice == 3:
        return "neutral", 0.5
    elif choice == 4:
        return "custom", 0.6

