"""ML panel dataset on existing algebra primitives. Leakage discipline first.

Features are trailing-only by construction (evaluator windows end at bar i);
labels are forward returns with embargoed splits: no training row may see a
label overlapping validation/test dates.
"""
from __future__ import annotations
from typing import Dict, List, Tuple
from ..features.algebra import evaluate, columns_from_bars
from ..data.store import query_equity


def _ratio(a, b):
    return {"op": "ratio", "args": [a, b]}


def _sub1(x):
    return {"op": "sub", "args": [x, {"const": 1.0}]}


def _lag(field: str, n: int):
    return {"op": "lag", "args": [{"field": field}, {"const": n}]}


FEATURES: Dict[str, dict] = {
    "ret_1": _sub1(_ratio({"field": "close"}, _lag("close", 1))),
    "ret_3": _sub1(_ratio({"field": "close"}, _lag("close", 3))),
    "ret_5": _sub1(_ratio({"field": "close"}, _lag("close", 5))),
    "ret_10": _sub1(_ratio({"field": "close"}, _lag("close", 10))),
    "ret_20": _sub1(_ratio({"field": "close"}, _lag("close", 20))),
    "ret_60": _sub1(_ratio({"field": "close"}, _lag("close", 60))),
    "vol_ratio": _ratio({"field": "volume"},
                        {"op": "rolling_mean", "args": [{"field": "volume"}, {"const": 20}]}),
    "vol_ratio_5": _ratio({"field": "volume"},
                          {"op": "rolling_mean", "args": [{"field": "volume"}, {"const": 5}]}),
    "zret_20": {"op": "zscore", "args": [{"field": "returns"}, {"const": 20}]},
    "vol_20": {"op": "rolling_std", "args": [{"field": "returns"}, {"const": 20}]},
    "trend_20": _sub1(_ratio({"field": "close"},
                             {"op": "rolling_mean", "args": [{"field": "close"}, {"const": 20}]})),
    "range_20": {"op": "div", "args": [
        {"op": "sub", "args": [
            {"op": "rolling_max", "args": [{"field": "high"}, {"const": 20}]},
            {"op": "rolling_min", "args": [{"field": "low"}, {"const": 20}]}]},
        {"field": "close"}]},
    "range_pos": {"op": "div", "args": [
        {"op": "sub", "args": [{"field": "close"},
                               {"op": "rolling_min", "args": [{"field": "low"}, {"const": 20}]}]},
        {"op": "sub", "args": [
            {"op": "rolling_max", "args": [{"field": "high"}, {"const": 20}]},
            {"op": "rolling_min", "args": [{"field": "low"}, {"const": 20}]}]}]},
    "pos_60": {"op": "div", "args": [
        {"op": "sub", "args": [{"field": "close"},
                               {"op": "rolling_min", "args": [{"field": "low"}, {"const": 60}]}]},
        {"op": "sub", "args": [
            {"op": "rolling_max", "args": [{"field": "high"}, {"const": 60}]},
            {"op": "rolling_min", "args": [{"field": "low"}, {"const": 60}]}]}]},
    "dist_high": _sub1(_ratio({"field": "close"},
                              {"op": "rolling_max", "args": [{"field": "high"}, {"const": 20}]})),
    # Phase 1 (FixesIssues #6): data before model — vol-normalized momentum,
    # drawdown distance, short-vs-long reversal, range-per-unit-vol.
    "mom_vol_20": {"op": "div", "args": [
        _sub1(_ratio({"field": "close"}, _lag("close", 20))),
        {"op": "rolling_std", "args": [{"field": "returns"}, {"const": 20}]}]},
    "dd_high_60": _sub1(_ratio({"field": "close"},
                               {"op": "rolling_max", "args": [{"field": "high"}, {"const": 60}]})),
    "rev_5_20": {"op": "sub", "args": [
        _sub1(_ratio({"field": "close"}, _lag("close", 5))),
        _sub1(_ratio({"field": "close"}, _lag("close", 20)))]},
    "range_vol": {"op": "div", "args": [
        {"op": "div", "args": [
            {"op": "sub", "args": [
                {"op": "rolling_max", "args": [{"field": "high"}, {"const": 20}]},
                {"op": "rolling_min", "args": [{"field": "low"}, {"const": 20}]}]},
            {"field": "close"}]},
        {"op": "rolling_std", "args": [{"field": "returns"}, {"const": 20}]}]},
}

# Sector/market-relative (cross-sectional, trailing-only; computed in
# symbol_frame from bench_map, NOT algebra — needs index bars).
REL_FEATURES = ("rel_mkt_5", "rel_mkt_20", "rel_sec_20", "sec_disp_20")
ALL_FEATURES = (*FEATURES, *REL_FEATURES)


def _xs_normalize(rows, with_target: bool = True, target_mode: str = "demean"):
    """Cross-sectional disciplinarian: target framing per date + z-score
    features per date. `target_mode`: raw (no target transform), demean
    (default, current behavior), demean+winsor (1/99 tame fat tails),
    rank-gauss (rank -> inverse-normal; robust to earnings jumps).
    Needs a real cross-section: groups < 3 symbols pass through untouched
    (unit tests, single-name probes). Applied identically to labeled and
    serving frames (serving uses with_target=False: features only)."""
    if not rows:
        return rows
    by_ts: dict = {}
    for r in rows:
        by_ts.setdefault(r["ts"], []).append(r)
    feat_keys = [k for k in rows[0] if k not in ("ts", "symbol", "fwd_ret")]
    for grp in by_ts.values():
        if len(grp) < 3:
            continue
        if with_target:
            if target_mode == "rank-gauss":
                from statistics import NormalDist
                order = sorted(range(len(grp)), key=lambda j: grp[j]["fwd_ret"])
                for pos, j in enumerate(order):
                    p = (pos + 0.75) / (len(grp) + 0.5)
                    grp[j]["fwd_ret"] = NormalDist().inv_cdf(
                        min(0.9999, max(0.0001, p)))
            else:
                m = sum(r["fwd_ret"] for r in grp) / len(grp)
                vals = [r["fwd_ret"] - m for r in grp]
                if target_mode == "demean+winsor":
                    s = sorted(vals)
                    lo, hi = s[max(0, int(0.01 * len(s)))], s[min(len(s) - 1, int(0.99 * len(s)))]
                    vals = [min(hi, max(lo, v)) for v in vals]
                for r, v in zip(grp, vals):
                    r["fwd_ret"] = v
        n = float(len(grp))
        for f in feat_keys:
            mu = sum(r[f] for r in grp) / n
            sd = (sum((r[f] - mu) ** 2 for r in grp) / n) ** 0.5
            if not sd:
                continue
            for r in grp:
                r[f] = (r[f] - mu) / sd
    return rows


def _ret(closes, i, n):
    c0, c1 = closes[i - n] if i - n >= 0 else None, closes[i]
    return None if not c0 or not c1 or c0 == 0 else (c1 - c0) / c0


def symbol_frame(bars: List[Dict], fwd: int = 5, warmup: int = 65,
                 bench: Dict | None = None, need_label: bool = True) -> List[Dict]:
    """One symbol -> feature rows. Drops warmup head and (if need_label)
    label-unknown tail. Serving (scoring) uses need_label=False: prediction
    needs trailing-only features, never future labels."""
    cols = columns_from_bars(bars)
    series = {name: evaluate(expr, cols) for name, expr in FEATURES.items()}
    closes = cols["close"]
    out = []
    end = len(bars) - fwd if need_label else len(bars)
    for i in range(warmup, end):
        row = {"ts": bars[i]["ts"]}
        ok = True
        for name, s in series.items():
            v = s[i]
            if v is None or not isinstance(v, (int, float)):
                ok = False
                break
            row[name] = float(v)
        if not ok:
            continue
        if need_label:
            c0, c1 = closes[i], closes[i + fwd]
            if c0 is None or c1 is None or c0 == 0:
                continue
            row["fwd_ret"] = float(c1 - c0) / float(c0)
        else:
            c0 = closes[i]
            row["fwd_ret"] = None
        b = (bench or {}).get(bars[i]["ts"]) or {}
        r5, r20 = _ret(closes, i, 5), _ret(closes, i, 20)
        row["rel_mkt_5"] = float((r5 or 0.0) - b.get("mkt_5", 0.0))
        row["rel_mkt_20"] = float((r20 or 0.0) - b.get("mkt_20", 0.0))
        row["rel_sec_20"] = float((r20 or 0.0) - b.get("sec_20", 0.0))
        row["sec_disp_20"] = float(b.get("sec_disp_20", 0.0))
        out.append(row)
    return out


def build_panel(symbols: List[str], db_path: str | None = None, timeframe: str = "1D",
                fwd: int = 5, warmup: int = 30, include_relative: bool = True):
    """(symbol, date) panel as pandas DataFrame. Empty when no data."""
    import pandas as pd
    try:
        bench = None
        if include_relative:
            from .sectors import bench_map as _bm
            bench = _bm(db_path, timeframe) or None
    except Exception:
        bench = None
    rows = []
    for s in symbols:
        bars = query_equity(f"NSE:{s}", timeframe, db_path=db_path)
        for r in symbol_frame(bars, fwd, warmup, bench):
            rows.append({"symbol": s, **r})
    cols = ["symbol", "ts", *FEATURES, *REL_FEATURES, "fwd_ret"]
    return pd.DataFrame(rows, columns=cols) if rows else pd.DataFrame(columns=cols)


def purged_date_split(dates: List[str], train_frac: float = 0.6, val_frac: float = 0.2,
                      embargo: int = 5) -> Tuple[str, str, str, str]:
    """(train_end, val_start, val_end, test_start) with embargo gaps in days.

    Date strings are ISO-sortable; gaps measured in calendar days so a label
    computed over `fwd` future bars can never cross a boundary.
    """
    from datetime import datetime
    ds = sorted(set(dates))
    n = len(ds)
    te = ds[max(0, int(n * train_frac) - 1)]
    vs = _shift(ds, te, embargo)
    ve = ds[min(n - 1, int(n * (train_frac + val_frac)) - 1)]
    ts = _shift(ds, ve, embargo)
    if not (te < vs <= ve < ts):
        raise ValueError("not enough dates for embargoed split")
    return te, vs, ve, ts


def _shift(ds: List[str], anchor: str, days: int) -> str:
    from datetime import datetime, timedelta
    target = datetime.fromisoformat(anchor) + timedelta(days=days)
    for d in ds:
        if datetime.fromisoformat(d) >= target:
            return d
    return ds[-1]


def split_panel(df, train_frac: float = 0.6, val_frac: float = 0.2, embargo: int = 5):
    te, vs, ve, ts = purged_date_split(list(df["ts"]), train_frac, val_frac, embargo)
    return (df[df["ts"] <= te], df[(df["ts"] >= vs) & (df["ts"] <= ve)], df[df["ts"] >= ts],
            {"train_end": te, "val_start": vs, "val_end": ve, "test_start": ts})
