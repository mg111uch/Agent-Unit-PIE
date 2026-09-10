"""Validation pipeline: cost stress -> perturbation -> walk-forward -> locked OOS.

Hard seal: `seal()` snapshots (strategy_hash, cut) before OOS; `run_locked_oos`
refuses if candidate hash != sealed hash. A strategy carrying `meta.oos_seal`
already saw OOS and is REJECTed on re-validation; `mutate()` clears it (new lineage).
"""
from __future__ import annotations
import copy
import hashlib
import json
from typing import Dict, List, Any
from ..strategies.model import Strategy
from ..strategies.genome import mutate
from .engine import run_backtest
from .costs import stressed_costs

MIN_TRADES, MIN_SHARPE, MAX_DD = 20, 0.5, -0.35


def strategy_hash(d: Dict[str, Any]) -> str:
    canon = {k: v for k, v in d.items() if k not in ("name", "meta")}
    return hashlib.sha256(json.dumps(canon, sort_keys=True).encode()).hexdigest()[:16]


def _corr(xs: List[float], ys: List[float]) -> float:
    n = len(xs)
    if n < 10:
        return 0.0
    mx, my = sum(xs) / n, sum(ys) / n
    dx = [x - mx for x in xs]
    dy = [y - my for y in ys]
    den = (sum(a * a for a in dx) * sum(b * b for b in dy)) ** 0.5
    return sum(a * b for a, b in zip(dx, dy)) / den if den else 0.0


def rank_validation(bars: Dict[str, List], lookback: int = 20, top_n: int = 5,
                    hold: int = 5, cfg: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Cross-sectional rank validation (Adds): is there rank edge, not just a
    single-symbol curve-fit? Each date: rank symbols by trailing `lookback`
    return, hold top_n for `hold` bars vs bottom_n. Reports mean spread,
    hit-rate, mean rank IC. Date-aligned; symbols missing a date sit out."""
    cfg = cfg or {}
    px: Dict[str, Dict[str, float]] = {}
    for s, bl in bars.items():
        for b in bl:
            if b.get("close"):
                px.setdefault(s, {})[b["ts"]] = float(b["close"])
    dates = sorted({d for m in px.values() for d in m})
    spreads, ics, n = [], [], 0
    for i in range(lookback, len(dates) - hold):
        d0, d1, d2 = dates[i - lookback], dates[i], dates[i + hold]
        uni = [(s, m[d1] / m[d0] - 1, m[d2] / m[d1] - 1)
               for s, m in px.items() if d0 in m and d1 in m and d2 in m and m[d0] > 0]
        if len(uni) < max(4, top_n * 2):
            continue
        uni.sort(key=lambda t: t[1])
        lo, hi = uni[:top_n], uni[-top_n:]
        spreads.append(sum(t[2] for t in hi) / top_n - sum(t[2] for t in lo) / top_n)
        ranks = {s: r for r, (s, _, _) in enumerate(uni)}
        ics.append(_corr([ranks[s] for s, _, _ in uni], [f for _, _, f in uni]))
        n += 1
    mean_sp = sum(spreads) / len(spreads) if spreads else 0.0
    hit = sum(1 for x in spreads if x > 0) / len(spreads) if spreads else 0.0
    mean_ic = sum(ics) / len(ics) if ics else 0.0
    ok = (n >= int(cfg.get("rank_min_periods", 20)) and mean_sp > 0
          and hit >= float(cfg.get("rank_min_hit", 0.55)))
    return {"pass": ok, "mean_spread": round(mean_sp, 4), "hit_rate": round(hit, 3),
            "mean_rank_ic": round(mean_ic, 4), "periods": n,
            "params": {"lookback": lookback, "top_n": top_n, "hold": hold}}


def seal(strategy_d: Dict[str, Any], cut: str, oos_frac: float) -> Dict[str, Any]:
    return {"strategy_hash": strategy_hash(strategy_d), "cut": cut, "oos_frac": oos_frac}


def run_locked_oos(strategy: Strategy, oos: Dict[str, List],
                   sealed: Dict[str, Any], start_cash: float = 50000.0) -> Dict[str, Any]:
    if strategy_hash(strategy.to_dict()) != sealed.get("strategy_hash"):
        return {"error": "MUTATED_AFTER_SEAL", "verdict": "REJECT",
                "reason": "strategy mutated after seal; new lineage required"}
    r = run_backtest(strategy, oos, start_cash=start_cash, min_bars=0)
    return {k: r.get(k) for k in ("n", "sharpe", "max_dd", "cagr",
                                  "avg_net_per_trade", "net_profit",
                                  "avg_hold_days")}


def _split(bars: Dict[str, List], frac: float) -> tuple:
    """Shared-date split: one OOS period for all symbols (late entrants keep own window)."""
    dates = sorted({b["ts"] for bl in bars.values() for b in bl})
    cut = dates[max(5, int(len(dates) * frac) - 1)] if dates else ""
    tr = {s: [b for b in bl if b["ts"] <= cut] for s, bl in bars.items()}
    te = {s: [b for b in bl if b["ts"] > cut] for s, bl in bars.items()}
    return {s: v for s, v in tr.items() if v}, {s: v for s, v in te.items() if v}


def validate_strategy(strategy: Strategy, bars: Dict[str, List[Dict[str, Any]]],
                      oos_frac: float = 0.2, start_cash: float = 50000.0,
                      min_bars: int | None = None, early_kill: bool = True) -> Dict[str, Any]:
    if (strategy.meta or {}).get("oos_seal"):
        return {"verdict": "REJECT", "reason": "MUTATED_AFTER_SEAL",
                "robustness": 0.0, "seal": (strategy.meta or {})["oos_seal"]}
    if min_bars is None:
        try:
            from ..config import load_capital
            min_bars = int(load_capital().get("min_history_bars", 60) or 60)
        except Exception:
            min_bars = 60
    eligible = {s: bl for s, bl in bars.items() if len(bl) >= min_bars}
    stages: Dict[str, Any] = {"excluded": sorted(set(bars) - set(eligible))}
    train, oos = _split(eligible, 1 - oos_frac)
    dates = sorted({b["ts"] for bl in eligible.values() for b in bl})
    cut = dates[max(5, int(len(dates) * (1 - oos_frac)) - 1)] if dates else ""
    sealed = seal(strategy.to_dict(), cut, oos_frac)
    stages["seal"] = sealed
    stages["cut"] = cut  # IS/OOS leg scoping for capital-ladder probe
    base = run_backtest(strategy, train, start_cash=start_cash, min_bars=0)
    stages["backtest"] = {k: base.get(k) for k in ("n", "sharpe", "max_dd", "cagr",
                                                   "avg_net_per_trade", "net_profit",
                                                   "avg_hold_days")}
    if early_kill:  # IS-dead pays 1 backtest, not ~10 (batch-2: most REJECTs here)
        _bn, _bnet = base.get("n", 0) or 0, base.get("avg_net_per_trade", 0) or 0
        if _bn < MIN_TRADES or not _bnet > 0:
            stages.update(verdict="REJECT",
                          reason="LOW_N_IS" if _bn < MIN_TRADES else "NEG_IS",
                          robustness=0.0, perturbation={"avg_nets": [], "stable": False},
                          walk_forward={"avg_nets": []}, locked_oos={})
            return stages
    s2 = copy.deepcopy(strategy)
    s2.fee_bps, s2.slippage_bps = stressed_costs(strategy.fee_bps, strategy.slippage_bps)
    if hasattr(s2, "flat_cost") and s2.flat_cost:
        s2.flat_cost = s2.flat_cost * 2  # stress flat costs too
    stress = run_backtest(s2, train, start_cash=start_cash, min_bars=0)
    stages["cost_stress"] = {"sharpe": stress.get("sharpe"), "n": stress.get("n"),
                             "avg_net_per_trade": stress.get("avg_net_per_trade")}
    try:  # honest drag report: realistic roundtrip at representative notional
        from .costs import realistic_breakdown as _real
        from ..config import load_capital as _ccap
        _cc = _ccap()
        _not = start_cash * float(getattr(strategy, "position_frac", 0.1) or 0.1)
        stages["realistic_costs"] = {"per_trade_drag": _real(_not, _cc)["total"],
                                     "notional": round(_not, 2)}
    except Exception:
        pass
    perts = []
    for i in range(4):
        m = mutate(strategy, seed=100 + i, kind="threshold")
        r = run_backtest(m, train, start_cash=start_cash, min_bars=0)
        perts.append(r.get("avg_net_per_trade", 0) or 0)
    stages["perturbation"] = {"avg_nets": perts,
                              "stable": sum(1 for x in perts if x > 0) >= 2}
    # walk-forward: 3 folds on train
    wfs = []
    for f in range(3):
        wcut = int(len(next(iter(train.values()))) * (0.5 + 0.15 * f))
        sub = {s: bl[:wcut] for s, bl in train.items()}
        wfs.append(run_backtest(strategy, sub, start_cash=start_cash, min_bars=0).get("avg_net_per_trade", 0) or 0)
    stages["walk_forward"] = {"avg_nets": wfs}
    locked = run_locked_oos(strategy, oos, sealed, start_cash=start_cash)
    if locked.get("error") == "MUTATED_AFTER_SEAL":
        locked["reason"] = locked.pop("error")
        stages["locked_oos"] = locked
        stages["verdict"] = "REJECT"
        stages["robustness"] = 0.0
        return stages
    stages["locked_oos"] = locked
    base_net = base.get("avg_net_per_trade", 0) or 0
    oos_net = locked.get("avg_net_per_trade", 0) or 0
    ok = (locked.get("n", 0) >= 5 and oos_net > 0
          and (base.get("max_dd", 0) or 0) >= MAX_DD
          and (base.get("n", 0) or 0) >= MIN_TRADES
          and base_net > 0
          and stages["perturbation"]["stable"])
    stages["verdict"] = "PAPER_READY" if ok else "REJECT"
    if not ok and "reason" not in stages:
        if (locked.get("n", 0) or 0) < 5:
            stages["reason"] = "LOW_N_OOS"
        elif not oos_net > 0:
            stages["reason"] = "NEG_OOS"
        elif not (base.get("max_dd", 0) or 0) >= MAX_DD:
            stages["reason"] = "DEEP_DD"
        elif (base.get("n", 0) or 0) < MIN_TRADES:
            stages["reason"] = "LOW_N_IS"
        elif not base_net > 0:
            stages["reason"] = "NEG_IS"
        else:
            stages["reason"] = "UNSTABLE"
    stages["robustness"] = round(sum(1 for v in [ok, stages["perturbation"]["stable"],
        oos_net > 0, (stress.get("avg_net_per_trade", 0) or 0) > 0] if v) / 4, 2)
    if ok:
        try:  # falsification: break it before promoting (passers only, bounded)
            from ..research.falsify import falsify_symbolic
            from ..config import load_capital as _fcap
            fal = falsify_symbolic(strategy, train, base_net, start_cash, _fcap())
            stages["falsification"] = fal
            if not fal.get("survived"):
                stages["verdict"] = "REJECT"
                stages["reason"] = "FALSIFIED"
                ok = False
        except Exception:
            pass
    if ok:
        try:  # P16 liquidity/capacity: untradable size is not a strategy
            from ..research.liquidity import gate as _liqgate
            from ..config import load_capital as _lcap
            liq = _liqgate(eligible, strategy.position_frac, start_cash, _lcap())
            stages["liquidity"] = {k: v for k, v in liq.items() if k != "per_symbol"}
            if not liq["pass"]:
                stages["verdict"] = "REJECT"
                stages["reason"] = "ILLIQUID"
                ok = False
        except Exception:
            pass
    try:
        from ..research.scoring import score as _score
        from ..config import load_capital as _cap
        stages["research_score"] = _score(strategy.to_dict(), stages, _cap())
    except Exception:
        pass
    return stages
