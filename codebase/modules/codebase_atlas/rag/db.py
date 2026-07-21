"""Code RAG database operations — schema init, symbol insertion, call edges."""

import sys
import sqlite3
from pathlib import Path
from typing import Dict, Tuple

from ..graph.backend.graph_models import GraphData

try:
    from agent_tools.atlas_tools.token_count import count_tokens_string
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    from agent_tools.atlas_tools.token_count import count_tokens_string

DB_FILENAME = "code_rag.db"


def init_schema(conn: sqlite3.Connection):
    conn.executescript("""
        DROP TABLE IF EXISTS symbols_fts;
        DROP TABLE IF EXISTS call_edges;
        DROP TABLE IF EXISTS symbols;
        DROP TABLE IF EXISTS meta;
        CREATE TABLE symbols (
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
            entry_point INTEGER DEFAULT 0,
            token_count INTEGER DEFAULT 0
        );
        CREATE TABLE call_edges (
            source_id INTEGER NOT NULL,
            target_id INTEGER NOT NULL,
            edge_type TEXT NOT NULL,
            PRIMARY KEY (source_id, target_id, edge_type),
            FOREIGN KEY (source_id) REFERENCES symbols(id),
            FOREIGN KEY (target_id) REFERENCES symbols(id)
        );
        CREATE TABLE meta (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        CREATE INDEX idx_sym_name ON symbols(symbol_name);
        CREATE INDEX idx_sym_file ON symbols(file_path);
        CREATE INDEX idx_call_source ON call_edges(source_id);
        CREATE INDEX idx_call_target ON call_edges(target_id);
    """)
    try:
        conn.execute("""
            CREATE VIRTUAL TABLE symbols_fts USING fts5(
                symbol_name, docstring, code, file_path,
                tokenize='porter'
            )
        """)
    except sqlite3.OperationalError:
        pass
    conn.commit()


def insert_function(
    conn: sqlite3.Connection,
    file_path: str,
    func,
    parent_name: str,
    name_to_id: Dict[Tuple[str, str], int],
) -> int:
    args_str = ', '.join(a[0] for a in func.args)
    signature = f"{func.name}({args_str})"
    docstring = func.docstring or ""
    start_line = func.line_number
    end_line = start_line + func.source_code.count('\n') if func.source_code else start_line
    tok_count = count_tokens_string(func.source_code) if func.source_code else 0

    cur = conn.execute(
        """INSERT INTO symbols
           (file_path, symbol_name, symbol_type, parent_name,
            signature, docstring, code, start_line, end_line,
            risk_level, entry_point, token_count)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (file_path, func.name,
         "method" if parent_name else "function",
         parent_name, signature, docstring,
         func.source_code, start_line, end_line,
         func.risk_level.value if func.risk_level else "none",
         1 if func.is_entry else 0,
         tok_count)
    )
    sym_id = cur.lastrowid
    name_to_id[(file_path, func.name)] = sym_id

    try:
        conn.execute(
            "INSERT INTO symbols_fts (rowid, symbol_name, docstring, code, file_path) VALUES (?, ?, ?, ?, ?)",
            (sym_id, func.name, docstring, func.source_code, file_path)
        )
    except sqlite3.OperationalError:
        pass
    return sym_id


def insert_class(
    conn: sqlite3.Connection,
    file_path: str,
    cls,
    name_to_id: Dict[Tuple[str, str], int],
) -> int:
    docstring = cls.docstring or ""
    start_line = cls.line_number
    end_line = start_line + cls.source_code.count('\n') if cls.source_code else start_line
    signature = f"class {cls.name}"
    tok_count = count_tokens_string(cls.source_code) if cls.source_code else 0

    cur = conn.execute(
        """INSERT INTO symbols
           (file_path, symbol_name, symbol_type, parent_name,
            signature, docstring, code, start_line, end_line,
            token_count)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (file_path, cls.name, "class", "",
         signature, docstring, cls.source_code,
         start_line, end_line, tok_count)
    )
    sym_id = cur.lastrowid
    name_to_id[(file_path, cls.name)] = sym_id

    try:
        conn.execute(
            "INSERT INTO symbols_fts (rowid, symbol_name, docstring, code, file_path) VALUES (?, ?, ?, ?, ?)",
            (sym_id, cls.name, docstring, cls.source_code, file_path)
        )
    except sqlite3.OperationalError:
        pass
    return sym_id


def insert_file_as_symbol(
    conn: sqlite3.Connection,
    file_path: str,
    name_to_id: Dict[Tuple[str, str], int],
) -> int:
    try:
        content = Path(file_path).read_text(encoding='utf-8')
    except Exception:
        return 0
    name = Path(file_path).name
    lines = content.split('\n')
    tok_count = count_tokens_string(content)

    cur = conn.execute(
        """INSERT INTO symbols
           (file_path, symbol_name, symbol_type, parent_name,
            signature, docstring, code, start_line, end_line,
            token_count)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (file_path, name, "file", "",
         "", "", content, 1, len(lines), tok_count)
    )
    sym_id = cur.lastrowid
    name_to_id[(file_path, name)] = sym_id

    try:
        conn.execute(
            "INSERT INTO symbols_fts (rowid, symbol_name, docstring, code, file_path) VALUES (?, ?, ?, ?, ?)",
            (sym_id, name, "", content, file_path)
        )
    except sqlite3.OperationalError:
        pass
    return sym_id


def insert_file_symbols(
    conn: sqlite3.Connection,
    file_path: str,
    file_info,
    name_to_id: Dict[Tuple[str, str], int],
):
    is_python = file_path.endswith(".py")

    if is_python and file_info.error is None and (file_info.functions or file_info.classes):
        for func in file_info.functions:
            insert_function(conn, file_path, func, "", name_to_id)
        for cls in file_info.classes:
            insert_class(conn, file_path, cls, name_to_id)
            for method in cls.methods:
                insert_function(conn, file_path, method, cls.name, name_to_id)
    else:
        insert_file_as_symbol(conn, file_path, name_to_id)


def update_from_graph(
    conn: sqlite3.Connection,
    unified_graph: GraphData,
    name_to_id: Dict[Tuple[str, str], int],
):
    """Update risk/entry levels and insert call edges from graph data."""
    file_refs = {
        n.id: n.metadata.get("path", "")
        for n in unified_graph.nodes.values()
        if n.node_type.value == "file"
    }
    func_node_to_sym: Dict[str, int] = {}
    for node in unified_graph.nodes.values():
        if node.node_type.value != "function":
            continue
        func_name = node.metadata.get("function_name", "")
        file_ref = node.metadata.get("file_ref", "")
        file_path = file_refs.get(file_ref, "")
        sym_id = name_to_id.get((file_path, func_name))
        if sym_id is not None:
            func_node_to_sym[node.id] = sym_id
            risk = node.risk_level.value if node.risk_level else "none"
            entry = 1 if node.entry_point else 0
            conn.execute(
                "UPDATE symbols SET risk_level = ?, entry_point = ? WHERE id = ?",
                (risk, entry, sym_id)
            )

    edge_count = 0
    for edge in unified_graph.edges.values():
        if edge.edge_type.value != "calls":
            continue
        source_id = func_node_to_sym.get(edge.source)
        target_id = func_node_to_sym.get(edge.target)
        if source_id is not None and target_id is not None:
            try:
                conn.execute(
                    "INSERT INTO call_edges (source_id, target_id, edge_type) VALUES (?, ?, ?)",
                    (source_id, target_id, "calls")
                )
                edge_count += 1
            except sqlite3.IntegrityError:
                pass

    conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('ingested', '1')")
    conn.commit()
    return edge_count
