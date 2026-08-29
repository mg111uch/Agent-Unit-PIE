#!/usr/bin/env python3
"""D6: record an intentional removal as a decision node in project_history.

Routes through kernel semantic memory via argu_god.engine.topic_store
(SQLite canonical); graph.json is regenerated as a derived view.
Idempotent: duplicate node names and (source, target, relation) triples
are never re-added. A contradicts edge between two agreed beliefs raises
a kernel contradiction_detected signal.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "codebase" / "modules"))

from argu_god.engine import topic_store as ts  # noqa: E402
from argu_god.engine.topic_store import TopicStoreError  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GRAPH = PROJECT_ROOT / "data" / "topics" / "project_history" / "graph.json"


def record_removal(name, premise, evidence=None, sources=None,
                   contradicts=None, discipline="Project Archaeology",
                   confidence=1.0, persist=True):
    evidence = list(evidence or [])
    sources = list(sources or [])

    try:
        ts.hydrate()
    except TopicStoreError:
        return []

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
    if persist:
        changes = [ts.add_node("project_history", node)]
        contradictions = []
        if contradicts:
            change = ts.add_edge("project_history", name, contradicts,
                                 "contradicts")
            changes.append(change)
            if change["kind"] == "edge_added":
                contradictions = ts.check_contradictions(
                    "project_history", (name, contradicts))
        return changes if not contradictions else _with_flags(
            changes, contradictions)
    # dry-run: existence checks only, no writes
    exists = ts.find_node("project_history", name) is not None
    changes = [{"kind": "node_skipped" if exists else "node_added", "name": name}]
    if contradicts:
        edge_id = f"edge_contradicts_{name}_{contradicts}".replace(" ", "_")
        known = ts.find_node("project_history", contradicts) is not None
        changes.append({
            "kind": "edge_added" if known and edge_id not in ts.semantic_memory.edges
            else "edge_skipped",
            "source": name, "target": contradicts})
    return changes


def _with_flags(changes, contradictions):
    for pair in contradictions:
        ts.emit_contradiction_signal(pair, "project_history")
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
