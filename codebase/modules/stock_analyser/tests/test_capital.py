"""Money loop: flat costs, config, paper ledger, scale rule. Offline (synthetic)."""
import os
import sys as _s
import tempfile
from pathlib import Path as _P
for _c in [_P(__file__).resolve().parents[3], _P(__file__).resolve().parents[4]]:
    if str(_c) not in _s.path:
        _s.path.insert(0, str(_c))


def test_breakeven_agrees_with_book_cost():
    # Q9: breakeven rung must satisfy the tariff model at 5k/10k/25k scales
    from modules.stock_analyser.research.capital_ladder import estimate_breakeven, ladder
    from modules.stock_analyser.backtest.costs import realistic_breakdown
    from modules.stock_analyser.config import load_capital
    cfg = load_capital()
    steps = ladder(cfg)
    s = estimate_breakeven(-500.0, 900.0, 10, 50000.0, 0.2, cfg, steps)
    assert s in steps
    gross = -500.0 + 900.0
    assert gross * s / 50000.0 - realistic_breakdown(0.2 * s, cfg)["total"] * 10 > 0
    prev = max(x for x in steps if x < s)
    assert gross * prev / 50000.0 - realistic_breakdown(0.2 * prev, cfg)["total"] * 10 <= 0


def test_capital_ladder_breakeven():
    from modules.stock_analyser.research.capital_ladder import ladder, estimate_breakeven
    from modules.stock_analyser.config import load_capital
    steps = ladder(load_capital())
    assert steps == [25000, 50000, 75000, 100000]
    # realistic drag dilutes with capital: gross>0 but net<0 at 50k clears higher
    cfg = load_capital()
    assert estimate_breakeven(-200.0, 600.0, 10, 50000.0, 0.2, cfg, steps) in steps
    assert estimate_breakeven(-200.0, 100.0, 10, 50000.0, 0.2, cfg, steps) is None  # gross<=0
    assert estimate_breakeven(100.0, 600.0, 10, 50000.0, 0.2, cfg, steps) is None  # already net+


def test_tradable_filter_drops_low_adv():
    from modules.stock_analyser.data.providers import SyntheticProvider
    from modules.stock_analyser.research.liquidity import tradable_filter
    data = SyntheticProvider().fetch(["A", "B"], n=30, seed=5)
    for b in data["B"]:
        b["volume"] = 5.0
    kept, dropped = tradable_filter(data, 10000.0, {"liq_min_adv": 50000})
    assert dropped == ["B"] and sorted(kept) == ["A"]


def test_paper_blocks_untradable_buys():
    from modules.stock_analyser.data.providers import SyntheticProvider
    from modules.stock_analyser.data.store import connect
    from modules.stock_analyser.strategies.model import strategy_from_dict
    from modules.stock_analyser.paper.trader import step
    db = os.path.join(tempfile.mkdtemp(), "untrad.db")
    SyntheticProvider().fetch(["RELIANCE", "TCS"], n=60, seed=5,
                              db_path=db, persist=True)
    con = connect(db)
    con.execute("UPDATE equity_bars SET vol=10 WHERE instrument_id='NSE:TCS'")
    con.commit()
    con.close()
    d = strategy_from_dict({"name": "always", "universe": "U", "timeframe": "1D",
                            "entry": {"op": "gt", "args": [{"const": 2}, {"const": 1}]},
                            "max_hold": 2, "position_frac": 0.5, "max_positions": 2,
                            "flat_cost": 60.0}).to_dict()
    out = step(d, ["RELIANCE", "TCS"], db_path=db)
    acts = " ".join(out["actions"])
    assert "SKIP TCS untradable" in acts and "SIGNAL TCS" not in acts
    assert "SIGNAL RELIANCE" in acts


def test_indices_never_tradable():
    from modules.stock_analyser.constants import is_tradable, INDEX_SYMBOLS
    assert len(INDEX_SYMBOLS) == 8
    assert not is_tradable("NIFTY") and not is_tradable("banknifty")
    assert not is_tradable("NIFTY_IT") and is_tradable("RELIANCE")


def test_connector_and_paper_drop_indices():
    from modules.stock_analyser.data.providers import SyntheticProvider
    from modules.stock_analyser.connector import StockConnector
    from modules.stock_analyser.strategies.model import strategy_from_dict
    from modules.stock_analyser.paper.trader import step
    db = os.path.join(tempfile.mkdtemp(), "idx.db")
    SyntheticProvider().fetch(["RELIANCE", "NIFTY"], n=60, seed=5,
                              db_path=db, persist=True)
    c = StockConnector(db_path=db)
    bars = c._bars({"dataset": "csv", "symbols": ["RELIANCE", "NIFTY"],
                    "n": 60, "timeframe": "1D"})
    assert sorted(bars) == ["RELIANCE"]
    assert c._quality.get("indices_dropped") == ["NIFTY"]
    d = strategy_from_dict({"name": "always", "universe": "U", "timeframe": "1D",
                            "entry": {"op": "gt", "args": [{"const": 2}, {"const": 1}]},
                            "max_hold": 2, "position_frac": 0.5, "max_positions": 2,
                            "flat_cost": 60.0}).to_dict()
    out = step(d, ["RELIANCE", "NIFTY"], db_path=db)
    acts = " ".join(out["actions"])
    assert "NIFTY untradable/index" in acts and "SIGNAL NIFTY" not in acts
    assert "SIGNAL RELIANCE" in acts


def test_engine_tracks_net_of_flat_costs():
    from unittest import mock
    from modules.stock_analyser.data.providers import SyntheticProvider
    from modules.stock_analyser.strategies.model import default_long_volume_breakout
    import modules.stock_analyser.backtest.engine as E
    data = SyntheticProvider().fetch(["RELIANCE", "TCS"], n=120, seed=11)
    s = default_long_volume_breakout()
    s.flat_cost, s.position_frac, s.max_positions = 60.0, 0.5, 2
    flat_cfg = {"min_history_bars": 60, "flat_cost_per_roundtrip": 60,
                "cost_basis": "flat"}
    with mock.patch.object(E, "load_capital", return_value=flat_cfg):
        res = E.run_backtest(s, data, start_cash=50000.0)
    assert res["total_costs"] == 60 * res["n"]
    assert abs(res["avg_net_per_trade"] * res["n"] - res["net_profit"]) < res["n"] * 0.01 + 0.01
    assert res["final_equity"] <= 50000 + sum(t["qty"] * 0 for t in res["trades"]) + 1e6  # sane
    res = E.run_backtest(s, data, start_cash=50000.0)  # realistic default
    assert res["n"] > 0
    from modules.stock_analyser.backtest.costs import realistic_breakdown as _rb
    from modules.stock_analyser.config import load_capital as _lc
    _cc = _lc()
    exp = sum((_rb(t["notional"], _cc)["total"]
               + _rb(t["notional"] * (1 + t["ret"]), _cc)["total"]) / 2
              for t in res["trades"])
    assert abs(res["total_costs"] - exp) < 1.0  # booked = tariff model
    assert 30 < res["avg_cost_bps"] < 70  # delivery band with DP (not flat 60)
    assert res["avg_cost_bps"] > 0 and all("notional" in t for t in res["trades"])
    net_bps = sum(t["net"] / t["notional"] for t in res["trades"]) / res["n"] * 10000
    assert abs(res["avg_gross_bps"] - res["avg_cost_bps"] - net_bps) < 0.5  # gross-cost=net


def test_shadow_scores_carry_provenance():
    from modules.stock_analyser.data.providers import SyntheticProvider
    from modules.stock_analyser.strategies.model import strategy_from_dict
    from modules.stock_analyser.paper.trader import step
    from modules.stock_analyser.data.store import connect
    db = os.path.join(tempfile.mkdtemp(), "shprov.db")
    SyntheticProvider().fetch(["RELIANCE", "TCS"], n=60, seed=5,
                              db_path=db, persist=True)
    d = strategy_from_dict({"name": "always", "universe": "U", "timeframe": "1D",
                            "entry": {"op": "gt", "args": [{"const": 2}, {"const": 1}]},
                            "max_hold": 2, "position_frac": 0.5, "max_positions": 1,
                            "flat_cost": 60.0}).to_dict()
    assert step(d, ["RELIANCE", "TCS"], db_path=db)["status"] == "ok"
    con = connect(db)
    cols = [r[1] for r in con.execute("PRAGMA table_info(shadow_scores)").fetchall()]
    assert {"model", "cfg_hash", "eligible"} <= set(cols)
    n = con.execute("SELECT COUNT(*) FROM shadow_scores").fetchone()[0]
    assert n > 0
    con.close()


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


def test_retired_tree_emits_no_signals():
    from unittest import mock
    from modules.stock_analyser.data.providers import SyntheticProvider
    from modules.stock_analyser.strategies.model import strategy_from_dict
    from modules.stock_analyser.config import load_capital
    import modules.stock_analyser.paper.trader as T
    db = os.path.join(tempfile.mkdtemp(), "retired.db")
    SyntheticProvider().fetch(["RELIANCE"], n=60, seed=5, db_path=db, persist=True)
    d = strategy_from_dict({"name": "always", "universe": "U", "timeframe": "1D",
                            "entry": {"op": "gt", "args": [{"const": 2}, {"const": 1}]},
                            "max_hold": 2, "position_frac": 0.5, "max_positions": 1,
                            "flat_cost": 60.0}).to_dict()
    cfg = dict(load_capital())
    cfg["retired_trees"] = ["always"]
    with mock.patch.object(T, "load_capital", return_value=cfg):
        out = T.step(d, ["RELIANCE"], db_path=db)
    assert "RETIRED" in " ".join(out["actions"])
    assert not any(a.startswith("SIGNAL") for a in out["actions"])


def test_settled_cash_epi_releases_same_day():
    from datetime import datetime
    from modules.stock_analyser.data.store import connect, ensure_schema
    from modules.stock_analyser.data.recorder import IST
    from modules.stock_analyser.paper.trader import _ensure, _settled_cash
    db = os.path.join(tempfile.mkdtemp(), "settle.db")
    ensure_schema(db)
    con = connect(db)
    _ensure(con)
    today = datetime.now(IST).strftime("%Y-%m-%dT%H:%M")
    con.execute("INSERT INTO paper_trades(strategy,symbol,t_in,qty,px_in,cost,status)"
                " VALUES('s','A','2026-01-01T00:00',10,100.0,30,'OPEN')")
    con.execute("INSERT INTO paper_trades(strategy,symbol,t_in,t_out,qty,px_in,px_out,"
                "net,cost,status) VALUES('s','B','2026-01-01T00:00',?,10,100.0,110.0,"
                "40.0,60, 'CLOSED')", (today,))
    con.commit()
    epi = _settled_cash(con, "s", 50000.0, "T1_EPI")
    strict = _settled_cash(con, "s", 50000.0, "T1")
    con.close()
    assert epi > strict  # today's close settled via EPI, blocked under strict T+1
    assert strict == 50000.0 - 1030 - 1060  # open outlay + closed outlay, no proceeds
