"""Cheap alpha gate (stdlib + sklearn probe): hierarchical L0, no portfolio sim.

L0-A sanity (observations, panel depth) → L0-B univariate linear IC →
L0-C rank/nonlinear (quintile spread) → L0-D interaction probe (best pair
product) → L0-E tiny ML probe (capped HGB, subsampled). A pass at ANY of
B/C/D/E keeps the candidate: standalone IC ≈ 0 must not kill nonlinear,
conditional, or interaction-only signal before ML sees it.
Symbolic entries keep the freq/turnover/complexity gate.
"""
from __future__ import annotations
import math
from typing import Any, Dict, List


def expr_nodes(e: Any) -> int:
    if not isinstance(e, dict):
        return 1
    if "const" in e or "field" in e:
        return 1
    return 1 + sum(expr_nodes(a) for a in e.get("args", []))


def _corr(xs: List[float], ys: List[float]) -> float:
    n = len(xs)
    if n < 10:
        return 0.0
    mx, my = sum(xs) / n, sum(ys) / n
    dx = [x - mx for x in xs]
    dy = [y - my for y in ys]
    den = math.sqrt(sum(a * a for a in dx) * sum(b * b for b in dy))
    return sum(a * b for a, b in zip(dx, dy)) / den if den else 0.0


def _symbolic_stats(entry: Dict, bars: Dict[str, List[Dict]]) -> Dict[str, Any]:
    from ..features.algebra import columns_from_bars, evaluate
    freqs, flips, nobs = [], [], 0
    for bl in bars.values():
        if len(bl) < 30:
            continue
        sigs = evaluate(entry, columns_from_bars(bl))
        hot = [1 if s is True else 0 for s in sigs]
        n = len(hot)
        nobs += n
        f = sum(hot) / n if n else 0
        freqs.append(f)
        flips.append(sum(1 for a, b in zip(hot, hot[1:]) if a != b) / n if n else 0)
    if not freqs:
        return {"freq": 0.0, "nobs": 0, "turnover": 1.0, "stab_sym": 0.0, "stab_time": 0.0}
    mf = sum(freqs) / len(freqs)
    sd = math.sqrt(sum((f - mf) ** 2 for f in freqs) / len(freqs)) if len(freqs) > 1 else 0.0
    return {"freq": mf, "nobs": nobs,
            "turnover": sum(flips) / len(flips),
            "stab_sym": 1.0 / (1.0 + sd * 10),
            "stab_time": 1.0 if 0.005 <= mf <= 0.4 else max(0.0, 1.0 - abs(mf - 0.1) * 5)}


def _ml_stats(bars: Dict[str, List[Dict]]) -> Dict[str, Any]:
    from ..ml.dataset import symbol_frame
    xs: Dict[str, List[float]] = {}
    ys: List[float] = []
    rows = []
    for bl in bars.values():
        rows.extend(symbol_frame(bl))
    if len(rows) < 50:
        return {"ic": 0.0, "nobs": len(rows), "stab": 0.0}
    feats = [k for k in rows[0] if k not in ("ts", "symbol", "fwd_ret")]
    half = len(rows) // 2
    best, stab = 0.0, 0.0
    for f in feats:
        x = [r[f] for r in rows]
        y = [r["fwd_ret"] for r in rows]
        ic = abs(_corr(x, y))
        ic1 = abs(_corr(x[:half], y[:half]))
        ic2 = abs(_corr(x[half:], y[half:]))
        if ic > best:
            best = ic
            stab = 1.0 - min(1.0, abs(ic1 - ic2) * 10)
    return {"ic": best, "nobs": len(rows), "stab": stab}


def _rank_spread(vals: List[float], y: List[float], qs: int = 5) -> float:
    """L0-C: mean(fwd_ret | top quintile of feat) - mean(bottom quintile)."""
    n = len(vals)
    if n < 50:
        return 0.0
    order = sorted(range(n), key=lambda i: vals[i])
    q = max(1, n // qs)
    lo = [y[i] for i in order[:q]]
    hi = [y[i] for i in order[-q:]]
    return sum(hi) / len(hi) - sum(lo) / len(lo)


def hierarchy(bars: Dict[str, List[Dict]], feats: List[str] | None = None,
              cfg: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """L0-A→E probe ladder over one shared panel. Pass at ANY of B/C/D/E keeps."""
    from ..ml.dataset import symbol_frame
    cfg = cfg or {}
    min_obs = int(cfg.get("alpha_min_obs", 200))
    rows = []
    for bl in bars.values():
        rows.extend(symbol_frame(bl))
    # L0-A sanity
    if len(rows) < min_obs:
        return {"pass": False, "score": -1.0, "levels": {"A": {"nobs": len(rows)}}}
    allf = [k for k in rows[0] if k not in ("ts", "symbol", "fwd_ret")]
    use = [f for f in (feats or allf) if f in allf] or allf
    y = [r["fwd_ret"] for r in rows]
    ysd = (sum((v - sum(y) / len(y)) ** 2 for v in y) / len(y)) ** 0.5 or 1.0
    half = len(rows) // 2
    # L0-B univariate linear IC (+ stability on best)
    b_ic, b_stab, b_feat = 0.0, 0.0, ""
    ics: Dict[str, float] = {}
    for f in use:
        x = [r[f] for r in rows]
        ic = abs(_corr(x, y))
        ics[f] = ic
        if ic > b_ic:
            b_ic = ic
            b_feat = f
            b_stab = 1.0 - min(1.0, abs(abs(_corr(x[:half], y[:half]))
                                       - abs(_corr(x[half:], y[half:])) * 10))
    # L0-C rank/nonlinear spread on best-B feature + best spread overall
    b_spread = 0.0
    for f in sorted(ics, key=lambda k: -ics[k])[:5]:
        sp = abs(_rank_spread([r[f] for r in rows], y)) / ysd
        b_spread = max(b_spread, sp)
    # L0-D interaction probe: product of top-2 univariate features
    top2 = sorted(ics, key=lambda k: -ics[k])[:2]
    d_ic = 0.0
    if len(top2) == 2:
        z = [rows[i][top2[0]] * rows[i][top2[1]] for i in range(len(rows))]
        d_ic = abs(_corr(z, y))
    # L0-E tiny ML probe: capped HGB on subsample, IC of OOS-fold predictions
    e_ic = 0.0
    try:
        import numpy as np
        from sklearn.ensemble import HistGradientBoostingRegressor
        cap = min(int(cfg.get("alpha_probe_cap", 2000)), len(rows))
        rng = np.random.RandomState(7)
        idx = rng.choice(len(rows), cap, replace=False)
        X = np.array([[rows[i][f] for f in use] for i in idx], dtype=float)
        yy = np.array([rows[i]["fwd_ret"] for i in idx], dtype=float)
        k = max(1, cap // 2)
        m = HistGradientBoostingRegressor(max_iter=50, max_depth=2, random_state=7)
        m.fit(X[:k], yy[:k])
        e_ic = abs(_corr(list(m.predict(X[k:])), list(yy[k:])))
    except Exception:
        pass
    lv = {"A": {"nobs": len(rows)},
          "B": {"ic": round(b_ic, 4), "feat": b_feat, "stab": round(b_stab, 3)},
          "C": {"spread": round(b_spread, 4)},
          "D": {"ic": round(d_ic, 4), "pair": top2},
          "E": {"ic": round(e_ic, 4)}}
    ok = (b_ic >= float(cfg.get("alpha_min_ic", 0.02))
          or b_spread >= float(cfg.get("alpha_min_spread", 0.15))
          or d_ic >= float(cfg.get("alpha_min_ic", 0.02))
          or e_ic >= float(cfg.get("alpha_min_e_ic", 0.05)))
    score = max(b_ic * 2 + b_stab * 0.5, b_spread, d_ic * 2, e_ic * 3)
    return {"pass": ok, "score": round(score, 3), "levels": lv}


def screen(strategy_d: Dict[str, Any], bars: Dict[str, List[Dict]],
           cfg: Dict[str, Any] | None = None) -> Dict[str, Any]:
    cfg = cfg or {}
    fam = (strategy_d.get("meta", {}) or {}).get("family", "sym")
    min_obs = int(cfg.get("alpha_min_obs", 200))
    max_nodes = int(cfg.get("alpha_max_nodes", 60))
    if fam == "ml":
        m = strategy_d.get("meta", {}) or {}
        h = hierarchy(bars, m.get("features"), cfg)
        lv = h.get("levels", {})
        b = lv.get("B", {})
        return {"pass": h["pass"], "score": h["score"],
                "metrics": {"ic": b.get("ic", 0.0), "spread": lv.get("C", {}).get("spread", 0.0),
                            "inter_ic": lv.get("D", {}).get("ic", 0.0),
                            "probe_ic": lv.get("E", {}).get("ic", 0.0),
                            "stab": b.get("stab", 0.0),
                            "nobs": lv.get("A", {}).get("nobs", 0)}}
    st = _symbolic_stats(strategy_d.get("entry", {}), bars)
    nodes = expr_nodes(strategy_d.get("entry", {}))
    cx = 0.0 if nodes <= max_nodes else (nodes - max_nodes) / max_nodes
    score = st["stab_sym"] + st["stab_time"] - st["turnover"] * 2 - cx
    ok = (st["nobs"] >= min_obs and 0.005 <= st["freq"] <= 0.4
          and st["turnover"] <= float(cfg.get("alpha_max_turnover", 0.5))
          and nodes <= max_nodes * 2)
    return {"pass": ok, "score": round(score, 3),
            "metrics": {"freq": round(st["freq"], 4), "turnover": round(st["turnover"], 3),
                        "stab_sym": round(st["stab_sym"], 3), "nobs": st["nobs"],
                        "nodes": nodes}}
