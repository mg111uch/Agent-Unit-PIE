"""P1 tests: panel integrity + causality (no future peek) + embargo splits."""
import sys as _s
from pathlib import Path as _P
for _c in [_P(__file__).resolve().parents[3], _P(__file__).resolve().parents[4]]:
    if str(_c) not in _s.path:
        _s.path.insert(0, str(_c))


def test_panel_shape_and_no_nans():
    from modules.stock_analyser.ml.dataset import build_panel, FEATURES
    df = build_panel(["RELIANCE", "TCS", "INFY"])
    assert len(df) > 500 and set(FEATURES) <= set(df.columns)
    assert df[[*FEATURES, "fwd_ret"]].notna().all().all()
    assert ((df["fwd_ret"] > -1.0) & (df["fwd_ret"] < 5.0)).all()


def test_features_are_causal():
    """Row i from full history == row i from history truncated at i (no peek)."""
    from modules.stock_analyser.ml.dataset import symbol_frame, FEATURES
    from modules.stock_analyser.data.store import query_equity
    bars = query_equity("NSE:RELIANCE", "1D")
    assert len(bars) > 100
    full = {r["ts"]: r for r in symbol_frame(bars)}
    cut = symbol_frame(bars[:80])
    for r in cut:
        f = full[r["ts"]]
        for k in FEATURES:
            assert abs(f[k] - r[k]) < 1e-9, (k, r["ts"])


def test_embargo_split_has_gaps():
    from datetime import datetime
    from modules.stock_analyser.ml.dataset import build_panel, split_panel
    df = build_panel(["RELIANCE", "TCS", "INFY", "HDFCBANK", "SBIN"])
    tr, va, te, bounds = split_panel(df)
    assert len(tr) > len(va) > 0 and len(te) > 0
    g1 = (datetime.fromisoformat(bounds["val_start"]) -
          datetime.fromisoformat(bounds["train_end"])).days
    g2 = (datetime.fromisoformat(bounds["test_start"]) -
          datetime.fromisoformat(bounds["val_end"])).days
    assert g1 >= 5 and g2 >= 5  # fwd-5 labels can't cross
    assert tr["ts"].max() < va["ts"].min() <= va["ts"].max() < te["ts"].min()
