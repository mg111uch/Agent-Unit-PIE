#!/usr/bin/env python3
"""Verify file.py:function() citations in system_devpt_reports/*.md against codebase.

Queries code_rag.db first, then falls back to direct grep for non-indexed modules."""

import re
import sys
import sqlite3
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "system_devpt_reports"
CODEBASE_DIR = PROJECT_ROOT / "codebase"
ATLAS_DB = PROJECT_ROOT / "atlas_output" / "code_rag.db"

CITATION_RE = re.compile(r'(\w+\.py):(\w+)\(\)')

SKIP_FILES = {"file.py"}  # template patterns, not real citations


def resolve_via_atlas(cur, filename, func_name):
    row = cur.execute(
        "SELECT symbol_name FROM symbols WHERE symbol_name = ? AND file_path LIKE ?",
        (func_name, f"%/{filename}"),
    ).fetchone()
    return row is not None


def resolve_via_grep(filename, func_name):
    result = subprocess.run(
        ["grep", "-rl", f"def {func_name}(", str(CODEBASE_DIR), "--include", filename],
        capture_output=True, text=True, timeout=30,
    )
    return bool(result.stdout.strip())


def main():
    run_validate = "--validate" in sys.argv

    atlas_available = ATLAS_DB.exists()
    conn = None
    cur = None
    if atlas_available:
        conn = sqlite3.connect(str(ATLAS_DB))
        cur = conn.cursor()
    else:
        print(f"NOTE: atlas db not found at {ATLAS_DB}, using direct grep fallback")

    failed = 0
    passed = 0
    results = []

    md_files = sorted(REPORTS_DIR.rglob("*.md"))

    for md_file in md_files:
        rel = md_file.relative_to(PROJECT_ROOT)
        text = md_file.read_text(encoding="utf-8")

        for match in CITATION_RE.finditer(text):
            filename = match.group(1)
            func_name = match.group(2)

            if filename in SKIP_FILES:
                continue

            line_num = text[: match.start()].count("\n") + 1

            found = False
            source = ""
            if cur:
                found = resolve_via_atlas(cur, filename, func_name)
                source = "atlas"
            if not found:
                found = resolve_via_grep(filename, func_name)
                source = "grep"

            if found:
                passed += 1
                tag = "PASS"
            else:
                failed += 1
                tag = "FAIL"
            results.append((tag, rel, line_num, filename, func_name, source))

    if conn:
        conn.close()

    key = lambda r: (r[0], str(r[1]), r[2])
    for tag, rel, line_num, filename, func_name, source in sorted(results, key=key):
        print(f"  {tag}  [{source:5s}] {rel}:{line_num}  {filename}:{func_name}()")

    print()
    print("=" * 52)
    print(f"  Total: {passed + failed}  Passed: {passed}  Failed: {failed}")
    if failed:
        print("  ❌ Some citations failed verification.")
    else:
        print("  ✅ All citations verified.")
    print("=" * 52)

    if run_validate:
        print()
        print("--- Capability validation ---")
        try:
            sys.path.insert(0, str(CODEBASE_DIR))
            from seed_hypotheses import seed_all
            from kernel.hypothesis.hypothesis_engine import hypothesis_engine
            from validate_capabilities import validate_capabilities
            seed_all(hypothesis_engine)
            vr = validate_capabilities(hypothesis_engine)
            for hid, tag, msg in vr["details"]:
                h = hypothesis_engine.get_hypothesis(hid)
                s = h.status if h else "?"
                print(f"  {tag:4s}  {hid:20s}  [{s:10s}]  {msg}")
            print(f"  Capabilities: {vr['passed']} passed, {vr['failed']} failed, {vr['skipped']} skipped")
        except Exception as e:
            print(f"  Capability validation skipped: {e}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
