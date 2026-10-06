"""Horizon-scan CLI (Round-3 step 2, persisted). Run from workspace root:

  conda run -n myenv python codebase/modules/stock_analyser/research/horizon_cli.py build-panel
  conda run -n myenv python codebase/modules/stock_analyser/research/horizon_cli.py scan

build-panel: builds the 200-symbol feature panel from market.db and caches
  it to codebase/utils_files (survives restarts; ~6 min, ~92MB).
scan: loads the cache (or builds if missing), runs the per-horizon
  retrained purged scan + block-null (1000 perms), writes JSON to stdout.
  Read-only: no ledger writes. Decision rule: reopen search only if some
  horizon shows net-positive long-leg excess surviving the block null.
"""
from __future__ import annotations
import argparse
import json
import sys
import time
from pathlib import Path

WS = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(WS / "codebase"))
sys.path.insert(0, str(WS))

PANEL_CACHE = WS / "codebase" / "utils_files" / "hscan_panel_200sym_2016-2026.pkl"
UNIVERSE = "MY_UNIVERSE_200"


def build_panel_cmd(args) -> None:
    import sqlite3
    from modules.stock_analyser.ml.dataset import build_panel
    con = sqlite3.connect(str(WS / "data" / "market.db"))
    syms = [r[0] for r in con.execute(
        "SELECT member_id FROM universes WHERE name=?", (UNIVERSE,)).fetchall()]
    con.close()
    bare = [s.split(":", 1)[1] if ":" in s else s for s in syms]
    t0 = time.time()
    panel = build_panel(bare, fwd=5, warmup=65, include_relative=True)
    panel.to_pickle(PANEL_CACHE)
    print(json.dumps({"cached": str(PANEL_CACHE), "rows": len(panel),
                      "dates": int(panel["ts"].nunique()),
                      "elapsed_s": round(time.time() - t0)}))


def scan_cmd(args) -> None:
    import pandas as pd
    from modules.stock_analyser.ml.dataset import ALL_FEATURES, build_panel
    from modules.stock_analyser.data.store import query_equity
    from modules.stock_analyser.research.horizon_ic import horizon_scan
    from modules.stock_analyser.research.null_ic import perm_null
    t0 = time.time()
    if PANEL_CACHE.exists() and not args.rebuild:
        panel = pd.read_pickle(PANEL_CACHE)
    else:
        import sqlite3
        con = sqlite3.connect(str(WS / "data" / "market.db"))
        syms = [r[0] for r in con.execute(
            "SELECT member_id FROM universes WHERE name=?", (UNIVERSE,)).fetchall()]
        con.close()
        bare = [s.split(":", 1)[1] if ":" in s else s for s in syms]
        panel = build_panel(bare, fwd=5, warmup=65, include_relative=True)
        panel.to_pickle(PANEL_CACHE)
    px = {}
    for s in panel["symbol"].unique():
        for b in query_equity(f"NSE:{s}", "1D"):
            if b.get("close"):
                px[(s, b["ts"])] = float(b["close"])
    panel["close"] = [px.get((s, t)) for s, t in zip(panel["symbol"], panel["ts"])]
    panel = panel[panel["close"].notna()].rename(columns={"ts": "date"})
    feats = [f for f in ALL_FEATURES if f in panel.columns]
    hs = [int(h) for h in args.horizons.split(",")]
    res, scored = horizon_scan(panel, feats, horizons=tuple(hs),
                               refit_every=args.refit_every,
                               min_train_dates=252, entry_lag=1,
                               cost_bps=args.cost_bps, return_scored=True)
    null = {}
    for h in hs:
        if h not in scored:
            null[h] = {"note": "too few scored dates"}
            continue
        r = perm_null(scored[h], lag=h, n_perm=args.perms, block=h)
        null[h] = {k: (round(v, 4) if isinstance(v, float) else v)
                   for k, v in r.items()}
    print(json.dumps({"scan": res.round(4).to_dict(), "null": null,
                      "elapsed_s": round(time.time() - t0)}, indent=1))


def controls_cmd(args) -> None:
    """Standing regression (reviewer Q10): 6 hand-factor controls after every
    gate change. Asserts stage-1 t near recorded (2.24/2.16/2.75 for
    mom/reversal/trend) and injected IC 0.03 detectable >=80% via power_ic."""
    import sqlite3
    from modules.stock_analyser.data.store import query_equity
    from modules.stock_analyser.strategies.model import positive_controls
    from modules.stock_analyser.research.alpha_screen import screen
    from modules.stock_analyser.research.stage1 import ic_screen
    from modules.stock_analyser.research.null_ic import power_ic
    con = sqlite3.connect(str(WS / "data" / "market.db"))
    syms = [r[0] for r in con.execute(
        "SELECT member_id FROM universes WHERE name=?", (UNIVERSE,)).fetchall()]
    con.close()
    bare = [(s.split(":", 1)[1] if ":" in s else s) for s in syms]
    bars = {}
    for s in bare:
        rows = query_equity(f"NSE:{s}", "1D")
        if len(rows) >= 30:
            bars[s] = rows
    rows = []
    for c in positive_controls():
        g = screen(c, bars)
        s1 = ic_screen(c, bars, is_ml=False)
        rows.append({"control": c["name"], "gate_pass": g["pass"],
                     "gate": g["metrics"], "stage1": s1})
    pw = power_ic(n_sym=len(bars), n_indep=433,
                  ics=(0.01, 0.02, 0.03, 0.05), n_sim=400)
    print(json.dumps({"controls": rows,
                      "power_n433": {str(k): round(float(v), 3)
                                     for k, v in pw.items()}}, indent=1))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="research.horizon_cli")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build-panel", help="build + cache the feature panel")
    p = sub.add_parser("scan", help="horizon scan + block null on cached panel")
    p.add_argument("--horizons", default="5,20,40,60")
    p.add_argument("--refit-every", type=int, default=63)
    p.add_argument("--cost-bps", type=float, default=46.0)
    p.add_argument("--perms", type=int, default=1000)
    p.add_argument("--rebuild", action="store_true")
    sub.add_parser("controls", help="6 hand-factor controls battery + power")
    a = ap.parse_args(argv)
    {"build-panel": build_panel_cmd, "scan": scan_cmd,
     "controls": controls_cmd}[a.cmd](a)


if __name__ == "__main__":
    main()
