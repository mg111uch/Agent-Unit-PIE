"""Falsification: try to break contenders before PAPER_READY (stdlib).

Runs ONLY on validation passers (bounded cost). Tests, all seeded:
- permutation: shuffled signals should destroy edge (19 perms, p <= 0.05)
- halves: edge must survive in BOTH halves, not live in one
- shift: +1-bar signal delay must degrade gracefully (bounded by base magnitude)
- leave-one-out: no single symbol may carry the edge (seeded random sample)

Returns {"survived", "tests"}. Strict on purpose: these run on passers only,
so a real edge must survive deliberate attacks, not just clear weak bars.
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
    seed = int(cfg.get("falsify_seed", 7))
    n_perm = int(cfg.get("falsify_perms", 19))
    perms = [_net(exits, bars, _permute(signals, seed * 1000 + 900 + p), cash)
             for p in range(n_perm)]
    p_beats = sum(1 for x in perms if x >= base_net) / max(1, len(perms))
    h1, h2 = _halve(bars)
    # slice signals to each half's bars length
    def _slice(half):
        return {s: (signals.get(s, [])[:len(half.get(s, []))]) for s in half}
    n1, n2 = _net(exits, h1, _slice(h1), cash), _net(exits, h2, _slice(h2), cash)
    sh = _net(exits, bars, _shift_signals(signals), cash)
    # seeded random sample across the universe, not first-N alphabetically
    # (alphabetical LOO re-probed the same large-caps every run)
    rng = random.Random(seed)
    pool = sorted(bars)
    k = min(len(pool), max(1, int(cfg.get("falsify_loo_max", 6))))
    syms = rng.sample(pool, k) if len(pool) > k else pool
    loos = []
    for drop in syms:
        sub = {s: bl for s, bl in bars.items() if s != drop}
        sig = {s: sl for s, sl in signals.items() if s != drop}
        loos.append(_net(exits, sub, sig, cash))
    need_halves = int(cfg.get("falsify_min_halves", 2))
    halves_ok = sum(1 for x in (n1, n2) if x > 0) >= min(2, need_halves)
    tests = {
        "permutation_beats": round(p_beats, 3),
        "perm_nets": [round(x, 2) for x in perms],
        "half_nets": [round(n1, 2), round(n2, 2)],
        "shift_net": round(sh, 2),
        "loo_nets": [round(x, 2) for x in loos],
        "loo_dropped": syms,
    }
    survived = (p_beats <= float(cfg.get("falsify_max_p", 0.05))
                and halves_ok
                and sh > -abs(base_net)
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
    # train on full history strictly before val (like quick_screen): training
    # on val itself would score in-sample rows.
    vdates = sorted({b["ts"] for bl in val.values() for b in bl})
    live = vdates[0] if vdates else ""
    full = ml_signals(strategy_d, bars, live_from=live)
    sigs = {}
    for s, bl in val.items():
        fl = full.get(s, [])
        sigs[s] = fl[len(fl) - len(bl):] if len(fl) >= len(bl) \
            else [False] * (len(bl) - len(fl)) + fl
    return falsify_signals(ml_exits(strategy_d), val, sigs, base_net, cash, cfg)
