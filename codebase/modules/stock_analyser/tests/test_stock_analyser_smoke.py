"""Smoke: synthetic -> feature eval -> backtest next-bar fill -> mutate -> finding."""
import sys as _s
from pathlib import Path as _P
for _c in [_P(__file__).resolve().parents[3], _P(__file__).resolve().parents[4]]:
    if str(_c) not in _s.path:
        _s.path.insert(0, str(_c))
import tempfile, os


def test_smoke():
    tmp = tempfile.mkdtemp()
    db = os.path.join(tmp, "kernel.db")
    from modules.stock_analyser.data.store import ensure_schema
    from modules.stock_analyser.data.providers import SyntheticProvider
    from modules.stock_analyser.features.algebra import evaluate, columns_from_bars
    from modules.stock_analyser.strategies.model import default_long_volume_breakout
    from modules.stock_analyser.strategies.genome import mutate
    from modules.stock_analyser.backtest.engine import run_backtest
    from modules.stock_analyser.connector import StockConnector
    from modules.stock_analyser.paper import propose_paper, execute_live

    ensure_schema(db)
    syms = ["RELIANCE", "TCS", "INFY"]
    data = SyntheticProvider().fetch(syms, n=120, seed=7, db_path=db, persist=True)
    assert all(len(data[s]) == 120 for s in syms)
    cols = columns_from_bars(data["RELIANCE"])
    expr = {"op": "rolling_mean", "args": [{"field": "close"}, {"const": 20}]}
    feat = evaluate(expr, cols)
    assert feat[19] is not None and feat[5] is None  # warmup
    strat = default_long_volume_breakout("MY_RESEARCH_UNIVERSE")
    res = run_backtest(strat, data)
    assert res["n"] >= 0 and "sharpe" in res and len(res["equity_curve"]) > 0
    m2 = mutate(strat, seed=1)
    assert m2.name != strat.name
    # connector contract: run_basic + policy ids
    conn = StockConnector(db_path=db)
    params = {"strategy": strat.to_dict(), "dataset": "synthetic",
              "symbols": syms, "n": 120, "timeframe": "1D", "seed": 7}
    out = conn.run_and_extract(params, "run_basic")
    assert "run_basic" in out
    reg = conn.register_to_kernel("run_basic", "smoke premise", None)
    assert reg.get("topic") == "sim_stock"
    # paper blocked without approval; live always raises
    assert propose_paper(strat.to_dict(), human_approved=False)["status"] == "BLOCKED"
    try:
        execute_live({})
        assert False, "live must raise"
    except NotImplementedError:
        pass
