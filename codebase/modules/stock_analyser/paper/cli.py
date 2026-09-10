"""User CLI for the paper league. Run from workspace root (/home/manigupt/Hello/Agentic_Unit_PIE):

  conda run -n myenv python codebase/modules/stock_analyser/paper/cli.py portfolio
  conda run -n myenv python codebase/modules/stock_analyser/paper/cli.py next
  conda run -n myenv python codebase/modules/stock_analyser/paper/cli.py portfolio --trees TREE1 TREE2

portfolio: open positions + per-position/day/overall PnL per tree (PAPER/LIVE split).
next: step all trees on today's closed bars, print tomorrow's buy list w/ sizes.
Run `next` once each evening after market close; `portfolio` anytime.
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List

WS = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(WS / "codebase"))
sys.path.insert(0, str(WS))

LEAGUE = ["ml_ridge_rel_t5~top_n8",
          "ml_ridge_rel_t3~hold12~features13~hold12",
          "ml_ridge_rel_t3~hold12~features13",
          "ml_ridge_rel_t3~hold12~features13~hold12~top_n4"]


def _pct(x: float, base: float) -> str:
    return f"{100 * x / base:+.2f}%" if base else "+0.00%"


def _closes(symbols: List[str], db_path: str | None, n: int = 2) -> Dict[str, list]:
    from modules.stock_analyser.data.store import query_equity
    out = {}
    for s in symbols:
        rows = query_equity(f"NSE:{s}", "1D", db_path=db_path)
        if rows:
            out[s] = rows[-n:]
    return out


def portfolio(trees: List[str], db_path: str | None = None,
              use_live: bool = False) -> Dict[str, Any]:
    from modules.stock_analyser.data.store import connect, ensure_schema
    from modules.stock_analyser.config import load_capital
    ensure_schema(db_path)
    cap = load_capital()
    base = float(cap.get("capital", 50000))
    con = connect(db_path)
    try:
        syms = {r[0] for r in con.execute(
            "SELECT DISTINCT symbol FROM paper_trades WHERE strategy IN (%s)"
            % ",".join("?" * len(trees)), trees).fetchall()}
        px = _closes(sorted(syms), db_path)
        cmp_src: Dict[str, str] = {}
        live_mode = "closed"
        try:
            from modules.stock_analyser.config import load_capital as _cap
            if bool(_cap().get("paper_use_cmp", True)) and syms:
                if use_live:
                    from modules.stock_analyser.data.live import get_cmps, save_cmps
                    fresh = get_cmps(sorted(syms))
                    if fresh:
                        save_cmps(fresh, db_path)
                    for s, q in fresh.items():
                        if px.get(s) and q.get("px", 0) > 0:
                            px[s][-1] = dict(px[s][-1], close=float(q["px"]))
                            cmp_src[s] = str(q.get("source", "?"))
                    live_mode = "live" if fresh else "closed"
                else:
                    from modules.stock_analyser.data.live import load_cmps
                    cached = load_cmps(sorted(syms), db_path)
                    for s, q in cached.items():
                        if px.get(s) and q.get("px", 0) > 0:
                            px[s][-1] = dict(px[s][-1], close=float(q["px"]))
                            cmp_src[s] = str(q.get("source", "?"))
                    live_mode = "cache" if cached else "closed"
        except Exception:
            pass
        today = max((b[-1]["ts"][:10] for b in px.values()), default="")
        if not today:
            from modules.stock_analyser.data.store import connect as _c
            _con = _c(db_path)
            try:
                today = (_con.execute("SELECT MAX(ts) FROM equity_bars").fetchone()[0]
                         or "?")[:10]
            finally:
                _con.close()
        out = {"as_of": today, "trees": [], "cmp": cmp_src, "price_mode": live_mode}
        for t in trees:
            t_out: Dict[str, Any] = {"strategy": t, "modes": {}}
            for mode in ("PAPER", "LIVE"):
                opened = con.execute(
                    "SELECT symbol,qty,px_in,t_in FROM paper_trades WHERE strategy=?"
                    " AND mode=? AND status='OPEN'", (t, mode)).fetchall()
                closed = con.execute(
                    "SELECT symbol,qty,px_in,px_out,net,t_in,t_out FROM paper_trades"
                    " WHERE strategy=? AND mode=? AND status='CLOSED'", (t, mode)).fetchall()
                pos, unreal, holding_tot = [], 0.0, 0.0
                for sym, qty, px_in, t_in in opened:
                    bars = px.get(sym, [])
                    last = bars[-1]["close"] if bars else px_in
                    u = qty * (last - px_in)
                    prev = bars[-2]["close"] if len(bars) > 1 else px_in
                    hold = qty * last
                    pos.append({"symbol": sym, "qty": int(qty), "entry": px_in,
                                "t_in": (t_in or "")[:10], "live": round(last, 1),
                                "unreal": round(u, 1), "unreal_pct": _pct(u, qty * px_in),
                                "holding": round(hold, 0), "status": "OPEN"})
                    unreal += u
                    holding_tot += hold
                for sym, qty, px_in, px_out, net, t_in, t_out in closed:
                    pos.append({"symbol": sym, "qty": int(qty), "entry": px_in,
                                "t_in": (t_in or "")[:10], "live": round(px_out or 0, 1),
                                "unreal": round(net or 0, 1),
                                "unreal_pct": _pct(net or 0, qty * px_in),
                                "holding": 0, "status": f"CLOSED@{(t_out or '')[:10]}"})
                day = sum(r[4] for r in closed if (r[6] or "")[:10] == today)
                for sym, qty, px_in, t_in in opened:
                    bars = px.get(sym, [])
                    last = bars[-1]["close"] if bars else px_in
                    prev = bars[-2]["close"] if len(bars) > 1 else px_in
                    prev_ts = bars[-2]["ts"] if len(bars) > 1 else ""
                    # same-day buy: day move is (CMP - entry), not (CMP - prev close)
                    day_base = px_in if (prev_ts and (t_in or "")[:10] >= prev_ts[:10]) else prev
                    day += qty * (last - day_base)
                real = sum(r[4] or 0 for r in closed)
                tot = real + unreal
                from modules.stock_analyser.paper.trader import _settled_cash
                settled = _settled_cash(con, t, base,
                                        str(cap.get("settlement_mode", "T1_EPI")))
                t_out["modes"][mode] = {"positions": pos, "open": len(opened),
                    "closed_n": len(closed), "realized": round(real, 1),
                    "unrealized": round(unreal, 1), "holding": round(holding_tot, 0),
                    "settled": round(settled, 0),
                    "day_pnl": round(day, 1), "day_pct": _pct(day, base),
                    "overall": round(tot, 1), "overall_pct": _pct(tot, base)}
            out["trees"].append(t_out)
        rank = sorted(out["trees"],
                      key=lambda t: t["modes"]["PAPER"]["overall"]
                      + t["modes"]["LIVE"]["overall"], reverse=True)
        out["leader"] = rank[0]["strategy"] if rank else None
        return out
    finally:
        con.close()


def _table(rows: List[List[str]]) -> List[str]:
    """Minimal ASCII table, stdlib only. First row = header."""
    if not rows:
        return []
    w = [0] * len(rows[0])
    for r in rows:
        for i, c in enumerate(r):
            w[i] = max(w[i], len(c))
    sep = "+" + "+".join("-" * (x + 2) for x in w) + "+"
    out = [sep]
    for ri, r in enumerate(rows):
        out.append("| " + " | ".join(c.ljust(w[i]) for i, c in enumerate(r)) + " |")
        if ri == 0:
            out.append(sep)
    out.append(sep)
    return out


def print_portfolio(p: Dict[str, Any]) -> None:
    cmp = p.get("cmp") or {}
    mode = p.get("price_mode", "closed")
    tag = (f" +CMP({len(cmp)} live)" if mode == "live"
           else f" +CMP-cache({len(cmp)})" if mode == "cache"
           else " (closed bars)")
    print(f"PORTFOLIO as of {p['as_of']}{tag} (base Rs50000/tree)")
    for t in p["trees"]:
        print(f"== {t['strategy']}")
        for mode, m in t["modes"].items():
            if mode == "LIVE" and not m["open"] and not m["closed_n"]:
                continue  # live twin exists only for the promoted tree(s)
            print(f"  [{mode}] day {m['day_pnl']:+.0f} ({m['day_pct']})"
                  f"  holding Rs{m['holding']:.0f} [{m['unrealized']:+.0f} ({m['overall_pct']})]"
                  f"  realized {m['realized']:+.0f} unreal {m['unrealized']:+.0f}"
                  f"  settled cash Rs{m['settled']:.0f}")
            if not m["positions"]:
                print("    (no open positions)")
                continue
            rows = [["Symbol", "Qty", "Entry", "Since", "Live", "Unreal", "Holding", "Status"]]
            for q in m["positions"]:
                rows.append([str(q["symbol"]), str(q["qty"]), f"{q['entry']:.2f}",
                             str(q["t_in"]), f"{q['live']:.1f}",
                             f"{q['unreal']:+.0f} ({q['unreal_pct']})",
                             f"{q['holding']:.0f}", str(q["status"])])
            for line in _table(rows):
                print(f"    {line}")
    print(f"LEADER: {p.get('leader')}")


def migrate(from_tree: str, to_tree: str, db_path: str | None = None) -> Dict[str, Any]:
    """Rotation plan: sell old OPEN at CMP (EPI → proceeds today, T1 → tomorrow),
    release new-tree PENDING against settled cash. Read-only."""
    from modules.stock_analyser.data.store import connect, ensure_schema
    from modules.stock_analyser.config import load_capital
    from modules.stock_analyser.paper.trader import report
    ensure_schema(db_path)
    cap = load_capital()
    epi = str(cap.get("settlement_mode", "T1_EPI")) == "T1_EPI"
    con = connect(db_path)
    try:
        old = con.execute("SELECT symbol,qty,px_in FROM paper_trades WHERE strategy=?"
                          " AND status='OPEN'", (from_tree,)).fetchall()
        new = con.execute("SELECT symbol,signal_ts FROM paper_orders WHERE strategy=?"
                          " AND status='PENDING'", (to_tree,)).fetchall()
    finally:
        con.close()
    syms = sorted({r[0] for r in old} | {r[0] for r in new})
    cmps: Dict[str, Dict] = {}
    try:
        from modules.stock_analyser.data.live import get_cmps, load_cmps
        cmps = get_cmps(syms) or load_cmps(syms, db_path)
    except Exception:
        cmps = {}
    sells, proceeds = [], 0.0
    for sym, qty, px_in in old:
        px = (cmps.get(sym) or {}).get("px", px_in)
        sells.append({"symbol": sym, "qty": int(qty), "px": round(px, 1),
                      "proceeds": round(qty * px, 0),
                      "avail": "today (EPI)" if epi else "T+1"})
        proceeds += qty * px
    rep = report(to_tree, db_path=db_path)
    rows = [["Symbol", "Qty", "Sell@CMP", "Proceeds", "Avail"]]
    for s in sells:
        rows.append([s["symbol"], str(s["qty"]), f"{s['px']:.1f}",
                     f"{s['proceeds']:.0f}", s["avail"]])
    print(f"MIGRATE {from_tree} -> {to_tree} ({cap.get('settlement_mode')})")
    for line in _table(rows):
        print(f"  {line}")
    print(f"  sell proceeds Rs{proceeds:.0f} | {to_tree} settled cash Rs{rep.get('settled_cash')}"
          f" | pending: {', '.join(r[0] for r in new) or '—'}")
    return {"from": from_tree, "to": to_tree, "sells": sells,
            "proceeds": round(proceeds, 0), "new_settled": rep.get("settled_cash"),
            "new_pending": [r[0] for r in new]}


def next_day(trees: List[str], db_path: str | None = None) -> Dict[str, Any]:
    """Step all trees on today's closed bars; print tomorrow's shopping list."""
    import json
    import sqlite3
    from modules.stock_analyser.data.universe import resolve_universe
    from modules.stock_analyser.paper.league import step_all
    db = sqlite3.connect("data/market.db")
    strats = []
    for n in trees:
        row = db.execute("select strategy_json from research_candidates"
                         " where json_extract(strategy_json,'$.name')=?", (n,)).fetchone()
        if not row:
            print(f"WARN unknown tree {n}")
            continue
        d = json.loads(row[0])
        d.get("meta", {}).pop("reject_reason", None)
        d.get("meta", {}).pop("oos_seal", None)
        strats.append(d)
    db.close()
    out = step_all(strats, resolve_universe("MY_UNIVERSE_200"), db_path=db_path)
    for name, r in out["trees"].items():
        print(f"== {name}: {r.get('status')}")
        for a in r.get("actions", []):
            if a.startswith(("SIGNAL", "FILL", "CLOSE")):
                print(f"   {a}")
    return out


def main(argv: List[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="paper.cli")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p1 = sub.add_parser("portfolio", help="positions + PnL per tree")
    p1.add_argument("--trees", nargs="*", default=LEAGUE)
    p1.add_argument("--db", default=None)
    p1.add_argument("--live", action="store_true",
                    help="fetch fresh CMP; default shows last fetched CMP (no network)")
    p2 = sub.add_parser("next", help="step trees, show tomorrow's buys")
    p2.add_argument("--trees", nargs="*", default=LEAGUE)
    p2.add_argument("--db", default=None)
    p3 = sub.add_parser("migrate", help="rotation plan old tree -> new tree")
    p3.add_argument("--from", dest="from_tree", required=True)
    p3.add_argument("--to", dest="to_tree", required=True)
    p3.add_argument("--db", default=None)
    a = ap.parse_args(argv)
    if a.cmd == "portfolio":
        print_portfolio(portfolio(a.trees, db_path=a.db, use_live=bool(a.live)))
    elif a.cmd == "migrate":
        migrate(a.from_tree, a.to_tree, db_path=a.db)
    else:
        next_day(a.trees, db_path=a.db)


if __name__ == "__main__":
    main()
