"""SQLite viewer + row CRUD API for the editor area.

All paths resolve through the user workspace (same guard as /api/files/*),
table names are validated against sqlite_master, and every value is bound as
a parameter — no caller-supplied SQL is ever executed.
"""

from __future__ import annotations

import os
import sqlite3

from fastapi import Depends, HTTPException

from agent_core.server import app
from agent_core.server.auth import require_auth
import agent_core.server as _srv

DB_EXTS = {".db", ".sqlite", ".sqlite3"}
DEFAULT_ROWS = 50
MAX_ROWS = 200


def _db_path(path, user: dict) -> str:
    if not isinstance(path, str) or not path.strip():
        raise HTTPException(status_code=400, detail="path is required")
    if os.path.splitext(path)[1].lower() not in DB_EXTS:
        raise HTTPException(status_code=400, detail="Not a SQLite file (.db/.sqlite/.sqlite3)")
    _srv.set_user_workspace(str(user.get("id")))
    try:
        full = _srv.ws_resolve(path)
    except _srv.PathEscapeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not os.path.isfile(full):
        raise HTTPException(status_code=404, detail=f"Not found: {path}")
    return full


def _connect(full: str, write: bool = False) -> sqlite3.Connection:
    try:
        if write:
            conn = sqlite3.connect(full, timeout=5.0)
        else:
            conn = sqlite3.connect(f"file:{full}?mode=ro", uri=True, timeout=5.0)
    except sqlite3.Error as e:
        raise HTTPException(status_code=400, detail=f"Cannot open database: {e}")
    conn.row_factory = sqlite3.Row
    return conn


def _quote(name: str) -> str:
    return '"' + str(name).replace('"', '""') + '"'


def _objects(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT name, type FROM sqlite_master "
        "WHERE type IN ('table', 'view') AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
    return [{"name": r["name"], "type": r["type"]} for r in rows]


def _table(conn: sqlite3.Connection, name, writable: bool = False) -> dict:
    for item in _objects(conn):
        if item["name"] == name:
            if writable and item["type"] != "table":
                raise HTTPException(status_code=400, detail=f"View is read-only: {name}")
            return item
    raise HTTPException(status_code=404, detail=f"Unknown table: {name}")


def _columns(conn: sqlite3.Connection, table: str) -> list[dict]:
    rows = conn.execute(f"PRAGMA table_info({_quote(table)})").fetchall()
    return [
        {
            "name": r["name"],
            "type": r["type"] or "",
            "pk": int(r["pk"] or 0),
            "notnull": bool(r["notnull"]),
        }
        for r in rows
    ]


def _pk(conn: sqlite3.Connection, table: str, cols: list[dict]) -> tuple[list[str], bool]:
    pks = sorted((c for c in cols if c["pk"] > 0), key=lambda c: c["pk"])
    if pks:
        return [c["name"] for c in pks], False
    try:  # rowid tables without an explicit primary key stay editable
        conn.execute(f"SELECT rowid FROM {_quote(table)} LIMIT 1").fetchall()
        return ["__rowid__"], True
    except sqlite3.Error:
        return [], False


def _cell(value):
    if isinstance(value, bytes):
        return f"<blob {len(value)} bytes>"
    return value


def _coerce(col: dict, value):
    if value is None:
        return None
    col_type = (col.get("type") or "").upper()
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)) and not any(k in col_type for k in ("CHAR", "TEXT", "CLOB")):
        return value
    text = str(value)
    if text == "":
        return None
    if "INT" in col_type:
        try:
            return int(text)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"{col['name']} expects an integer")
    if any(k in col_type for k in ("REAL", "FLOA", "DOUB", "NUM", "DEC")):
        try:
            return float(text)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"{col['name']} expects a number")
    return text


def _where(pk: dict, cols: dict[str, dict], allowed: list[str], rowid_ok: bool) -> tuple[str, list]:
    keys = [k for k in pk.keys() if k in allowed and k in cols]
    use_rowid = rowid_ok and "__rowid__" in pk
    if not keys and not use_rowid:
        raise HTTPException(status_code=400, detail="Primary key values are required")
    parts = [f"{_quote(k)} = ?" for k in keys]
    params = [_coerce(cols[k], pk[k]) for k in keys]
    if use_rowid:  # PK-less tables are addressed through their implicit rowid
        try:
            params.append(int(pk["__rowid__"]))
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="Invalid rowid")
        parts.append("rowid = ?")
    return " AND ".join(parts), params


@app.get("/api/db/info")
async def db_info(path: str, user: dict = Depends(require_auth)):
    full = _db_path(path, user)
    conn = _connect(full)
    try:
        tables = [
            {"name": o["name"], "type": o["type"],
             "rows": conn.execute(f"SELECT COUNT(*) FROM {_quote(o['name'])}").fetchone()[0]}
            for o in _objects(conn)
        ]
    except sqlite3.Error as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()
    return {"path": path, "size": os.path.getsize(full), "tables": tables}


@app.get("/api/db/table")
async def db_table(path: str, table: str, limit: int = DEFAULT_ROWS, offset: int = 0,
                   order: str = "", dir: str = "asc", user: dict = Depends(require_auth)):
    full = _db_path(path, user)
    limit = max(1, min(int(limit or DEFAULT_ROWS), MAX_ROWS))
    offset = max(0, int(offset or 0))
    conn = _connect(full)
    try:
        info = _table(conn, table)
        cols = _columns(conn, table)
        names = [c["name"] for c in cols]
        pks, rowid = _pk(conn, table, cols)
        select = "rowid AS __rowid__, *" if rowid else "*"
        sql = f"SELECT {select} FROM {_quote(table)}"
        if order in names or (rowid and order == "__rowid__"):
            sql += f" ORDER BY {_quote(order)} {'DESC' if str(dir).lower() == 'desc' else 'ASC'}"
        total = conn.execute(f"SELECT COUNT(*) FROM {_quote(table)}").fetchone()[0]
        rows = conn.execute(sql + " LIMIT ? OFFSET ?", (limit, offset)).fetchall()
        data = [{k: _cell(r[k]) for k in r.keys()} for r in rows]
    except sqlite3.Error as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()
    return {
        "table": info["name"], "readonly": info["type"] != "table",
        "columns": cols, "pk": pks, "rowid": rowid, "rows": data,
        "total": total, "limit": limit, "offset": offset, "order": order, "dir": dir,
    }


@app.post("/api/db/row")
async def db_insert(data: dict, user: dict = Depends(require_auth)):
    full = _db_path(data.get("path"), user)
    values = data.get("values") or {}
    if not isinstance(values, dict):
        raise HTTPException(status_code=400, detail="values must be an object")
    conn = _connect(full, write=True)
    try:
        table = _table(conn, data.get("table"), writable=True)["name"]
        cols = {c["name"]: c for c in _columns(conn, table)}
        keys = [k for k in values.keys() if k in cols]
        if not keys:
            raise HTTPException(status_code=400, detail="No valid columns supplied")
        sql = (f"INSERT INTO {_quote(table)} ({', '.join(_quote(k) for k in keys)}) "
               f"VALUES ({', '.join('?' for _ in keys)})")
        cur = conn.execute(sql, [_coerce(cols[k], values[k]) for k in keys])
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()
    return {"status": "ok", "rowid": cur.lastrowid}


@app.patch("/api/db/row")
async def db_update(data: dict, user: dict = Depends(require_auth)):
    full = _db_path(data.get("path"), user)
    values = data.get("values") or {}
    if not isinstance(values, dict) or not values:
        raise HTTPException(status_code=400, detail="values must be a non-empty object")
    conn = _connect(full, write=True)
    try:
        table = _table(conn, data.get("table"), writable=True)["name"]
        col_list = _columns(conn, table)
        cols = {c["name"]: c for c in col_list}
        pks, rowid = _pk(conn, table, col_list)
        sets = [k for k in values.keys() if k in cols]
        if not sets:
            raise HTTPException(status_code=400, detail="No valid columns supplied")
        clause, params = _where(data.get("pk") or {}, cols, pks, rowid)
        sql = (f"UPDATE {_quote(table)} SET {', '.join(f'{_quote(k)} = ?' for k in sets)} "
               f"WHERE {clause}")
        cur = conn.execute(sql, [_coerce(cols[k], values[k]) for k in sets] + params)
        conn.commit()
        changed = cur.rowcount
    except sqlite3.Error as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()
    return {"status": "ok", "changed": changed}


@app.delete("/api/db/row")
async def db_delete(data: dict, user: dict = Depends(require_auth)):
    full = _db_path(data.get("path"), user)
    conn = _connect(full, write=True)
    try:
        table = _table(conn, data.get("table"), writable=True)["name"]
        col_list = _columns(conn, table)
        cols = {c["name"]: c for c in col_list}
        pks, rowid = _pk(conn, table, col_list)
        clause, params = _where(data.get("pk") or {}, cols, pks, rowid)
        cur = conn.execute(f"DELETE FROM {_quote(table)} WHERE {clause}", params)
        conn.commit()
        changed = cur.rowcount
    except sqlite3.Error as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()
    return {"status": "ok", "changed": changed}
