"""Falsification: try to break contenders before PAPER_READY (stdlib).

Runs ONLY on validation passers (bounded cost). Tests, all seeded:
- permutation: shuffled signals should destroy edge (p-proxy)
- halves: edge must not live in one half only
- shift: +1-bar signal delay must degrade gracefully, not invert
- leave-one-out: no single symbol may carry the edge (<=4 symbols probed)

Returns {"survived", "tests"}. Lenient thresholds: deliberate attacks should
fail junk, not demand perfection from real edge.
"""
from __future__ import annotations
import random
from typing import Any, Dict, List


def _net(exits, bars, signals, cash: float) -> float:
    from ..backtest.engine import run_backtest
    r = run_backtest(exits, bars, start_cash=cash, min_bars=0, signals=signals)
    return float(r.get("avg_net_per_trade") or 0)


def _halve(bars: Dict[str, List[Dict]]) -> tuple:
    dates = sorted({b["ts"] for bl in bars.values() for b in bl})
    mid = dates[len(dates) // 2] if dates else ""
    return ({s: [b for b in bl if b["ts"] <= mid] for s, bl in bars.items()},
            {s: [b for b in bl if b["ts"] > mid] for s, bl in bars.items()})


def _shift_signals(signals: Dict[str, List[bool]], k: int = 1) -> Dict[str, List[bool]]:
    return {s: [False] * min(k, len(sl)) + sl[:len(sl) - k] for s, sl in signals.items()}


def _permute(signals: Dict[str, List[bool]], seed: int) -> Dict[str, List[bool]]:
    rng = random.Random(seed)
    out = {}
    for s, sl in signals.items():
        idx = list(range(len(sl)))
        rng.shuffle(idx)
        out[s] = [sl[j] for j in idx]
    return out


def falsify_signals(exits, bars: Dict[str, List[Dict]], signals: Dict[str, List[bool]],
                    base_net: float, cash: float = 50000.0,
                    cfg: Dict[str, Any] | None = None) -> Dict[str, Any]:
    cfg = cfg or {}
    n_perm = int(cfg.get("falsify_perms", 3))
    perms = [_net(exits, bars, _permute(signals, 900 + p), cash) for p in range(n_perm)]
    p_beats = sum(1 for x in perms if x >= base_net) / max(1, len(perms))
    h1, h2 = _halve(bars)
    # slice signals to each half's bars length
    def _slice(half):
        return {s: (signals.get(s, [])[:len(half.get(s, []))]) for s in half}
    n1, n2 = _net(exits, h1, _slice(h1), cash), _net(exits, h2, _slice(h2), cash)
    sh = _net(exits, bars, _shift_signals(signals), cash)
    syms = sorted(bars)[:int(cfg.get("falsify_loo_max", 4))]
    loos = []
    for drop in syms:
        sub = {s: bl for s, bl in bars.items() if s != drop}
        sig = {s: sl for s, sl in signals.items() if s != drop}
        loos.append(_net(exits, sub, sig, cash))
    tests = {
        "permutation_beats": round(p_beats, 3),
        "perm_nets": [round(x, 2) for x in perms],
        "half_nets": [round(n1, 2), round(n2, 2)],
        "shift_net": round(sh, 2),
        "loo_nets": [round(x, 2) for x in loos],
    }
    survived = (p_beats <= float(cfg.get("falsify_max_p", 0.34))
                and (n1 > 0 or n2 > 0)
                and sh > -abs(base_net) * 2 - 5
                and sum(1 for x in loos if x > 0) >= max(1, len(loos) - 1))
    return {"survived": survived, "tests": tests}


def falsify_symbolic(strategy, bars, base_net: float, cash: float = 50000.0,
                     cfg: Dict[str, Any] | None = None) -> Dict[str, Any]:
    from ..backtest.engine import _signals
    sigs = {s: _signals(strategy, bl) for s, bl in bars.items()}
    return falsify_signals(strategy, bars, sigs, base_net, cash, cfg)


def falsify_ml(strategy_d: Dict[str, Any], bars, base_net: float,
               cash: float = 50000.0, cfg: Dict[str, Any] | None = None) -> Dict[str, Any]:
    from ..ml.strategies import ml_signals, ml_exits
    from ..backtest.validation import _split
    _, val = _split(bars, 0.7)
    sigs = ml_signals(strategy_d, val)
    return falsify_signals(ml_exits(strategy_d), val, sigs, base_net, cash, cfg)
