#!/usr/bin/env python3
"""Validate capability hypotheses against actual codebase symbols using atlas + grep."""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "codebase"))

from kernel.hypothesis.hypothesis_engine import hypothesis_engine
from kernel.persistence.db import kernel_db
from scripts.lib.citations import resolve_symbol, extract_module_name, CODEBASE_DIR


def _evidence_mtime(ev_path):
    """Return file mtime for a cited path (codebase- or project-relative), or None."""
    for base in (CODEBASE_DIR, PROJECT_ROOT):
        try:
            return (base / ev_path).stat().st_mtime
        except OSError:
            continue
    return None


def export_validated(engine=None):
    """Export validated capabilities + gaps to semantic memory (E5)."""
    if engine is None:
        engine = hypothesis_engine
    exported = 0
    for h in engine.hypotheses.values():
        if h.status == "proposed":
            continue
        engine.export_to_semantic_memory(h.hypothesis_id)
        exported += 1
    return exported


def detect_regressions(engine, details):
    """Regressions = previously-`supported` capability claims that now FAIL."""
    regressions = []
    for hid, tag, msg in details:
        if tag != "FAIL":
            continue
        cached = kernel_db.load_citation_cache(hid)
        if cached and cached["status"] == "supported":
            h = engine.get_hypothesis(hid)
            regressions.append({"id": hid,
                                "title": h.title if h else hid,
                                "message": msg})
    return regressions


def emit_regression_signal(regressions):
    if not regressions:
        return 0
    try:
        from kernel.signals.signal_engine import signal_engine
    except ImportError:
        return 0
    signal_engine.create_signal(
        signal_type="capability_regression",
        source_unit_id="scripts",
        value=json.dumps(regressions, separators=(",", ":")),
        category="developer_experience",
        title=f"Capability regression: {len(regressions)} supported claim(s) now fail",
        description="; ".join(r["id"] for r in regressions),
    )
    return 1


def validate_capabilities(engine=None, module_prefix=None):
    if engine is None:
        engine = hypothesis_engine

    caps = engine.get_by_type("capability_claim")
    if module_prefix:
        caps = [h for h in caps if h.hypothesis_id.startswith(f"cap_{module_prefix}")]

    results = {"passed": 0, "failed": 0, "skipped": 0, "details": [], "modules": {}}

    def add_detail(hid, tag, msg):
        mod = hid.split("_")[1] if hid.startswith("cap_") else "unknown"
        results["modules"].setdefault(mod, {"passed": 0, "failed": 0, "skipped": 0})
        key = {"PASS": "passed", "FAIL": "failed", "SKIP": "skipped"}.get(tag, "skipped")
        results["modules"][mod][key] += 1
        results["details"].append((hid, tag, msg))

    for h in caps:
        hid = h.hypothesis_id
        ev_path = h.metadata.get("evidence_path", "")
        ev_sym = h.metadata.get("evidence_symbol", "")

        if not ev_sym:
            add_detail(hid, "SKIP", "No function symbol in metadata")
            continue

        filename = ev_path.split("/")[-1] if ev_path else ""
        if not filename:
            add_detail(hid, "SKIP", "No file path in metadata")
            continue

        mtime = _evidence_mtime(ev_path)
        cached = kernel_db.load_citation_cache(hid)
        if (mtime is not None and cached
                and cached["evidence_path"] == ev_path
                and cached["evidence_symbol"] == ev_sym
                and cached["file_mtime"] == mtime):
            h.status = cached["status"]
            tag = "PASS" if cached["status"] == "supported" else "FAIL"
            add_detail(hid, tag, f"{ev_path}:{ev_sym}() cached (mtime unchanged)")
            continue

        found, resolved_path = resolve_symbol(filename, ev_sym)

        if found:
            engine.add_supporting_evidence(hid, "code_verified")
            engine.validate_hypothesis(hid)
            add_detail(hid, "PASS", f"{ev_path}:{ev_sym}() resolved")
            kernel_db.save_citation_cache(hid, ev_path, ev_sym, mtime, h.status)
        else:
            engine.add_contradicting_evidence(hid, "symbol_not_found")
            engine.validate_hypothesis(hid)
            cmd = (f"python scripts/record_removal.py --name \"{hid} removed\" "
                   f"--premise \"{ev_path}:{ev_sym}() no longer resolves\" "
                   f"--evidence \"symbol_not_found\" --source \"{ev_path}\" "
                   f"--contradicts \"{hid}\"")
            add_detail(hid, "FAIL",
                       f"{ev_path}:{ev_sym}() not found -> record removal: {cmd}")
            if mtime is not None:
                kernel_db.save_citation_cache(hid, ev_path, ev_sym, mtime, h.status)

    results["passed"] = sum(1 for d in results["details"] if d[1] == "PASS")
    results["failed"] = sum(1 for d in results["details"] if d[1] == "FAIL")
    results["skipped"] = sum(1 for d in results["details"] if d[1] == "SKIP")
    results["regressions"] = detect_regressions(engine, results["details"])
    emit_regression_signal(results["regressions"])
    export_validated(engine)
    return results


def main():
    module_prefix = None
    output_json = False
    quiet = False
    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg == "--module" and i + 1 < len(args):
            module_prefix = args[i + 1]
        elif arg == "--json":
            output_json = True
        elif arg == "--quiet" or arg == "-q":
            quiet = True

    import logging
    if quiet:
        logging.getLogger("agent_unit_pie").setLevel(logging.WARNING)
        logging.getLogger("agent_unit_pie.hypothesis_engine").setLevel(logging.WARNING)
        logging.getLogger("agent_unit_pie").handlers.clear()

    from scripts.seed_hypotheses import seed_all
    seed_all(hypothesis_engine)

    results = validate_capabilities(hypothesis_engine, module_prefix)

    if output_json:
        print(json.dumps({
            "passed": results["passed"],
            "failed": results["failed"],
            "skipped": results["skipped"],
            "regressions": results["regressions"],
            "details": [{"id": d[0], "status": d[1], "message": d[2]} for d in results["details"]],
            "modules": {k: v for k, v in results["modules"].items()},
        }, separators=(",", ":")))
    else:
        if not quiet:
            print(f"\nValidation results for {module_prefix or 'all modules'}:")
            print("-" * 60)
            for hid, tag, msg in results["details"]:
                h = hypothesis_engine.get_hypothesis(hid)
                status = h.status if h else "?"
                print(f"  {tag:4s}  {hid:20s}  [{status:10s}]  {msg}")

        print("\n" + "=" * 60)
        total = results["passed"] + results["failed"] + results["skipped"]
        print(f"  Total: {total}  Passed: {results['passed']}  Failed: {results['failed']}  Skipped: {results['skipped']}")
        for mod, counts in sorted(results["modules"].items()):
            print(f"  Module '{mod}': {counts['passed']} passed, {counts['failed']} failed, {counts['skipped']} skipped")
        if results["failed"]:
            print("  Some capabilities could not be validated.")
        else:
            print("  All verified capabilities pass validation.")
        if results["regressions"]:
            print("  Regressions (previously supported, now failing):")
            for r in results["regressions"]:
                print(f"    - {r['id']}: {r['title'][:60]}")

        status_counts = {}
        for h in hypothesis_engine.get_by_type("capability_claim"):
            s = h.status
            status_counts[s] = status_counts.get(s, 0) + 1
        print(f"  Final status distribution: {status_counts}")
        print("=" * 60)

    return 1 if results["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
