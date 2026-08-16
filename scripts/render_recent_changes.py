#!/usr/bin/env python3
"""E7: drive status.md Recent Changes from the last 10 dev_change events.

Hybrid rule: event bullets (summary + paths, newest first) are prepended to
existing manual bullets not already covered by an event, capped at 10 total.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "codebase"))

from kernel.memory.memory_engine import memory_engine
from scripts.lib.citations import discover_status_files, extract_module_name

MAX_ENTRIES = 10
RECENT_TITLE = "Recent Changes"


def load_dev_change_events(limit=MAX_ENTRIES, module=None):
    events = []
    for oid in memory_engine.list_objects("episodic"):
        data = memory_engine.load_object("episodic", oid)
        if not data or data.get("event_type") != "dev_change":
            continue
        extra = (data.get("metadata") or {}).get("extra", {}) or {}
        if module and extra.get("module") != module:
            continue
        events.append(data)
    events.sort(key=lambda d: d.get("timestamp", ""), reverse=True)
    return events[:limit]


def event_bullet(event):
    summary = event.get("description") or event.get("title", "")
    paths = (event.get("metadata") or {}).get("extra", {}).get("paths", [])
    paths = [p for p in paths if p]
    cit = ", ".join(f"`{p}`" for p in paths)
    return f"- {summary} \u2014 {cit}" if cit else f"- {summary}"


def _section_lines(text):
    """Return (header_index, content_lines) of the Recent Changes section."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith("## ") and RECENT_TITLE in line:
            content = []
            for j in range(i + 1, len(lines)):
                if lines[j].strip().startswith("## "):
                    break
                content.append(lines[j])
            return i, content
    return None, None


def render_recent_changes(existing_content, events):
    """Hybrid: event bullets (newest first) + uncovered manual bullets, cap 10."""
    summaries = [e.get("description", "") for e in events]
    event_bullets = [event_bullet(e) for e in events]
    manual = []
    for line in existing_content:
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        if any(s and s in stripped for s in summaries):
            continue
        manual.append(line)
    return (event_bullets + manual)[:MAX_ENTRIES]


def update_status_file(path, events, write=False):
    """Rewrite the Recent Changes section; returns (new_text, num_events) or (None, 0)."""
    if not events:
        return None, 0
    text = path.read_text(encoding="utf-8")
    idx, content = _section_lines(text)
    if idx is None:
        return None, 0
    merged = render_recent_changes(content, events)
    lines = text.splitlines()
    new_lines = lines[: idx + 1] + merged + lines[idx + 1 + len(content):]
    new_text = "\n".join(new_lines)
    if write:
        path.write_text(new_text, encoding="utf-8")
    return new_text, len(events)


def main():
    quiet = "--quiet" in sys.argv or "-q" in sys.argv
    write = "--write" in sys.argv
    module = None
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == "--module" and i + 1 < len(args):
            module = args[i + 1]
    files = [p for p in discover_status_files()
             if not module or extract_module_name(p) == module]
    for path in files:
        mod = extract_module_name(path)
        events = load_dev_change_events(module=mod)
        new_text, n = update_status_file(path, events, write=write)
        if new_text is None:
            continue
        verb = "updated" if write else "preview"
        print(f"{verb} {path.relative_to(PROJECT_ROOT)}: {n} dev_change bullet(s)")
        if not quiet:
            for e in events:
                print(f"  {event_bullet(e)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())