#!/usr/bin/env python3
"""Prune kernel.db logs table, keeping the N newest rows (default 200).

Idempotent below the threshold. Hot-path noise is already gone at the
source (hot-path loggers emit DEBUG now); this only trims history.

Usage: python scripts/prune_kernel_logs.py [--keep 200]
"""

import argparse
import sqlite3
import sys
from pathlib import Path

DB = Path(__file__).resolve().parents[1] / "data" / "kernel.db"


def main():
    ap = argparse.ArgumentParser(description="Trim kernel.db logs table")
    ap.add_argument("--keep", type=int, default=200)
    args = ap.parse_args()

    if not DB.exists():
        print(f"error: {DB} not found", file=sys.stderr)
        return 1

    conn = sqlite3.connect(str(DB))
    try:
        before = conn.execute("SELECT COUNT(*) FROM logs").fetchone()[0]
        conn.execute(
            "DELETE FROM logs WHERE id NOT IN "
            "(SELECT id FROM logs ORDER BY id DESC LIMIT ?)",
            (args.keep,),
        )
        conn.commit()
        after = conn.execute("SELECT COUNT(*) FROM logs").fetchone()[0]
        print(f"logs: {before} -> {after} rows (kept newest {min(before, args.keep)})")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
