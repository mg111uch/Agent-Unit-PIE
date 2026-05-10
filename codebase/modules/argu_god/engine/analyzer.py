def detect_contradictions(beliefs, graph):
    contradictions = []

    nodes = {n["name"]: n for n in graph.get("nodes", [])}

    for edge in graph.get("edges", []):
        src = edge["source"]
        tgt = edge["target"]
        relation = edge["relation"]

        if relation == "refutes":
            if src in beliefs["arguments"] and tgt in beliefs["arguments"]:
                s1 = beliefs["arguments"][src]["stance"]
                s2 = beliefs["arguments"][tgt]["stance"]

                if s1 == "agree" and s2 == "agree":
                    contradictions.append((src, tgt))

    return contradictions