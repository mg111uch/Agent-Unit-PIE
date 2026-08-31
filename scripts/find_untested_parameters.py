#!/usr/bin/env python3
"""
find_untested_parameters.py

Analyzes simulation runs in a topic to identify:
1. Which parameter values have been tested
2. Gaps in tested ranges
3. Parameters that have never been tested

Usage:
    python scripts/find_untested_parameters.py --topic popu_sim
    python scripts/find_untested_parameters.py --topic popu_sim --gap-type birth_rate
"""

import argparse
import json
import os
import sys
import yaml
from collections import defaultdict
from pathlib import Path


def find_simulations_base():
    # primary: data/units/simulations/popula_dyn, fallback: codebase/units/simulations for backward compat
    p = Path("data/units/simulations/popula_dyn")
    if p.exists():
        return Path("data/units/simulations")
    return Path("codebase/units/simulations")


def scan_run_params(run_path: Path) -> dict:
    params_file = run_path / "params.yaml"
    if not params_file.exists():
        return {}
    with open(params_file) as f:
        return yaml.safe_load(f) or {}


def scan_run_summary(run_path: Path) -> dict:
    summary_file = run_path / "summary.json"
    if not summary_file.exists():
        return {}
    with open(summary_file) as f:
        return json.load(f)


def extract_tested_values(topic: str) -> dict:
    sim_base = find_simulations_base()
    tested = defaultdict(lambda: defaultdict(list))

    if not sim_base.exists():
        return tested

    # handle sharded layout data/units/simulations/{sim}/{run}
    scan_roots = [sim_base]
    if (sim_base / "popula_dyn").exists():
        scan_roots.append(sim_base / "popula_dyn")
    if (sim_base / "eco_sim").exists():
        scan_roots.append(sim_base / "eco_sim")

    for root in scan_roots:
        for run_dir in root.iterdir():
            if not run_dir.is_dir():
                continue
            params = scan_run_params(run_dir)
            if not params:
                continue
            tested["params"][run_dir.name] = params

    return tested


def analyze_gaps(tested: dict) -> dict:
    gaps = {}
    numeric_params = ["birth_rate", "death_rate", "metabolism", "initial_pop",
                      "fertile_min_age", "fertile_max_age", "max_age", "vision",
                      "grid_width", "grid_height", "initial_healers", "initial_toolmakers",
                      "initial_traders", "healer_healing_rate", "toolmaker_production_rate"]

    for param_name in numeric_params:
        values = set()
        run_values = {}
        for run_id, params in tested.get("params", {}).items():
            if param_name in params:
                val = params[param_name]
                if val is not None:
                    values.add(val)
                    run_values[run_id] = val

        if values:
            gaps[param_name] = {
                "tested": sorted(list(values)),
                "by_run": run_values,
                "type": "numeric" if all(isinstance(v, (int, float)) for v in values) else "mixed"
            }

    return gaps


def print_gap_report(gaps: dict, topic: str) -> None:
    print(f"\n=== Parameter Gap Analysis: {topic} ===\n")

    if not gaps:
        print("No parameters tested yet.")
        return

    print("TESTED PARAMETERS:")
    print("-" * 60)

    for param, data in sorted(gaps.items()):
        values = data["tested"]
        print(f"\n  {param}: {values}")

        if len(values) > 1:
            sorted_vals = sorted(values)
            gaps_found = []
            for i in range(len(sorted_vals) - 1):
                step = sorted_vals[i + 1] - sorted_vals[i]
                if step > 0.01:
                    gaps_found.append(f"    Gap between {sorted_vals[i]} and {sorted_vals[i+1]}")

            if gaps_found:
                print("    GAPS:")
                for g in gaps_found:
                    print(g)

    print("\n" + "=" * 60)
    print("UNTESTED PARAMETERS:")
    print("-" * 60)

    all_tested_params = set(gaps.keys())
    known_params = ["birth_rate", "death_rate", "metabolism", "initial_pop",
                   "fertile_min_age", "fertile_max_age", "max_age", "vision",
                   "grid_width", "grid_height", "initial_healers", "initial_toolmakers",
                   "initial_traders", "healer_healing_rate", "toolmaker_production_rate",
                   "toolmaker_quality", "toolmaker_cost", "trader_margin", "trader_range"]

    untested = [p for p in known_params if p not in all_tested_params]
    if untested:
        for p in untested:
            print(f"  - {p}")
    else:
        print("  All known parameters have been tested.")


def format_gap_suggestions(gaps: dict) -> str:
    suggestions = []
    suggestions.append("SUGGESTED NEXT PARAMETERS TO TEST:")

    birth_rate_gaps = []
    if "birth_rate" in gaps:
        tested = sorted(gaps["birth_rate"]["tested"])
        if len(tested) >= 2:
            for i in range(len(tested) - 1):
                mid = (tested[i] + tested[i + 1]) / 2
                if mid not in tested:
                    birth_rate_gaps.append(mid)

    if birth_rate_gaps:
        suggestions.append(f"  birth_rate gaps: {[round(g, 4) for g in birth_rate_gaps]}")

    untested_critical = []
    for param in ["metabolism", "death_rate", "initial_pop"]:
        if param not in gaps:
            untested_critical.append(param)

    if untested_critical:
        suggestions.append(f"  Untested critical params: {untested_critical}")

    return "\n".join(suggestions)


def main():
    parser = argparse.ArgumentParser(description="Find untested simulation parameters")
    parser.add_argument("--topic", required=True, help="Topic name to analyze")
    parser.add_argument("--gap-type", help="Specific parameter to analyze")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--suggest", action="store_true", help="Include suggested next parameters")

    args = parser.parse_args()

    tested = extract_tested_values(args.topic)
    gaps = analyze_gaps(tested)

    if args.gap_type:
        if args.gap_type in gaps:
            result = {args.gap_type: gaps[args.gap_type]}
        else:
            result = {args.gap_type: {"tested": [], "by_run": {}, "type": "untested"}}
    else:
        result = gaps

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_gap_report(gaps, args.topic)

        if args.suggest:
            print("\n" + format_gap_suggestions(gaps))

    return 0


if __name__ == "__main__":
    sys.exit(main())
