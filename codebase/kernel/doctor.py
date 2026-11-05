"""Kernel doctor report (KRN-04): one dict, no printing.

`scripts/topic_ops.py doctor` renders this; tests call it directly. Keeping the
diagnostics out of the CLI keeps both files small and lets another surface reuse
the same checks.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List

DOCS_HINT = ("Docs: system_devpt_reports/kernel/usage.md | "
             "Agent loop: data/workflows/kernel_ops.md")


def build_report(topic_store) -> Dict[str, Any]:
    from kernel.memory.memory_engine import memory_engine
    from kernel.memory.semantic_memory import semantic_memory
    from kernel.persistence.db import kernel_db, kernel_db_ro

    try:
        integrity = kernel_db_ro.ro_conn.execute("PRAGMA integrity_check").fetchone()[0]
    except Exception:
        integrity = "ok"
    try:
        logs_n = kernel_db_ro.ro_conn.execute("SELECT COUNT(*) FROM logs").fetchone()[0]
    except Exception:
        logs_n = 0
    try:
        signals = sum(1 for i in memory_engine.list_objects_ro("episodic")
                      if i.startswith("contradiction_detected_"))
    except Exception:
        signals = sum(1 for i in memory_engine.list_objects("episodic")
                      if i.startswith("contradiction_detected_"))

    # KRN-04: show write concurrency here instead of letting it surface later
    # as a random "database is locked" in a job.
    try:
        journal = kernel_db_ro.ro_conn.execute("PRAGMA journal_mode").fetchone()[0]
        busy_ms = kernel_db_ro.ro_conn.execute("PRAGMA busy_timeout").fetchone()[0]
    except Exception:
        journal, busy_ms = "unknown", None
    lock_probe = "ok"
    try:
        conn = kernel_db.conn
        conn.execute("BEGIN IMMEDIATE")
        conn.rollback()
    except Exception as e:
        lock_probe = f"locked: {e}"

    topics_out: List[Dict[str, Any]] = []
    issues: List[str] = []
    if integrity != "ok":
        issues.append(f"db integrity: {integrity}")
    if logs_n > 200:
        issues.append(f"logs table has {logs_n} rows (>200) — "
                      f"run scripts/prune_kernel_logs.py --keep 200")
    for t in topic_store.list_topics():
        tnodes = [n for n in semantic_memory.nodes.values() if n.topic_id == t]
        id2name = {n.node_id: n.title for n in tnodes}
        tedges = [e for e in semantic_memory.edges.values() if e.topic_id == t]
        live = [e for e in tedges
                if e.source_node_id in id2name and e.target_node_id in id2name]
        dangling = len(tedges) - len(live)
        exported = topic_store.export_graph(t)
        path = topic_store.graph_path(t)
        disk = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
        parity = ("no export" if disk is None else
                  ("match" if (len(disk["nodes"]), len(disk["edges"]))
                   == (len(exported["nodes"]), len(exported["edges"])) else "STALE"))
        if dangling:
            issues.append(f"topic {t}: {dangling} dangling edge(s)")
        if parity == "STALE":
            issues.append(f"topic {t}: derived export stale — rerun "
                          f"scripts/backfill_topics.py {t}")
        topics_out.append({"topic": t, "nodes": len(tnodes), "edges": len(live),
                           "dangling": dangling, "export": parity})

    if lock_probe != "ok":
        issues.append(f"db write probe: {lock_probe} — another writer holds the "
                      f"file; raise PIE_DB_BUSY_TIMEOUT_MS or use one writer")
    return {"db_integrity": integrity, "log_rows": logs_n,
            "contradiction_signals": signals,
            "db_journal_mode": journal, "db_busy_timeout_ms": busy_ms,
            "db_write_probe": lock_probe, "topics": topics_out,
            "issues": issues, "docs": DOCS_HINT}
