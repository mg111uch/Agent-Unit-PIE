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
from ..backtest.validation import MIN_TRADES, MAX_DD, seal, strategy_hash
from ..strategies.model import strategy_from_dict
import hashlib
import json


def ml_hash(strategy_d: Dict[str, Any]) -> str:
    m = strategy_d.get("meta", {}) or {}
    core = {"exits": [m.get("stop_atr"), m.get("take_atr"), m.get("max_hold"),
                       m.get("position_frac"), m.get("max_positions")],
            "ml": [m.get("model", "hgb"), m.get("top_n"), m.get("max_depth"),
                   m.get("features")],
            "flat": strategy_d.get("flat_cost")}
    return hashlib.sha256(json.dumps(core, sort_keys=True).encode()).hexdigest()[:16]


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
    model = train_ranker(past, top_n=m.get("top_n", 5), model=m.get("model", "hgb"),
                         feats=m.get("features"), max_depth=m.get("max_depth", 3))
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
        import pandas as pd
        dates = sorted({b["ts"] for bl in val.values() for b in bl})
        live = dates[0] if dates else ""
        m = strategy_d.get("meta", {}) or {}
        # train on full history strictly before val (val-only panel starves
        # training: past would be empty by construction); score mapped onto
        # val bars with pre-live masking, so no peek.
        df_all = pd.DataFrame(_panel_rows(bars))
        past = df_all[df_all["ts"] < live] if live else df_all
        if df_all.empty or len(past) < 50:
            sigs = {s: [False] * len(bl) for s, bl in val.items()}
        else:
            model = train_ranker(past, top_n=m.get("top_n", 5),
                                 model=m.get("model", "hgb"),
                                 feats=m.get("features"),
                                 max_depth=m.get("max_depth", 3))
            sigs = top_n_signals(add_scores(model, df_all), val,
                                 top_n=m.get("top_n", 5), live_from=live)
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
    if (strategy_d.get("meta", {}) or {}).get("oos_seal"):
        return {"verdict": "REJECT", "reason": "MUTATED_AFTER_SEAL",
                "robustness": 0.0, "seal": strategy_d["meta"]["oos_seal"]}
    h0 = ml_hash(strategy_d)
    rows = _panel_rows(bars)
    df = pd.DataFrame(rows)
    if df.empty:
        return {"verdict": "REJECT", "reason": "no panel", "robustness": 0.0}
    try:
        tr_df, va_df, te_df, bounds = split_panel(df)
    except ValueError:  # non-ISO ts (e.g. synthetic): positional 60/20/20 split
        df = df.sort_values("ts").reset_index(drop=True)
        n = len(df)
        c1, c2 = int(n * 0.6), int(n * 0.8)
        tr_df, va_df = df.iloc[:c1], df.iloc[c1:c2]
        bounds = {"train_end": str(df["ts"].iloc[c1 - 1]), "val_start": str(df["ts"].iloc[c1]),
                  "val_end": str(df["ts"].iloc[c2 - 1]), "test_start": str(df["ts"].iloc[c2])}
    stages["seal"] = {"strategy_hash": h0, "cut": bounds["test_start"], "oos_frac": "ml-embargo"}
    m = strategy_d.get("meta", {})
    exits = ml_exits(strategy_d)
    # validation-slice backtest (the screen, recorded)
    v0 = run_backtest(exits, {s: [b for b in bars.get(s, []) if b["ts"] <= bounds["val_end"]]
                              for s in bars}, start_cash=start_cash, min_bars=0,
                      signals=top_n_signals(add_scores(train_ranker(
                          tr_df, top_n=m.get("top_n", 5), model=m.get("model", "hgb"),
                          feats=m.get("features"), max_depth=m.get("max_depth", 3)), df),
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
    # cost stress + locked test: train strictly pre-test, score full panel, mask past
    stress_exits = ml_exits({**strategy_d, "flat_cost": (strategy_d.get("flat_cost", 0) or 60) * 2})
    st = run_backtest(stress_exits, bars, start_cash=start_cash, min_bars=0,
                      signals=ml_signals(strategy_d, bars, live_from=bounds["test_start"]))
    stages["cost_stress"] = {"n": st.get("n"), "avg_net_per_trade": st.get("avg_net_per_trade")}
    if ml_hash(strategy_d) != h0:
        return {"verdict": "REJECT", "reason": "MUTATED_AFTER_SEAL",
                "robustness": 0.0, "seal": stages["seal"]}
    locked = run_backtest(exits, bars, start_cash=start_cash, min_bars=0,
                          signals=ml_signals(strategy_d, bars, live_from=bounds["test_start"]))
    stages["locked_oos"] = {k: locked.get(k) for k in ("n", "sharpe", "max_dd", "cagr",
                                                       "avg_net_per_trade", "net_profit")}
    stages["locked_oos"]["from"] = bounds["test_start"]
    try:
        from .ranker import attribution as _attr
        probe = train_ranker(tr_df, top_n=m.get("top_n", 5), model=m.get("model", "hgb"),
                             feats=m.get("features"), max_depth=m.get("max_depth", 3))
        stages["attribution"] = {"model": getattr(probe, "model_name_", "hgb"),
                                 "top_features": _attr(probe, va_df)}
    except Exception:
        pass
    base_net = v0.get("avg_net_per_trade", 0) or 0
    oos_net = locked.get("avg_net_per_trade", 0) or 0
    ok = ((locked.get("n", 0) or 0) >= 5 and oos_net > 0
          and (locked.get("max_dd", 0) or 0) >= MAX_DD
          and (v0.get("n", 0) or 0) >= 10 and base_net > 0
          and stages["perturbation"]["stable"])
    stages["verdict"] = "PAPER_READY" if ok else "REJECT"
    stages["robustness"] = round(sum(1 for v in [ok, stages["perturbation"]["stable"],
        oos_net > 0, (st.get("avg_net_per_trade", 0) or 0) > 0] if v) / 4, 2)
    if ok:
        try:  # falsification: break it before promoting (passers only, bounded)
            from ..research.falsify import falsify_ml
            from ..config import load_capital as _fcap
            fal = falsify_ml(strategy_d, bars, base_net, start_cash, _fcap())
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
            m2 = strategy_d.get("meta", {}) or {}
            liq = _liqgate(bars, float(m2.get("position_frac", 0.2)), start_cash, _lcap())
            stages["liquidity"] = {k: v for k, v in liq.items() if k != "per_symbol"}
            if not liq["pass"]:
                stages["verdict"] = "REJECT"
                stages["reason"] = "ILLIQUID"
        except Exception:
            pass
    try:
        from ..research.scoring import score as _score
        from ..config import load_capital as _cap
        stages["research_score"] = _score(strategy_d, stages, _cap())
    except Exception:
        pass
    return stages
