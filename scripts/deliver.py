"""Assemble one customer deliverable with QC attached (REV-04/REV-07).

Input JSON: {"project": "...", "records": [{record_id, fields, source}],
             "submissions": [{record_id, value}],
             "gold": [{"record_id": "g1", "fields": {...}}]}

    conda run -n myenv python scripts/deliver.py bundle.json --outdir out/
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "codebase"))

from modules.economy import assembly, qc  # noqa: E402


def main(argv: list[str]) -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("bundle", help="path to the deliverable JSON")
    ap.add_argument("--outdir", default="deliverables")
    ap.add_argument("--analysts", default="analyst-1,analyst-2")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    spec = json.loads(Path(a.bundle).read_text())
    records = spec.get("records") or []
    submissions = spec.get("submissions") or [
        {"record_id": r["record_id"], "value": r.get("fields") or {}}
        for r in records]
    report = qc.run(
        [r["record_id"] for r in records],
        [x.strip() for x in a.analysts.split(",") if x.strip()],
        submissions, gold_records=spec.get("gold") or [], seed=0)
    out = assembly.build(records, a.outdir,
                         project=spec.get("project") or "deliverable",
                         qc_report=report,
                         limits=spec.get("limits") or [
                             "Facts change quickly; re-verify before contracts.",
                             "No data was scraped from behind a login.",
                         ])
    print(json.dumps(out, indent=1) if a.json else
          "\n".join([f"rows={out['rows']} qc_pass={out['qc']['pass']}"]
                    + [f"{k}: {v}" for k, v in out["files"].items()]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
