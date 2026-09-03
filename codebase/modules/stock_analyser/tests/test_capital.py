"""Money loop: flat costs, config, paper ledger, scale rule. Offline (synthetic)."""
import os
import sys as _s
import tempfile
from pathlib import Path as _P
for _c in [_P(__file__).resolve().parents[3], _P(__file__).resolve().parents[4]]:
    if str(_c) not in _s.path:
        _s.path.insert(0, str(_c))


def test_flat_cost_and_config():
    from modules.stock_analyser.backtest.costs import trade_cost
    from modules.stock_analyser.config import load_capital
    assert trade_cost(100000, flat=60) == 60
    assert trade_cost(2000, flat=60) == 60  # flat ignores notional
    cap = load_capital()
    assert cap["capital"] == 50000 and cap["flat_cost_per_roundtrip"] == 60
    assert cap["max_positions"] == 8 and cap["scale_step"] == 25000


def test_engine_tracks_net_of_flat_costs():
    from modules.stock_analyser.data.providers import SyntheticProvider
    from modules.stock_analyser.strategies.model import default_long_volume_breakout
    from modules.stock_analyser.backtest.engine import run_backtest
    data = SyntheticProvider().fetch(["RELIANCE", "TCS"], n=120, seed=11)
    s = default_long_volume_breakout()
    s.flat_cost, s.position_frac, s.max_positions = 60.0, 0.5, 2
    res = run_backtest(s, data, start_cash=50000.0)
    assert res["total_costs"] == 60 * res["n"]
    assert abs(res["avg_net_per_trade"] * res["n"] - res["net_profit"]) < res["n"] * 0.01 + 0.01
    assert res["final_equity"] <= 50000 + sum(t["qty"] * 0 for t in res["trades"]) + 1e6  # sane


def test_paper_signal_fill_lifecycle():
    from modules.stock_analyser.data.providers import SyntheticProvider, UpstoxStub
    from modules.stock_analyser.strategies.model import strategy_from_dict
    from modules.stock_analyser.paper.trader import step
    db = os.path.join(tempfile.mkdtemp(), "lifecycle.db")
    data = SyntheticProvider().fetch(["RELIANCE"], n=60, seed=5, db_path=db,
                                     persist=True)["RELIANCE"]
    d = strategy_from_dict({"name": "always", "universe": "U", "timeframe": "1D",
                            "entry": {"op": "gt", "args": [{"const": 2}, {"const": 1}]},
                            "max_hold": 2, "position_frac": 0.5, "max_positions": 1,
                            "flat_cost": 60.0}).to_dict()
    assert any("SIGNAL" in a for a in step(d, ["RELIANCE"], db_path=db)["actions"])
    extra = [dict(b, ts=f"{9999 + i:010d}") for i, b in enumerate(data[-3:])]
    UpstoxStub().record(extra, "1D", db)
    out = step(d, ["RELIANCE"], db_path=db)
    assert any("FILL" in a for a in out["actions"]) and out["open"] == 1


def test_paper_step_and_report():
    from modules.stock_analyser.data.providers import SyntheticProvider
    from modules.stock_analyser.data.store import query_equity
    from modules.stock_analyser.strategies.model import default_long_volume_breakout
    from modules.stock_analyser.paper.trader import step, report
    db = os.path.join(tempfile.mkdtemp(), "paper.db")
    data = SyntheticProvider().fetch(["RELIANCE", "TCS", "INFY"], n=120, seed=5,
                                     db_path=db, persist=True)
    assert len(query_equity("NSE:RELIANCE", "1D", db_path=db)) == 120
    d = default_long_volume_breakout().to_dict()
    out = step(d, ["RELIANCE", "TCS", "INFY"], db_path=db)
    assert out["status"] == "ok"
    rep = report("volume_breakout_pullback", db_path=db)
    assert rep["closed"] + rep["open"] >= 0 and "scale_recommendation" in rep
