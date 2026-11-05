"""Delivery capacity + cost per verified record (REV-03).

    python scripts/capacity.py 100 --agents 2 --payout 500,500 --compute 100
    python scripts/capacity.py 100 --assign tasks.json --agent-file agents.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "codebase"))

from modules.economy import delivery  # noqa: E402


def main(argv: list[str]) -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("records", type=int)
    ap.add_argument("--agents", type=int, default=1)
    ap.add_argument("--records-per-agent-day", type=int,
                    default=delivery.DEFAULT_RECORDS_PER_AGENT_DAY)
    ap.add_argument("--qc-minutes", type=float,
                    default=delivery.DEFAULT_QC_MINUTES_PER_RECORD)
    ap.add_argument("--qc-humans", type=int, default=1)
    ap.add_argument("--payout", default="", help="comma-separated payouts")
    ap.add_argument("--compute", type=float, default=0.0)
    ap.add_argument("--assign", help="JSON list of tasks")
    ap.add_argument("--agent-file", help="JSON list of agents")
    a = ap.parse_args(argv)

    payouts = [float(x) for x in a.payout.split(",") if x.strip()]
    plan = delivery.capacity_plan(
        a.records, agents=a.agents,
        records_per_agent_day=a.records_per_agent_day,
        qc_minutes_per_record=a.qc_minutes,
        qc_humans=a.qc_humans)
    cost = delivery.cost_per_verified_record(
        a.records, payouts=payouts, qc_hours=plan["qc_hours"],
        compute=a.compute)
    out = {"capacity": plan, "cost": cost}

    if a.assign:
        tasks = json.loads(Path(a.assign).read_text())
        agents = json.loads(Path(a.agent_file).read_text()) if a.agent_file else []
        out["assignment"] = delivery.assign_executors(tasks, agents)

    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
