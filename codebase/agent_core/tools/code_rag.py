import sqlite3
import json
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

from agent_core.config import CODEBASE_ATLAS_DIR as _CONFIG_ATLAS_DIR, CODEBASE_ROOT as _CODEBASE_ROOT


def _resolve_path(path: str) -> str:
    p = Path(path)
    if p.is_absolute():
        return str(p)
    return str(Path(_CODEBASE_ROOT) / p)

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
        sql += " ORDER BY s.token_count ASC, rank LIMIT ?"
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

    def get_symbols_meta(self, names: List[str], file_path: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        placeholders = ",".join("?" * len(names))
        if file_path:
            cur = conn.execute(
                f"SELECT symbol_name, symbol_type, file_path, parent_name, "
                f"signature, docstring, token_count, risk_level, entry_point, "
                f"start_line, end_line FROM symbols "
                f"WHERE symbol_name IN ({placeholders}) AND file_path = ?",
                (*names, file_path)
            )
        else:
            cur = conn.execute(
                f"SELECT symbol_name, symbol_type, file_path, parent_name, "
                f"signature, docstring, token_count, risk_level, entry_point, "
                f"start_line, end_line FROM symbols "
                f"WHERE symbol_name IN ({placeholders})",
                names
            )
        return [dict(r) for r in cur.fetchall()]

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

    def get_index_info(self) -> Dict[str, Any]:
        conn = self._get_conn()
        c = conn.execute
        total = c("SELECT COUNT(*) FROM symbols").fetchone()[0]
        funcs = c("SELECT COUNT(*) FROM symbols WHERE symbol_type IN ('function','method')").fetchone()[0]
        classes = c("SELECT COUNT(*) FROM symbols WHERE symbol_type = 'class'").fetchone()[0]
        file_entries = c("SELECT COUNT(*) FROM symbols WHERE symbol_type = 'file'").fetchone()[0]
        files = c("SELECT COUNT(DISTINCT file_path) FROM symbols").fetchone()[0]
        edges = c("SELECT COUNT(*) FROM call_edges").fetchone()[0]
        entry = c("SELECT COUNT(*) FROM symbols WHERE entry_point = 1").fetchone()[0]
        big = c("SELECT COUNT(*) FROM symbols WHERE token_count > 500").fetchone()[0]

        ft = c("SELECT MIN(token_count), AVG(token_count), MAX(token_count), SUM(token_count) FROM symbols WHERE symbol_type IN ('function','method')").fetchone()
        fl = c("SELECT MIN(token_count), AVG(token_count), MAX(token_count), SUM(token_count) FROM symbols WHERE symbol_type = 'file'").fetchone()
        total_tok = c("SELECT SUM(token_count) FROM symbols").fetchone()[0]

        risk_rows = c("SELECT risk_level, COUNT(*) FROM symbols WHERE symbol_type IN ('function','method') GROUP BY risk_level").fetchall()
        risk_dist = {r[0]: r[1] for r in risk_rows}

        return {
            "total_symbols": total,
            "functions_methods": funcs,
            "classes": classes,
            "file_symbols": file_entries,
            "unique_files": files,
            "call_edges": edges,
            "entry_points": entry,
            "symbols_over_500_tokens": big,
            "function_tokens": {
                "min": ft[0] or 0,
                "avg": round(ft[1]) if ft[1] else 0,
                "max": ft[2] or 0,
                "total": ft[3] or 0,
            },
            "file_tokens": {
                "min": fl[0] or 0,
                "avg": round(fl[1]) if fl[1] else 0,
                "max": fl[2] or 0,
                "total": fl[3] or 0,
            },
            "total_codebase_tokens": total_tok or 0,
            "risk_distribution": risk_dist,
        }


# ── Proposed MCP tools (improvement.md) ──────────────────────────────────

    def file_api(self, path: str) -> Dict[str, Any]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT symbol_name, symbol_type, parent_name, signature, "
            "       docstring, start_line, end_line, risk_level "
            "FROM symbols WHERE file_path = ? AND symbol_type != 'file' "
            "ORDER BY start_line",
            (path,)
        ).fetchall()

        classes = {}
        functions = []
        for r in rows:
            d = dict(r)
            if d.get("docstring"):
                d["docstring_first_line"] = d["docstring"].split("\n")[0].strip()
            else:
                d["docstring_first_line"] = ""
            d.pop("docstring", None)

            if d["symbol_type"] == "method" and d.get("parent_name"):
                parent = d.pop("parent_name")
                classes.setdefault(parent, {"methods": []})["methods"].append(d)
            elif d["symbol_type"] == "class":
                classes.setdefault(d["symbol_name"], {"methods": []})
            else:
                functions.append(d)

        result = {"file_path": path, "functions": functions, "classes": []}
        for cname, cbody in classes.items():
            result["classes"].append({"class_name": cname, "methods": cbody["methods"]})
        result["total_api_symbols"] = len(functions) + sum(len(c["methods"]) for c in result["classes"])
        return result

    def call_chain(self, start_fn: str, end_module: str,
                   file_path: Optional[str] = None) -> Dict[str, Any]:
        sym = self.get_symbol(start_fn, file_path)
        if sym is None:
            return {"error": f"Symbol '{start_fn}' not found."}
        if "matches" in sym:
            return sym

        conn = self._get_conn()
        start_id = sym["id"]

        parent_map = {}
        for r in conn.execute("SELECT id, file_path FROM symbols").fetchall():
            parent_map[r["id"]] = r["file_path"]

        visited = {start_id}
        queue = [[start_id]]

        while queue:
            path = queue.pop(0)
            cur = path[-1]
            cur_path = parent_map.get(cur, "")
            if end_module in cur_path:
                names = []
                for pid in path:
                    row = conn.execute(
                        "SELECT symbol_name, file_path FROM symbols WHERE id = ?", (pid,)
                    ).fetchone()
                    if row:
                        names.append(f"{row['symbol_name']} ({row['file_path']})")
                return {"chain": names, "length": len(names)}

            for row in conn.execute(
                "SELECT source_id, target_id FROM call_edges "
                "WHERE source_id = ? OR target_id = ?",
                (cur, cur)
            ).fetchall():
                nxt = row["target_id"] if row["source_id"] == cur else row["source_id"]
                if nxt not in visited:
                    visited.add(nxt)
                    queue.append(path + [nxt])

        return {"error": f"No call chain from '{start_fn}' to module '{end_module}'."}

    def compare_apis(self, path_a: str, path_b: str) -> Dict[str, Any]:
        api_a = self.file_api(path_a)
        api_b = self.file_api(path_b)

        def key(sym):
            return (sym.get("parent_name") or "", sym["symbol_name"])

        sigs_a = {}
        for f in api_a["functions"]:
            sigs_a[key(f)] = f.get("signature", "")
        for c in api_a["classes"]:
            for m in c["methods"]:
                sigs_a[(c["class_name"], m["symbol_name"])] = m.get("signature", "")

        sigs_b = {}
        for f in api_b["functions"]:
            sigs_b[key(f)] = f.get("signature", "")
        for c in api_b["classes"]:
            for m in c["methods"]:
                sigs_b[(c["class_name"], m["symbol_name"])] = m.get("signature", "")

        keys_a = set(sigs_a)
        keys_b = set(sigs_b)

        only_a = [{"parent": p, "name": n, "signature": sigs_a[(p, n)]}
                  for p, n in sorted(keys_a - keys_b)]
        only_b = [{"parent": p, "name": n, "signature": sigs_b[(p, n)]}
                  for p, n in sorted(keys_b - keys_a)]
        mismatches = []
        for pn in sorted(keys_a & keys_b):
            if sigs_a[pn] != sigs_b[pn]:
                mismatches.append({
                    "parent": pn[0], "name": pn[1],
                    "signature_a": sigs_a[pn], "signature_b": sigs_b[pn],
                })

        return {
            "file_a": path_a, "file_b": path_b,
            "only_in_a": only_a, "only_in_b": only_b,
            "signature_mismatches": mismatches,
            "total_a": len(sigs_a), "total_b": len(sigs_b),
            "common": len(keys_a & keys_b),
        }

    def symbols_by_file(self, path: str) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT symbol_name, symbol_type, parent_name, start_line, end_line, "
            "       risk_level, signature "
            "FROM symbols WHERE file_path = ? AND symbol_type != 'file' "
            "ORDER BY start_line",
            (path,)
        ).fetchall()
        return [dict(r) for r in rows]


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

BUDGET_TOKENS = 8000


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
        total_tokens = 0
        truncated_names = []
        for sym in symbols:
            sym_tokens = sym.get("token_count", 0) or 0
            total_tokens += sym_tokens
            if total_tokens > BUDGET_TOKENS and results:
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


def get_symbols_meta_tool(params: dict) -> str:
    rag = _get_rag()
    if rag is None:
        return "Codebase atlas not found."
    rag.ensure_indexed()
    names = params.get("names", [])
    if isinstance(names, str):
        names = [names]
    if not names:
        return "Error: 'names' (list) parameter is required."
    file_path = params.get("file_path")
    symbols = rag.get_symbols_meta(names, file_path)
    for s in symbols:
        if s.get("docstring") and len(s["docstring"]) > 200:
            s["docstring"] = s["docstring"][:200] + "..."
    found_names = {s["symbol_name"] for s in symbols}
    missing_names = [n for n in names if n not in found_names]
    output = {"symbols": symbols}
    if missing_names:
        output["missing_names"] = missing_names
        output["hint"] = "Use search_symbols for misspelled names."
    return json.dumps(output, indent=2)


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


def get_index_info_tool(params: dict) -> str:
    rag = _get_rag()
    if rag is None:
        return "Codebase atlas not found."
    if not rag.ensure_indexed():
        return "Code RAG database not found or not indexed."
    info = rag.get_index_info()
    return json.dumps(info, indent=2)


def file_api_tool(params: dict) -> str:
    rag = _get_rag()
    if rag is None:
        return "Codebase atlas not found."
    if not rag.ensure_indexed():
        return "Code RAG database not found or not indexed."
    path = params.get("path", "")
    if not path:
        return "Error: 'path' parameter is required."
    resolved = _resolve_path(path)
    result = rag.file_api(resolved)
    if result["total_api_symbols"] == 0:
        return json.dumps({"file_path": resolved, "note": "No symbols found. File may not be indexed."}, indent=2)
    return json.dumps(result, indent=2)


def call_chain_tool(params: dict) -> str:
    rag = _get_rag()
    if rag is None:
        return "Codebase atlas not found."
    if not rag.ensure_indexed():
        return "Code RAG database not found or not indexed."
    start_fn = params.get("start_fn", "")
    end_module = params.get("end_module", "")
    if not start_fn or not end_module:
        return "Error: 'start_fn' and 'end_module' parameters are required."
    file_path = params.get("file_path")
    result = rag.call_chain(start_fn, end_module, file_path)
    if "error" in result:
        return result["error"]
    return json.dumps(result, indent=2)


def compare_apis_tool(params: dict) -> str:
    rag = _get_rag()
    if rag is None:
        return "Codebase atlas not found."
    if not rag.ensure_indexed():
        return "Code RAG database not found or not indexed."
    path_a = params.get("path_a", "")
    path_b = params.get("path_b", "")
    if not path_a or not path_b:
        return "Error: 'path_a' and 'path_b' parameters are required."
    result = rag.compare_apis(_resolve_path(path_a), _resolve_path(path_b))
    return json.dumps(result, indent=2)


def symbols_by_file_tool(params: dict) -> str:
    rag = _get_rag()
    if rag is None:
        return "Codebase atlas not found."
    if not rag.ensure_indexed():
        return "Code RAG database not found or not indexed."
    path = params.get("path", "")
    if not path:
        return "Error: 'path' parameter is required."
    resolved = _resolve_path(path)
    result = rag.symbols_by_file(resolved)
    if not result:
        return json.dumps({"file_path": resolved, "symbols": [], "note": "No symbols found for this file."}, indent=2)
    return json.dumps({"file_path": resolved, "symbols": result, "count": len(result)}, indent=2)
