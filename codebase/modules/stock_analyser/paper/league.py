"""Paper league: N strategy trees stepped daily on full notional each.

Each tree is an independent parallel universe asking 'what would full
starting capital do under this strategy' — no capital splitting. Ledger
isolation is by strategy name (paper_trades/paper_orders already key it).
Live fills join later via mode column (log_live_fill in trader.py).
"""
from __future__ import annotations
from typing import Any, Dict, List


def step_all(strategies: List[Dict[str, Any]], symbols: List[str],
             db_path: str | None = None, lookback: int | None = None) -> Dict[str, Any]:
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


def shadow_eval(db_path: str | None = None, horizon: int = 21) -> Dict[str, Any]:
    """Forward-OOS read of the shadow ledger: for each matured pick (signal +
    horizon bars available), excess 21-day return vs the universe mean that
    day. Free OOS across ALL live strategies, not just promoted ones."""
    from ..data.store import connect, query_equity
    con = connect(db_path)
    try:
        try:
            picks = con.execute("SELECT strategy,symbol,signal_ts FROM shadow_picks").fetchall()
        except Exception:
            return {"strategies": {}, "note": "no shadow_picks yet (accrues via next)"}
    finally:
        con.close()
    px: Dict[str, Dict[str, float]] = {}
    syms = sorted({p[1] for p in picks})
    for s in syms:
        for b in query_equity(f"NSE:{s}", "1D", db_path=db_path):
            if b.get("close"):
                px.setdefault(s, {})[b["ts"]] = float(b["close"])
    dates = sorted({d for m in px.values() for d in m})
    pos = {d: i for i, d in enumerate(dates)}
    rows: Dict[str, List[float]] = {}
    for strat, sym, ts in picks:
        m = px.get(sym, {})
        d0 = next((d for d in dates if d >= (ts or "")), "")
        i = pos.get(d0)
        if i is None or i + horizon >= len(dates):
            continue  # immature pick: horizon not yet observable
        d0, d1 = dates[i], dates[i + horizon]
        if d0 not in m or d1 not in m or m[d0] <= 0:
            continue
        uni = [(x[d1] / x[d0] - 1) for x in px.values()
               if d0 in x and d1 in x and x[d0] > 0]
        if not uni:
            continue
        rows.setdefault(strat, []).append(m[d1] / m[d0] - 1 - sum(uni) / len(uni))
    out = {}
    for strat, xs in rows.items():
        out[strat] = {"picks": len(xs), "hit": round(sum(1 for x in xs if x > 0) / len(xs), 3),
                      "avg_excess": round(sum(xs) / len(xs), 5)}
    return {"strategies": out,
            "note": "matured picks only; needs 60+ days of logging for power"}


def shadow_ic(db_path: str | None = None, horizon: int = 21,
              primary: str | None = None) -> Dict[str, Any]:
    """Forward rank-IC read over the full score vector (PlanFixes3 #5): per
    scored date with >=10 names and a matured horizon, Spearman(score,
    realized forward return). Needs 60+ days of logging for power; doubles
    as the graduation statistic (one-sided t > 2 after Holm over shadows).
    primary: pre-named promotion candidate (Q6 — logging several raises M);
    defaults to the first member of the newest ACTIVE tree. A second model id
    under one strategy raises refit_warning (silent refits contaminate IC)."""
    from ..data.store import connect, query_equity
    con = connect(db_path)
    try:
        try:
            rows = con.execute("SELECT strategy,symbol,signal_ts,score,model FROM shadow_scores").fetchall()
        except Exception:
            return {"strategies": {}, "note": "no shadow_scores yet (accrues via next)"}
    finally:
        con.close()
    if not rows:
        return {"strategies": {}, "note": "no shadow_scores yet (accrues via next)"}
    if primary is None:
        try:  # pre-named promotion candidate: newest ACTIVE tree's lead member
            from .trees import default_tree, members
            _dt = default_tree(db_path)
            _mm = members(_dt.get("tree_id", ""), db_path) if _dt else []
            primary = _mm[0] if _mm else None
        except Exception:
            primary = None
    px: Dict[str, Dict[str, float]] = {}
    for _, s, _, _ in rows:
        if s not in px:
            for b in query_equity(f"NSE:{s}", "1D", db_path=db_path):
                if b.get("close"):
                    px.setdefault(s, {})[b["ts"]] = float(b["close"])
    dates = sorted({d for m in px.values() for d in m})
    pos = {d: i for i, d in enumerate(dates)}
    by_strat: Dict[str, Dict[str, List]] = {}
    models: Dict[str, set] = {}
    for strat, sym, ts, sc, mo in rows:
        models.setdefault(strat, set()).add(mo or "?")
        m = px.get(sym, {})
        d0 = next((d for d in dates if d >= (ts or "")), "")
        i = pos.get(d0)
        if i is None or i + horizon >= len(dates):
            continue  # immature: horizon not yet observable
        d1 = dates[i + horizon]
        if d0 not in m or d1 not in m or m[d0] <= 0:
            continue
        by_strat.setdefault(strat, {}).setdefault(d0, []).append(
            (float(sc), m[d1] / m[d0] - 1))
    out = {}
    for strat, per_date in by_strat.items():
        ics = []
        for v in per_date.values():
            if len(v) < 10:
                continue
            o = sorted(range(len(v)), key=lambda j: v[j][0])
            r = sorted(range(len(v)), key=lambda j: v[j][1])
            ra, rb = [0.0] * len(v), [0.0] * len(v)
            for p, j in enumerate(o):
                ra[j] = p
            for p, j in enumerate(r):
                rb[j] = p
            n = len(v)
            ma, mb = sum(ra) / n, sum(rb) / n
            cov = sum((a - ma) * (b - mb) for a, b in zip(ra, rb)) / n
            sa = (sum((a - ma) ** 2 for a in ra) / n) ** 0.5
            sb = (sum((b - mb) ** 2 for b in rb) / n) ** 0.5
            ics.append(cov / (sa * sb) if sa and sb else 0.0)
        if not ics:
            continue
        m = sum(ics) / len(ics)
        sd = (sum((x - m) ** 2 for x in ics) / len(ics)) ** 0.5
        out[strat] = {"dates": len(ics), "mean_ic": round(m, 4),
                      "t": round(m / (sd / (len(ics) ** 0.5)), 2) if sd else 0.0,
                      "primary": strat == primary,
                      "models": sorted(models.get(strat, set()))}
        if len(models.get(strat, set()) - {"", "?"}) > 1:
            out[strat]["refit_warning"] = ("model id changed mid-logging;"
                                            " shadow IC contaminated")
    return {"primary": primary, "strategies": out,
            "note": "matured score-dates only; needs 60+ days of logging for power"}


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
