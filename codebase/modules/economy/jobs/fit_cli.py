"""Thin I/O bridge: FireFlow scores jobs via PIE fit engine (single source).

Usage: python codebase/modules/economy/jobs/fit_cli.py '{"job": {...}, "twin": {...}, "prefs": {...}}'
Prints {"score","verdict","confidence","reasons","matched","evidence"}.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

try:
    from . import fit as _FIT
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    from modules.economy.jobs import fit as _FIT


def main() -> None:
    raw = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    try:
        payload = json.loads(raw)
    except Exception as e:
        print(json.dumps({"error": f"bad JSON input: {e}"}))
        raise SystemExit(1)
    job = payload.get("job", payload)
    twin = payload.get("twin") or {"skills": {}}
    prefs = payload.get("prefs") or {}
    for k in ("skills", "eligible_countries"):
        if isinstance(job.get(k), str):
            try:
                job[k] = json.loads(job[k])
            except Exception:
                job[k] = []
    try:
        print(json.dumps(_FIT.score_job(job, twin, prefs)))
    except Exception as e:
        print(json.dumps({"error": f"fit failed: {e}"}))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
