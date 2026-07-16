import sqlite3
import json
import os
import ast
from pathlib import Path
from typing import Optional, List, Dict, Any

from agent_core.config import CODEBASE_ATLAS_DIR as _CONFIG_ATLAS_DIR, CODEBASE_ROOT as _CODEBASE_ROOT

DB_FILENAME = "code_rag.db"


class _SymbolVisitor(ast.NodeVisitor):
    def __init__(self, lines: List[str]):
        self.lines = lines
        self.symbols: List[Dict[str, Any]] = []
        self._class_stack: List[str] = []

    def visit_ClassDef(self, node: ast.ClassDef):
        self._class_stack.append(node.name)
        start = node.lineno
        end = getattr(node, 'end_lineno', start)
        code = '\n'.join(self.lines[start-1:end])
        docstring = ast.get_docstring(node) or ''
        self.symbols.append({
            "symbol_name": node.name,
            "symbol_type": "class",
            "parent_name": "",
            "signature": f"class {node.name}",
            "docstring": docstring,
            "code": code,
            "start_line": start,
            "end_line": end,
        })
        self.generic_visit(node)
        self._class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._extract_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._extract_function(node)

    def _extract_function(self, node):
        name = node.name
        start = node.lineno
        end = getattr(node, 'end_lineno', start)
        code = '\n'.join(self.lines[start-1:end])
        docstring = ast.get_docstring(node) or ''
        parent_name = self._class_stack[-1] if self._class_stack else ""
        args = [a.arg for a in node.args.args]
        signature = f"{name}({', '.join(args)})"
        self.symbols.append({
            "symbol_name": name,
            "symbol_type": "method" if parent_name else "function",
            "parent_name": parent_name,
            "signature": signature,
            "docstring": docstring,
            "code": code,
            "start_line": start,
            "end_line": end,
        })
        self.generic_visit(node)


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
        conn = self._get_conn()
        self._init_schema(conn)
        cur = conn.execute("SELECT value FROM meta WHERE key = 'ingested'")
        if cur.fetchone():
            return False
        self._ingest(conn)
        return True

    def needs_index(self) -> bool:
        graph_path = self.atlas_dir / "graphdata.json"
        if not graph_path.exists():
            return True
        conn = self._get_conn()
        self._init_schema(conn)
        cur = conn.execute("SELECT value FROM meta WHERE key = 'ingested'")
        return cur.fetchone() is None

    def _init_schema(self, conn: sqlite3.Connection):
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS symbols (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                symbol_name TEXT NOT NULL,
                symbol_type TEXT NOT NULL,
                parent_name TEXT,
                signature TEXT,
                docstring TEXT,
                code TEXT,
                start_line INTEGER,
                end_line INTEGER,
                risk_level TEXT DEFAULT 'none',
                entry_point INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS call_edges (
                source_id INTEGER NOT NULL,
                target_id INTEGER NOT NULL,
                edge_type TEXT NOT NULL,
                PRIMARY KEY (source_id, target_id, edge_type),
                FOREIGN KEY (source_id) REFERENCES symbols(id),
                FOREIGN KEY (target_id) REFERENCES symbols(id)
            );
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_sym_name ON symbols(symbol_name);
            CREATE INDEX IF NOT EXISTS idx_sym_file ON symbols(file_path);
            CREATE INDEX IF NOT EXISTS idx_call_source ON call_edges(source_id);
            CREATE INDEX IF NOT EXISTS idx_call_target ON call_edges(target_id);
        """)
        try:
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS symbols_fts USING fts5(
                    symbol_name, docstring, code, file_path,
                    tokenize='porter'
                )
            """)
        except sqlite3.OperationalError:
            pass

    def _ingest(self, conn: sqlite3.Connection):
        graph_path = self.atlas_dir / "graphdata.json"
        if not graph_path.exists():
            return

        with open(graph_path) as f:
            graph = json.load(f)

        file_refs: Dict[str, str] = {}
        for node in graph.get("nodes", []):
            if node.get("type") == "file":
                file_refs[node["id"]] = node["metadata"]["path"]

        name_to_id: Dict[tuple, int] = {}

        for file_ref, file_path in sorted(file_refs.items()):
            if not os.path.isfile(file_path):
                continue
            ext = os.path.splitext(file_path)[1]
            if ext == ".py":
                symbols = self._parse_python(file_path)
            else:
                symbols = self._parse_generic(file_path)

            for sym in symbols:
                sym["file_path"] = file_path
                cur = conn.execute(
                    """INSERT INTO symbols
                       (file_path, symbol_name, symbol_type, parent_name,
                        signature, docstring, code, start_line, end_line)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (sym["file_path"], sym["symbol_name"], sym["symbol_type"],
                     sym["parent_name"], sym["signature"],
                     sym["docstring"], sym["code"],
                     sym["start_line"], sym["end_line"])
                )
                sym_id = cur.lastrowid
                key = (file_path, sym["symbol_name"], sym["parent_name"])
                name_to_id[key] = sym_id

                conn.execute(
                    "INSERT INTO symbols_fts (rowid, symbol_name, docstring, code, file_path) VALUES (?, ?, ?, ?, ?)",
                    (sym_id, sym["symbol_name"], sym["docstring"], sym["code"], file_path)
                )

        func_node_to_sym: Dict[str, int] = {}
        for node in graph.get("nodes", []):
            if node.get("type") != "function":
                continue
            meta = node.get("metadata", {})
            func_name = meta.get("function_name", "")
            file_ref = meta.get("file_ref", "")
            file_path = file_refs.get(file_ref, "")
            key = (file_path, func_name, "")
            sym_id = name_to_id.get(key)
            if sym_id is None:
                key = (file_path, func_name, "")
                sym_id = name_to_id.get(key)
            if sym_id:
                func_node_to_sym[node["id"]] = sym_id
                risk = node.get("risk_level", "none")
                entry = 1 if node.get("entry_point") else 0
                conn.execute(
                    "UPDATE symbols SET risk_level = ?, entry_point = ? WHERE id = ?",
                    (risk, entry, sym_id)
                )

        for edge in graph.get("edges", []):
            if edge.get("type") != "calls":
                continue
            source_id = func_node_to_sym.get(edge["source"])
            target_id = func_node_to_sym.get(edge["target"])
            if source_id is not None and target_id is not None:
                try:
                    conn.execute(
                        "INSERT INTO call_edges (source_id, target_id, edge_type) VALUES (?, ?, ?)",
                        (source_id, target_id, "calls")
                    )
                except sqlite3.IntegrityError:
                    pass

        conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('ingested', '1')")
        conn.commit()

    def _parse_python(self, file_path: str) -> List[Dict[str, Any]]:
        with open(file_path, encoding='utf-8') as f:
            source = f.read()
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return self._parse_generic(file_path)
        lines = source.split('\n')
        visitor = _SymbolVisitor(lines)
        visitor.visit(tree)
        return visitor.symbols

    def _parse_generic(self, file_path: str) -> List[Dict[str, Any]]:
        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return []
        name = os.path.basename(file_path)
        lines = content.split('\n')
        return [{
            "symbol_name": name,
            "symbol_type": "file",
            "parent_name": "",
            "signature": "",
            "docstring": "",
            "code": content,
            "start_line": 1,
            "end_line": len(lines),
        }]

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
