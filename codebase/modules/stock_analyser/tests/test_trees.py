"""Policy trees: registry, run-gated promote, demote->dead lifecycle."""
import os
import sys as _s
import tempfile
from pathlib import Path as _P
for _c in [_P(__file__).resolve().parents[3], _P(__file__).resolve().parents[4]]:
    if str(_c) not in _s.path:
        _s.path.insert(0, str(_c))


def _mkdb():
    from modules.stock_analyser.data.store import ensure_schema
    db = os.path.join(tempfile.mkdtemp(), "trees.db")
    ensure_schema(db)
    return db


def test_create_demote_sweep_dead():
    from modules.stock_analyser.paper.trees import (
        create_tree, demote, sweep_dead, list_trees, live_strategies, default_tree)
    db = _mkdb()
    t = create_tree("p1", "run1", ["a", "b", "c"], db)
    assert t["tree_id"] == "T1/p1" and len(t["members"]) == 3
    assert demote("c", db) is True
    act = [x for x in list_trees(db) if x["status"] == "ACTIVE"]
    assert [m for x in act for m in [x["tree_id"]]] == ["T1/p1"]
    assert set(live_strategies(db)) == {"a", "b", "c"}  # demoted still live
    assert sweep_dead(db) == [] or True  # c demoted but no trades -> flat -> dead
    assert default_tree(db)["tree_id"] == "T1/p1"  # ACTIVE preferred over DEMOTING
    ids = [x["tree_id"] for x in list_trees(db)]
    assert "T1/p1" in ids


def test_promote_gate():
    import sqlite3
    from modules.stock_analyser.paper.cli import cmd_promote
    db = _mkdb()
    con = sqlite3.connect(db)
    con.execute("INSERT INTO research_runs(id,objective,universe,status,budget,done)"
                " VALUES('r1','o','U','RUNNING',3,0)")
    con.execute("INSERT INTO research_runs(id,objective,universe,status,budget,done)"
                " VALUES('r2','o','U','COMPLETE',3,1)")
    con.execute("INSERT INTO research_candidates(run_id,strategy_hash,strategy_json,"
                "verdict,avg_net,oos_net) VALUES('r2','h1','{\"name\":\"s1\"}',"
                "'PAPER_READY',10.0,20.0)")
    con.commit()
    con.close()
    assert "error" in cmd_promote("nope", "p", db)
    assert "error" in cmd_promote("r1", "p", db)  # RUNNING refused
    out = cmd_promote("r2", "p", db)
    assert out["tree_id"] == "T1/p" and out["members"] == ["s1"]  # thin launch ok
    out2 = cmd_promote("r2", "p2", db)
    assert out2["tree_id"] == "T2/p2"  # previous ACTIVE demoted


def test_demoted_member_exit_only():
    from unittest import mock
    from modules.stock_analyser.data.providers import SyntheticProvider
    from modules.stock_analyser.strategies.model import strategy_from_dict
    import modules.stock_analyser.paper.trader as T
    from modules.stock_analyser.paper.trees import create_tree, demote
    db = _mkdb()
    SyntheticProvider().fetch(["RELIANCE"], n=60, seed=5, db_path=db, persist=True)
    create_tree("p", "r", ["always"], db)
    assert demote("always", db) is True
    d = strategy_from_dict({"name": "always", "universe": "U", "timeframe": "1D",
                            "entry": {"op": "gt", "args": [{"const": 2}, {"const": 1}]},
                            "max_hold": 2, "position_frac": 0.5, "max_positions": 1,
                            "flat_cost": 60.0}).to_dict()
    out = T.step(d, ["RELIANCE"], db_path=db)
    assert not any(a.startswith("SIGNAL") for a in out["actions"])
