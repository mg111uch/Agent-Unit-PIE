"""Deterministic backtester: signal at close t, fill at open t+1. Long-only V1.

Bars per symbol: list of dicts with ts/open/high/low/close/volume, sorted by ts.
ATR stops computed from prior atr_n bars. One shared cash pool; position_frac per trade.
"""
from __future__ import annotations
import math
from typing import Dict, List, Any
from ..features.algebra import evaluate, columns_from_bars, _eval
from ..strategies.model import Strategy
from .costs import trade_cost
from ..config import load_capital


def _flat(strategy: Strategy) -> float:
    f = strategy.flat_cost
    if f > 0:
        return f
    try:
        return float(load_capital().get("flat_cost_per_roundtrip", 0) or 0)
    except Exception:
        return 0.0


def _atr(bars: List[Dict[str, Any]], i: int, n: int) -> float | None:
    if i - n < 0:
        return None
    trs = []
    for j in range(i - n + 1, i + 1):
        h, lo, pc = bars[j]["high"], bars[j]["low"], bars[j - 1]["close"]
        trs.append(max(h - lo, abs(h - pc), abs(lo - pc)))
    return sum(trs) / len(trs) if trs else None


_COLS_CACHE: Dict[tuple, Dict[str, List[float | None]]] = {}


def _signals(strategy: Strategy, bars: List[Dict[str, Any]]) -> List[bool]:
    base = columns_from_bars(bars)
    key = (bars[0].get("instrument_id", "?"), len(bars),
           bars[-1].get("ts", ""), tuple(sorted(strategy.features)),
           hash(tuple(base["close"])))  # data fingerprint: same shape ≠ same data
    hit = _COLS_CACHE.get(key)
    if hit is not None and len(next(iter(hit.values()), [])) == len(bars):
        full = hit
    else:
        feat = {k: evaluate(v, base) for k, v in strategy.features.items()}
        full = dict(base)
        full.update(feat)
        if len(_COLS_CACHE) < 512:
            _COLS_CACHE[key] = full
    out = []
    for i in range(len(bars)):
        try:
            out.append(_eval(strategy.entry, full, i) is True)
        except Exception:
            out.append(False)
    return out


def run_backtest(strategy: Strategy, bars_by_symbol: Dict[str, List[Dict[str, Any]]],
                 start_cash: float = 100000.0, min_bars: int | None = None,
                 signals: Dict[str, List[bool]] | None = None) -> Dict[str, Any]:
    """Date-aligned union panel: symbols join on dates they trade; <min_bars excluded.

    No lookahead: a fill on date d uses signals/ATR from that symbol's own bars
    strictly before d. Late entrants (IPOs) trade only inside their window.
    `signals` (ML adapter): precomputed per-symbol bool lists aligned to each
    symbol's bars; entry on date d reads signals[idx(d)-1], same as symbolic.
    """
    if min_bars is None:
        try:
            min_bars = int(load_capital().get("min_history_bars", 60) or 60)
        except Exception:
            min_bars = 60
    cash, positions, trades = start_cash, {}, []
    total_costs = 0.0
    flat = _flat(strategy)
    equity_curve = []
    syms = sorted(s for s, bl in bars_by_symbol.items() if len(bl) >= min_bars)
    excluded = sorted(set(bars_by_symbol) - set(syms))
    if not syms:
        return {"error": "no data", "excluded": excluded}
    idx_of = {s: {b["ts"]: i for i, b in enumerate(bars_by_symbol[s])} for s in syms}
    if signals is None:
        sigs = {s: _signals(strategy, bars_by_symbol[s]) for s in syms}
    else:
        sigs = {}
        for s in syms:
            sl = list(signals.get(s) or [])
            sigs[s] = (sl + [False] * len(bars_by_symbol[s]))[:len(bars_by_symbol[s])]
    all_dates = sorted({b["ts"] for s in syms for b in bars_by_symbol[s]})
    for k, d in enumerate(all_dates):
        # exits first (stop/take/time) on each held symbol's bar for d, if any
        for s in list(positions):
            p = positions[s]
            i = idx_of[s].get(d)
            if i is None:
                continue  # suspended: hold at last price
            b = bars_by_symbol[s][i]
            p["last_px"] = b["close"]
            hold = k - p["k_in"]
            stop = p["px_in"] - strategy.stop_atr * p["atr"]
            take = p["px_in"] + strategy.take_atr * p["atr"]
            exit_px = None
            if b["low"] <= stop:
                exit_px = stop
            elif b["high"] >= take:
                exit_px = take
            elif hold >= strategy.max_hold:
                exit_px = b["open"]
            if exit_px is not None:
                notional = p["qty"] * exit_px
                cost = trade_cost(notional, flat, strategy.fee_bps, strategy.slippage_bps) / 2
                total_costs += cost + p["entry_cost"]
                cash += notional - cost
                ret = (exit_px - p["px_in"]) / p["px_in"]
                trades.append({"symbol": s, "t_in": p["t_in"], "t_out": d,
                               "ret": ret, "qty": p["qty"],
                               "net": p["qty"] * (exit_px - p["px_in"]) - cost - p["entry_cost"]})
                del positions[s]
        # entries: signal from symbol's own prior bar -> fill at d open
        if k > 0 and len(positions) < strategy.max_positions:
            for s in syms:
                if s in positions:
                    continue
                if len(positions) >= strategy.max_positions:
                    break
                i = idx_of[s].get(d)
                if i is None or i < 1 or not sigs[s][i - 1]:
                    continue
                b = bars_by_symbol[s][i]
                atr = _atr(bars_by_symbol[s], i - 1, strategy.atr_n)
                if not atr:
                    continue
                alloc = (cash + sum(p["qty"] * p["last_px"]
                                    for p in positions.values())) * strategy.position_frac
                qty = alloc / b["open"] if b["open"] > 0 else 0
                if qty <= 0:
                    continue
                cost = trade_cost(qty * b["open"], flat, strategy.fee_bps, strategy.slippage_bps) / 2
                cash -= qty * b["open"] + cost  # pay notional + costs, not costs alone
                positions[s] = {"qty": qty, "px_in": b["open"], "atr": atr,
                                "t_in": d, "k_in": k, "last_px": b["open"],
                                "entry_cost": cost}
        mtm = cash + sum(p["qty"] * p["last_px"] for p in positions.values())
        equity_curve.append(mtm)
    return {**_metrics(trades, equity_curve, start_cash, total_costs),
            "trades": trades, "equity_curve": equity_curve[-5:], "excluded": excluded}


def _metrics(trades: List[Dict], eq: List[float], start: float,
             total_costs: float = 0.0) -> Dict[str, Any]:
    n = len(trades)
    rets = [t["ret"] for t in trades]
    nets = [t.get("net", 0.0) for t in trades]
    wins = sum(1 for r in rets if r > 0)
    avg = sum(rets) / n if n else 0.0
    med = sorted(rets)[n // 2] if n else 0.0
    peak, dd = start, 0.0
    for v in eq:
        peak = max(peak, v)
        dd = min(dd, (v - peak) / peak if peak else 0.0)
    sd = (sum((r - avg) ** 2 for r in rets) / (n - 1)) ** 0.5 if n > 1 else 0.0
    sharpe = (avg / sd * math.sqrt(252)) if sd else 0.0
    downside = [r for r in rets if r < 0]
    dsd = (sum(r ** 2 for r in downside) / len(downside)) ** 0.5 if downside else 0.0
    sortino = (avg / dsd * math.sqrt(252)) if dsd else 0.0
    cagr = ((eq[-1] / start) ** (252 / max(1, len(eq))) - 1) if eq and start else 0.0
    return {"n": n, "wins": wins, "losses": n - wins, "avg_ret": round(avg, 5),
            "median_ret": round(med, 5), "max_dd": round(dd, 5),
            "sharpe": round(sharpe, 3), "sortino": round(sortino, 3),
            "cagr": round(cagr, 4), "final_equity": round(eq[-1], 2) if eq else start,
            "total_costs": round(total_costs, 2),
            "net_profit": round(sum(nets), 2),
            "avg_net_per_trade": round(sum(nets) / n, 2) if n else 0.0}
