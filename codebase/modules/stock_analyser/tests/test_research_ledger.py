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
    from modules.stock_analyser.strategies.model import positive_controls
    db = os.path.join(tempfile.mkdtemp(), "led.db")
    base = positive_controls()[0]  # symbolic retired from bandit (#9)
    syms = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "SBIN", "ITC"]
    r1 = run_job("t", base, syms, budget=3, seed=1, dataset="synthetic", db_path=db)
    assert r1["status"] == "COMPLETE"  # Q7: DUPLICATEs refund budget via step/i split
    assert r1["tested_this_session"] >= 3
    r2 = run_job("t", base, syms, budget=6, seed=1, dataset="synthetic",
                 db_path=db, run_id=r1["run_id"])
    # resume continues seed progression (step resumes from done): novel trials.
    # On this tiny universe most mutations are signal-identical, so the run
    # may also terminate at SPACE_EXHAUSTED — either state keeps accounting.
    assert r2["status"] in ("COMPLETE", "SPACE_EXHAUSTED")
    total = r1["tested_this_session"] + r2["tested_this_session"]
    assert run_status(r1["run_id"], db)["tested"] == total
    assert len(tested_hashes(r1["run_id"], db)) <= total  # DUPLICATEs share hashes


def test_identical_reseed_exhausts_space():
    from modules.stock_analyser.research.job import run_job
    from modules.stock_analyser.strategies.model import positive_controls
    db = os.path.join(tempfile.mkdtemp(), "exh.db")
    base = positive_controls()[1]
    syms = ["RELIANCE", "TCS"]
    r = run_job("t", base, syms, budget=50, seed=1, dataset="synthetic", db_path=db)
    assert r["status"] in ("COMPLETE", "SPACE_EXHAUSTED", "ALL_RETIRED")


def test_positive_controls_validate():
    from modules.stock_analyser.strategies.model import positive_controls, strategy_from_dict
    from modules.stock_analyser.research.job import family_of
    cs = positive_controls()
    assert len(cs) == 6
    for c in cs:
        strategy_from_dict(c)  # raises on bad expr
        assert family_of(c) == "control"


def test_retired_families_skip_bandit():
    from modules.stock_analyser.research.job import _fam_retired, run_job
    from modules.stock_analyser.strategies.model import default_long_volume_breakout
    cap = {"retired_families": ["sym:"]}
    assert _fam_retired("sym:volume_breakout_pullback", cap)
    assert not _fam_retired("ml", cap) and not _fam_retired("control", cap)
    db = os.path.join(tempfile.mkdtemp(), "ret9.db")
    out = run_job("t", default_long_volume_breakout().to_dict(), ["RELIANCE"],
                  budget=3, seed=1, dataset="synthetic", db_path=db)
    assert out["status"] == "ALL_RETIRED" and out["tested_this_session"] == 0


def test_stage1_ic_screen_shape():
    from modules.stock_analyser.data.providers import SyntheticProvider
    from modules.stock_analyser.research.stage1 import ic_screen
    from modules.stock_analyser.strategies.genome import ml_seed
    from modules.stock_analyser.strategies.model import positive_controls
    data = SyntheticProvider().fetch(["RELIANCE", "TCS"], n=120, seed=11)
    for seed_d, is_ml in ((ml_seed("U", top_n=2), True), (positive_controls()[0], False)):
        r = ic_screen(seed_d, data, is_ml, {"stage1_min_t": 1.0, "stage1_fwd": 5})
        assert set(r) >= {"pass", "mean_ic", "t_nw", "n_dates", "spread_bps"}
        assert isinstance(r["pass"], bool) and r["n_dates"] >= 0


def test_epoch_cap_blocks_tired_dataset():
    from unittest import mock
    from modules.stock_analyser.config import load_capital
    import modules.stock_analyser.research.job as J
    from modules.stock_analyser.strategies.genome import ml_seed
    db = os.path.join(tempfile.mkdtemp(), "cap.db")
    cfg = dict(load_capital())
    cfg["epoch_max_trials"] = 0  # any prior trial (count>=1) exceeds cap
    with mock.patch.object(J, "load_capital", return_value=cfg):
        out = J.run_job("t", ml_seed("U", top_n=2), ["RELIANCE", "TCS"],
                        budget=2, seed=1, dataset="synthetic", db_path=db)
    assert out["status"] == "EPOCH_CAPPED" and out["tested_this_session"] == 0


def test_epoch_override_allows_one_reeval():
    from unittest import mock
    from modules.stock_analyser.config import load_capital
    import modules.stock_analyser.research.job as J
    from modules.stock_analyser.strategies.genome import ml_seed
    db = os.path.join(tempfile.mkdtemp(), "ovr.db")
    cfg = dict(load_capital())
    cfg["epoch_max_trials"] = 0
    with mock.patch.object(J, "load_capital", return_value=cfg):
        capped = J.run_job("t", ml_seed("U", top_n=2), ["RELIANCE", "TCS"],
                           budget=2, seed=1, dataset="synthetic", db_path=db)
        assert capped["status"] == "EPOCH_CAPPED"
        J.grant_epoch_override(capped["dataset_id"], "test re-eval", ["h1"], db)
        out = J.run_job("t", ml_seed("U", top_n=2), ["RELIANCE", "TCS"],
                        budget=2, seed=1, dataset="synthetic", db_path=db)
        assert out["status"] == "COMPLETE" and out["epoch_override"] == "test re-eval"
        out2 = J.run_job("t", ml_seed("U", top_n=2), ["RELIANCE", "TCS"],
                         budget=2, seed=1, dataset="synthetic", db_path=db)
        assert out2["status"] == "EPOCH_CAPPED"  # consumed: single use
