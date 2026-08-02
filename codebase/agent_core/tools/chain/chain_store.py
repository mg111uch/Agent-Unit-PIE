"""ChainStore: SQLite persistence for chain specs, approval status, mining, and
the evolving workflow graph.

One persistence path (kernel.db, SQLite). Handwritten chains are synced here so
mined chains live alongside them; everything queryable through the same store.
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional

from agent_core.tools.chain.chain_spec import ChainSpec, Step


def _db():
    from kernel.persistence.db import kernel_db
    return kernel_db.conn


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS chain_specs (
    name TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    params_json TEXT NOT NULL DEFAULT '{}',
    steps_json TEXT NOT NULL DEFAULT '[]',
    budget_tokens INTEGER NOT NULL DEFAULT 16000,
    step_cap_chars INTEGER NOT NULL DEFAULT 8000,
    source TEXT NOT NULL DEFAULT 'handwritten',
    status TEXT NOT NULL DEFAULT 'approved',
    read_only INTEGER NOT NULL DEFAULT 1,
    use_count INTEGER NOT NULL DEFAULT 0,
    last_used_at REAL,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS chain_candidates (
    signature TEXT PRIMARY KEY,
    tool_seq_json TEXT NOT NULL,
    occurrences INTEGER NOT NULL DEFAULT 1,
    savings_est INTEGER NOT NULL DEFAULT 0,
    first_seen REAL NOT NULL,
    last_seen REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS tool_sequences (
    session_id TEXT PRIMARY KEY,
    seq_json TEXT NOT NULL,
    outcome TEXT NOT NULL DEFAULT '',
    ts REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS graph_clusters (
    id TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    chain_id TEXT NOT NULL DEFAULT '',
    color TEXT NOT NULL DEFAULT '#335533'
);

CREATE TABLE IF NOT EXISTS graph_nodes (
    id TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    shape TEXT NOT NULL DEFAULT 'rect',
    color TEXT NOT NULL DEFAULT '#ffffff',
    cluster_id TEXT NOT NULL DEFAULT '',
    chain_id TEXT NOT NULL DEFAULT '',
    stats_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS graph_edges (
    src TEXT NOT NULL,
    dst TEXT NOT NULL,
    label TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (src, dst)
);

CREATE TABLE IF NOT EXISTS graph_notes (
    section TEXT NOT NULL,
    text TEXT NOT NULL,
    tag TEXT NOT NULL DEFAULT 'do',
    ts REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS graph_state (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    version INTEGER NOT NULL DEFAULT 0,
    last_evolved_at REAL
);
"""


def _spec_to_dict(spec: ChainSpec) -> Dict[str, Any]:
    return {
        "name": spec.name,
        "category": spec.category,
        "description": spec.description,
        "params": spec.params,
        "steps": [
            {"tool": s.tool, "args": s.args, "name": s.name, "collect": s.collect, "optional": s.optional}
            for s in spec.steps
        ],
        "budget_tokens": spec.budget_tokens,
        "step_cap_chars": spec.step_cap_chars,
    }


def _dict_to_spec(d: Dict[str, Any]) -> ChainSpec:
    return ChainSpec(
        name=d["name"],
        category=d["category"],
        description=d["description"],
        params=d.get("params", {}),
        steps=[
            Step(tool=s["tool"], args=s.get("args", {}), name=s.get("name", ""),
                 collect=s.get("collect", {}), optional=s.get("optional", False))
            for s in d.get("steps", [])
        ],
        budget_tokens=d.get("budget_tokens", 16000),
        step_cap_chars=d.get("step_cap_chars", 8000),
    )


class ChainStore:
    def __init__(self):
        self._init_db()

    def _init_db(self):
        conn = _db()
        for statement in SCHEMA_SQL.split(";"):
            stripped = statement.strip()
            if stripped:
                conn.execute(stripped)
        try:
            conn.execute("ALTER TABLE chain_candidates ADD COLUMN savings_est INTEGER DEFAULT 0")
        except Exception:
            pass  # column already present
        conn.commit()

    # --- spec persistence ---

    def upsert_spec(self, spec: ChainSpec, *, source: str, status: str, read_only: bool):
        conn = _db()
        now = time.time()
        d = _spec_to_dict(spec)
        conn.execute(
            """INSERT INTO chain_specs
               (name, category, description, params_json, steps_json, budget_tokens,
                step_cap_chars, source, status, read_only, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(name) DO UPDATE SET
                   category=excluded.category, description=excluded.description,
                   params_json=excluded.params_json, steps_json=excluded.steps_json,
                   budget_tokens=excluded.budget_tokens, step_cap_chars=excluded.step_cap_chars,
                   source=excluded.source, status=excluded.status,
                   read_only=excluded.read_only, updated_at=excluded.updated_at""",
            (spec.name, spec.category, spec.description, json.dumps(d["params"]),
             json.dumps(d["steps"]), spec.budget_tokens, spec.step_cap_chars,
             source, status, 1 if read_only else 0, now, now),
        )
        conn.commit()

    def get_spec(self, name: str) -> Optional[Dict[str, Any]]:
        row = _db().execute(
            "SELECT * FROM chain_specs WHERE name=?", (name,)
        ).fetchone()
        if not row:
            return None
        return self._row_to_spec(row)

    def list_specs(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        if status:
            rows = _db().execute(
                "SELECT * FROM chain_specs WHERE status=? ORDER BY updated_at DESC", (status,)
            ).fetchall()
        else:
            rows = _db().execute(
                "SELECT * FROM chain_specs ORDER BY updated_at DESC"
            ).fetchall()
        return [self._row_to_spec(r) for r in rows]

    def set_status(self, name: str, status: str):
        _db().execute(
            "UPDATE chain_specs SET status=?, updated_at=? WHERE name=?",
            (status, time.time(), name),
        )
        _db().commit()

    def delete_spec(self, name: str) -> bool:
        cur = _db().execute("DELETE FROM chain_specs WHERE name=?", (name,))
        _db().commit()
        return cur.rowcount > 0

    def record_use(self, name: str):
        _db().execute(
            "UPDATE chain_specs SET use_count=use_count+1, last_used_at=? WHERE name=?",
            (time.time(), name),
        )
        _db().commit()

    @staticmethod
    def _row_to_spec(row) -> Dict[str, Any]:
        d = dict(row)
        d["params"] = json.loads(d.pop("params_json", "{}"))
        d["steps"] = json.loads(d.pop("steps_json", "[]"))
        d["read_only"] = bool(d["read_only"])
        return d

    # --- mining candidates ---

    def upsert_candidate(self, signature: str, tool_seq: List[str], savings_est: int = 0) -> int:
        conn = _db()
        now = time.time()
        conn.execute(
            """INSERT INTO chain_candidates (signature, tool_seq_json, occurrences, savings_est, first_seen, last_seen)
               VALUES (?, ?, 1, ?, ?, ?)
               ON CONFLICT(signature) DO UPDATE SET
                   occurrences=occurrences+1, savings_est=excluded.savings_est,
                   last_seen=excluded.last_seen""",
            (signature, json.dumps(tool_seq), savings_est, now, now),
        )
        conn.commit()
        row = conn.execute(
            "SELECT occurrences FROM chain_candidates WHERE signature=?", (signature,)
        ).fetchone()
        return row["occurrences"] if row else 1

    def get_candidate(self, signature: str) -> Optional[Dict[str, Any]]:
        row = _db().execute(
            "SELECT * FROM chain_candidates WHERE signature=?", (signature,)
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        d["tool_seq"] = json.loads(d.pop("tool_seq_json", "[]"))
        return d

    def list_candidates(self, limit: int = 50) -> List[Dict[str, Any]]:
        rows = _db().execute(
            "SELECT * FROM chain_candidates ORDER BY last_seen DESC LIMIT ?", (limit,)
        ).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["tool_seq"] = json.loads(d.pop("tool_seq_json", "[]"))
            out.append(d)
        return out
    def delete_candidate(self, signature: str) -> bool:
        cur = _db().execute("DELETE FROM chain_candidates WHERE signature=?", (signature,))
        _db().commit()
        return cur.rowcount > 0

    # --- tool sequences (session telemetry for the evolver) ---

    def upsert_sequence(self, session_id: str, tool_seq: List[str], outcome: str = ""):
        conn = _db()
        now = time.time()
        conn.execute(
            """INSERT INTO tool_sequences (session_id, seq_json, outcome, ts)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(session_id) DO UPDATE SET
                   seq_json=excluded.seq_json, outcome=excluded.outcome, ts=excluded.ts""",
            (session_id, json.dumps(tool_seq), outcome, now),
        )
        conn.commit()

    def list_sequences(self, limit: int = 200) -> List[Dict[str, Any]]:
        rows = _db().execute(
            "SELECT * FROM tool_sequences ORDER BY ts DESC LIMIT ?", (limit,)
        ).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["tool_seq"] = json.loads(d.pop("seq_json", "[]"))
            out.append(d)
        return out

    # --- workflow graph (nodes / edges / clusters / notes / state) ---

    def upsert_cluster(self, cluster_id: str, label: str, chain_id: str = "", color: str = "#335533"):
        conn = _db()
        conn.execute(
            """INSERT INTO graph_clusters (id, label, chain_id, color) VALUES (?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                   label=excluded.label, chain_id=excluded.chain_id, color=excluded.color""",
            (cluster_id, label, chain_id, color),
        )
        conn.commit()

    def delete_cluster(self, cluster_id: str):
        conn = _db()
        conn.execute("DELETE FROM graph_clusters WHERE id=?", (cluster_id,))
        conn.execute("UPDATE graph_nodes SET cluster_id='' WHERE cluster_id=?", (cluster_id,))
        conn.commit()

    def upsert_node(self, node_id: str, label: str, shape: str = "rect",
                    color: str = "#ffffff", cluster_id: str = "", chain_id: str = "",
                    stats: Optional[Dict[str, Any]] = None):
        conn = _db()
        conn.execute(
            """INSERT INTO graph_nodes (id, label, shape, color, cluster_id, chain_id, stats_json)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                   label=excluded.label, shape=excluded.shape, color=excluded.color,
                   cluster_id=excluded.cluster_id, chain_id=excluded.chain_id,
                   stats_json=excluded.stats_json""",
            (node_id, label, shape, color, cluster_id, chain_id,
             json.dumps(stats or {})),
        )
        conn.commit()

    def delete_node(self, node_id: str):
        conn = _db()
        conn.execute("DELETE FROM graph_nodes WHERE id=?", (node_id,))
        conn.execute("DELETE FROM graph_edges WHERE src=? OR dst=?", (node_id, node_id))
        conn.commit()

    def upsert_edge(self, src: str, dst: str, label: str = ""):
        conn = _db()
        conn.execute(
            """INSERT INTO graph_edges (src, dst, label) VALUES (?, ?, ?)
               ON CONFLICT(src, dst) DO UPDATE SET label=excluded.label""",
            (src, dst, label),
        )
        conn.commit()

    def delete_edge(self, src: str, dst: str):
        conn = _db().execute("DELETE FROM graph_edges WHERE src=? AND dst=?", (src, dst))
        conn.commit()
        return conn.rowcount > 0

    def upsert_note(self, section: str, text: str, tag: str = "do"):
        conn = _db()
        conn.execute(
            "INSERT INTO graph_notes (section, text, tag, ts) VALUES (?, ?, ?, ?)",
            (section, text, tag, time.time()),
        )
        conn.commit()

    def list_notes(self, limit: int = 100) -> List[Dict[str, Any]]:
        rows = _db().execute(
            "SELECT section, text, tag FROM graph_notes ORDER BY ts DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_graph(self) -> Dict[str, Any]:
        nodes = [dict(r) for r in _db().execute("SELECT * FROM graph_nodes").fetchall()]
        for n in nodes:
            n["stats"] = json.loads(n.pop("stats_json", "{}"))
        edges = [dict(r) for r in _db().execute("SELECT * FROM graph_edges").fetchall()]
        clusters = [dict(r) for r in _db().execute("SELECT * FROM graph_clusters").fetchall()]
        return {"nodes": nodes, "edges": edges, "clusters": clusters}

    def get_graph_state(self) -> Dict[str, Any]:
        row = _db().execute("SELECT * FROM graph_state WHERE id=1").fetchone()
        return {"version": row["version"], "last_evolved_at": row["last_evolved_at"]} if row \
            else {"version": 0, "last_evolved_at": None}

    def bump_graph_state(self):
        conn = _db()
        conn.execute(
            """INSERT INTO graph_state (id, version, last_evolved_at) VALUES (1, 1, ?)
               ON CONFLICT(id) DO UPDATE SET
                   version=version+1, last_evolved_at=excluded.last_evolved_at""",
            (time.time(),),
        )
        conn.commit()


chain_store = ChainStore()
