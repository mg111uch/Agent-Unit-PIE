"""Paper trader: live-CMP execution for trading trees (backtest-only uses history).

Run on closed bars for signals, but PENDING fills + OPEN exits + sizing use
live CMP (NSE quote, Yahoo-1m fallback) when reachable; closed-open fallback
keeps offline/tests deterministic. ATR frozen at entry, max_positions cap kept.
fill_src audits CMP/* vs OPEN.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List
from ..data.store import connect, ensure_schema, query_equity
from ..data.recorder import IST, market_open
from ..backtest.engine import _signals, _atr
from ..backtest.costs import trade_cost, floor_qty as _floor_qty
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
    for _alter in ("ALTER TABLE paper_trades ADD COLUMN atr REAL DEFAULT 0",
                   "ALTER TABLE paper_trades ADD COLUMN mode TEXT DEFAULT 'PAPER'",
                   "ALTER TABLE paper_trades ADD COLUMN fill_src TEXT DEFAULT ''"):
        try:
            con.execute(_alter)
        except Exception:
            pass


def _bars_held(bl: List[Dict], t_in: str, ci: int) -> int:
    """Bars held like the engine: index distance from fill bar to latest closed."""
    idx = next((k for k, b in enumerate(bl) if b["ts"] > t_in), None)
    if idx is None:  # fill bar is last or t_in unknown: fall back to 0
        idx = next((k for k, b in enumerate(bl) if b["ts"] == t_in), ci)
    return max(0, ci - idx)


def _stale_days(ts: str, now: datetime | None = None) -> int:
    try:
        last = datetime.fromisoformat(ts[:10])
        today = (now or datetime.now(IST)).astimezone(IST).replace(tzinfo=None)
        return max(0, (today - last).days)
    except Exception:
        return 0


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


def _settled_cash(con, strategy: str, capital: float, mode: str) -> float:
    """Buying power honoring settlement. T1_EPI: EPI releases proceeds same day
    (all closes settled). T1 strict: closes settle next day (t_out date < today).
    Approximation: 1 calendar day (no holiday calendar); exit leg ≈ flat/2."""
    from datetime import datetime
    today = datetime.now(IST).strftime("%Y-%m-%d")
    rows = con.execute("SELECT qty,px_in,px_out,cost,t_out,status FROM paper_trades"
                       " WHERE strategy=?", (strategy,)).fetchall()
    cash = capital
    for qty, px_in, px_out, cost, t_out, st in rows:
        qty = qty or 0
        if st == "OPEN":
            cash -= qty * (px_in or 0) + (cost or 0)
        else:
            cash -= qty * (px_in or 0) + (cost or 0)
            settled = (mode == "T1_EPI") or ((t_out or "")[:10] < today)
            if settled and px_out:
                cash += qty * px_out
    return cash


def _cap_by_cash(qty: int, px: float, cash: float) -> tuple:
    """Cap qty to settled buying power. Returns (qty, capped_flag)."""
    if px <= 0:
        return qty, False
    afford = _floor_qty(cash / px)
    if afford >= qty:
        return qty, False
    return max(0, afford), True


def _est_qty(bl: List[Dict], i: int, strat, cap: Dict, con, closes: Dict) -> str:
    """Preview share count at signal time (close as open proxy; fill recomputes)."""
    try:
        from .costs import sized_frac as _sized
        px = bl[i]["close"]
        atr = _atr(bl, i, strat.atr_n)
        if not px or not atr:
            return ""
        equity = _paper_equity(con, strat.name, float(cap.get("capital", 50000)), closes)
        q = _floor_qty(equity * _sized(strat.position_frac, atr, px, cap) / px)
        return f" ~{q} shares @ ~Rs{px:.1f}" if q > 0 else ""
    except Exception:
        return ""


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
        from ..research.liquidity import tradable_filter as _tf
        from ..constants import is_tradable as _tradable
        _allbars, _untrad = _tf(bars, capital * strat.position_frac, cap)
        untrad = set(_untrad) | {s for s in bars if not _tradable(s)}  # buys blocked; exits never blocked
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
        # 1. fills: CMP intraday when available, else first open after signal (parity)
        use_cmp = bool(cap.get("paper_use_cmp", True))
        settle_mode = str(cap.get("settlement_mode", "T1_EPI"))
        retired = strat.name in (cap.get("retired_trees") or [])
        if retired:
            log.append(f"RETIRED {strat.name} exit-only (no new signals)")
        cmps: Dict[str, Dict] = {}
        if use_cmp:
            try:
                from ..data.live import get_cmps
                pend = [r[0] for r in con.execute(
                    "SELECT symbol FROM paper_orders WHERE strategy=? AND status='PENDING'",
                    (strat.name,)).fetchall()]
                opn = [r[0] for r in con.execute(
                    "SELECT symbol FROM paper_trades WHERE strategy=? AND status='OPEN'",
                    (strat.name,)).fetchall()]
                cmps = get_cmps(sorted(set(pend + opn)))
            except Exception:
                cmps = {}
        for oid, sym, sig_ts in con.execute(
                "SELECT id,symbol,signal_ts FROM paper_orders WHERE strategy=? AND status='PENDING'",
                (strat.name,)).fetchall():
            bl = bars.get(sym)
            if not bl:
                continue
            if sym in untrad:  # buys blocked; held positions always exit (section 2)
                con.execute("UPDATE paper_orders SET status='CANCELLED' WHERE id=?", (oid,))
                log.append(f"ACTION-SKIP {sym} untradable/index")
                continue
            n_open = con.execute("SELECT COUNT(*) FROM paper_trades WHERE strategy=? AND status='OPEN'",
                                 (strat.name,)).fetchone()[0]
            if n_open >= strat.max_positions:  # engine parity: capped book
                log.append(f"SKIP {sym} book full ({n_open}/{strat.max_positions})")
                continue
            q = cmps.get(sym) if use_cmp else None
            if q and q.get("px", 0) > 0:
                px, t_in, src = float(q["px"]), q["ts"], f"CMP/{q.get('source', '?')}"
                atr = _atr(bl, ci.get(sym, len(bl) - 1), strat.atr_n)
                if atr is None:
                    continue
                from ..backtest.costs import sized_frac as _sized
                equity = _paper_equity(con, strat.name, capital, closes)
                qty = _floor_qty(equity * _sized(strat.position_frac, atr, px, cap) / px) if px > 0 else 0
                if qty < 1:
                    con.execute("UPDATE paper_orders SET status='CANCELLED' WHERE id=?", (oid,))
                    continue
                qty, capped = _cap_by_cash(qty, px, _settled_cash(con, strat.name, capital, settle_mode))
                if qty < 1:
                    log.append(f"SKIP {sym} funds in settlement ({settle_mode})")
                    continue  # stays PENDING, retries next step
                cost = trade_cost(qty * px, flat) / 2
                con.execute("INSERT INTO paper_trades(strategy,symbol,t_in,qty,px_in,atr,cost,"
                            "status,fill_src,created_at) VALUES(?,?,?,?,?,?,?,'OPEN',?,?)",
                            (strat.name, sym, t_in, qty, px, atr, cost, src, _now()))
                con.execute("UPDATE paper_orders SET status='FILLED' WHERE id=?", (oid,))
                log.append(f"FILL {sym} qty {qty} @ Rs{px:.1f} ({src})"
                           + (" [cash-capped]" if capped else ""))
                continue
            fills = [b for b in bl if b["ts"] > sig_ts]
            if not fills:
                continue
            fb = fills[0]
            fi = bl.index(fb)
            prev = bl[fi - 1] if fi >= 1 else None
            if prev and fb["open"] and prev["close"]:
                gap = abs(fb["open"] - prev["close"]) / prev["close"]
                if gap > float(cap.get("paper_max_gap", 0.15)):
                    con.execute("UPDATE paper_orders SET status='CANCELLED' WHERE id=?", (oid,))
                    log.append(f"ACTION-SKIP {sym} gap {gap:.1%} (split/bonus?)")
                    continue
            equity = _paper_equity(con, strat.name, capital, closes)
            atr = _atr(bl, fi - 1, strat.atr_n) if fi >= 1 else None
            if atr is None:
                continue
            from ..backtest.costs import sized_frac as _sized
            qty = _floor_qty(equity * _sized(strat.position_frac, atr, fb["open"], cap) / fb["open"]) \
                if fb["open"] > 0 else 0
            if qty < 1:
                con.execute("UPDATE paper_orders SET status='CANCELLED' WHERE id=?", (oid,))
                continue
            qty, capped = _cap_by_cash(qty, fb["open"], _settled_cash(con, strat.name, capital, settle_mode))
            if qty < 1:
                log.append(f"SKIP {sym} funds in settlement ({settle_mode})")
                continue  # stays PENDING, retries next step
            cost = trade_cost(qty * fb["open"], flat) / 2
            con.execute("INSERT INTO paper_trades(strategy,symbol,t_in,qty,px_in,atr,cost,"
                        "status,fill_src,created_at) VALUES(?,?,?,?,?,?,?,'OPEN','OPEN',?)",
                        (strat.name, sym, fb["ts"], qty, fb["open"], atr, cost, _now()))
            con.execute("UPDATE paper_orders SET status='FILLED' WHERE id=?", (oid,))
            log.append(f"FILL {sym} qty {qty} @ Rs{fb['open']:.1f}"
                       + (" [cash-capped]" if capped else ""))
        # 2. exits at CMP intraday when available, else latest closed bar
        for tid, sym, qty, px_in, t_in, atr in con.execute(
                "SELECT id,symbol,qty,px_in,t_in,atr FROM paper_trades"
                " WHERE strategy=? AND status='OPEN'", (strat.name,)).fetchall():
            bl = bars.get(sym)
            if not bl:
                continue
            stop, take = px_in - strat.stop_atr * atr, px_in + strat.take_atr * atr
            q = cmps.get(sym) if use_cmp else None
            if q and q.get("px", 0) > 0:
                cmp = float(q["px"])
                hit = cmp <= stop or cmp >= take
                held = _bars_held(bl, t_in, ci[sym]) >= strat.max_hold
                if not (hit or held):
                    continue
                cost = trade_cost(qty * cmp, flat) / 2
                entry_cost = con.execute("SELECT cost FROM paper_trades WHERE id=?", (tid,)).fetchone()[0]
                net = qty * (cmp - px_in) - cost - (entry_cost or 0)
                con.execute("UPDATE paper_trades SET t_out=?,px_out=?,net=?,cost=cost+?,"
                            "status='CLOSED' WHERE id=?", (q["ts"], cmp, net, cost, tid))
                log.append(f"CLOSE {sym} net Rs{net:.0f} (CMP/{q.get('source', '?')})")
                continue
            last = bl[ci[sym]]
            px = stop if last["low"] <= stop else (take if last["high"] >= take else None)
            if px is None and _bars_held(bl, t_in, ci[sym]) >= strat.max_hold:
                px = last["close"]  # engine parity: bar-count hold, not calendar days
            if px is None:
                continue
            cost = trade_cost(qty * px, flat) / 2
            entry_cost = con.execute("SELECT cost FROM paper_trades WHERE id=?", (tid,)).fetchone()[0]
            net = qty * (px - px_in) - cost - (entry_cost or 0)
            con.execute("UPDATE paper_trades SET t_out=?,px_out=?,net=?,cost=cost+?,"
                        "status='CLOSED' WHERE id=?", (last["ts"], px, net, cost, tid))
            log.append(f"CLOSE {sym} net Rs{net:.0f}")
        # 3. signals on latest closed bar -> pending (skipped for retired trees)
        stale_after = int(cap.get("paper_stale_days", 5))
        for s, bl in bars.items():
            if retired:
                break
            i = ci[s]
            if i < 1:
                continue
            if s in untrad:
                log.append(f"SKIP {s} untradable/index; no signal")
                continue
            if _stale_days(bl[i]["ts"]) > stale_after:  # recorder downtime: no fresh bars
                log.append(f"STALE {s} last {bl[i]['ts'][:10]}; no signal")
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
            log.append(f"SIGNAL {s} for next open{_est_qty(bl, i, strat, cap, con, closes)}")
        con.commit()
        n_open = con.execute("SELECT COUNT(*) FROM paper_trades WHERE strategy=? AND status='OPEN'",
                             (strat.name,)).fetchone()[0]
        return {"status": "ok", "actions": log, "open": n_open}
    finally:
        con.close()


def report(strategy: str, db_path: str | None = None,
           mode: str | None = None) -> Dict[str, Any]:
    """Paper ledger vs backtest expectation + scale-up recommendation.

    mode filters paper_trades ('PAPER'/'LIVE'); None = all modes."""
    cap = load_capital()
    con = connect(db_path)
    try:
        _ensure(con)
        mf, args = (" AND mode=?" , (strategy, mode)) if mode else ("", (strategy,))
        rows = con.execute("SELECT net FROM paper_trades WHERE strategy=?"
                           + mf + " AND status='CLOSED'", args).fetchall()
        n_open = con.execute("SELECT COUNT(*) FROM paper_trades WHERE strategy=?"
                             + mf + " AND status='OPEN'", args).fetchone()[0]
        n_pend = con.execute("SELECT COUNT(*) FROM paper_orders WHERE strategy=? AND status='PENDING'",
                             (strategy,)).fetchone()[0]
        try:
            n_cmp = con.execute("SELECT COUNT(*) FROM paper_trades WHERE strategy=?"
                                + mf + " AND fill_src LIKE 'CMP%'", args).fetchone()[0]
        except Exception:
            n_cmp = 0
        settle_mode = str(cap.get("settlement_mode", "T1_EPI"))
        cash = round(_settled_cash(con, strategy, float(cap.get("capital", 50000)), settle_mode), 0)
    finally:
        con.close()
    nets = [r[0] for r in rows]
    n, total = len(nets), round(sum(nets), 2)
    avg = round(total / n, 2) if n else 0.0
    gate_n = int(cap.get("scale_min_closed_trades", 10))
    gate_avg = float(cap.get("scale_min_avg_net_per_trade", 90))
    scale = (n >= gate_n and avg >= gate_avg and total > 0)
    return {"strategy": strategy, "mode": mode or "ALL", "closed": n, "open": n_open,
            "pending": n_pend, "cmp_fills": n_cmp, "settled_cash": cash,
            "settlement_mode": settle_mode, "total_net": total, "avg_net_per_trade": avg,
            "scale_recommendation": ("ADD Rs%s (human approval required — edit capital.yaml)"
                                     % cap.get("scale_step") if scale else "hold",
                                     {"need_trades": max(0, gate_n - n), "need_avg": gate_avg})}
