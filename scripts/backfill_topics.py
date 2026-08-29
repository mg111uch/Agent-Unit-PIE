#!/usr/bin/env python3
"""One-shot migration: import legacy topic graph.json into kernel semantic
memory (SQLite), regenerate the derived export, and verify parity.

Usage: python scripts/backfill_topics.py [topic ...]
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "codebase" / "modules"))

from argu_god.engine import topic_store as ts  # noqa: E402


def backfill_and_verify(topic: str) -> bool:
    stats = ts.backfill(topic)
    ok = (stats["json_nodes"] == stats["store_nodes"]
          and stats["json_edges"]
          == stats["store_edges"] + stats["edges_unresolvable"])
    if stats["edges_unresolvable"]:
        # Edges whose endpoints never existed as nodes: dropped from the
        # canonical store on purpose (dangling legacy references).
        status = f"WARN ({stats['edges_unresolvable']} dangling edge(s) dropped)"
    else:
        status = "OK"
    print(f"{topic}: json(n={stats['json_nodes']},e={stats['json_edges']}) -> "
          f"store(n={stats['store_nodes']},e={stats['store_edges']}) {status}")
    return ok


def main():
    topics = sys.argv[1:] or ["theism_atheism", "project_history"]
    results = []
    for topic in topics:
        try:
            results.append(backfill_and_verify(topic))
        except ts.TopicStoreError as e:
            print(f"{topic}: error: {e}", file=sys.stderr)
            results.append(False)
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
