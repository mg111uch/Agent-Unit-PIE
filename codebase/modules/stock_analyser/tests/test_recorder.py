"""Recorder tests: offline normalize + dup-safety (no network)."""
import os
import sys as _s
import tempfile
from pathlib import Path as _P
for _c in [_P(__file__).resolve().parents[3], _P(__file__).resolve().parents[4]]:
    if str(_c) not in _s.path:
        _s.path.insert(0, str(_c))

FAKE_CHAIN = {"records": {"underlyingValue": 25000, "expiryDates": ["04-Sep-2026"],
              "data": [{"strikePrice": 25000, "expiryDate": "04-Sep-2026",
                        "CE": {"lastPrice": 120.5, "openInterest": 1000,
                               "changeinOpenInterest": 50, "impliedVolatility": 11.2,
                               "totalTradedVolume": 5000, "bidprice": 119.0, "askPrice": 121.0},
                        "PE": {"lastPrice": 98.0, "openInterest": 2000,
                               "changeinOpenInterest": -30, "impliedVolatility": 12.1,
                               "totalTradedVolume": 4000, "bidprice": 97.0, "askPrice": 99.0}},
                       {"strikePrice": 25100, "expiryDate": "11-Sep-2026",  # not front
                        "CE": {"lastPrice": 1.0}, "PE": {}}]}}


def test_chain_normalize_front_expiry_only():
    from modules.stock_analyser.data.recorder import chain_to_option_rows
    rows = chain_to_option_rows(FAKE_CHAIN, "2026-09-03T10:00")
    assert len(rows) == 2  # CE+PE front expiry; next expiry skipped
    ce = [r for r in rows if r["right"] == "CE"][0]
    assert ce["strike"] == 25000 and ce["ltp"] == 120.5
    assert ce["oi"] == 1000 and ce["oi_change"] == 50 and ce["iv"] == 11.2
    assert ce["expiry"] == "04-Sep-2026"


def test_forming_bar_refreshes_not_frozen():
    from modules.stock_analyser.data.providers import UpstoxStub
    from modules.stock_analyser.data.store import query_equity
    db = os.path.join(tempfile.mkdtemp(), "k2.db")
    stub = UpstoxStub()
    bar = {"instrument_id": "NSE:X", "ts": "2026-09-03T10:00", "open": 100.0,
           "high": 101.0, "low": 99.0, "close": 100.5, "volume": 10.0}
    assert stub.record([bar], "15m", db) == 1
    assert stub.record([bar], "15m", db) == 0  # identical re-record: 0 new
    bar["close"], bar["high"], bar["volume"] = 102.0, 103.0, 25.0
    assert stub.record([bar], "15m", db) == 0  # still 0 new...
    got = query_equity("NSE:X", "15m", db_path=db)[0]
    assert got["close"] == 102.0 and got["volume"] == 25.0  # ...but values refreshed


def test_yahoo_range_backfill_then_topup():
    from modules.stock_analyser.data.recorder import Recorder
    from modules.stock_analyser.data.providers import UpstoxStub
    db = os.path.join(tempfile.mkdtemp(), "k3.db")
    r = Recorder(index_symbols=(), equity_symbols=("RELIANCE",), db_path=db)
    assert r._yahoo_range("RELIANCE") == "1d"  # nothing stored
    stub = UpstoxStub()
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M")
    stub.record([{"instrument_id": "NSE:RELIANCE", "ts": now, "open": 1.0,
                  "high": 1.0, "low": 1.0, "close": 1.0, "volume": 1.0}], "15m", db)
    assert r._yahoo_range("RELIANCE") == "1h"  # fresh bars -> top-up
    stub.record([{"instrument_id": "NSE:RELIANCE", "ts": "2026-09-01T10:00", "open": 1.0,
                  "high": 1.0, "low": 1.0, "close": 1.0, "volume": 1.0}], "15m", db)
    r2 = Recorder(index_symbols=(), equity_symbols=("RELIANCE",), db_path=db)
    # max ts is fresh -> still top-up; stale-only case:
    import sqlite3
    con = sqlite3.connect(db)
    con.execute("DELETE FROM equity_bars WHERE ts=?", (now,))
    con.commit(); con.close()
    assert r2._yahoo_range("RELIANCE") == "1d"  # only stale bar left -> backfill


def test_record_dup_safe_and_hours_guard():
    from datetime import datetime, timezone
    from modules.stock_analyser.data.recorder import market_open, chain_to_option_rows, IST
    from modules.stock_analyser.data.providers import UpstoxStub
    db = os.path.join(tempfile.mkdtemp(), "kernel.db")
    rows = chain_to_option_rows(FAKE_CHAIN, "2026-09-03T10:00")
    stub = UpstoxStub()
    assert stub.record_options(rows, "15m", db) == 2
    assert stub.record_options(rows, "15m", db) == 0  # restart-safe dups
    assert market_open(datetime(2026, 9, 3, 10, 0, tzinfo=IST)) is True  # Thu 10:00 IST
    assert market_open(datetime(2026, 9, 6, 10, 0, tzinfo=IST)) is False  # Sun
    assert market_open(datetime(2026, 9, 3, 16, 0, tzinfo=IST)) is False  # post-close


def test_prune_keeps_newest_50():
    import json
    import tempfile as _tf
    from pathlib import Path
    from modules.stock_analyser import kernel_bridge as KB
    root = Path(_tf.mkdtemp())
    import os
    import time as _t
    base = _t.time() - 1000
    for i in range(55):
        d = root / f"run_{i:03d}"
        d.mkdir()
        (d / "summary.json").write_text(json.dumps({"n": i}))
        os.utime(d, (base + i, base + i))  # deterministic mtime order
    (root / "run_007" / "summary.json").write_text(json.dumps({"error": "no data"}))
    out = KB.prune_shards(keep=50, root=root)
    assert out == {"kept": 50, "deleted": 5}
    assert not (root / "run_000").exists() and not (root / "run_007").exists()
    assert (root / "run_054").exists()
