"""Universe import + resumable research ledger. Offline (synthetic/temp db)."""
import os
import sys as _s
import tempfile
from pathlib import Path as _P
for _c in [_P(__file__).resolve().parents[3], _P(__file__).resolve().parents[4]]:
    if str(_c) not in _s.path:
        _s.path.insert(0, str(_c))


def test_import_universe_and_resolve():
    from modules.stock_analyser.data.universe import import_universe, resolve_universe
    db = os.path.join(tempfile.mkdtemp(), "uni.db")
    out = import_universe(["reliance", "TCS", "reliance", " infused "], "MY_TEST_UNI", db)
    assert out == {"universe": "MY_TEST_UNI", "count": 3}
    assert resolve_universe("MY_TEST_UNI", db) == ["INFUSED", "RELIANCE", "TCS"]


def test_ledger_resume_and_dedup():
    from modules.stock_analyser.research.job import run_job, run_status, tested_hashes
    from modules.stock_analyser.strategies.model import default_long_volume_breakout
    db = os.path.join(tempfile.mkdtemp(), "led.db")
    base = default_long_volume_breakout().to_dict()
    syms = ["RELIANCE", "TCS"]
    r1 = run_job("t", base, syms, budget=3, seed=1, dataset="synthetic", db_path=db)
    assert r1["tested_this_session"] == 3 and r1["status"] == "COMPLETE"
    assert len(tested_hashes(r1["run_id"], db)) == 3
    r2 = run_job("t", base, syms, budget=6, seed=1, dataset="synthetic",
                 db_path=db, run_id=r1["run_id"])
    assert 1 <= r2["tested_this_session"] <= 3  # skips tested; rng collisions dedup too
    total = 3 + r2["tested_this_session"]
    assert run_status(r1["run_id"], db)["tested"] == total
    assert len(tested_hashes(r1["run_id"], db)) == total
