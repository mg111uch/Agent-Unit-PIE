"""Proposal → magic link → invoice → paid (REV-07 no-escrow path).

    python scripts/proposal.py create --customer "Acme" --title "Supplier list" \
        --price 2500 --deliverable deliverables/acme.xlsx
    python scripts/proposal.py list
    python scripts/proposal.py paid prop_xxx --reference UPI-123
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "codebase"))

from modules.economy import portal  # noqa: E402


def main(argv: list[str]) -> int:
    import argparse
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create")
    c.add_argument("--customer", required=True)
    c.add_argument("--title", required=True)
    c.add_argument("--price", type=float, required=True)
    c.add_argument("--deliverable", default="")
    sub.add_parser("list")
    p = sub.add_parser("paid")
    p.add_argument("proposal_id")
    p.add_argument("--reference", default="")
    p.add_argument("--actor", default="human:1")
    a = ap.parse_args(argv)

    if a.cmd == "create":
        out = portal.create(a.customer, a.title, a.price, a.deliverable)
        print(json.dumps(out, indent=1))
        return 0 if out.get("ok") else 1
    if a.cmd == "list":
        print(json.dumps(portal.list_all(), indent=1))
        return 0
    out = portal.mark_paid(a.proposal_id, a.reference, a.actor)
    print(json.dumps(out, indent=1))
    return 0 if out.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
