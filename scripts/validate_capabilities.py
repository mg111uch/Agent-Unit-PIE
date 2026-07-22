#!/usr/bin/env python3
"""Validate capability hypotheses against actual codebase symbols using atlas + grep."""

import re
import sys
import sqlite3
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "codebase"))

from kernel.hypothesis.hypothesis_engine import hypothesis_engine
from seed_hypotheses import seed_all

REPORTS_DIR = PROJECT_ROOT / "system_devpt_reports"
CODEBASE_DIR = PROJECT_ROOT / "codebase"
ATLAS_DB = PROJECT_ROOT / "atlas_output" / "code_rag.db"


def resolve_symbol(filename, funcname):
    """Resolve a symbol and return (found, resolved_path_relative_to_project_root)."""
    atlas_path = ATLAS_DB
    conn = None
    cur = None
    if atlas_path.exists():
        conn = sqlite3.connect(str(atlas_path))
        cur = conn.cursor()

    found = False
    resolved_path = None
    if cur:
        row = cur.execute(
            "SELECT file_path FROM symbols WHERE symbol_name = ? AND file_path LIKE ?",
            (funcname, f"%/{filename}"),
        ).fetchone()
        if row:
            found = True
            abs_path = row[0]
            try:
                resolved_path = str(Path(abs_path).relative_to(PROJECT_ROOT))
            except ValueError:
                resolved_path = abs_path

    if not found:
        result = subprocess.run(
            ["grep", "-rl", f"def {funcname}(", str(CODEBASE_DIR), "--include", filename],
            capture_output=True, text=True, timeout=30,
        )
        stdout = result.stdout.strip()
        if stdout:
            found = True
            abs_path = stdout.splitlines()[0]
            try:
                resolved_path = str(Path(abs_path).relative_to(PROJECT_ROOT))
            except ValueError:
                resolved_path = abs_path

    if conn:
        conn.close()
    return found, resolved_path


def validate_capabilities(engine=None):
    if engine is None:
        engine = hypothesis_engine

    caps = engine.get_by_type("capability_claim")

    results = {"passed": 0, "failed": 0, "skipped": 0, "details": []}

    for h in caps:
        hid = h.hypothesis_id
        ev_path = h.metadata.get("evidence_path", "")
        ev_sym = h.metadata.get("evidence_symbol", "")

        if not ev_sym:
            results["skipped"] += 1
            results["details"].append((hid, "SKIP", "No function symbol in metadata"))
            continue

        filename = ev_path.split("/")[-1] if ev_path else ""
        if not filename:
            results["skipped"] += 1
            results["details"].append((hid, "SKIP", f"No file path in metadata"))
            continue

        found, resolved_path = resolve_symbol(filename, ev_sym)

        if found:
            engine.add_supporting_evidence(hid, "code_verified")
            outcome = engine.validate_hypothesis(hid)

            git_path = resolved_path or (f"codebase/{ev_path}" if ev_path else "")
            if git_path:
                try:
                    ch = subprocess.run(
                        ["git", "log", "-1", "--format=%H", "--", git_path],
                        capture_output=True, text=True, timeout=10,
                        cwd=PROJECT_ROOT,
                    ).stdout.strip()
                    cm = subprocess.run(
                        ["git", "log", "-1", "--format=%s", "--", git_path],
                        capture_output=True, text=True, timeout=10,
                        cwd=PROJECT_ROOT,
                    ).stdout.strip()
                    if ch:
                        h = engine.get_hypothesis(hid)
                        if h:
                            h.metadata["git_commit"] = ch
                            h.metadata["git_message"] = cm
                except Exception:
                    pass

            results["passed"] += 1
            results["details"].append((hid, "PASS", f"{ev_path}:{ev_sym}() resolved"))
        else:
            engine.add_contradicting_evidence(hid, "symbol_not_found")
            outcome = engine.validate_hypothesis(hid)
            results["failed"] += 1
            results["details"].append((hid, "FAIL", f"{ev_path}:{ev_sym}() not found"))

    return results


def main():
    print("Seeding hypotheses...")
    seed_all(hypothesis_engine)

    print("Validating capability claims...")
    results = validate_capabilities(hypothesis_engine)

    print()
    for hid, tag, msg in results["details"]:
        h = hypothesis_engine.get_hypothesis(hid)
        status = h.status if h else "?"
        print(f"  {tag:4s}  {hid:20s}  [{status:10s}]  {msg}")

    print()
    print("=" * 60)
    total = results["passed"] + results["failed"] + results["skipped"]
    print(f"  Total: {total}  Passed: {results['passed']}  Failed: {results['failed']}  Skipped: {results['skipped']}")
    if results["failed"]:
        print("  Some capabilities could not be validated.")
    else:
        print("  All verified capabilities pass validation.")

    status_counts = {}
    for h in hypothesis_engine.get_by_type("capability_claim"):
        s = h.status
        status_counts[s] = status_counts.get(s, 0) + 1
    print(f"  Final status distribution: {status_counts}")
    print("=" * 60)

    return 1 if results["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
