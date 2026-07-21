from argu_god.engine.vector_store import search_similar


def get_best_counter(argument):
    results = search_similar(argument)

    if not results or not results.get("metadatas"):
        return None

    for meta in results["metadatas"][0]:
        if meta["name"] != argument["name"] and meta["side"] != argument["side"]:
            return meta

    return None
