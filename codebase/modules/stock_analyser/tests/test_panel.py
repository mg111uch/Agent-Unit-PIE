"""Date-aligned panels: late entrants don't truncate the panel."""
import sys as _s
from pathlib import Path as _P
for _c in [_P(__file__).resolve().parents[3], _P(__file__).resolve().parents[4]]:
    if str(_c) not in _s.path:
        _s.path.insert(0, str(_c))


def _bars(n: int, start: int = 0, seed_px: float = 100.0, drift: float = 0.002):
    out, px = [], seed_px
    for i in range(n):
        o = px
        c = o * (1 + drift)
        out.append({"instrument_id": "X", "ts": f"{start + i:010d}", "timeframe": "1D",
                    "open": o, "high": max(o, c) * 1.005, "low": min(o, c) * 0.995,
                    "close": c, "volume": 1e6})
        px = c
    return out


def _strat():
    from modules.stock_analyser.strategies.model import strategy_from_dict
    entry = {"op": "gt", "args": [{"field": "close"},
              {"op": "lag", "args": [
                  {"op": "rolling_max", "args": [{"field": "close"}, {"const": 5}]},
                  {"const": 1}]}]}
    return strategy_from_dict({"name": "t", "universe": "U", "timeframe": "1D",
                               "entry": entry, "max_hold": 3, "flat_cost": 0.0,
                               "fee_bps": 0.0, "slippage_bps": 0.0})


def test_late_entrant_keeps_full_panel():
    from modules.stock_analyser.backtest.engine import run_backtest
    full = {"A": _bars(120, 0), "B": _bars(120, 0, 200.0)}
    late = {"A": _bars(120, 0), "IPO": _bars(70, 50, 50.0)}  # entrant from day 50
    r_full = run_backtest(_strat(), full, start_cash=50000.0, min_bars=60)
    r_late = run_backtest(_strat(), late, start_cash=50000.0, min_bars=60)
    assert "excluded" in r_late and r_late["excluded"] == []
    # same trade count on A: panel not truncated by IPO's short history
    assert (sum(1 for t in r_late["trades"] if t["symbol"] == "A") ==
            sum(1 for t in r_full["trades"] if t["symbol"] == "A"))
    assert any(t["symbol"] == "IPO" for t in r_late["trades"])
    # entrant never trades before its first bar
    assert all(t["t_in"] >= "0000000050" for t in r_late["trades"] if t["symbol"] == "IPO")


def test_short_history_excluded_and_reported():
    from modules.stock_analyser.backtest.engine import run_backtest
    bars = {"A": _bars(120, 0), "NEW": _bars(30, 90, 50.0)}
    r = run_backtest(_strat(), bars, start_cash=50000.0, min_bars=60)
    assert r["excluded"] == ["NEW"]
    assert all(t["symbol"] != "NEW" for t in r["trades"])
