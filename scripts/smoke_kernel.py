#!/usr/bin/env python3
"""Kernel regression harness.

Exercises the flows documented in system_devpt_reports/kernel/usage.md:
hydration/parity, stance CLI path, contradiction detection (positive +
negative control), signal persistence, prune idempotency and the
record_removal idempotent skip-path. Mutations are sandboxed in a throwaway
topic; kernel.db and belief_state.json are restored afterwards.

Usage: conda run -n myenv python scripts/smoke_kernel.py
Exit: 0 all pass, 1 any failure.
"""

import json
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "codebase" / "modules"))

from argu_god.engine import topic_store as ts  # noqa: E402

DB = Path("data/kernel.db")
BELIEF = Path("data/mindmaps/local_user/belief_state.json")
SMOKE_TOPIC = "_smoke_k"
RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok)))
    print(f"{'PASS' if ok else 'FAIL'}  {name}{(' — ' + detail) if detail else ''}")


def log_rows():
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        return conn.execute("SELECT COUNT(*) FROM logs").fetchone()[0]
    finally:
        conn.close()


def _cleanup_smoke_topic():
    from kernel.memory.memory_engine import memory_engine
    from kernel.memory.semantic_memory import semantic_memory
    for nid in list(semantic_memory.nodes):
        if semantic_memory.nodes[nid].topic_id == SMOKE_TOPIC:
            memory_engine.delete_object("semantic", nid)
            semantic_memory.remove_node(nid)
    for eid in list(semantic_memory.edges):
        if semantic_memory.edges[eid].topic_id == SMOKE_TOPIC:
            memory_engine.delete_object("semantic", eid)
            semantic_memory.remove_edge(eid)
    # fallback: delete by known ids even if not in RAM
    for oid in ("argu__smoke_k_ClaimA", "argu__smoke_k_ClaimB",
                "edge_requires_ClaimA_ClaimB", "edge_contradicts_ClaimA_ClaimB"):
        try:
            memory_engine.delete_object("semantic", oid)
        except Exception:
            pass
    shutil.rmtree(Path("data/topics") / SMOKE_TOPIC, ignore_errors=True)


def main():
    tmp = Path(tempfile.mkdtemp(prefix="smoke_kernel_"))
    shutil.copy(DB, tmp / "kernel.db")
    if BELIEF.exists():
        shutil.copy(BELIEF, tmp / "belief_state.json")

    # cold-start hydration: every CLI process must do this first
    ts.hydrate()
    _cleanup_smoke_topic()

    # S0 embedding cold start (must load from encoding_cache without download)
    import pathlib
    cache_p = pathlib.Path("codebase/encoding_cache/all-MiniLM-L6-v2")
    tokenizer_p = pathlib.Path("codebase/encoding_cache/9b5ad71b2ce5302211f9c61530b329a4922fc6a4")
    try:
        from kernel.hypothesis.contradiction_gate import _embed, _similar, _ST_MODEL
        import kernel.hypothesis.contradiction_gate as cg
        cg._embed.cache_clear()
        cg._ST_MODEL = None
        cg._ST_FAILED = False
        import time
        t0 = time.time()
        v = _embed("hello world test")
        dt = time.time() - t0
        ok = (cache_p.exists() and tokenizer_p.exists() and v is not None and len(v) == 384 and dt < 15)
        # embedding paraphrase should be > jaccard
        sim = _similar("Objective moral values exist", "Moral objectivism holds")
        check("embedding cold start", ok and sim > 0.3, f"cache={cache_p.exists()} dt={dt:.2f}s sim={sim:.2f}")
    except Exception as e:
        check("embedding cold start", False, str(e))

    # S1 topics known to the kernel
    topics = ts.list_topics()
    check("topics listed", {"theism_atheism", "project_history"} <= set(topics),
          str(topics))

    # S2 hydration parity vs derived exports
    for t in ("theism_atheism", "project_history"):
        g = ts.export_graph(t)
        d = json.loads(ts.graph_path(t).read_text(encoding="utf-8"))
        check(f"parity {t}", (len(g["nodes"]), len(g["edges"]))
              == (len(d["nodes"]), len(d["edges"])),
              f"store {len(g['nodes'])}n/{len(g['edges'])}e")

    # S3-S5 contradiction loop on a throwaway topic
    ts.add_node(SMOKE_TOPIC, {"name": "ClaimA", "premise": "A"})
    ts.add_node(SMOKE_TOPIC, {"name": "ClaimB", "premise": "not A"})
    ts.set_stance(SMOKE_TOPIC, "ClaimA", "agree")
    ts.set_stance(SMOKE_TOPIC, "ClaimB", "agree")

    ts.add_edge(SMOKE_TOPIC, "ClaimA", "ClaimB", "requires")
    neg = ts.check_contradictions(SMOKE_TOPIC, ("ClaimA", "ClaimB"))
    check("negative control (requires edge silent)", neg == [])

    ts.add_edge(SMOKE_TOPIC, "ClaimA", "ClaimB", "contradicts")
    pos = ts.check_contradictions(SMOKE_TOPIC, ("ClaimA", "ClaimB"))
    check("contradiction fires on contradicts edge",
          ("ClaimA", "ClaimB") in [tuple(p) for p in pos])

    before = sum(1 for i in _episodic_ids()
                 if i.startswith("contradiction_detected_"))
    sid = ts.emit_contradiction_signal(("ClaimA", "ClaimB"), SMOKE_TOPIC)
    after = sum(1 for i in _episodic_ids()
                if i.startswith("contradiction_detected_"))
    check("signal emitted + persisted", sid and after == before + 1,
          f"signal={sid}")

    # S6 prune idempotency (second run must not change the row count)
    import re
    _prune()
    out2 = _prune()
    m = re.search(r"logs: (\d+) -> (\d+) rows", out2)
    check("prune idempotent", bool(m) and m.group(1) == m.group(2),
          out2.strip())

    # S7 record_removal skip-path leaves data untouched
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from record_removal import record_removal
    changes = record_removal("analyzer.py deleted from argu_god", "x")
    kinds = {c["kind"] for c in changes}
    check("record_removal idempotent skip",
          "node_skipped" in kinds and not any(k.endswith("_added") for k in kinds),
          str(sorted(kinds)))

    # cleanup
    _cleanup_smoke_topic()
    for wal in ("-wal", "-shm"):
        p = DB.with_name(DB.name + wal)
        p.unlink(missing_ok=True)
    shutil.copy(tmp / "kernel.db", DB)
    if (tmp / "belief_state.json").exists():
        shutil.copy(tmp / "belief_state.json", BELIEF)
    shutil.rmtree(tmp, ignore_errors=True)
    # restore in-memory view from restored DB
    try:
        ts.hydrate(force=True)
    except Exception:
        pass

    failed = [n for n, ok in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} passed"
          + (f"; FAILED: {failed}" if failed else ""))
    return 1 if failed else 0


def _episodic_ids():
    from kernel.memory.memory_engine import memory_engine
    return memory_engine.list_objects("episodic")


def _prune():
    return subprocess.run(
        [sys.executable, str(Path(__file__).resolve().parent
                             / "prune_kernel_logs.py"), "--keep", "200"],
        capture_output=True, text=True).stdout


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"HARNESS ERROR: {e}")
        sys.exit(1)
