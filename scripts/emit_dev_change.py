#!/usr/bin/env python3
"""E6: emit a dev_change event for an intentional session end.

Records what changed this session (paths + summary) as a kernel event so the
timeline / status pipeline can surface it later.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "codebase"))

from kernel.events.event_engine import event_engine
from kernel.events.timeline_engine import timeline_engine


def emit_dev_change(
    summary: str,
    paths=None,
    module: str = "general",
    importance: float = 0.6,
    persist: bool = True,
):
    """Create + persist a dev_change event carrying changed paths + summary."""
    event = event_engine.create_event(
        event_type="dev_change",
        title=f"Dev change: {summary}",
        description=summary,
        category="development",
        subtype="session_end",
        source_unit_id="agent",
        importance=importance,
        tags=["dev", module, "session_end"],
        metadata={"paths": list(paths or []), "module": module},
        persist=persist,
    )
    for tag in ("dev", module, "session_end"):
        event.add_tag(tag)
    if persist:
        timeline_engine.add_event(event)
    return event


def main():
    quiet = "--quiet" in sys.argv or "-q" in sys.argv
    persist = "--dry-run" not in sys.argv
    summary = ""
    module = "general"
    paths = []
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--summary" and i + 1 < len(args):
            summary = args[i + 1]
            i += 2
        elif a == "--module" and i + 1 < len(args):
            module = args[i + 1]
            i += 2
        elif a in ("--quiet", "-q", "--dry-run"):
            i += 1
        else:
            paths.append(a)
            i += 1
    if not summary:
        print("usage: python scripts/emit_dev_change.py --summary <text> [path ...]")
        return 2
    event = emit_dev_change(summary, paths, module, persist=persist)
    print(f"Emitted dev_change {event.event_id} ({event.metadata.extra.get('paths', [])})")
    if not quiet:
        print(f"  {event.title}")
    return 0


if __name__ == "__main__":
    sys.exit(main())