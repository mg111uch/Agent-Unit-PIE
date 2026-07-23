#!/usr/bin/env python3
"""Validate capability hypotheses against actual codebase symbols using atlas + grep."""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "codebase"))

from kernel.hypothesis.hypothesis_engine import hypothesis_engine
from scripts.lib.citations import resolve_symbol, extract_module_name


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

        found, resolved_path = resolve_symbol(filename, ev_sym)

        if found:
            engine.add_supporting_evidence(hid, "code_verified")
            engine.validate_hypothesis(hid)
            add_detail(hid, "PASS", f"{ev_path}:{ev_sym}() resolved")
        else:
            engine.add_contradicting_evidence(hid, "symbol_not_found")
            engine.validate_hypothesis(hid)
            add_detail(hid, "FAIL", f"{ev_path}:{ev_sym}() not found")

    results["passed"] = sum(1 for d in results["details"] if d[1] == "PASS")
    results["failed"] = sum(1 for d in results["details"] if d[1] == "FAIL")
    results["skipped"] = sum(1 for d in results["details"] if d[1] == "SKIP")
    return results


def main():
    module_prefix = None
    output_json = False
    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg == "--module" and i + 1 < len(args):
            module_prefix = args[i + 1]
        elif arg == "--json":
            output_json = True

    from scripts.seed_hypotheses import seed_all
    seed_all(hypothesis_engine)

    results = validate_capabilities(hypothesis_engine, module_prefix)

    if output_json:
        print(json.dumps({
            "passed": results["passed"],
            "failed": results["failed"],
            "skipped": results["skipped"],
            "details": [{"id": d[0], "status": d[1], "message": d[2]} for d in results["details"]],
            "modules": {k: v for k, v in results["modules"].items()},
        }, indent=2))
    else:
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

        status_counts = {}
        for h in hypothesis_engine.get_by_type("capability_claim"):
            s = h.status
            status_counts[s] = status_counts.get(s, 0) + 1
        print(f"  Final status distribution: {status_counts}")
        print("=" * 60)

    return 1 if results["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
