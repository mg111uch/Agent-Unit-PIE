"""Paper trader: pending-order queue mirroring backtest execution exactly.

Backtest semantics: signal at close t -> fill open t+1 -> ATR exits.
Paper mirror, run once daily on CLOSED bars:
  1. fill PENDING orders at first bar open after their signal bar,
  2. exit checks on open positions against the latest closed bar,
  3. signals on the latest closed bar -> new PENDING orders for tomorrow.
ATR is frozen at entry (as in backtest), sizing mirrors engine position_frac
on live paper equity. Never places real orders.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List
from ..data.store import connect, ensure_schema, query_equity
from ..data.recorder import IST, market_open
from ..backtest.engine import _signals, _atr
from ..backtest.costs import trade_cost
from ..config import load_capital
from ..strategies.model import strategy_from_dict

ORDERS_SCHEMA = """
CREATE TABLE IF NOT EXISTS paper_orders(
 id INTEGER PRIMARY KEY AUTOINCREMENT, strategy TEXT, symbol TEXT,
 signal_ts TEXT, status TEXT DEFAULT 'PENDING', created_at TEXT DEFAULT '');
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure(con) -> None:
    con.executescript(ORDERS_SCHEMA)
    try:
        con.execute("ALTER TABLE paper_trades ADD COLUMN atr REAL DEFAULT 0")
    except Exception:
        pass


def _closed_idx(bl: List[Dict], now: datetime | None = None) -> int:
    """Index of latest CLOSED bar; today's bar is forming while market is open."""
    now = (now or datetime.now(IST)).astimezone(IST)
    today = now.strftime("%Y-%m-%d")
    if market_open(now) and len(bl) > 1 and bl[-1]["ts"][:10] == today:
        return len(bl) - 2
    return len(bl) - 1


def _paper_equity(con, strategy: str, capital: float, closes: Dict[str, float]) -> float:
    closed = con.execute("SELECT COALESCE(SUM(net),0) FROM paper_trades"
                         " WHERE strategy=? AND status='CLOSED'", (strategy,)).fetchone()[0]
    mtm = 0.0
    for sym, qty, px_in in con.execute("SELECT symbol,qty,px_in FROM paper_trades"
                                       " WHERE strategy=? AND status='OPEN'", (strategy,)):
        if sym in closes:
            mtm += qty * (closes[sym] - px_in)
    return capital + closed + mtm


def step(strategy_d: Dict[str, Any], symbols: List[str], db_path: str | None = None,
         lookback: int = 120) -> Dict[str, Any]:
    is_ml = (strategy_d.get("meta", {}) or {}).get("family") == "ml"
    if is_ml:
        from ..ml.strategies import ml_exits, ml_signals
        strat = ml_exits(strategy_d)
    else:
        strat = strategy_from_dict(strategy_d)
    cap = load_capital()
    flat = strat.flat_cost or float(cap.get("flat_cost_per_roundtrip", 60) or 0)
    capital = float(cap.get("capital", 50000))
    ensure_schema(db_path)
    con = connect(db_path)
    try:
        _ensure(con)
        bars = {}
        for s in symbols:
            rows = query_equity(f"NSE:{s}", strat.timeframe, db_path=db_path)
            if len(rows) >= 20:
                bars[s] = rows[-lookback:]
        if not bars:
            return {"status": "no-data"}
        ci = {s: _closed_idx(bl) for s, bl in bars.items()}
        closes = {s: bars[s][ci[s]]["close"] for s in bars}
        log: List[str] = []
        ml_sig: Dict[str, List[bool]] = {}
        if is_ml:
            from ..ml.strategies import ml_signals as _mls
            try:
                ml_sig = _mls(strategy_d, bars,
                              live_from=max(bars[s][ci[s]]["ts"] for s in bars))
            except Exception:
                ml_sig = {}
        # 1. fills: first bar open strictly after the signal bar
        for oid, sym, sig_ts in con.execute(
                "SELECT id,symbol,signal_ts FROM paper_orders WHERE strategy=? AND status='PENDING'",
                (strat.name,)).fetchall():
            bl = bars.get(sym)
            if not bl:
                continue
            fills = [b for b in bl if b["ts"] > sig_ts]
            if not fills:
                continue
            fb = fills[0]
            fi = bl.index(fb)
            equity = _paper_equity(con, strat.name, capital, closes)
            qty = equity * strat.position_frac / fb["open"] if fb["open"] > 0 else 0
            if qty <= 0:
                con.execute("UPDATE paper_orders SET status='CANCELLED' WHERE id=?", (oid,))
                continue
            atr = _atr(bl, fi - 1, strat.atr_n) if fi >= 1 else None
            if atr is None:
                continue
            cost = trade_cost(qty * fb["open"], flat) / 2
            con.execute("INSERT INTO paper_trades(strategy,symbol,t_in,qty,px_in,atr,cost,"
                        "status,created_at) VALUES(?,?,?,?,?,?,?,'OPEN',?)",
                        (strat.name, sym, fb["ts"], qty, fb["open"], atr, cost, _now()))
            con.execute("UPDATE paper_orders SET status='FILLED' WHERE id=?", (oid,))
            log.append(f"FILL {sym} qty {qty:.2f} @ Rs{fb['open']:.1f}")
        # 2. exits on latest closed bar (ATR frozen at entry, as in backtest)
        for tid, sym, qty, px_in, t_in, atr in con.execute(
                "SELECT id,symbol,qty,px_in,t_in,atr FROM paper_trades"
                " WHERE strategy=? AND status='OPEN'", (strat.name,)).fetchall():
            bl = bars.get(sym)
            if not bl:
                continue
            last = bl[ci[sym]]
            stop, take = px_in - strat.stop_atr * atr, px_in + strat.take_atr * atr
            px = stop if last["low"] <= stop else (take if last["high"] >= take else None)
            try:
                hold = (datetime.fromisoformat(last["ts"]) -
                        datetime.fromisoformat(t_in)).days
            except ValueError:
                hold = 0
            if px is None and hold >= strat.max_hold:
                px = last["close"]
            if px is None:
                continue
            cost = trade_cost(qty * px, flat) / 2
            entry_cost = con.execute("SELECT cost FROM paper_trades WHERE id=?", (tid,)).fetchone()[0]
            net = qty * (px - px_in) - cost - (entry_cost or 0)
            con.execute("UPDATE paper_trades SET t_out=?,px_out=?,net=?,cost=cost+?,"
                        "status='CLOSED' WHERE id=?", (last["ts"], px, net, cost, tid))
            log.append(f"CLOSE {sym} net Rs{net:.0f}")
        # 3. signals on latest closed bar -> pending for next session
        for s, bl in bars.items():
            i = ci[s]
            if i < 1:
                continue
            if is_ml:
                sl = ml_sig.get(s, [])
                fired = bool(len(sl) > i and sl[i] is True)
            else:
                fired = _signals(strat, bl[:i + 1])[-1] is True
            if not fired:
                continue
            exists = con.execute("SELECT 1 FROM paper_trades WHERE strategy=? AND symbol=?"
                                 " AND status='OPEN'", (strat.name, s)).fetchone()
            pend = con.execute("SELECT 1 FROM paper_orders WHERE strategy=? AND symbol=?"
                               " AND status='PENDING'", (strat.name, s)).fetchone()
            if exists or pend:
                continue
            con.execute("INSERT INTO paper_orders(strategy,symbol,signal_ts,status,created_at)"
                        " VALUES(?,?,?,'PENDING',?)", (strat.name, s, bl[i]["ts"], _now()))
            log.append(f"SIGNAL {s} for next open")
        con.commit()
        n_open = con.execute("SELECT COUNT(*) FROM paper_trades WHERE strategy=? AND status='OPEN'",
                             (strat.name,)).fetchone()[0]
        return {"status": "ok", "actions": log, "open": n_open}
    finally:
        con.close()


def report(strategy: str, db_path: str | None = None) -> Dict[str, Any]:
    """Paper ledger vs backtest expectation + scale-up recommendation."""
    cap = load_capital()
    con = connect(db_path)
    try:
        rows = con.execute("SELECT net FROM paper_trades WHERE strategy=? AND status='CLOSED'",
                           (strategy,)).fetchall()
        n_open = con.execute("SELECT COUNT(*) FROM paper_trades WHERE strategy=? AND status='OPEN'",
                             (strategy,)).fetchone()[0]
        n_pend = con.execute("SELECT COUNT(*) FROM paper_orders WHERE strategy=? AND status='PENDING'",
                             (strategy,)).fetchone()[0]
    finally:
        con.close()
    nets = [r[0] for r in rows]
    n, total = len(nets), round(sum(nets), 2)
    avg = round(total / n, 2) if n else 0.0
    gate_n = int(cap.get("scale_min_closed_trades", 10))
    gate_avg = float(cap.get("scale_min_avg_net_per_trade", 90))
    scale = (n >= gate_n and avg >= gate_avg and total > 0)
    return {"strategy": strategy, "closed": n, "open": n_open, "pending": n_pend,
            "total_net": total, "avg_net_per_trade": avg,
            "scale_recommendation": ("ADD Rs%s (human approval required — edit capital.yaml)"
                                     % cap.get("scale_step") if scale else "hold",
                                     {"need_trades": max(0, gate_n - n), "need_avg": gate_avg})}
