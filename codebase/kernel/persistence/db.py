from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from kernel.config.kernel_config import DATA_ROOT
from kernel.utils.logger import get_child_logger

logger = get_child_logger("kernel_db")

DB_PATH = DATA_ROOT / "kernel.db"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    level TEXT NOT NULL,
    module TEXT NOT NULL,
    message TEXT NOT NULL,
    context_json TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS semantic_nodes (
    node_id TEXT PRIMARY KEY,
    node_type TEXT NOT NULL,
    title TEXT DEFAULT '',
    content TEXT DEFAULT '',
    concepts_json TEXT DEFAULT '[]',
    tags_json TEXT DEFAULT '[]',
    importance REAL DEFAULT 0.5,
    confidence REAL DEFAULT 1.0,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    topic_id TEXT DEFAULT '',
    embedding BLOB,
    metadata_json TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS semantic_edges (
    edge_id TEXT PRIMARY KEY,
    source_node_id TEXT NOT NULL,
    target_node_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    confidence REAL DEFAULT 1.0,
    created_at REAL NOT NULL,
    topic_id TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS patterns (
    pattern_id TEXT PRIMARY KEY,
    pattern_type TEXT NOT NULL,
    category TEXT DEFAULT 'general',
    title TEXT DEFAULT '',
    description TEXT DEFAULT '',
    source_ids_json TEXT DEFAULT '[]',
    confidence REAL DEFAULT 1.0,
    importance REAL DEFAULT 0.5,
    created_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS hypotheses (
    hypothesis_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    hypothesis_type TEXT NOT NULL,
    category TEXT DEFAULT 'general',
    confidence REAL DEFAULT 0.5,
    status TEXT DEFAULT 'proposed',
    supporting_json TEXT DEFAULT '[]',
    contradicting_json TEXT DEFAULT '[]',
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS generic_memory (
    memory_id TEXT PRIMARY KEY,
    memory_type TEXT NOT NULL,
    data_json TEXT NOT NULL,
    created_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS working_memory (
    memory_id TEXT PRIMARY KEY,
    memory_type TEXT NOT NULL,
    content_json TEXT DEFAULT '{}',
    importance REAL DEFAULT 0.5,
    confidence REAL DEFAULT 1.0,
    ttl_seconds REAL DEFAULT 3600,
    created_at REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level);
CREATE INDEX IF NOT EXISTS idx_logs_module ON logs(module);
CREATE INDEX IF NOT EXISTS idx_logs_ts ON logs(ts);
CREATE INDEX IF NOT EXISTS idx_semantic_nodes_type ON semantic_nodes(node_type);
CREATE INDEX IF NOT EXISTS idx_semantic_nodes_topic ON semantic_nodes(topic_id);
CREATE INDEX IF NOT EXISTS idx_semantic_edges_relation ON semantic_edges(relation_type);
CREATE INDEX IF NOT EXISTS idx_semantic_edges_source ON semantic_edges(source_node_id);
CREATE INDEX IF NOT EXISTS idx_semantic_edges_target ON semantic_edges(target_node_id);
CREATE INDEX IF NOT EXISTS idx_semantic_edges_topic ON semantic_edges(topic_id);
CREATE INDEX IF NOT EXISTS idx_patterns_type ON patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_hypotheses_type ON hypotheses(hypothesis_type);
CREATE INDEX IF NOT EXISTS idx_hypotheses_status ON hypotheses(status);
CREATE INDEX IF NOT EXISTS idx_working_memory_type ON working_memory(memory_type);
CREATE INDEX IF NOT EXISTS idx_generic_memory_type ON generic_memory(memory_type);

CREATE TABLE IF NOT EXISTS tool_stats (
    tool_name TEXT PRIMARY KEY,
    call_count INTEGER DEFAULT 1,
    last_called_at REAL NOT NULL,
    total_duration_ms REAL DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    output_chars INTEGER DEFAULT 0,
    token_estimate INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS file_access (
    file_path TEXT NOT NULL,
    operation TEXT NOT NULL,
    access_count INTEGER DEFAULT 1,
    last_accessed_at REAL NOT NULL,
    PRIMARY KEY (file_path, operation)
);

CREATE TABLE IF NOT EXISTS daily_read_budget (
    date TEXT PRIMARY KEY,
    lines_used INTEGER DEFAULT 0,
    budget INTEGER DEFAULT 500
);

CREATE TABLE IF NOT EXISTS citation_cache (
    hypothesis_id TEXT PRIMARY KEY,
    evidence_path TEXT NOT NULL,
    evidence_symbol TEXT NOT NULL,
    file_mtime REAL,
    status TEXT NOT NULL,
    updated_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS simulation_versions (
    version_id TEXT PRIMARY KEY,
    simulator TEXT DEFAULT 'popula_dyn',
    parent_version_id TEXT DEFAULT NULL,
    code_hash TEXT DEFAULT '',
    created_at REAL NOT NULL,
    change_reason TEXT DEFAULT '',
    change_summary TEXT DEFAULT '',
    affected_concepts_json TEXT DEFAULT '[]',
    git_branch TEXT DEFAULT '',
    git_message TEXT DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_sim_versions_sim ON simulation_versions(simulator);

CREATE TABLE IF NOT EXISTS simulation_runs (
    run_id TEXT PRIMARY KEY,
    simulator TEXT DEFAULT 'popula_dyn',
    version_id TEXT NOT NULL,
    parameters_json TEXT DEFAULT '{}',
    baseline_run_id TEXT DEFAULT NULL,
    result_json TEXT DEFAULT '{}',
    horizon INTEGER DEFAULT 0,
    status TEXT DEFAULT 'completed',
    created_at REAL NOT NULL,
    FOREIGN KEY(version_id) REFERENCES simulation_versions(version_id)
);

CREATE INDEX IF NOT EXISTS idx_sim_runs_version ON simulation_runs(version_id);

CREATE TABLE IF NOT EXISTS workflow_states (
    simulator TEXT PRIMARY KEY,
    current TEXT NOT NULL,
    history_json TEXT DEFAULT '[]',
    outputs_json TEXT DEFAULT '{}',
    updated_at REAL NOT NULL
);
"""


class KernelDB:
    def __init__(self, db_path: str | Path = DB_PATH, read_only: bool = False):
        self.db_path = Path(db_path)
        self.read_only = read_only
        if not read_only:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None
        self._ro_conn: sqlite3.Connection | None = None
        if not read_only:
            self._init_db()

    @property
    def conn(self) -> sqlite3.Connection:
        if self.read_only:
            return self.ro_conn
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
        return self._conn

    @property
    def ro_conn(self) -> sqlite3.Connection:
        if self._ro_conn is None:
            if not self.db_path.exists():
                # open in-memory empty DB for inspection when file missing
                self._ro_conn = sqlite3.connect(":memory:")
                self._ro_conn.row_factory = sqlite3.Row
                return self._ro_conn
            uri = f"file:{self.db_path}?mode=ro"
            self._ro_conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
            self._ro_conn.row_factory = sqlite3.Row
            try:
                self._ro_conn.execute("PRAGMA query_only=ON")
            except Exception:
                pass
        return self._ro_conn

    def _init_db(self):
        if self.read_only:
            return
        for statement in SCHEMA_SQL.split(";"):
            stripped = statement.strip()
            if stripped:
                try:
                    self.conn.execute(stripped)
                except sqlite3.OperationalError:
                    pass
        for col_sql in [
            "ALTER TABLE semantic_nodes ADD COLUMN topic_id TEXT DEFAULT ''",
            "ALTER TABLE semantic_edges ADD COLUMN topic_id TEXT DEFAULT ''",
            "ALTER TABLE tool_stats ADD COLUMN output_chars INTEGER DEFAULT 0",
            "ALTER TABLE tool_stats ADD COLUMN token_estimate INTEGER DEFAULT 0",
            "ALTER TABLE semantic_nodes ADD COLUMN embedding BLOB",
            "ALTER TABLE semantic_nodes ADD COLUMN metadata_json TEXT DEFAULT '{}'",
            "ALTER TABLE simulation_versions ADD COLUMN git_branch TEXT DEFAULT ''",
            "ALTER TABLE simulation_versions ADD COLUMN git_message TEXT DEFAULT ''",
            "ALTER TABLE simulation_versions ADD COLUMN simulator TEXT DEFAULT 'popula_dyn'",
            "ALTER TABLE simulation_runs ADD COLUMN simulator TEXT DEFAULT 'popula_dyn'",
        ]:
            try:
                self.conn.execute(col_sql)
            except sqlite3.OperationalError:
                pass
        self.conn.commit()

    def close(self):
        if self._conn is not None:
            self._conn.close()
            self._conn = None
        if self._ro_conn is not None:
            try:
                self._ro_conn.close()
            except Exception:
                pass
            self._ro_conn = None

    # --- LOGS ---

    def insert_log(
        self,
        level: str,
        module: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> int:
        cur = self.conn.execute(
            "INSERT INTO logs (ts, level, module, message, context_json) VALUES (?, ?, ?, ?, ?)",
            (time.time(), level, module, message, json.dumps(context or {})),
        )
        self.conn.commit()
        return cur.lastrowid

    def query_logs(
        self,
        level: Optional[str] = None,
        module: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        clauses: List[str] = []
        params: List[Any] = []
        if level:
            clauses.append("level = ?")
            params.append(level)
        if module:
            clauses.append("module = ?")
            params.append(module)
        where = " AND ".join(clauses) if clauses else "1"
        rows = self.conn.execute(
            f"SELECT * FROM logs WHERE {where} ORDER BY ts DESC LIMIT ? OFFSET ?",
            (*params, limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]

    # --- SEMANTIC NODES ---

    def save_semantic_node(
        self,
        node_id: str,
        node_type: str,
        title: str = "",
        content: str = "",
        concepts: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        importance: float = 0.5,
        confidence: float = 1.0,
        created_at: Optional[float] = None,
        updated_at: Optional[float] = None,
        topic_id: str = "",
        embedding: Optional[bytes] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        now = time.time()
        self.conn.execute(
            """INSERT OR REPLACE INTO semantic_nodes
               (node_id, node_type, title, content, concepts_json, tags_json,
                importance, confidence, created_at, updated_at, topic_id, embedding, metadata_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                node_id,
                node_type,
                title,
                content,
                json.dumps(concepts or []),
                json.dumps(tags or []),
                importance,
                confidence,
                created_at or now,
                updated_at or now,
                topic_id,
                embedding,
                json.dumps(metadata or {}),
            ),
        )
        self.conn.commit()

    def save_semantic_embedding(self, node_id: str, embedding: bytes):
        self.conn.execute(
            "UPDATE semantic_nodes SET embedding = ? WHERE node_id = ?", (embedding, node_id)
        )
        self.conn.commit()

    def load_semantic_embedding(self, node_id: str) -> Optional[bytes]:
        row = self.conn.execute(
            "SELECT embedding FROM semantic_nodes WHERE node_id = ?", (node_id,)
        ).fetchone()
        return bytes(row["embedding"]) if row and row["embedding"] is not None else None

    def load_all_embeddings(self) -> List[Tuple[str, bytes]]:
        rows = self.conn.execute(
            "SELECT node_id, embedding FROM semantic_nodes WHERE embedding IS NOT NULL"
        ).fetchall()
        return [(r["node_id"], bytes(r["embedding"])) for r in rows]

    def load_semantic_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        row = self.conn.execute(
            "SELECT * FROM semantic_nodes WHERE node_id = ?", (node_id,)
        ).fetchone()
        if not row:
            return None
        return self._row_to_node(dict(row))

    def load_all_semantic_nodes(self) -> List[Dict[str, Any]]:
        rows = self.conn.execute("SELECT * FROM semantic_nodes").fetchall()
        return [self._row_to_node(dict(r)) for r in rows]

    def load_semantic_nodes_by_topic(self, topic_id: str) -> List[Dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM semantic_nodes WHERE topic_id = ?", (topic_id,)
        ).fetchall()
        return [self._row_to_node(dict(r)) for r in rows]

    def search_semantic_nodes(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        like = f"%{query}%"
        rows = self.conn.execute(
            """SELECT * FROM semantic_nodes
               WHERE title LIKE ? OR content LIKE ?
               ORDER BY importance DESC LIMIT ?""",
            (like, like, limit),
        ).fetchall()
        return [self._row_to_node(dict(r)) for r in rows]

    def delete_semantic_node(self, node_id: str) -> bool:
        cur = self.conn.execute("DELETE FROM semantic_nodes WHERE node_id = ?", (node_id,))
        self.conn.commit()
        return cur.rowcount > 0

    def delete_semantic_edge(self, edge_id: str) -> bool:
        cur = self.conn.execute("DELETE FROM semantic_edges WHERE edge_id = ?", (edge_id,))
        self.conn.commit()
        return cur.rowcount > 0

    def delete_semantic_nodes_by_topic(self, topic_id: str) -> int:
        cur = self.conn.execute("DELETE FROM semantic_nodes WHERE topic_id = ?", (topic_id,))
        self.conn.commit()
        return cur.rowcount

    def delete_semantic_edges_by_topic(self, topic_id: str) -> int:
        cur = self.conn.execute("DELETE FROM semantic_edges WHERE topic_id = ?", (topic_id,))
        self.conn.commit()
        return cur.rowcount

    @staticmethod
    def _row_to_node(row: Dict[str, Any]) -> Dict[str, Any]:
        row["concepts"] = json.loads(row.pop("concepts_json", "[]"))
        row["tags"] = json.loads(row.pop("tags_json", "[]"))
        row["topic_id"] = row.get("topic_id", "")
        try:
            row["metadata"] = json.loads(row.pop("metadata_json", "{}") or "{}")
        except Exception:
            row["metadata"] = {}
        # keep raw json for debug but ensure dict
        if not isinstance(row.get("metadata"), dict):
            row["metadata"] = {}
        return row

    # --- SEMANTIC EDGES ---

    def save_semantic_edge(
        self,
        edge_id: str,
        source_node_id: str,
        target_node_id: str,
        relation_type: str,
        weight: float = 1.0,
        confidence: float = 1.0,
        created_at: Optional[float] = None,
        topic_id: str = "",
    ):
        self.conn.execute(
            """INSERT OR REPLACE INTO semantic_edges
               (edge_id, source_node_id, target_node_id, relation_type,
                weight, confidence, created_at, topic_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                edge_id,
                source_node_id,
                target_node_id,
                relation_type,
                weight,
                confidence,
                created_at or time.time(),
                topic_id,
            ),
        )
        self.conn.commit()

    def load_semantic_edge(self, edge_id: str) -> Optional[Dict[str, Any]]:
        row = self.conn.execute(
            "SELECT * FROM semantic_edges WHERE edge_id = ?", (edge_id,)
        ).fetchone()
        return dict(row) if row else None

    def get_edges_by_type(self, relation_type: str) -> List[Dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM semantic_edges WHERE relation_type = ?", (relation_type,)
        ).fetchall()
        return [dict(r) for r in rows]

    def load_all_semantic_edges(self) -> List[Dict[str, Any]]:
        rows = self.conn.execute("SELECT * FROM semantic_edges").fetchall()
        return [dict(r) for r in rows]

    def load_semantic_edges_by_topic(self, topic_id: str) -> List[Dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM semantic_edges WHERE topic_id = ?", (topic_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    # --- PATTERNS ---

    def save_pattern(
        self,
        pattern_id: str,
        pattern_type: str,
        category: str = "general",
        title: str = "",
        description: str = "",
        source_ids: Optional[List[str]] = None,
        confidence: float = 1.0,
        importance: float = 0.5,
        created_at: Optional[float] = None,
    ):
        self.conn.execute(
            """INSERT OR REPLACE INTO patterns
               (pattern_id, pattern_type, category, title, description,
                source_ids_json, confidence, importance, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                pattern_id,
                pattern_type,
                category,
                title,
                description,
                json.dumps(source_ids or []),
                confidence,
                importance,
                created_at or time.time(),
            ),
        )
        self.conn.commit()

    def load_pattern(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        row = self.conn.execute(
            "SELECT * FROM patterns WHERE pattern_id = ?", (pattern_id,)
        ).fetchone()
        if not row:
            return None
        row = dict(row)
        row["source_ids"] = json.loads(row.pop("source_ids_json", "[]"))
        return row

    def list_patterns(self, pattern_type: Optional[str] = None) -> List[Dict[str, Any]]:
        if pattern_type:
            rows = self.conn.execute(
                "SELECT * FROM patterns WHERE pattern_type = ? ORDER BY created_at DESC",
                (pattern_type,),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM patterns ORDER BY created_at DESC"
            ).fetchall()
        result = []
        for r in rows:
            r = dict(r)
            r["source_ids"] = json.loads(r.pop("source_ids_json", "[]"))
            result.append(r)
        return result

    # --- HYPOTHESES ---

    def save_hypothesis(
        self,
        hypothesis_id: str,
        title: str,
        description: str = "",
        hypothesis_type: str = "generic",
        category: str = "general",
        confidence: float = 0.5,
        status: str = "proposed",
        supporting: Optional[List[str]] = None,
        contradicting: Optional[List[str]] = None,
        created_at: Optional[float] = None,
        updated_at: Optional[float] = None,
    ):
        now = time.time()
        self.conn.execute(
            """INSERT OR REPLACE INTO hypotheses
               (hypothesis_id, title, description, hypothesis_type, category,
                confidence, status, supporting_json, contradicting_json,
                created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                hypothesis_id,
                title,
                description,
                hypothesis_type,
                category,
                confidence,
                status,
                json.dumps(supporting or []),
                json.dumps(contradicting or []),
                created_at or now,
                updated_at or now,
            ),
        )
        self.conn.commit()

    def load_hypothesis(self, hypothesis_id: str) -> Optional[Dict[str, Any]]:
        row = self.conn.execute(
            "SELECT * FROM hypotheses WHERE hypothesis_id = ?", (hypothesis_id,)
        ).fetchone()
        if not row:
            return None
        row = dict(row)
        row["supporting_evidence"] = json.loads(row.pop("supporting_json", "[]"))
        row["contradicting_evidence"] = json.loads(row.pop("contradicting_json", "[]"))
        return row

    def load_all_hypotheses(self) -> List[Dict[str, Any]]:
        rows = self.conn.execute("SELECT * FROM hypotheses").fetchall()
        result = []
        for r in rows:
            r = dict(r)
            r["supporting_evidence"] = json.loads(r.pop("supporting_json", "[]"))
            r["contradicting_evidence"] = json.loads(r.pop("contradicting_json", "[]"))
            result.append(r)
        return result

    # --- WORKING MEMORY ---

    def save_working_memory(
        self,
        memory_id: str,
        memory_type: str,
        content: Dict[str, Any],
        importance: float = 0.5,
        confidence: float = 1.0,
        ttl_seconds: float = 3600,
        created_at: Optional[float] = None,
    ):
        self.conn.execute(
            """INSERT OR REPLACE INTO working_memory
               (memory_id, memory_type, content_json, importance, confidence,
                ttl_seconds, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                memory_id,
                memory_type,
                json.dumps(content),
                importance,
                confidence,
                ttl_seconds,
                created_at or time.time(),
            ),
        )
        self.conn.commit()

    def load_working_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        row = self.conn.execute(
            "SELECT * FROM working_memory WHERE memory_id = ?", (memory_id,)
        ).fetchone()
        if not row:
            return None
        row = dict(row)
        row["content"] = json.loads(row.pop("content_json", "{}"))
        return row

    def load_all_working_memory(self) -> List[Dict[str, Any]]:
        rows = self.conn.execute("SELECT * FROM working_memory").fetchall()
        result = []
        for r in rows:
            r = dict(r)
            r["content"] = json.loads(r.pop("content_json", "{}"))
            result.append(r)
        return result

    # --- GENERIC MEMORY (catch-all for episodic signals, events, and future types) ---

    def save_generic_memory(
        self,
        memory_id: str,
        memory_type: str,
        data: Dict[str, Any],
    ):
        self.conn.execute(
            """INSERT OR REPLACE INTO generic_memory
               (memory_id, memory_type, data_json, created_at)
               VALUES (?, ?, ?, ?)""",
            (memory_id, memory_type, json.dumps(data), time.time()),
        )
        self.conn.commit()

    def load_generic_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        row = self.conn.execute(
            "SELECT * FROM generic_memory WHERE memory_id = ?", (memory_id,)
        ).fetchone()
        if not row:
            return None
        row = dict(row)
        row["data"] = json.loads(row.pop("data_json", "{}"))
        return row

    def list_generic_memory_ids(self, memory_type: str) -> List[str]:
        rows = self.conn.execute(
            "SELECT memory_id FROM generic_memory WHERE memory_type = ? ORDER BY created_at",
            (memory_type,),
        ).fetchall()
        return [r["memory_id"] for r in rows]

    # --- CITATION CACHE (C7: skip re-resolution when cited files unchanged) ---

    def save_citation_cache(
        self,
        hypothesis_id: str,
        evidence_path: str,
        evidence_symbol: str,
        file_mtime: Optional[float],
        status: str,
    ):
        self.conn.execute(
            """INSERT OR REPLACE INTO citation_cache
               (hypothesis_id, evidence_path, evidence_symbol, file_mtime, status, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (hypothesis_id, evidence_path, evidence_symbol, file_mtime, status, time.time()),
        )
        self.conn.commit()

    def load_citation_cache(
        self,
        hypothesis_id: str,
    ) -> Optional[Dict[str, Any]]:
        row = self.conn.execute(
            "SELECT * FROM citation_cache WHERE hypothesis_id = ?", (hypothesis_id,)
        ).fetchone()
        return dict(row) if row else None

    def delete_generic_memory(self, memory_id: str) -> bool:
        cur = self.conn.execute(
            "DELETE FROM generic_memory WHERE memory_id = ?", (memory_id,)
        )
        self.conn.commit()
        return cur.rowcount > 0

    def generic_memory_exists(self, memory_id: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM generic_memory WHERE memory_id = ?", (memory_id,)
        ).fetchone()
        return row is not None

    # --- TOOL STATS ---

    def record_tool_call(self, tool_name: str, duration_ms: float = 0, is_error: bool = False, output_chars: int = 0):
        now = time.time()
        tokens = output_chars // 4
        self.conn.execute(
            """INSERT INTO tool_stats (tool_name, call_count, last_called_at, total_duration_ms, error_count, output_chars, token_estimate)
               VALUES (?, 1, ?, ?, ?, ?, ?)
               ON CONFLICT(tool_name) DO UPDATE SET
                   call_count = call_count + 1,
                   last_called_at = ?,
                   total_duration_ms = total_duration_ms + ?,
                   error_count = error_count + ?,
                   output_chars = output_chars + ?,
                   token_estimate = token_estimate + ?""",
            (tool_name, now, duration_ms, 1 if is_error else 0, output_chars, tokens,
             now, duration_ms, 1 if is_error else 0, output_chars, tokens),
        )
        self.conn.commit()

    def get_tool_stats(self) -> List[Dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT tool_name, call_count, last_called_at, total_duration_ms, error_count, "
            "output_chars, token_estimate, "
            "CASE WHEN call_count > 0 THEN total_duration_ms / call_count ELSE 0 END AS avg_duration_ms, "
            "CASE WHEN call_count > 0 THEN CAST(error_count AS REAL) / call_count ELSE 0 END AS error_rate, "
            "CASE WHEN call_count > 0 THEN output_chars / call_count ELSE 0 END AS avg_chars, "
            "CASE WHEN call_count > 0 THEN token_estimate / call_count ELSE 0 END AS avg_tokens "
            "FROM tool_stats ORDER BY call_count DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    # --- FILE ACCESS ---

    def record_file_access(self, file_path: str, operation: str):
        now = time.time()
        self.conn.execute(
            """INSERT INTO file_access (file_path, operation, access_count, last_accessed_at)
               VALUES (?, ?, 1, ?)
               ON CONFLICT(file_path, operation) DO UPDATE SET
                   access_count = access_count + 1,
                   last_accessed_at = ?""",
            (file_path, operation, now, now),
        )
        self.conn.commit()

    def get_file_stats(self, limit: int = 20) -> List[Dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT file_path, operation, access_count, last_accessed_at "
            "FROM file_access ORDER BY access_count DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    # --- DAILY READING BUDGET ---

    def record_llm_output_lines(self, lines: int):
        today = time.strftime("%Y-%m-%d")
        self.conn.execute(
            """INSERT INTO daily_read_budget (date, lines_used, budget)
               VALUES (?, ?, 500)
               ON CONFLICT(date) DO UPDATE SET
                   lines_used = lines_used + ?""",
            (today, lines, lines),
        )
        self.conn.commit()

    def get_daily_budget(self, date_str: Optional[str] = None) -> Dict[str, Any]:
        if date_str is None:
            date_str = time.strftime("%Y-%m-%d")
        row = self.conn.execute(
            "SELECT date, lines_used, budget FROM daily_read_budget WHERE date = ?",
            (date_str,),
        ).fetchone()
        if row:
            result = dict(row)
        else:
            result = {"date": date_str, "lines_used": 0, "budget": 500}
        result["remaining"] = max(0, result["budget"] - result["lines_used"])
        return result

    def reset_daily_budget(self, budget: int = 500):
        today = time.strftime("%Y-%m-%d")
        self.conn.execute(
            "INSERT INTO daily_read_budget (date, lines_used, budget) VALUES (?, 0, ?) "
            "ON CONFLICT(date) DO UPDATE SET lines_used = 0, budget = ?",
            (today, budget, budget),
        )
        self.conn.commit()

    # --- MAINTENANCE ---

    def vacuum(self):
        self.conn.execute("VACUUM")

    # --- SIMULATION LINEAGE (Phase 0 refactored — Git-backed, per-simulator) ---
    def save_simulation_version(self, version_id: str, parent_version_id: Optional[str], code_hash: str, change_reason: str = "", change_summary: str = "", affected_concepts: Optional[List[str]] = None, created_at: Optional[float] = None, git_branch: str = "", git_message: str = "", simulator: str = "popula_dyn"):
        self.conn.execute(
            """INSERT OR REPLACE INTO simulation_versions
               (version_id, simulator, parent_version_id, code_hash, created_at, change_reason, change_summary, affected_concepts_json, git_branch, git_message)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (version_id, simulator, parent_version_id, code_hash, created_at or time.time(), change_reason, change_summary, json.dumps(affected_concepts or []), git_branch, git_message),
        )
        self.conn.commit()

    def load_simulation_version(self, version_id: str, simulator: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if simulator:
            row = self.conn.execute("SELECT * FROM simulation_versions WHERE version_id=? AND simulator=?", (version_id, simulator)).fetchone()
        else:
            row = self.conn.execute("SELECT * FROM simulation_versions WHERE version_id=?", (version_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["affected_concepts"] = json.loads(d.pop("affected_concepts_json", "[]"))
        return d

    def load_all_simulation_versions(self, simulator: Optional[str] = None) -> List[Dict[str, Any]]:
        if simulator:
            rows = self.conn.execute("SELECT * FROM simulation_versions WHERE simulator=? ORDER BY created_at", (simulator,)).fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM simulation_versions ORDER BY created_at").fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["affected_concepts"] = json.loads(d.pop("affected_concepts_json", "[]"))
            out.append(d)
        return out

    def load_latest_version(self, simulator: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if simulator:
            row = self.conn.execute("SELECT * FROM simulation_versions WHERE simulator=? ORDER BY created_at DESC LIMIT 1", (simulator,)).fetchone()
        else:
            row = self.conn.execute("SELECT * FROM simulation_versions ORDER BY created_at DESC LIMIT 1").fetchone()
        if not row:
            return None
        d = dict(row)
        d["affected_concepts"] = json.loads(d.pop("affected_concepts_json", "[]"))
        return d

    def save_simulation_run(self, run_id: str, version_id: str, parameters: Dict[str, Any], baseline_run_id: Optional[str], result: Dict[str, Any], horizon: int = 0, status: str = "completed", created_at: Optional[float] = None, simulator: str = "popula_dyn"):
        self.conn.execute(
            """INSERT OR REPLACE INTO simulation_runs
               (run_id, simulator, version_id, parameters_json, baseline_run_id, result_json, horizon, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (run_id, simulator, version_id, json.dumps(parameters or {}), baseline_run_id, json.dumps(result or {}), horizon, status, created_at or time.time()),
        )
        self.conn.commit()

    def load_simulation_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        row = self.conn.execute("SELECT * FROM simulation_runs WHERE run_id=?", (run_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["parameters"] = json.loads(d.pop("parameters_json", "{}"))
        d["result"] = json.loads(d.pop("result_json", "{}"))
        return d

    def save_workflow_state(self, simulator: str, current: str, history: List[str], outputs: Dict[str, Any]):
        self.conn.execute(
            """INSERT OR REPLACE INTO workflow_states (simulator, current, history_json, outputs_json, updated_at)
               VALUES (?, ?, ?, ?, ?)""",
            (simulator, current, json.dumps(history), json.dumps(outputs), time.time()),
        )
        self.conn.commit()

    def load_workflow_state(self, simulator: str) -> Optional[Dict[str, Any]]:
        row = self.conn.execute("SELECT * FROM workflow_states WHERE simulator=?", (simulator,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["history"] = json.loads(d.pop("history_json", "[]"))
        d["outputs"] = json.loads(d.pop("outputs_json", "{}"))
        return d

    def stats(self) -> Dict[str, int]:
        counts = {}
        for table in [
            "logs",
            "semantic_nodes",
            "semantic_edges",
            "patterns",
            "hypotheses",
            "working_memory",
            "generic_memory",
            "tool_stats",
            "file_access",
            "daily_read_budget",
            "simulation_versions",
            "simulation_runs",
            "workflow_states",
        ]:
            row = self.conn.execute(
                f"SELECT COUNT(*) as cnt FROM {table}"
            ).fetchone()
            counts[table] = row["cnt"] if row else 0
        return counts


kernel_db = KernelDB()
kernel_db_ro = KernelDB(read_only=True)
