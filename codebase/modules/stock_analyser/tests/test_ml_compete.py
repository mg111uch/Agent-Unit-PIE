"""P3: ML competes — genome, screen, validation, retirement, dispatch."""
import os
import sys as _s
import tempfile
import pytest
from pathlib import Path as _P
for _c in [_P(__file__).resolve().parents[3], _P(__file__).resolve().parents[4]]:
    if str(_c) not in _s.path:
        _s.path.insert(0, str(_c))

SYMS = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "SBIN"]


def _ml_base():
    from modules.stock_analyser.strategies.genome import ml_seed
    return ml_seed("U", top_n=3)


@pytest.mark.slow  # real-data csv bars + full ML validation
def test_screen_and_validate_ml_structure():
    from modules.stock_analyser.connector import StockConnector
    from modules.stock_analyser.ml.strategies import quick_screen, validate_ml
    c = StockConnector()
    bars = c._bars({"dataset": "csv", "symbols": SYMS, "n": 252, "timeframe": "1D"})
    scr = quick_screen(_ml_base(), bars, 50000.0)
    assert set(scr) >= {"pass", "n", "avg_net"} and scr["n"] >= 0
    v = validate_ml(_ml_base(), bars, 50000.0)
    assert v["verdict"] in ("PAPER_READY", "REJECT")
    assert set(v) >= {"backtest", "perturbation", "cost_stress", "locked_oos", "robustness"}
    assert isinstance(v["robustness"], float)


def test_retirement_kills_dead_family():
    import sqlite3
    from modules.stock_analyser.research.job import run_job, family_rejects, start_run
    from modules.stock_analyser.strategies.model import default_long_volume_breakout
    db = os.path.join(tempfile.mkdtemp(), "ret.db")
    rid = start_run("t", "U", "day", 5, db)
    con = sqlite3.connect(db)
    for i in range(25):
        con.execute("INSERT INTO research_candidates(run_id,strategy_hash,strategy_json,"
                    "verdict,family,created_at) VALUES(?,?,?,?,?,?)",
                    (rid, f"h{i}", "{}", "REJECT", "sym:dead", "t"))
    con.commit()
    con.close()
    assert family_rejects(rid, "sym:dead", db) >= 25
    dead = default_long_volume_breakout().to_dict()
    dead["name"] = "dead"
    out = run_job("t", None, ["RELIANCE", "TCS"], budget=4, seed=1,
                  dataset="synthetic", db_path=db, run_id=rid, seeds=[dead])
    assert out["status"] == "ALL_RETIRED" and out["tested_this_session"] == 0


def test_connector_ml_dispatch():
    from modules.stock_analyser.connector import StockConnector
    c = StockConnector()
    out = run_job_ml_dispatch_check(c)
    assert out is True


def run_job_ml_dispatch_check(c):
    import json
    params = {"strategy": _ml_base(), "dataset": "synthetic",
              "symbols": ["RELIANCE", "TCS"], "n": 120, "seed": 7}
    res = json.loads(c.run_and_extract(params, "run_basic"))
    return "metrics" in res and res["metrics"].get("n", 0) >= 0
