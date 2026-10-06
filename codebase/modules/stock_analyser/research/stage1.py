"""Stage-1 discovery screen (PlanFixes3 #1/#10): signal-level rank-IC on the
full cross-section with no exits and no costs. The portfolio sim (stage 2:
quick_screen + full validation) runs only on survivors; falsification
(stage 3) only on passers. Kill rule: Newey-West t below stage1_min_t
(default 1.0) never reaches the sim. Pre-lock window only (first 80%
shared dates, mirroring the alpha gate) so OOS stays sealed."""
from __future__ import annotations
from typing import Any, Dict, List


def _ranks(xs: List[float]) -> List[float]:
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    rk = [0.0] * len(xs)
    for pos, i in enumerate(order):
        rk[i] = float(pos)
    return rk


def _spearman(a: List[float], b: List[float]) -> float:
    n = len(a)
    if n < 3:
        return 0.0
    ra, rb = _ranks(a), _ranks(b)
    ma, mb = sum(ra) / n, sum(rb) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb)) / n
    sa = (sum((x - ma) ** 2 for x in ra) / n) ** 0.5
    sb = (sum((y - mb) ** 2 for y in rb) / n) ** 0.5
    return cov / (sa * sb) if sa and sb else 0.0


def _nw_t(xs: List[float], lag: int = 5) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    m = sum(xs) / n
    e = [x - m for x in xs]
    v = sum(v * v for v in e) / n
    for L in range(1, lag + 1):
        w = 1 - L / (lag + 1)
        v += 2 * w * sum(e[t] * e[t - L] for t in range(L, n)) / n
    return m / ((v / n) ** 0.5) if v > 0 else 0.0


def _fwd_map(bars: Dict[str, List[Dict]], fwd: int = 5) -> Dict[str, Dict[str, float]]:
    """Raw forward returns per (symbol, ts) from closes (no costs/exits)."""
    out: Dict[str, Dict[str, float]] = {}
    for s, bl in bars.items():
        closes = [b.get("close") or 0 for b in bl]
        m = {}
        for i, b in enumerate(bl):
            c0 = closes[i]
            c1 = closes[i + fwd] if i + fwd < len(closes) else 0
            if c0 and c1:
                m[b["ts"]] = c1 / c0 - 1
        out[s] = m
    return out


def ic_screen(strategy_d: Dict[str, Any], bars: Dict[str, List[Dict]],
              is_ml: bool, cfg: Dict[str, Any] | None = None) -> Dict[str, Any]:
    cfg = cfg or {}
    fwd = int(cfg.get("stage1_fwd", 5) or 5)
    min_t = float(cfg.get("stage1_min_t", 1.0))
    try:
        from ..backtest.validation import _split as _prelock
        pre = _prelock(bars, 0.8)[0] or bars
    except Exception:
        pre = bars
    dates = sorted({b["ts"] for bl in pre.values() for b in bl})
    if len(dates) < 40:
        return {"pass": False, "reason": "THIN", "mean_ic": 0.0,
                "t_nw": 0.0, "n_dates": 0, "spread_bps": 0.0}
    cut = dates[int(len(dates) * 0.55)]
    fwdm = _fwd_map(pre, fwd)
    pairs: Dict[str, List] = {}
    if is_ml:
        try:
            import pandas as pd
            from ..ml.strategies import _panel_rows
            from ..ml.ranker import train_ranker, add_scores
            m = strategy_d.get("meta", {}) or {}
            df = pd.DataFrame(_panel_rows(pre))
            if df.empty:
                return {"pass": False, "reason": "NOPANEL", "mean_ic": 0.0,
                        "t_nw": 0.0, "n_dates": 0, "spread_bps": 0.0}
            past = df[df["ts"] <= cut]
            if len(past) < 50:
                return {"pass": False, "reason": "LOW_N", "mean_ic": 0.0,
                        "t_nw": 0.0, "n_dates": 0, "spread_bps": 0.0}
            model = train_ranker(past, top_n=m.get("top_n", 5),
                                 model=m.get("model", "hgb"),
                                 feats=m.get("features"),
                                 max_depth=m.get("max_depth", 3))
            scored = add_scores(model, df[(df["ts"] > cut)])
            for ts, grp in scored.groupby("ts"):
                v = [(float(r["score"]), fwdm.get(str(r["symbol"]), {}).get(str(ts)))
                     for _, r in grp.iterrows()]
                v = [(a, b) for a, b in v if b is not None]
                if len(v) >= 10:
                    pairs[str(ts)] = v
        except Exception:
            return {"pass": False, "reason": "MLERR", "mean_ic": 0.0,
                    "t_nw": 0.0, "n_dates": 0, "spread_bps": 0.0}
    else:
        try:
            from ..backtest.engine import _signals
            from ..strategies.model import strategy_from_dict
            strat = strategy_from_dict(strategy_d)
            for s, bl in pre.items():
                try:
                    sigs = _signals(strat, bl)
                except Exception:
                    continue
                for b, sig in zip(bl, sigs):
                    if b["ts"] <= cut:
                        continue
                    f = fwdm.get(s, {}).get(b["ts"])
                    if f is None:
                        continue
                    pairs.setdefault(b["ts"], []).append((1.0 if sig else 0.0, f))
            pairs = {t: v for t, v in pairs.items() if len(v) >= 10}
        except Exception:
            return {"pass": False, "reason": "SYMERR", "mean_ic": 0.0,
                    "t_nw": 0.0, "n_dates": 0, "spread_bps": 0.0}
    ics, sps = [], []
    for v in pairs.values():
        ics.append(_spearman([a for a, _ in v], [b for _, b in v]))
        srt = sorted(v, key=lambda z: -z[0])
        k = max(2, len(srt) // 10)
        sps.append(sum(b for _, b in srt[:k]) / k - sum(b for _, b in srt[-k:]) / k)
    if not ics:
        return {"pass": False, "reason": "THIN", "mean_ic": 0.0,
                "t_nw": 0.0, "n_dates": 0, "spread_bps": 0.0}
    mic = sum(ics) / len(ics)
    t = _nw_t(ics, fwd)
    msp = sum(sps) / len(sps)
    return {"pass": bool(t >= min_t), "mean_ic": round(mic, 4), "t_nw": round(t, 2),
            "n_dates": len(ics), "spread_bps": round(msp * 10000, 1)}
