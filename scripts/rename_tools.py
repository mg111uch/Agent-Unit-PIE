#!/usr/bin/env python3
"""Rename agent tool identifiers across codebase and project_docs.

Word-boundary replacement so compound identifiers (execute_command_raw,
_read_file_content, cross_file_edit) are never touched. Run later when the
tool rename is wanted; --dry-run shows what would change without writing.

Usage:
    python scripts/rename_tools.py                # apply RENAME map
    python scripts/rename_tools.py --dry-run      # preview only
    python scripts/rename_tools.py --check        # verify no stale refs remain
"""

import argparse
import pathlib
import re

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent

RENAME = {
    "edit_file": "Edit",
    "execute_command": "Bash",
    "glob_search": "Glob",
    "grep_search": "Grep",
}

ROOTS = [PROJECT_ROOT / "codebase", PROJECT_ROOT / "project_docs"]

SKIP_DIRS = {
    "__pycache__", ".git", "node_modules", ".pytest_cache",
    "venv", ".venv", "encoding_cache", "data", "storage",
}

SKIP_FILES = {"code_dump.txt", "condensed.txt", "tui_output.txt"}

SUFFIXES = {".py", ".json", ".md", ".txt", ".toml", ".cfg"}

_PATTERN = re.compile(r"\b(%s)\b" % "|".join(sorted(RENAME, key=len, reverse=True)))


def iter_target_files():
    for root in ROOTS:
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in SUFFIXES or path.name in SKIP_FILES:
                continue
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            yield path


def collect_changes():
    changes = []
    for path in iter_target_files():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if _PATTERN.search(text):
            changes.append(path)
    return changes


def apply(paths):
    renamed = 0
    for path in paths:
        text = path.read_text(encoding="utf-8")
        updated = _PATTERN.sub(lambda m: RENAME[m.group(0)], text)
        if updated != text:
            path.write_text(updated, encoding="utf-8")
            renamed += 1
    return renamed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="report files without rewriting")
    parser.add_argument("--check", action="store_true", help="verify no unrenamed refs remain")
    args = parser.parse_args()

    if args.check:
        stale = [str(p) for p in iter_target_files() if _PATTERN.search(p.read_text(encoding="utf-8", errors="ignore"))]
        print("stale refs:", len(stale))
        for path in stale:
            print(" ", path)
        return

    paths = collect_changes()
    print("files touching old names:", len(paths))
    if args.dry_run:
        for path in paths:
            print(" ", path)
        return

    renamed = apply(paths)
    print("renamed files:", renamed)
    for path in paths:
        print(" ", path)


if __name__ == "__main__":
    main()