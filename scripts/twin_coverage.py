"""Twin coverage report (TWN-01): observed vs placeholder vs missing series.

    conda run -n myenv python scripts/twin_coverage.py
    conda run -n myenv python scripts/twin_coverage.py --json
    conda run -n myenv python scripts/twin_coverage.py --series-dir data/twins/series

Base values come from the shaped adapters (placeholder-heavy by design). Any
`<city>.json` in the series directory is validated and merged on top, so the
report shows exactly how much of a city is still a stand-in.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "codebase"))

from modules.digital_twins import city_adapters, city_series, city_state  # noqa: E402

CITIES = {
    "kanpur": ("city_kanpur", city_adapters.kanpur_fields),
    "delhi": ("city_delhi", city_adapters.delhi_fields),
}


def build_states(series_dir: Path | None) -> dict:
    states, loaded = {}, {}
    for name, (city_id, adapter) in CITIES.items():
        base = adapter()
        path = (series_dir / f"{name}.json") if series_dir else None
        if path and path.exists():
            out = city_series.ingest(path, base)
            states[name] = out["state"]
            loaded[name] = {"path": str(path), "rows": out.get("series_loaded", 0),
                            "rejected": out.get("rejected", [])}
        else:
            states[name] = city_state.build_state(city_id, base)
            loaded[name] = {"path": None, "reason": "no series file"}
    return {"states": states, "sources": loaded,
            "table": city_series.coverage_table(states)}


def render(table: dict, sources: dict) -> str:
    lines = ["TWIN COVERAGE (10 series per city)", ""]
    header = f"{'city':8} {'observed':>8} {'placeholder':>11} {'missing':>7} {'coverage':>9}"
    lines += [header, "-" * len(header)]
    for city, row in table["cities"].items():
        lines.append(f"{city:8} {row['observed']:>8} {row['placeholder']:>11} "
                     f"{row['missing']:>7} {row['coverage']:>9.1%}")
    lines.append("")
    lines.append(f"totals: observed={table['total_observed']} "
                 f"placeholder={table['total_placeholder']} "
                 f"missing={table['total_missing']}")
    for city, row in table["cities"].items():
        gaps = [k for k, v in row["by_field"].items() if v == "missing"]
        if gaps:
            lines.append(f"  {city} missing: {', '.join(gaps)}")
    for city, src in sources.items():
        if src.get("path"):
            lines.append(f"  {city} series: {src['rows']} row(s) from {src['path']}"
                         f"{', ' + str(len(src['rejected'])) + ' rejected' if src['rejected'] else ''}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--series-dir", default="data/twins/series")
    args = ap.parse_args()
    series_dir = Path(args.series_dir)
    if not series_dir.exists():
        series_dir = None
    report = build_states(series_dir)
    if args.json:
        print(json.dumps(report, indent=1, default=str))
    else:
        print(render(report["table"], report["sources"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
