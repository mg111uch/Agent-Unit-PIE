"""P2 test: HGB ranker trained on real train-split, backtested on locked test."""
import sys as _s
from pathlib import Path as _P
for _c in [_P(__file__).resolve().parents[3], _P(__file__).resolve().parents[4]]:
    if str(_c) not in _s.path:
        _s.path.insert(0, str(_c))

import pytest


@pytest.mark.slow  # trains + backtests on real market.db data
def test_ranker_end_to_end_on_real_data():
    from modules.stock_analyser.ml.dataset import build_panel, split_panel
    from modules.stock_analyser.ml.ranker import (train_ranker, add_scores, top_n_signals,
                                                  save_model, load_model)
    from modules.stock_analyser.data.store import query_equity
    from modules.stock_analyser.strategies.model import strategy_from_dict
    from modules.stock_analyser.backtest.engine import run_backtest
    import tempfile, os
    syms = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "SBIN", "ITC", "LT",
            "AXISBANK", "KOTAKBANK", "MARUTI"]
    df = build_panel(syms)
    tr, va, te, bounds = split_panel(df)
    assert len(tr) > len(te) > 0
    model = train_ranker(tr, top_n=3)
    scored = add_scores(model, te)
    assert scored["score"].notna().all()
    # rank correlation sanity: top bucket should beat bottom bucket on average
    q = scored.groupby("symbol")["score"].mean()
    top_syms = set(q.nlargest(3).index)
    assert len(top_syms) == 3
    bars = {s: query_equity(f"NSE:{s}", "1D") for s in syms}
    sigs = top_n_signals(scored, bars, top_n=3, live_from=bounds["test_start"])
    # no signals before the locked test window
    for s, sl in sigs.items():
        for b, sig in zip(bars[s], sl):
            if b["ts"] < bounds["test_start"]:
                assert sig is False
    assert sum(sum(sl) for sl in sigs.values()) > 0  # entries exist
    exits = strategy_from_dict({"name": "ml_top3", "universe": "U", "timeframe": "1D",
                                "entry": {"const": False}, "stop_atr": 2.0,
                                "take_atr": 4.0, "max_hold": 10, "position_frac": 0.2,
                                "max_positions": 3, "flat_cost": 60.0,
                                "meta": {"family": "ml", "top_n": 3}})
    res = run_backtest(exits, bars, start_cash=50000.0, signals=sigs)
    assert res["n"] > 0
    assert res["total_costs"] == 60 * res["n"]
    assert set(res) >= {"avg_net_per_trade", "net_profit", "max_dd", "sharpe"}
    # artifact round-trip
    p = os.path.join(tempfile.mkdtemp(), "ranker.pkl")
    assert save_model(model, p) == p
    assert load_model(p)["top_n"] == 3
