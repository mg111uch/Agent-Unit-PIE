from argu_god.engine.vector_store import search_similar

def index_arguments(graph):
    index = {
        "pro": [],
        "con": [],
        "all": []
    }

    for node in graph.get("nodes", []):
        side = node.get("side", "neutral")
        index["all"].append(node)

        if side == "pro":
            index["pro"].append(node)
        elif side == "con":
            index["con"].append(node)

    return index

def get_counter_argument(argument, index):
    side = argument.get("side")

    if side == "pro":
        pool = index["con"]
    elif side == "con":
        pool = index["pro"]
    else:
        pool = index["all"]

    if not pool:
        return None

    return pool[0]  # Phase 2: simple pick

def get_best_counter(argument):
    results = search_similar(argument)

    if not results or not results.get("metadatas"):
        return None

    for meta in results["metadatas"][0]:
        if meta["name"] != argument["name"] and meta["side"] != argument["side"]:
            return meta

    return None