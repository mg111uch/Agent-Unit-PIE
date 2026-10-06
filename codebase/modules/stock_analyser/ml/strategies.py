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


_PANEL_CACHE: dict = {}  # key -> rows list (symbol_frame algebra, ~99% of validate cost)
_SCORE_CACHE: dict = {}  # key -> label-free rows for serving (scores latest bars)


def _score_rows(bars: Dict[str, List[Dict]], fwd: int = 5):
    """Label-free feature rows incl. latest bars (prediction needs no labels)."""
    from .dataset import symbol_frame as _sf
    key = ("score",) + _panel_key(bars, fwd)
    hit = _SCORE_CACHE.get(key)
    if hit is not None:
        return hit
    from ..constants import is_tradable as _tradable
    try:
        from .sectors import bench_map as _bm
        tf = next((b.get("timeframe", "1D") for bl in bars.values() for b in bl[:1]), "1D")
        bench = _bm(None, tf) or None
    except Exception:
        bench = None
    rows = []
    for s, bl in bars.items():
        if not _tradable(s):
            continue
        for r in symbol_frame(bl, fwd, bench=bench, need_label=False):
            rows.append({"symbol": s, **r})
    from .dataset import _xs_normalize as _xs
    rows = _xs(rows, with_target=False)
    if len(_SCORE_CACHE) >= 8:
        _SCORE_CACHE.pop(next(iter(_SCORE_CACHE)))
    _SCORE_CACHE[key] = rows
    return rows


def _panel_key(bars: Dict[str, List[Dict]], fwd: int) -> tuple:
    return (fwd, tuple((s, len(bl), bl[0].get("ts", "") if bl else "",
                        bl[-1].get("ts", "") if bl else "",
                        bl[0].get("timeframe", "1D") if bl else "1D")
                       for s, bl in sorted(bars.items())))


def _panel_rows(bars: Dict[str, List[Dict]], fwd: int = 5):
    key = _panel_key(bars, fwd)
    hit = _PANEL_CACHE.get(key)
    if hit is not None:
        return hit
    rows = _panel_rows_uncached(bars, fwd)
    if len(_PANEL_CACHE) >= 8:
        _PANEL_CACHE.pop(next(iter(_PANEL_CACHE)))
    _PANEL_CACHE[key] = rows
    return rows


def _panel_rows_uncached(bars: Dict[str, List[Dict]], fwd: int = 5):
    rows = []
    from ..constants import is_tradable as _tradable
    try:
        from .sectors import bench_map as _bm
        tf = next((b.get("timeframe", "1D") for bl in bars.values() for b in bl[:1]), "1D")
        bench = _bm(None, tf) or None
    except Exception:
        bench = None
    for s, bl in bars.items():
        if not _tradable(s):
            continue
        for r in symbol_frame(bl, fwd, bench=bench):
            rows.append({"symbol": s, **r})
    from .dataset import _xs_normalize as _xs
    return _xs(rows, with_target=True, target_mode="rank-gauss")


def _rows_capped(bars: Dict[str, List[Dict]], fwd: int = 5, end_ts: str = ""):
    """Val-window rows sliced from the cached full panel (trailing-only, so
    framing-then-filtering == framing the truncated bars; ~1s vs ~85s rebuild)."""
    rows = _panel_rows(bars, fwd)
    if not end_ts:
        return rows
    return [r for r in rows if r.get("ts", "") <= end_ts]


def rolling_oos(strategy_d: Dict[str, Any], bars: Dict[str, List[Dict]],
                lock_from: str, start_cash: float = 50000.0,
                step_days: int = 21, max_origins: int = 30) -> Dict[str, Any]:
    """Stitched rolling-origin OOS: monthly expanding-window refit, each model
    scores only its own forward window; concatenated into one backtest. Gives
    2-3 years of OOS (vs 6-10 months for the one-shot lock) and matches how
    paper retrains. The final lock stays one-shot — rolling never sees it."""
    import pandas as pd
    from .ranker import score_lists as _sl
    m = strategy_d.get("meta", {}) or {}
    df = pd.DataFrame(_panel_rows(bars))
    if df.empty:
        return {"error": "no panel", "verdict": "REJECT"}
    dates = sorted(d for d in set(df["ts"]) if d < lock_from)
    if len(dates) < 60:
        return {"error": "thin pre-lock span", "verdict": "REJECT"}
    origins = dates[::max(1, step_days)][-max_origins:]
    parts = []
    for i, o in enumerate(origins):
        end = origins[i + 1] if i + 1 < len(origins) else lock_from
        if not (o < end):
            continue
        past = df[df["ts"] < o]
        # purge training labels overlapping the scoring window (see ml_signals)
        from datetime import datetime as _dt, timedelta as _td
        try:
            cut = (_dt.fromisoformat(o) - _td(days=10)).isoformat()
        except Exception:
            cut = o
        past = past[past["ts"] < cut]
        if len(past) < 50:
            continue
        try:
            model = train_ranker(past, top_n=m.get("top_n", 5),
                                 model=m.get("model", "hgb"),
                                 feats=m.get("features"),
                                 max_depth=m.get("max_depth", 3))
            parts.append(add_scores(model, df[(df["ts"] >= o) & (df["ts"] < end)]))
        except Exception:
            continue
    if not parts:
        return {"error": "no origins trained", "verdict": "REJECT"}
    import pandas as _pd
    scored = _pd.concat(parts)
    sigs = top_n_signals(scored, bars, top_n=m.get("top_n", 5),
                         live_from=origins[0])
    res = run_backtest(ml_exits(strategy_d), bars, start_cash=start_cash,
                       min_bars=0, signals=sigs, scores=_sl(scored, bars))
    res["origins"] = len(parts)
    res["from"] = origins[0]
    return res


def ml_signals(strategy_d: Dict[str, Any], bars: Dict[str, List[Dict]],
               live_from: str = "", _rows=None, _score=None,
               _keep: list | None = None, _freeze_db: str | None = None,
               _freeze_name: str = "") -> Dict[str, List[bool]]:
    """Train ranker on labeled bars strictly before live_from; score the
    label-free frame (incl. latest bars) and mask pre-live_from.

    Artifact freeze (ridge only): when _freeze_db is given, shadow scoring
    reuses ONE frozen ridge instead of retraining daily. First call trains
    and freezes; later calls load the hash-verified artifact. The frozen
    version is reported via _keep as {"frozen_version": v} so the ledger
    model id can tag it (refit_warning fires if the id ever changes)."""
    import pandas as pd
    m = strategy_d.get("meta", {})
    if m.get("model") == "ridge" and _freeze_db and _freeze_name:
        try:
            from .freeze import FrozenRidge, frozen_name
            fz = FrozenRidge(_freeze_db, frozen_name(_freeze_name))
            fz.top_n_ = int(m.get("top_n", 5) or 5)
            scored = add_scores(fz, pd.DataFrame(
                _score if _score is not None else _score_rows(bars)))
            if _keep is not None:
                _keep.append(scored)
                _keep.append({"frozen_version": fz.version})
            return top_n_signals(scored, bars, top_n=fz.top_n_, live_from=live_from)
        except KeyError:
            pass  # no frozen artifact yet: train below, then freeze
        except Exception:
            pass
    rows = _rows if _rows is not None else _panel_rows(bars)
    df = pd.DataFrame(rows)
    if df.empty:
        return {s: [False] * len(bl) for s, bl in bars.items()}
    if live_from:
        # purge: 5-bar labels (~7-9 calendar days over weekends) must not
        # overlap the scoring window; 10 calendar days is safely beyond.
        from datetime import datetime, timedelta
        try:
            cut = (datetime.fromisoformat(live_from) - timedelta(days=10)).isoformat()
        except Exception:
            cut = live_from
        past = df[df["ts"] < cut]
    else:
        past = df
    if len(past) < 50:
        return {s: [False] * len(bl) for s, bl in bars.items()}
    model = train_ranker(past, top_n=m.get("top_n", 5), model=m.get("model", "hgb"),
                         feats=m.get("features"), max_depth=m.get("max_depth", 3))
    if m.get("model") == "ridge" and _freeze_db and _freeze_name:
        try:  # first shadow run freezes; later runs reuse the artifact above
            from .freeze import freeze_sklearn_ridge, frozen_name
            v = freeze_sklearn_ridge(_freeze_db, frozen_name(_freeze_name),
                                     model, {"trained_through": live_from or ""})
            if _keep is not None:
                _keep.append({"frozen_version": v})
        except Exception:
            pass
    scored = add_scores(model, pd.DataFrame(
        _score if _score is not None else _score_rows(bars)))
    if _keep is not None:
        _keep.append(scored)
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
        # val bars with pre-live masking, so no peek. Purged 10d before val
        # start so 5-bar labels can't cross the boundary.
        df_all = pd.DataFrame(_panel_rows(bars))
        from datetime import datetime as _dt, timedelta as _td
        try:
            _cut = (_dt.fromisoformat(live) - _td(days=10)).isoformat() if live else ""
        except Exception:
            _cut = live
        past = df_all[df_all["ts"] < _cut] if live else df_all
        if df_all.empty or len(past) < 50:
            sigs = {s: [False] * len(bl) for s, bl in val.items()}
            val_scores = None
        else:
            model = train_ranker(past, top_n=m.get("top_n", 5),
                                 model=m.get("model", "hgb"),
                                 feats=m.get("features"),
                                 max_depth=m.get("max_depth", 3))
            _qsc = add_scores(model, df_all)
            from .ranker import score_lists as _qsl
            sigs = top_n_signals(_qsc, val,
                                 top_n=m.get("top_n", 5), live_from=live)
            val_scores = _qsl(_qsc, val)
        res = run_backtest(ml_exits(strategy_d), val, start_cash=start_cash,
                           min_bars=0, signals=sigs, scores=val_scores)
    else:
        from ..strategies.model import strategy_from_dict as sfd
        res = run_backtest(sfd(strategy_d), val, start_cash=start_cash, min_bars=0)
    n, net = res.get("n", 0) or 0, res.get("avg_net_per_trade", 0) or 0
    return {"pass": n >= min_trades and net >= min_avg_net, "n": n, "avg_net": net}


def validate_ml(strategy_d: Dict[str, Any], bars: Dict[str, List[Dict]],
                start_cash: float = 50000.0, early_kill: bool = True,
                dataset_id: str = "", db_path: str | None = None) -> Dict[str, Any]:
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
    stages["bounds"] = bounds  # leg scoping for capital-ladder probe
    m = strategy_d.get("meta", {})
    exits = ml_exits(strategy_d)
    # validation-slice backtest (the screen, recorded)
    from .ranker import score_lists as _sl
    _vsc = add_scores(train_ranker(
        tr_df, top_n=m.get("top_n", 5), model=m.get("model", "hgb"),
        feats=m.get("features"), max_depth=m.get("max_depth", 3)), df)
    v0 = run_backtest(exits, {s: [b for b in bars.get(s, []) if b["ts"] <= bounds["val_end"]]
                              for s in bars}, start_cash=start_cash, min_bars=0,
                      signals=top_n_signals(_vsc, bars, top_n=m.get("top_n", 5),
                                            live_from=bounds["val_start"]),
                      scores=_sl(_vsc, bars))
    stages["backtest"] = {k: v0.get(k) for k in ("n", "sharpe", "max_dd", "cagr",
                                                 "avg_net_per_trade", "net_profit",
                                                 "avg_hold_days")}
    if early_kill:  # IS-dead skips 2 dropout retrains + stress + locked (4 trains total)
        # bar matches the locked-OOS minimum (5): killing at 10 punished lack
        # of trades on a 20% slice, not lack of edge (P4 structural fix)
        _vn, _vnet = v0.get("n", 0) or 0, v0.get("avg_net_per_trade", 0) or 0
        if _vn < 5 or not _vnet > 0:
            stages.update(verdict="REJECT", reason="LOW_N_IS" if _vn < 5 else "NEG_IS",
                          robustness=0.0, perturbation={"avg_nets": [], "stable": False},
                          cost_stress={}, locked_oos={})
            return stages
    # perturbation = feature dropout: retrain without each of 2 top-variance feats
    # (val rows sliced from cached full panel — same values, no ~85s rebuild)
    val_rows = _rows_capped(bars, 5, bounds["val_end"])
    val_bars = {s: [b for b in bars.get(s, []) if b["ts"] <= bounds["val_end"]]
                for s in bars}
    full_score = _score_rows(bars)
    val_score = [r for r in full_score if r.get("ts", "") <= bounds["val_end"]]
    drops = []
    for f in list(tr_df[FEATS].var().nlargest(2).index):
        d2 = dict(strategy_d)
        d2["meta"] = {**m, "features": [x for x in m.get("features", FEATS) if x != f]}
        _dk: list = []
        r = run_backtest(exits, val_bars, start_cash=start_cash, min_bars=0,
                         signals=ml_signals(d2, val_bars, live_from=bounds["val_start"],
                                            _rows=val_rows, _score=val_score, _keep=_dk),
                         scores=_sl(_dk[0], val_bars) if _dk else None)
        drops.append(r.get("avg_net_per_trade", 0) or 0)
    stages["perturbation"] = {"avg_nets": drops, "stable": sum(1 for x in drops if x > 0) >= 2}
    # cost stress + locked test share one signal stream (same model inputs,
    # deterministic train → identical signals; exits differ only in costs)
    _tk: list = []
    sigs_test = ml_signals(strategy_d, bars, live_from=bounds["test_start"], _keep=_tk)
    test_scores = _sl(_tk[0], bars) if _tk else None
    stress_exits = ml_exits({**strategy_d, "flat_cost": (strategy_d.get("flat_cost", 0) or 60) * 2})
    st = run_backtest(stress_exits, bars, start_cash=start_cash, min_bars=0,
                      signals=sigs_test, scores=test_scores)
    stages["cost_stress"] = {"n": st.get("n"), "avg_net_per_trade": st.get("avg_net_per_trade")}
    if ml_hash(strategy_d) != h0:
        return {"verdict": "REJECT", "reason": "MUTATED_AFTER_SEAL",
                "robustness": 0.0, "seal": stages["seal"]}
    locked = run_backtest(exits, bars, start_cash=start_cash, min_bars=0,
                          signals=sigs_test, scores=test_scores)
    stages["locked_oos"] = {k: locked.get(k) for k in ("n", "sharpe", "max_dd", "cagr",
                                                       "avg_net_per_trade", "net_profit",
                                                       "avg_hold_days")}
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
          and (v0.get("n", 0) or 0) >= 5 and base_net > 0
          and stages["perturbation"]["stable"])
    if ok:  # Phase 2 honest gate: rank edge recorded (ML is rank-native),
        # excess-return CI binding
        try:
            from ..backtest.validation import rank_validation as _rv
            _tb = {s: [b for b in bl if b.get("ts", "") >= bounds["test_start"]]
                   for s, bl in bars.items()}
            stages["rank_validation"] = _rv(_tb)
        except Exception:
            pass
        try:
            from ..research.stats import excess_gate as _eg
            # gate on stitched rolling OOS (2-3 yrs, reachable periods); fall
            # back to the one-shot lock when rolling can't train
            _roll = rolling_oos(strategy_d, bars, bounds["test_start"], start_cash)
            if _roll.get("error"):
                stages["rolling_oos"] = {"error": _roll["error"], "origins": 0}
                _gtrades = locked.get("trades", [])
            else:
                stages["rolling_oos"] = {
                    k: _roll.get(k) for k in ("n", "sharpe", "max_dd", "cagr",
                                             "avg_net_per_trade", "net_profit",
                                             "avg_hold_days", "origins", "from")}
                _gtrades = _roll.get("trades", [])
            stages["excess_gate"] = _eg(_gtrades, dataset_id, db_path)
            if not stages["excess_gate"].get("pass"):
                ok = False
                stages["reason"] = str(stages["excess_gate"].get("reason")
                                       or "WEAK_EXCESS")[:24]
        except Exception:
            pass
    stages["verdict"] = "PAPER_READY" if ok else "REJECT"
    if not ok and "reason" not in stages:
        if (locked.get("n", 0) or 0) < 5:
            stages["reason"] = "LOW_N_OOS"
        elif not oos_net > 0:
            stages["reason"] = "NEG_OOS"
        elif not (locked.get("max_dd", 0) or 0) >= MAX_DD:
            stages["reason"] = "DEEP_DD"
        elif (v0.get("n", 0) or 0) < 5:
            stages["reason"] = "LOW_N_IS"
        elif not base_net > 0:
            stages["reason"] = "NEG_IS"  # ridge 2020-23 case: IS<0, OOS>0
        else:
            stages["reason"] = "UNSTABLE"
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
