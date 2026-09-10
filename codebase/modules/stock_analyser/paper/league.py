"""Paper league: N strategy trees stepped daily on full notional each.

Each tree is an independent parallel universe asking 'what would full
starting capital do under this strategy' — no capital splitting. Ledger
isolation is by strategy name (paper_trades/paper_orders already key it).
Live fills join later via mode column (log_live_fill in trader.py).
"""
from __future__ import annotations
from typing import Any, Dict, List


def step_all(strategies: List[Dict[str, Any]], symbols: List[str],
             db_path: str | None = None, lookback: int = 120) -> Dict[str, Any]:
    """One daily step per tree. Returns per-tree step outcomes."""
    from .trader import step
    out = {}
    for sd in strategies:
        name = sd.get("name", "?")
        try:
            out[name] = step(sd, symbols, db_path=db_path, lookback=lookback)
        except Exception as e:
            out[name] = {"status": f"error: {e}"}
    return {"trees": out,
            "ok": sum(1 for v in out.values() if v.get("status") == "ok"),
            "n": len(out)}


def log_live_fill(strategy: str, symbol: str, qty: float, px_in: float, t_in: str,
                  px_out: float | None = None, t_out: str | None = None,
                  cost: float = 0.0, db_path: str | None = None) -> Dict[str, Any]:
    """Manual real-money fill log. Entry-only → OPEN; with exit → CLOSED + net."""
    import math
    from datetime import datetime, timezone
    from .trader import _ensure
    from ..data.store import connect, ensure_schema
    qty = max(0, int(math.floor(float(qty) + 1e-9)))  # NSE: whole shares only
    if qty < 1:
        raise ValueError("qty floors to 0 — need >=1 share")
    ensure_schema(db_path)
    con = connect(db_path)
    try:
        _ensure(con)
        if px_out is None:
            con.execute("INSERT INTO paper_trades(strategy,symbol,t_in,qty,px_in,cost,"
                        "status,mode,created_at) VALUES(?,?,?,?,?,?,'OPEN','LIVE',?)",
                        (strategy, symbol, t_in, qty, px_in, cost,
                         datetime.now(timezone.utc).isoformat()))
        else:
            net = qty * (px_out - px_in) - cost
            con.execute("INSERT INTO paper_trades(strategy,symbol,t_in,t_out,qty,px_in,"
                        "px_out,net,cost,status,mode,created_at)"
                        " VALUES(?,?,?,?,?,?,?,?,?,'CLOSED','LIVE',?)",
                        (strategy, symbol, t_in, t_out, qty, px_in, px_out,
                         round(net, 2), cost,
                         datetime.now(timezone.utc).isoformat()))
        con.commit()
    finally:
        con.close()
    return {"strategy": strategy, "symbol": symbol, "mode": "LIVE",
            "status": "OPEN" if px_out is None else "CLOSED"}


def live_vs_paper(strategy: str, db_path: str | None = None) -> Dict[str, Any]:
    """Divergence: LIVE twin vs PAPER twin of one strategy + cross-check."""
    from .trader import report
    from .reality import check
    paper = report(strategy, db_path=db_path, mode="PAPER")
    live = report(strategy, db_path=db_path, mode="LIVE")
    out = check({"avg_net_per_trade": paper.get("avg_net_per_trade"),
                 "n": paper.get("closed")},
                {"avg_net_per_trade": live.get("avg_net_per_trade"),
                 "closed": live.get("closed")})
    out.update({"strategy": strategy, "paper": paper, "live": live})
    return out


def league_report(strategies: List[str], db_path: str | None = None) -> Dict[str, Any]:
    """Per-tree ledger stats + rank by total_net. No shared capital math."""
    from .trader import report
    rows = []
    for name in strategies:
        try:
            r = report(name, db_path=db_path)
        except Exception as e:
            r = {"strategy": name, "error": str(e), "closed": 0, "total_net": 0.0,
                 "avg_net_per_trade": 0.0, "open": 0, "pending": 0}
        rows.append(r)
    rows.sort(key=lambda r: (r.get("total_net") or 0), reverse=True)
    for i, r in enumerate(rows):
        r["rank"] = i + 1
    return {"trees": rows,
            "leader": rows[0].get("strategy") if rows else None}
