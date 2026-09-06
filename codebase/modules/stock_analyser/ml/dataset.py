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


def symbol_frame(bars: List[Dict], fwd: int = 5, warmup: int = 65) -> List[Dict]:
    """One symbol -> feature rows. Drops warmup head and label-unknown tail."""
    cols = columns_from_bars(bars)
    series = {name: evaluate(expr, cols) for name, expr in FEATURES.items()}
    closes = cols["close"]
    out = []
    for i in range(warmup, len(bars) - fwd):
        row = {"ts": bars[i]["ts"]}
        ok = True
        for name, s in series.items():
            v = s[i]
            if v is None or not isinstance(v, (int, float)):
                ok = False
                break
            row[name] = float(v)
        c0, c1 = closes[i], closes[i + fwd]
        if not ok or c0 is None or c1 is None or c0 == 0:
            continue
        row["fwd_ret"] = float(c1 - c0) / float(c0)
        out.append(row)
    return out


def build_panel(symbols: List[str], db_path: str | None = None, timeframe: str = "1D",
                fwd: int = 5, warmup: int = 30):
    """(symbol, date) panel as pandas DataFrame. Empty when no data."""
    import pandas as pd
    rows = []
    for s in symbols:
        bars = query_equity(f"NSE:{s}", timeframe, db_path=db_path)
        for r in symbol_frame(bars, fwd, warmup):
            rows.append({"symbol": s, **r})
    cols = ["symbol", "ts", *FEATURES, "fwd_ret"]
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
