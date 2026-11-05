"""Approval inbox CLI (STR-05).

    python scripts/approvals.py inbox items.json
    python scripts/approvals.py charter
    python scripts/approvals.py decide items.json --id 3 --actor user:1 --reject
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "codebase"))

from modules.economy import approvals  # noqa: E402


def main(argv: list[str]) -> int:
    import argparse
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_inbox = sub.add_parser("inbox")
    p_inbox.add_argument("file")
    sub.add_parser("charter")
    p_dec = sub.add_parser("decide")
    p_dec.add_argument("file")
    p_dec.add_argument("--id", type=int, required=True)
    p_dec.add_argument("--actor", required=True)
    p_dec.add_argument("--reject", action="store_true")
    p_dec.add_argument("--reason", default="")
    a = ap.parse_args(argv)

    if a.cmd == "charter":
        print(json.dumps(approvals.charter(), indent=1))
        return 0

    items = json.loads(Path(a.file).read_text())
    if a.cmd == "inbox":
        out = approvals.inbox(items)
        for i in out["items"]:
            flag = "!" if i["overdue"] else " "
            print(f"{flag} tier{i['tier']} {i['action']:<28} "
                  f"{i.get('amount_paise', 0):>9} due {i['due_at']}")
        print(f"counts={out['counts']} waiting_on_human={out['waiting_on_human']} "
              f"overdue={out['overdue']}")
        return 0

    idx = a.id - 1
    if not 0 <= idx < len(items):
        print(f"no item #{a.id}", file=sys.stderr)
        return 2
    item = approvals.enqueue(items[idx])
    out = approvals.decide(item, a.actor,
                           "reject" if a.reject else "approve", a.reason)
    items[idx] = out
    Path(a.file).write_text(json.dumps(items, indent=1))
    print(json.dumps(out, indent=1))
    return 0 if not out.get("error") else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
