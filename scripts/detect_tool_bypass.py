#!/usr/bin/env python3
"""O2: detect the tool-bypass pattern — repeated raw Reads on indexed files.

Queries kernel file_access stats for `read` operations on paths that the
codebase atlas indexes (kernel/ plus atlas-indexed roots), and feeds them to
pattern_engine.detect_repeated_events so the "repeated_event" pattern is
surfaced. Reads are cheap meta info; use get_symbol / file_api instead.
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "codebase"))

from kernel.persistence.db import kernel_db
from kernel.schemas.event_schema import EventSchema

THRESHOLD = 3


def _indexed_dirs() -> list:
    """Directories whose files are indexed by the codebase atlas."""
    codebase = PROJECT_ROOT / "codebase"
    dirs = [codebase / "kernel"]
    try:
        from agent_core.tools.code_rag.rag import get_rag
        rag = get_rag()
        indexed = getattr(rag, "indexed_dirs", None) or getattr(rag, "index_paths", None)
        if indexed:
            for d in indexed:
                p = Path(d)
                dirs.append(p if p.is_absolute() else codebase / p)
    except Exception:
        pass
    rel = []
    for d in dirs:
        try:
            rel.append(str(d.relative_to(codebase)))
        except ValueError:
            rel.append(str(d))
    return rel


def _is_indexed(path_str: str, indexed_rels: list) -> bool:
    s = path_str.replace("\\", "/")
    if s.startswith("codebase/"):
        s = s[len("codebase/"):]
    return any(s == rel or s.startswith(rel + "/") for rel in indexed_rels)


def detect_tool_bypass(threshold: int = THRESHOLD) -> list:
    indexed_rels = _indexed_dirs()
    rows = kernel_db.get_file_stats(limit=500)
    hits = []
    events = []
    for r in rows:
        if r["operation"] != "read" or r["access_count"] < threshold:
            continue
        if not _is_indexed(r["file_path"], indexed_rels):
            continue
        hits.append({"file": r["file_path"], "reads": r["access_count"],
                     "last_accessed_at": r["last_accessed_at"]})
        for _ in range(r["access_count"]):
            events.append(EventSchema.create(
                event_type="tool_bypass_read",
                title=str(r["file_path"]),
                description="raw Read on indexed file",
                source_type="system", source_id="agent_core"))
    patterns = []
    if events:
        try:
            from kernel.patterns.pattern_engine import pattern_engine
            patterns = [
                {"pattern_type": p.pattern_type, "title": p.title,
                 "subtype": p.subtype,
                 "event_ids": [e.event_id for e in p.events]}
                for p in pattern_engine.detect_repeated_events(events, threshold)
            ]
        except Exception:
            patterns = []
    return {"hits": hits, "patterns": patterns}


def main():
    quiet = "--quiet" in sys.argv or "-q" in sys.argv
    threshold = THRESHOLD
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == "--threshold" and i + 1 < len(args):
            threshold = int(args[i + 1])
    res = detect_tool_bypass(threshold=threshold)
    if "--json" in args:
        print(json.dumps({"threshold": threshold, **res}, separators=(",", ":")))
    else:
        if not quiet:
            for h in res["hits"]:
                print(f"  {h['file']}: {h['reads']} raw reads (indexed)")
            for p in res["patterns"]:
                print(f"  pattern: {p['title']} [{p['pattern_type']}]")
        print(f"Detected {len(res['hits'])} tool-bypass target(s) (threshold {threshold}). "
              "Prefer get_symbol / get_symbols_meta / file_api for indexed code.")
    return 0


if __name__ == "__main__":
    sys.exit(main())