"""Thin I/O bridge: FireFlow calls PIE scoring without duplicating logic.

Usage: echo '{"opportunity": {...}, "unit": {...}}' | python -m modules.economy.score_cli
Prints {"score":..., "breakdown":..., "verdict":..., "challenge":...}.
No weights here — all logic lives in scoring.py / challenge.py.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

# Allow direct execution: python codebase/modules/economy/score_cli.py '<json>'
try:
    from . import challenge as _CH
    from . import scoring as _SC
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from modules.economy import challenge as _CH
    from modules.economy import scoring as _SC


def main() -> None:
    raw = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    try:
        payload = json.loads(raw)
    except Exception as e:
        print(json.dumps({"error": f"bad JSON input: {e}"}))
        raise SystemExit(1)
    opp = payload.get("opportunity", payload)
    unit = payload.get("unit")
    try:
        s = _SC.score_opportunity(opp, unit)
    except Exception as e:
        print(json.dumps({"error": f"scoring failed: {e}"}))
        raise SystemExit(1)
    opp_id = opp.get("opportunity_id", "adhoc") if isinstance(opp, dict) else "adhoc"
    try:
        ch = _CH.challenge_for(dict(opp), opp_id) if isinstance(opp, dict) else None
    except Exception:
        ch = None
    print(json.dumps({**s, "challenge": ch}))


if __name__ == "__main__":
    main()
