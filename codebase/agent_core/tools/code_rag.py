import sqlite3
import json
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

from agent_core.config import CODEBASE_ATLAS_DIR as _CONFIG_ATLAS_DIR, CODEBASE_ROOT as _CODEBASE_ROOT

DB_FILENAME = "code_rag.db"


class CodeRAG:
    def __init__(self, atlas_dir: str):
        self.atlas_dir = Path(atlas_dir)
        self.db_path = self.atlas_dir / DB_FILENAME
        self._conn: Optional[sqlite3.Connection] = None

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def ensure_indexed(self) -> bool:
        if not self.db_path.exists():
            return False
        conn = self._get_conn()
        cur = conn.execute("SELECT value FROM meta WHERE key = 'ingested'")
        return cur.fetchone() is not None

    def needs_index(self) -> bool:
        return not self.db_path.exists()

    def get_symbol(self, name: str, file_path: Optional[str] = None,
                   parent_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        conn = self._get_conn()
        if file_path and parent_name:
            cur = conn.execute(
                "SELECT * FROM symbols WHERE symbol_name = ? AND file_path = ? AND parent_name = ?",
                (name, file_path, parent_name)
            )
        elif file_path:
            cur = conn.execute(
                "SELECT * FROM symbols WHERE symbol_name = ? AND file_path = ?",
                (name, file_path)
            )
        elif parent_name:
            cur = conn.execute(
                "SELECT * FROM symbols WHERE symbol_name = ? AND parent_name = ?",
                (name, parent_name)
            )
        else:
            cur = conn.execute(
                "SELECT * FROM symbols WHERE symbol_name = ? ORDER BY file_path",
                (name,)
            )
        rows = cur.fetchall()
        if not rows:
            return None
        if len(rows) == 1:
            return dict(rows[0])
        result = [dict(r) for r in rows]
        return {
            "note": f"Found {len(rows)} symbols named '{name}'. Use file_path or parent_name to disambiguate.",
            "matches": result,
        }

    def get_symbols(self, names: List[str], file_path: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        placeholders = ",".join("?" * len(names))
        if file_path:
            cur = conn.execute(
                f"SELECT * FROM symbols WHERE symbol_name IN ({placeholders}) AND file_path = ?",
                (*names, file_path)
            )
        else:
            cur = conn.execute(
                f"SELECT * FROM symbols WHERE symbol_name IN ({placeholders})",
                names
            )
        return [dict(r) for r in cur.fetchall()]

    def search_symbols(self, query: str, type_filter: Optional[str] = None,
                       top_k: int = 10) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        sql = """
            SELECT s.*, rank FROM symbols_fts f
            JOIN symbols s ON s.id = f.rowid
            WHERE symbols_fts MATCH ?
        """
        params: list = [query]
        if type_filter:
            sql += " AND s.symbol_type = ?"
            params.append(type_filter)
        sql += " ORDER BY rank LIMIT ?"
        params.append(top_k)
        cur = conn.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]

    def get_callers_callees(self, name: str, file_path: Optional[str] = None,
                            depth: int = 1, direction: str = "both") -> Dict[str, Any]:
        symbol = self.get_symbol(name, file_path)
        if symbol is None:
            return {"error": f"Symbol '{name}' not found. Run codebase atlas first."}
        if "matches" in symbol:
            return symbol

        result: Dict[str, Any] = {"symbol": symbol, "callers": [], "callees": []}
        conn = self._get_conn()

        if direction in ("callers", "both"):
            sql = """
                WITH RECURSIVE callers(n) AS (
                    SELECT source_id FROM call_edges WHERE target_id = ?
                    UNION
                    SELECT ce.source_id FROM call_edges ce
                    JOIN callers c ON ce.target_id = c.n
                    WHERE c.n != ce.source_id
                )
                SELECT DISTINCT s.* FROM symbols s
                JOIN callers c ON s.id = c.n
                LIMIT 50
            """
            cur = conn.execute(sql, (symbol["id"],))
            result["callers"] = [dict(r) for r in cur.fetchall()]

        if direction in ("callees", "both"):
            sql = """
                WITH RECURSIVE callees(n) AS (
                    SELECT target_id FROM call_edges WHERE source_id = ?
                    UNION
                    SELECT ce.target_id FROM call_edges ce
                    JOIN callees c ON ce.source_id = c.n
                    WHERE c.n != ce.target_id
                )
                SELECT DISTINCT s.* FROM symbols s
                JOIN callees c ON s.id = c.n
                LIMIT 50
            """
            cur = conn.execute(sql, (symbol["id"],))
            result["callees"] = [dict(r) for r in cur.fetchall()]

        return result

    def find_impact(self, name: str, file_path: Optional[str] = None) -> List[Dict[str, Any]]:
        symbol = self.get_symbol(name, file_path)
        if symbol is None:
            return []
        if "matches" in symbol:
            return []
        conn = self._get_conn()
        sql = """
            WITH RECURSIVE callers(n) AS (
                SELECT source_id FROM call_edges WHERE target_id = ?
                UNION
                SELECT ce.source_id FROM call_edges ce
                JOIN callers c ON ce.target_id = c.n
                WHERE c.n != ce.source_id
            )
            SELECT DISTINCT s.* FROM symbols s
            JOIN callers c ON s.id = c.n
            LIMIT 100
        """
        cur = conn.execute(sql, (symbol["id"],))
        return [dict(r) for r in cur.fetchall()]


_rag_instance: Optional[CodeRAG] = None


def _get_rag() -> Optional[CodeRAG]:
    global _rag_instance
    if _rag_instance is not None:
        return _rag_instance
    atlas_dir = ""
    if _CONFIG_ATLAS_DIR and os.path.isdir(_CONFIG_ATLAS_DIR):
        atlas_dir = _CONFIG_ATLAS_DIR
    if not atlas_dir:
        atlas_dir = os.environ.get("CODEBASE_ATLAS_DIR", "")
    if not atlas_dir:
        project_root = os.path.dirname(_CODEBASE_ROOT)
        candidate = os.path.join(project_root, "atlas_output")
        if os.path.isdir(candidate):
            atlas_dir = candidate
    if not atlas_dir or not os.path.isdir(atlas_dir):
        return None
    _rag_instance = CodeRAG(atlas_dir)
    return _rag_instance


# Agent tool functions (plain functions — @tool_call decorator applied in __init__.py)

BUDGET_CHARS = 10000


def get_symbol_tool(params: dict) -> str:
    rag = _get_rag()
    if rag is None:
        return "Codebase atlas not found. Run `python -m codebase_atlas.main --project-dir <path> --output-dir ./atlas_output --serve` to generate it."
    rag.ensure_indexed()

    names = params.get("names")
    if not names:
        single = params.get("name", "")
        if single:
            names = [single]
    if names:
        if isinstance(names, str):
            names = [names]
        file_path = params.get("file_path")
        symbols = rag.get_symbols(names, file_path)
        found_names = {s["symbol_name"] for s in symbols}
        missing_names = [n for n in names if n not in found_names]
        if not symbols:
            return json.dumps({
                "error": f"No symbols found for: {names}",
                "missing_names": list(names),
                "hint": "Use search_symbols with a fuzzy query for possible misspellings, then get_symbol only for the exact names you need.",
            }, indent=2)
        results = []
        total_chars = 0
        truncated_names = []
        for sym in symbols:
            serialized = json.dumps(sym, indent=2)
            total_chars += len(serialized)
            if total_chars > BUDGET_CHARS and results:
                truncated_names.append(sym["symbol_name"])
            else:
                results.append(sym)
        output: dict = {"symbols": results}
        if missing_names:
            output["missing_names"] = missing_names
            output["hint"] = (
                "Some names were not found (check spelling). "
                "Call search_symbols only for missing names, then get_symbol with corrected exact names."
            )
        if truncated_names:
            output["truncated_names"] = truncated_names
        return json.dumps(output, indent=2)

    return "Error: 'names' (list) or 'name' (string) parameter is required."


def search_symbols_tool(params: dict) -> str:
    """Metadata-only search. Does not prefetch definitions (avoids bloating with unrelated hits)."""
    rag = _get_rag()
    if rag is None:
        return "Codebase atlas not found. Run `python -m codebase_atlas.main --project-dir <path> --output-dir ./atlas_output --serve` to generate it."
    rag.ensure_indexed()
    query = params.get("query", "")
    if not query:
        return "Error: 'query' parameter is required."
    type_filter = params.get("type_filter")
    top_k = params.get("top_k", 10)
    results = rag.search_symbols(query, type_filter, top_k)
    if not results:
        return f"No symbols matching '{query}'."
    summary = []
    for r in results:
        summary.append({
            "symbol_name": r["symbol_name"],
            "symbol_type": r["symbol_type"],
            "file_path": r["file_path"],
            "parent_name": r["parent_name"],
            "start_line": r["start_line"],
            "end_line": r["end_line"],
            "risk_level": r["risk_level"],
        })
    return json.dumps({"results": summary}, indent=2)


def get_callers_callees_tool(params: dict) -> str:
    rag = _get_rag()
    if rag is None:
        return "Codebase atlas not found."
    rag.ensure_indexed()
    name = params.get("name", "")
    if not name:
        return "Error: 'name' parameter is required."
    file_path = params.get("file_path")
    depth = params.get("depth", 1)
    direction = params.get("direction", "both")
    result = rag.get_callers_callees(name, file_path, depth, direction)
    if "error" in result:
        return result["error"]
    summary = {
        "symbol": {
            "name": result["symbol"]["symbol_name"],
            "type": result["symbol"]["symbol_type"],
            "file_path": result["symbol"]["file_path"],
        },
        "callers": [
            {"name": c["symbol_name"], "file": c["file_path"], "type": c["symbol_type"]}
            for c in result["callers"]
        ],
        "callees": [
            {"name": c["symbol_name"], "file": c["file_path"], "type": c["symbol_type"]}
            for c in result["callees"]
        ],
    }
    return json.dumps(summary, indent=2)


def find_impact_tool(params: dict) -> str:
    rag = _get_rag()
    if rag is None:
        return "Codebase atlas not found."
    rag.ensure_indexed()
    name = params.get("name", "")
    if not name:
        return "Error: 'name' parameter is required."
    file_path = params.get("file_path")
    results = rag.find_impact(name, file_path)
    if not results:
        return f"Nothing depends on '{name}'."
    summary = [
        {"name": r["symbol_name"], "file": r["file_path"],
         "type": r["symbol_type"], "risk": r["risk_level"]}
        for r in results
    ]
    return json.dumps(summary, indent=2)
