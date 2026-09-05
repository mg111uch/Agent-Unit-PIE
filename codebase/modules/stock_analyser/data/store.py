"""SQLite store — market data lives in data/market.db (NOT kernel.db). Raw bars only."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Dict, List, Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS instruments(
 instrument_id TEXT PRIMARY KEY, symbol TEXT, exchange TEXT, asset_type TEXT,
 underlying TEXT, lot_size INTEGER, expiry TEXT, strike REAL, right TEXT,
 active_from TEXT, active_to TEXT, meta_json TEXT DEFAULT '{}');
CREATE TABLE IF NOT EXISTS equity_bars(
 instrument_id TEXT, ts TEXT, timeframe TEXT, open REAL, high REAL, low REAL,
 close REAL, vol REAL, source TEXT,
 PRIMARY KEY(instrument_id, ts, timeframe));
CREATE TABLE IF NOT EXISTS option_bars(
 instrument_id TEXT, ts TEXT, timeframe TEXT, underlying TEXT, expiry TEXT,
 strike REAL, right TEXT, ltp REAL, bid REAL, ask REAL, vol REAL, oi REAL,
 oi_change REAL, iv REAL, delta REAL, gamma REAL, theta REAL, vega REAL, source TEXT,
 PRIMARY KEY(instrument_id, ts, timeframe));
CREATE TABLE IF NOT EXISTS universes(
 name TEXT, member_id TEXT, effective_from TEXT DEFAULT '', effective_to TEXT DEFAULT '',
 PRIMARY KEY(name, member_id));
CREATE TABLE IF NOT EXISTS research_datasets(
 id TEXT PRIMARY KEY, name TEXT, universe TEXT, timeframe TEXT,
 start_ts TEXT, end_ts TEXT, split_json TEXT DEFAULT '{}');
CREATE TABLE IF NOT EXISTS paper_proposals(
 id TEXT PRIMARY KEY, strategy_json TEXT, status TEXT DEFAULT 'PROPOSED',
 human_approved INTEGER DEFAULT 0, created_at TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS paper_trades(
 id INTEGER PRIMARY KEY AUTOINCREMENT, strategy TEXT, symbol TEXT,
 t_in TEXT, t_out TEXT, qty REAL, px_in REAL, px_out REAL,
 net REAL, cost REAL, status TEXT DEFAULT 'OPEN', created_at TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS research_runs(
 id TEXT PRIMARY KEY, objective TEXT, universe TEXT, mode TEXT DEFAULT 'day',
 budget INTEGER DEFAULT 20, done INTEGER DEFAULT 0, status TEXT DEFAULT 'RUNNING',
 created_at TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS research_candidates(
 id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT, strategy_hash TEXT,
 strategy_json TEXT, parent TEXT, mutation TEXT, verdict TEXT,
 avg_net REAL, oos_net REAL, robustness REAL, created_at TEXT DEFAULT '',
 data_hash TEXT DEFAULT '', code_version TEXT DEFAULT '',
 feature_set_hash TEXT DEFAULT '', model_config_hash TEXT DEFAULT '',
 random_seed TEXT DEFAULT '', dataset_id TEXT DEFAULT '',
 signal_hash TEXT DEFAULT '',
 UNIQUE(run_id, strategy_hash));
CREATE INDEX IF NOT EXISTS idx_eq_inst_ts ON equity_bars(instrument_id, ts);
CREATE INDEX IF NOT EXISTS idx_eq_ts_inst ON equity_bars(ts, instrument_id);
CREATE INDEX IF NOT EXISTS idx_op_inst_ts ON option_bars(instrument_id, ts);
"""


def get_db_path(db_path: str | None = None) -> Path:
    if db_path:
        return Path(db_path)
    # codebase/modules/stock_analyser/data/store.py -> workspace/data/market.db
    here = Path(__file__).resolve()
    ws = here.parents[4]  # .../Agentic_Unit_PIE
    cand = ws / "data" / "market.db"
    if cand.parent.exists():
        return cand
    return Path("data/market.db")


def connect(db_path: str | None = None) -> sqlite3.Connection:
    p = get_db_path(db_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(p))
    con.execute("PRAGMA journal_mode=WAL")
    return con


def ensure_schema(db_path: str | None = None) -> str:
    con = connect(db_path)
    try:
        con.executescript(SCHEMA)
        con.commit()
    finally:
        con.close()
    return str(get_db_path(db_path))


def upsert_instruments(rows: List[tuple], db_path: str | None = None) -> int:
    con = connect(db_path)
    try:
        ensure_schema(db_path)
        con.executemany("INSERT OR REPLACE INTO instruments VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", rows)
        con.commit()
        return len(rows)
    finally:
        con.close()


def upsert_equity_bars(rows: List[tuple], db_path: str | None = None) -> int:
    """UPDATE existing (refreshes forming bar) + INSERT new. Returns new-row count."""
    con = connect(db_path)
    try:
        con.executescript(SCHEMA)
        con.executemany("UPDATE equity_bars SET open=?,high=?,low=?,close=?,vol=?,source=?"
                        " WHERE instrument_id=? AND ts=? AND timeframe=?",
                        [(r[3], r[4], r[5], r[6], r[7], r[8], r[0], r[1], r[2]) for r in rows])
        before = con.total_changes
        con.executemany("INSERT OR IGNORE INTO equity_bars VALUES(?,?,?,?,?,?,?,?,?)", rows)
        con.commit()
        return con.total_changes - before
    finally:
        con.close()


def upsert_option_bars(rows: List[tuple], db_path: str | None = None) -> int:
    """UPDATE existing + INSERT new. Returns new-row count."""
    con = connect(db_path)
    try:
        con.executescript(SCHEMA)
        con.executemany("UPDATE option_bars SET ltp=?,bid=?,ask=?,vol=?,oi=?,oi_change=?,"
                        "iv=?,delta=?,gamma=?,theta=?,vega=?,source=?"
                        " WHERE instrument_id=? AND ts=? AND timeframe=?",
                        [(r[7], r[8], r[9], r[10], r[11], r[12], r[13], r[14], r[15],
                          r[16], r[17], r[18], r[0], r[1], r[2]) for r in rows])
        before = con.total_changes
        con.executemany("INSERT OR IGNORE INTO option_bars VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
        con.commit()
        return con.total_changes - before
    finally:
        con.close()


def max_ts(instrument_id: str, timeframe: str, db_path: str | None = None) -> str:
    """Latest stored bar ts ('' if none). Decides backfill vs top-up range."""
    con = connect(db_path)
    try:
        try:
            r = con.execute("SELECT MAX(ts) FROM equity_bars WHERE instrument_id=? AND timeframe=?",
                            (instrument_id, timeframe)).fetchone()
        except Exception:
            return ""
        return r[0] or ""
    finally:
        con.close()


def query_equity(instrument_id: str, timeframe: str = "1D", start: str = "",
                 end: str = "", db_path: str | None = None) -> List[Dict[str, Any]]:
    con = connect(db_path)
    try:
        q = "SELECT instrument_id,ts,timeframe,open,high,low,close,vol,source FROM equity_bars WHERE instrument_id=? AND timeframe=?"
        args: List[Any] = [instrument_id, timeframe]
        if start:
            q += " AND ts>=?"; args.append(start)
        if end:
            q += " AND ts<=?"; args.append(end)
        q += " ORDER BY ts"
        cols = ["instrument_id", "ts", "timeframe", "open", "high", "low", "close", "volume", "source"]
        return [dict(zip(cols, r)) for r in con.execute(q, args).fetchall()]
    finally:
        con.close()


def seed_universe(name: str, members: List[str], db_path: str | None = None) -> int:
    con = connect(db_path)
    try:
        con.executescript(SCHEMA)
        con.executemany("INSERT OR IGNORE INTO universes VALUES(?,?, '', '')",
                        [(name, m) for m in members])
        con.commit()
        return len(members)
    finally:
        con.close()
