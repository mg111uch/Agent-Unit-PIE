"""Universe manager — named sets; 200 is a dataset size, not a code cap."""
from __future__ import annotations
import hashlib
import json
import sqlite3
from typing import Any, Dict, List
from ..constants import SEED_SYMBOLS
from .store import connect

DEFS = {
    "NIFTY_200": {"members": list(SEED_SYMBOLS), "options": list(SEED_SYMBOLS)},
    "OPTIONS_ELIGIBLE": {"members": list(SEED_SYMBOLS), "options": list(SEED_SYMBOLS)},
    "ALL_EQUITIES": {"members": list(SEED_SYMBOLS), "options": []},
    "MY_RESEARCH_UNIVERSE": {"members": list(SEED_SYMBOLS)[:5], "options": []},
}


def resolve_asof(name: str, ts: str, db_path: str | None = None) -> List[str]:
    """P19: point-in-time membership — only constituents eligible at `ts`.

    Rows with blank effective_from/to are all-time members (legacy seeds).
    Without this, backtests use 2026 survivors on 2020 data (bias).
    """
    try:
        con = connect(db_path)
        try:
            rows = con.execute("SELECT member_id,effective_from,effective_to FROM universes"
                               " WHERE name=?", (name,)).fetchall()
            if rows:
                return [m for m, fr, to in rows
                        if (not fr or fr <= ts) and (not to or ts <= to)]
        finally:
            con.close()
    except Exception:
        pass
    d = DEFS.get(name)
    return list(d["members"]) if d else []


def snapshot_hash(members: List[str]) -> str:
    return hashlib.sha256(json.dumps(sorted(members)).encode()).hexdigest()[:16]


def resolve_universe(name: str, db_path: str | None = None) -> List[str]:
    try:
        con = connect(db_path)  # default = market.db; holds user-imported lists
        try:
            rows = con.execute("SELECT member_id FROM universes WHERE name=?", (name,)).fetchall()
            if rows:
                return [r[0] for r in rows]
        finally:
            con.close()
    except Exception:
        pass
    d = DEFS.get(name)
    return list(d["members"]) if d else []


def list_universes(db_path: str | None = None) -> List[str]:
    names = set(DEFS)
    try:
        con = connect(db_path)
        try:
            names.update(r[0] for r in con.execute("SELECT DISTINCT name FROM universes").fetchall())
        finally:
            con.close()
    except Exception:
        pass
    return sorted(names)


def import_universe(symbols: List[str], name: str = "MY_UNIVERSE_200",
                    db_path: str | None = None) -> Dict[str, Any]:
    """User hand-picked list -> instruments + universe rows. Then backfill bars."""
    from .models import Instrument
    from .store import ensure_schema, upsert_instruments, seed_universe
    clean = sorted({s.strip().upper() for s in symbols if s and s.strip()})
    ensure_schema(db_path)
    upsert_instruments([Instrument.equity(s).to_row() for s in clean], db_path)
    seed_universe(name, clean, db_path)
    return {"universe": name, "count": len(clean)}


def import_universe_file(path: str, name: str = "MY_UNIVERSE_200",
                         db_path: str | None = None) -> Dict[str, Any]:
    with open(path) as f:
        syms = [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]
    return import_universe(syms, name, db_path)


def is_options_eligible(symbol: str) -> bool:
    return symbol in DEFS["OPTIONS_ELIGIBLE"]["members"]


def instrument_id(symbol: str, exchange: str = "NSE") -> str:
    return f"{exchange}:{symbol}"
