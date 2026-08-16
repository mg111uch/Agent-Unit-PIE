#!/usr/bin/env python3
"""D6: record an intentional removal as a decision node in project_history.

Appends a `side=decision` node and a `contradicts` edge to
data/topics/project_history/graph.json. Idempotent: a node with the same name
and an edge with the same (source, target, relation) are never duplicated.
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GRAPH = PROJECT_ROOT / "data" / "topics" / "project_history" / "graph.json"


def _load_graph() -> dict:
    if not GRAPH.exists():
        return {"nodes": [], "edges": []}
    return json.loads(GRAPH.read_text(encoding="utf-8"))


def record_removal(name, premise, evidence=None, sources=None,
                   contradicts=None, discipline="Project Archaeology",
                   confidence=1.0, persist=True):
    evidence = list(evidence or [])
    sources = list(sources or [])
    graph = _load_graph()
    changes = []

    if any(n.get("name") == name for n in graph["nodes"]):
        changes.append({"kind": "node_skipped", "name": name})
    else:
        node = {
            "name": name,
            "side": "decision",
            "premise": premise,
            "evidence": evidence,
            "examples": [],
            "sources": sources,
            "discipline": discipline,
            "confidence": float(confidence),
        }
        graph["nodes"].append(node)
        changes.append({"kind": "node_added", "name": name})

    if contradicts and not any(
        e.get("source") == name and e.get("target") == contradicts
        and e.get("relation") == "contradicts"
        for e in graph["edges"]
    ):
        graph["edges"].append({"source": name, "target": contradicts,
                               "relation": "contradicts"})
        changes.append({"kind": "edge_added", "source": name,
                        "target": contradicts})

    if persist and changes:
        GRAPH.parent.mkdir(parents=True, exist_ok=True)
        GRAPH.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
    return changes


def main():
    args = sys.argv[1:]
    if "--name" not in args or "--premise" not in args:
        print("Usage: record_removal.py --name N --premise P "
              "[--evidence E]... [--source S]... [--contradicts T] "
              "[--discipline D] [--confidence C] [--dry-run] [--json]")
        return 2

    def opt(flag, default=None):
        for i, a in enumerate(args):
            if a == flag and i + 1 < len(args):
                return args[i + 1]
        return default

    def multi(flag):
        out = []
        for i, a in enumerate(args):
            if a == flag and i + 1 < len(args):
                out.append(args[i + 1])
        return out

    quiet = "--quiet" in args or "-q" in args
    dry = "--dry-run" in args
    as_json = "--json" in args

    changes = record_removal(
        name=opt("--name"),
        premise=opt("--premise"),
        evidence=multi("--evidence"),
        sources=multi("--source"),
        contradicts=opt("--contradicts"),
        discipline=opt("--discipline", "Project Archaeology"),
        confidence=opt("--confidence", 1.0),
        persist=not dry,
    )
    if as_json:
        print(json.dumps({"graph": str(GRAPH), "dry_run": dry,
                          "changes": changes}, separators=(",", ":")))
    else:
        if not quiet:
            for c in changes:
                print(f"  {c['kind']:12s} {c.get('name') or c.get('source')}")
        added = [c for c in changes if c["kind"].endswith("_added")]
        print(f"Recorded {len(added)} change(s) in {GRAPH.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
