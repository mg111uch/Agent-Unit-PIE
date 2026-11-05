"""One healthcheck for supervisors and cron (OPS-01).

Exit codes are the contract:
  0 ok · 1 degraded (a flag is set) · 2 unreachable

    python scripts/healthcheck.py --pie http://localhost:8000 --ff http://localhost:5000
    python scripts/healthcheck.py --json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "codebase"))

from paths import DATA_ROOT, describe  # noqa: E402


def _get(url: str, timeout: float = 5.0):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read().decode() or "{}"), None
    except (urllib.error.URLError, ValueError, OSError) as e:
        return None, f"{type(e).__name__}: {e}"


def _stale_db(path: Path, max_age_hours: float = 26.0) -> dict:
    if not path.exists():
        return {"path": str(path), "exists": False}
    age_h = (time.time() - path.stat().st_mtime) / 3600.0
    return {"path": str(path), "exists": True,
            "age_hours": round(age_h, 1), "stale": age_h > max_age_hours}


def check(pie: str, ff: str) -> dict:
    out = {"paths": describe(), "alerts": []}
    pie_body, pie_err = _get(pie.rstrip("/") + "/health")
    out["pie"] = pie_body or {"error": pie_err}
    if pie_err:
        out["alerts"].append("pie_unreachable")

    ff_body, ff_err = _get(ff.rstrip("/") + "/api/health")
    out["fireflow"] = ff_body or {"error": ff_err}
    if ff_err:
        out["alerts"].append("fireflow_unreachable")
    elif not ff_body.get("ok", False):
        out["alerts"].append("fireflow_degraded")
        for name, on in (ff_body.get("alerts") or {}).items():
            if on:
                out["alerts"].append(f"fireflow:{name}")
        outbox = ff_body.get("outbox") or {}
        if outbox.get("dead"):
            out["alerts"].append("fireflow_outbox_dead")

    kernel_db = DATA_ROOT / "kernel.db"
    market_db = DATA_ROOT / "market.db"
    out["kernel_db"] = _stale_db(kernel_db)
    out["market_db"] = _stale_db(market_db)
    for key in ("kernel_db", "market_db"):
        if out[key].get("stale"):
            out["alerts"].append(f"{key}_stale")
    out["ok"] = not out["alerts"]
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pie", default="http://localhost:8000")
    ap.add_argument("--ff", default="http://localhost:5000")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    out = check(a.pie, a.ff)
    if a.json:
        print(json.dumps(out, indent=1))
    else:
        print(f"ok={out['ok']} alerts={out['alerts'] or 'none'}")
        print(json.dumps(out["paths"], indent=1))
    if out["alerts"] and all(x.endswith("unreachable") for x in out["alerts"]):
        return 2
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
