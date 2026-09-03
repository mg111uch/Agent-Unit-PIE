"""ML candidates as first-class strategies: validate like symbolic, same gates.

Two-stage economics: quick screen (1 backtest on a validation slice) runs first;
only screen-passers pay for the full pipeline (perturbation, walk-forward,
locked test). Dead families are retired upstream in run_job.
"""
from __future__ import annotations
from typing import Any, Dict, List
from .dataset import FEATURES, symbol_frame, purged_date_split, split_panel
from .ranker import train_ranker, add_scores, top_n_signals, FEATS
from ..backtest.engine import run_backtest
from ..backtest.validation import MIN_TRADES, MAX_DD
from ..strategies.model import strategy_from_dict


def ml_exits(strategy_d: Dict[str, Any]):
    m = strategy_d.get("meta", {})
    base = {"name": strategy_d.get("name", "ml"), "universe": strategy_d.get("universe", ""),
            "timeframe": strategy_d.get("timeframe", "1D"), "entry": {"const": False},
            "stop_atr": m.get("stop_atr", 2.0), "take_atr": m.get("take_atr", 4.0),
            "max_hold": m.get("max_hold", 10), "position_frac": m.get("position_frac", 0.2),
            "max_positions": m.get("max_positions", 3),
            "flat_cost": strategy_d.get("flat_cost", 0.0)}
    return strategy_from_dict(base)


def _panel_rows(bars: Dict[str, List[Dict]], fwd: int = 5):
    rows = []
    for s, bl in bars.items():
        for r in symbol_frame(bl, fwd):
            rows.append({"symbol": s, **r})
    return rows


def ml_signals(strategy_d: Dict[str, Any], bars: Dict[str, List[Dict]],
               live_from: str = "") -> Dict[str, List[bool]]:
    """Train ranker on bars strictly before live_from, score all, mask past."""
    import pandas as pd
    m = strategy_d.get("meta", {})
    rows = _panel_rows(bars)
    df = pd.DataFrame(rows)
    if df.empty:
        return {s: [False] * len(bl) for s, bl in bars.items()}
    past = df[df["ts"] < live_from] if live_from else df
    if len(past) < 50:
        return {s: [False] * len(bl) for s, bl in bars.items()}
    model = train_ranker(past, top_n=m.get("top_n", 5), max_depth=m.get("max_depth", 3))
    scored = add_scores(model, df)
    return top_n_signals(scored, bars, top_n=m.get("top_n", 5), live_from=live_from)


def quick_screen(strategy_d: Dict[str, Any], bars: Dict[str, List[Dict]],
                 start_cash: float = 50000.0, min_trades: int = 3,
                 min_avg_net: float = -30.0) -> Dict[str, Any]:
    """One cheap backtest on the trailing 30% date slice. Lenient by design."""
    from ..backtest.validation import _split
    fam = strategy_d.get("meta", {}).get("family", "sym")
    _, val = _split(bars, 0.7)
    if fam == "ml":
        dates = sorted({b["ts"] for bl in val.values() for b in bl})
        sigs = ml_signals(strategy_d, val, live_from=dates[0] if dates else "")
        res = run_backtest(ml_exits(strategy_d), val, start_cash=start_cash,
                           min_bars=0, signals=sigs)
    else:
        from ..strategies.model import strategy_from_dict as sfd
        res = run_backtest(sfd(strategy_d), val, start_cash=start_cash, min_bars=0)
    n, net = res.get("n", 0) or 0, res.get("avg_net_per_trade", 0) or 0
    return {"pass": n >= min_trades and net >= min_avg_net, "n": n, "avg_net": net}


def validate_ml(strategy_d: Dict[str, Any], bars: Dict[str, List[Dict]],
                start_cash: float = 50000.0) -> Dict[str, Any]:
    """Full pipeline for ML family: screen -> val -> dropout -> stress -> locked test."""
    import pandas as pd
    stages: Dict[str, Any] = {}
    rows = _panel_rows(bars)
    df = pd.DataFrame(rows)
    if df.empty:
        return {"verdict": "REJECT", "reason": "no panel", "robustness": 0.0}
    tr_df, va_df, te_df, bounds = split_panel(df)
    m = strategy_d.get("meta", {})
    exits = ml_exits(strategy_d)
    # validation-slice backtest (the screen, recorded)
    v0 = run_backtest(exits, {s: [b for b in bars.get(s, []) if b["ts"] <= bounds["val_end"]]
                              for s in bars}, start_cash=start_cash, min_bars=0,
                      signals=top_n_signals(add_scores(train_ranker(tr_df, top_n=m.get("top_n", 5),
                                                                   max_depth=m.get("max_depth", 3)), df),
                                            bars, top_n=m.get("top_n", 5),
                                            live_from=bounds["val_start"]))
    stages["backtest"] = {k: v0.get(k) for k in ("n", "sharpe", "max_dd", "cagr",
                                                 "avg_net_per_trade", "net_profit")}
    # perturbation = feature dropout: retrain without each of 2 top-variance feats
    drops = []
    for f in list(tr_df[FEATS].var().nlargest(2).index):
        d2 = dict(strategy_d)
        d2["meta"] = {**m, "features": [x for x in m.get("features", FEATS) if x != f]}
        r = run_backtest(exits, {s: [b for b in bars.get(s, []) if b["ts"] <= bounds["val_end"]]
                                 for s in bars}, start_cash=start_cash, min_bars=0,
                         signals=ml_signals(d2, {s: [b for b in bars.get(s, [])
                                                     if b["ts"] <= bounds["val_end"]] for s in bars},
                                            live_from=bounds["val_start"]))
        drops.append(r.get("avg_net_per_trade", 0) or 0)
    stages["perturbation"] = {"avg_nets": drops, "stable": sum(1 for x in drops if x > 0) >= 1}
    # cost stress on locked test slice
    te_bars = {s: [b for b in bars.get(s, []) if b["ts"] >= bounds["test_start"]] for s in bars}
    stress_exits = ml_exits({**strategy_d, "flat_cost": (strategy_d.get("flat_cost", 0) or 60) * 2})
    st = run_backtest(stress_exits, te_bars, start_cash=start_cash, min_bars=0,
                      signals=ml_signals(strategy_d, te_bars))
    stages["cost_stress"] = {"n": st.get("n"), "avg_net_per_trade": st.get("avg_net_per_trade")}
    locked = run_backtest(exits, te_bars, start_cash=start_cash, min_bars=0,
                          signals=ml_signals(strategy_d, te_bars))
    stages["locked_oos"] = {k: locked.get(k) for k in ("n", "sharpe", "max_dd", "cagr",
                                                       "avg_net_per_trade", "net_profit")}
    stages["locked_oos"]["from"] = bounds["test_start"]
    base_net = v0.get("avg_net_per_trade", 0) or 0
    oos_net = locked.get("avg_net_per_trade", 0) or 0
    ok = ((locked.get("n", 0) or 0) >= 5 and oos_net > 0
          and (locked.get("max_dd", 0) or 0) >= MAX_DD
          and (v0.get("n", 0) or 0) >= 10 and base_net > 0
          and stages["perturbation"]["stable"])
    stages["verdict"] = "PAPER_READY" if ok else "REJECT"
    stages["robustness"] = round(sum(1 for v in [ok, stages["perturbation"]["stable"],
        oos_net > 0, (st.get("avg_net_per_trade", 0) or 0) > 0] if v) / 4, 2)
    return stages
