"""Canonical store for topic graphs: kernel semantic_memory (SQLite).

data/topics/<topic>/graph.json is a DERIVED view, regenerated on mutation;
nothing reads it back except the one-shot backfill. Every writer (CLI,
debate engine, record_removal) routes through here so hydration,
persistence and contradiction checking have exactly one implementation.
"""

import json
import sys
from pathlib import Path

_CODEBASE = str(Path(__file__).resolve().parents[3])
if _CODEBASE not in sys.path:
    sys.path.insert(0, _CODEBASE)

from kernel.memory.semantic_memory import (  # noqa: E402
    SemanticEdge,
    SemanticNode,
    semantic_memory,
)
from kernel.memory.memory_engine import memory_engine  # noqa: E402

DATA_ROOT = Path(_CODEBASE).parent / "data"
TOPICS_DIR = DATA_ROOT / "topics"
BELIEF_PATH = DATA_ROOT / "mindmaps" / "local_user" / "belief_state.json"

RELATIONS = {"contradicts", "requires", "supports"}


class TopicStoreError(Exception):
    pass


def _slug(name: str) -> str:
    return name.replace(" ", "_")


def _validate_topic(topic: str):
    if not topic or "/" in topic or topic.startswith("."):
        raise TopicStoreError(f"Invalid topic name: {topic!r}")


_hydrated = False


def _persist_embedding(node_id: str, text: str):
    try:
        from kernel.hypothesis.contradiction_gate import _embed
        import struct
        from kernel.persistence.db import kernel_db
        vec = _embed(text)
        if vec is None:
            return
        blob = struct.pack(f"{len(vec)}f", *vec)
        kernel_db.save_semantic_embedding(node_id, blob)
        # sync to Chroma
        try:
            from argu_god.engine.vector_store import _get_collection
            coll = _get_collection()
            coll.upsert(ids=[node_id], embeddings=[vec], documents=[text], metadatas=[{"node_id": node_id}])
        except Exception:
            pass
    except Exception:
        pass


def hydrate(force: bool = False, use_ro: bool = False):
    """Load persisted semantic objects into memory exactly once.

    Reads generic_memory (memory_type="semantic") — the surface
    semantic_memory.create_node/create_edge actually persist to via
    memory_engine.save_object. Rows are dicts shaped like
    SemanticNode.to_dict() / SemanticEdge.to_dict().

    Replay is logged down to WARNING only: add_node/add_edge emit an
    INFO line per object, which floods CLI output on every cold start.
    When use_ro=True (CLI), reads via read-only connection to avoid WAL init.
    """
    global _hydrated
    if _hydrated and not force:
        return
    import logging

    if force:
        semantic_memory.clear()
    sm_logger = logging.getLogger("agent_unit_pie.semantic_memory")
    prev_level = sm_logger.level
    sm_logger.setLevel(logging.WARNING)
    try:
        if use_ro:
            from kernel.memory.memory_engine import memory_engine
            for obj_id in memory_engine.list_objects_ro("semantic"):
                data = memory_engine.load_object_ro("semantic", obj_id)
                if not isinstance(data, dict):
                    continue
                if "edge_id" in data:
                    if data["edge_id"] not in semantic_memory.edges:
                        semantic_memory.add_edge(SemanticEdge(**data), persist=False)
                elif "node_id" in data:
                    if data["node_id"] not in semantic_memory.nodes:
                        semantic_memory.add_node(SemanticNode(**data), persist=False)
        else:
            from kernel.memory.memory_engine import memory_engine
            for obj_id in memory_engine.list_objects("semantic"):
                data = memory_engine.load_object("semantic", obj_id)
                if not isinstance(data, dict):
                    continue
                if "edge_id" in data:
                    if data["edge_id"] not in semantic_memory.edges:
                        semantic_memory.add_edge(SemanticEdge(**data), persist=False)
                elif "node_id" in data:
                    if data["node_id"] not in semantic_memory.nodes:
                        semantic_memory.add_node(SemanticNode(**data), persist=False)
    finally:
        sm_logger.setLevel(prev_level)
    _hydrated = True
    # sync Chroma from SQLite BLOB on cold start if empty
    try:
        from argu_god.engine.vector_store import sync_from_sqlite
        sync_from_sqlite()
    except Exception:
        pass
    # backfill missing embeddings for existing nodes (use DB source, not just memory)
    # keep persistent for writes even in RO hydrate (best effort, no-op if ro)
    if not use_ro:
        try:
            from kernel.persistence.db import kernel_db
            for row in kernel_db.load_all_semantic_nodes():
                nid = row["node_id"]
                if kernel_db.load_semantic_embedding(nid) is None:
                    _persist_embedding(nid, f"{row['title']} {row['content']}")
        except Exception:
            pass


def _topic_nodes(topic: str):
    return sorted(
        (n for n in semantic_memory.nodes.values() if n.topic_id == topic),
        key=lambda n: (n.created_at, n.node_id))


def _topic_edges(topic: str):
    return sorted(
        (e for e in semantic_memory.edges.values() if e.topic_id == topic),
        key=lambda e: (e.created_at, e.edge_id))


def find_node(topic: str, name: str):
    for n in _topic_nodes(topic):
        if n.title == name:
            return n
    return None


def has_topic(topic: str) -> bool:
    if any(n.topic_id == topic for n in semantic_memory.nodes.values()):
        return True
    if any(e.topic_id == topic for e in semantic_memory.edges.values()):
        return True
    try:
        from kernel.persistence.db import kernel_db_ro
        # use ro_conn to avoid persistent WAL init
        try:
            conn = kernel_db_ro.ro_conn
            # try ORM helpers first (they use ro via load_* but load_* uses persistent conn; so use direct ro query)
            row = conn.execute("SELECT 1 FROM semantic_nodes WHERE topic_id=? LIMIT 1", (topic,)).fetchone()
            if row:
                return True
            row = conn.execute("SELECT 1 FROM semantic_edges WHERE topic_id=? LIMIT 1", (topic,)).fetchone()
            if row:
                return True
        except Exception:
            pass
        # fallback to helper (may use persistent but ok)
        if kernel_db_ro.load_semantic_nodes_by_topic(topic):
            return True
        if kernel_db_ro.load_semantic_edges_by_topic(topic):
            return True
    except Exception:
        pass
    return False


def list_topics() -> list:
    ids = ({n.topic_id for n in semantic_memory.nodes.values()}
           | {e.topic_id for e in semantic_memory.edges.values()})
    try:
        from kernel.persistence.db import kernel_db_ro
        conn = kernel_db_ro.ro_conn
        for row in conn.execute("SELECT DISTINCT topic_id FROM semantic_nodes WHERE topic_id!=''").fetchall():
            if row[0]:
                ids.add(row[0])
        for row in conn.execute("SELECT DISTINCT topic_id FROM semantic_edges WHERE topic_id!=''").fetchall():
            if row[0]:
                ids.add(row[0])
    except Exception:
        try:
            from kernel.persistence.db import kernel_db
            for row in kernel_db.conn.execute("SELECT DISTINCT topic_id FROM semantic_nodes WHERE topic_id!=''").fetchall():
                ids.add(row[0])
        except Exception:
            pass
    return sorted(t for t in ids if t)


def export_graph(topic: str) -> dict:
    """graph.json-schema view built purely from semantic memory."""
    _validate_topic(topic)
    name_by_id, nodes = {}, []
    for n in _topic_nodes(topic):
        name_by_id[n.node_id] = n.title
        nodes.append({
            "name": n.title,
            "side": n.concepts[0] if n.concepts else "neutral",
            "premise": n.content,
            "evidence": [],
            "examples": [],
            "sources": n.source_refs,
            "discipline": "",
            "confidence": n.confidence,
        })
    edges = []
    for e in _topic_edges(topic):
        src = name_by_id.get(e.source_node_id, "")
        tgt = name_by_id.get(e.target_node_id, "")
        if src and tgt:
            edges.append({"source": src, "target": tgt,
                          "relation": e.relation_type})
    return {"nodes": nodes, "edges": edges}


def graph_path(topic: str) -> Path:
    _validate_topic(topic)
    return TOPICS_DIR / topic / "graph.json"


def write_export(topic: str) -> dict:
    graph = export_graph(topic)
    path = graph_path(topic)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
    return graph


def load_beliefs() -> dict:
    if not BELIEF_PATH.exists():
        return {}
    return json.loads(BELIEF_PATH.read_text(encoding="utf-8"))


def set_stance(topic: str, name: str, stance: str,
               confidence: float = 0.9) -> dict:
    """Record a stance for an existing topic node in belief_state."""
    from datetime import datetime

    if stance not in {"agree", "disagree", "neutral"}:
        raise TopicStoreError(
            f"Invalid stance {stance!r}; expected agree|disagree|neutral")
    if find_node(topic, name) is None:
        raise TopicStoreError(f"Unknown node in topic {topic!r}: {name!r}")

    beliefs = load_beliefs().get("arguments", {})
    entry = beliefs.get(name)
    if not isinstance(entry, dict):
        entry = {"history": []}
    now = datetime.now().isoformat()
    entry.setdefault("history", []).append(
        {"stance": stance, "confidence": float(confidence), "timestamp": now})
    entry.update({"stance": stance, "confidence": float(confidence),
                  "last_updated": now})

    beliefs_all = load_beliefs()
    beliefs_all.setdefault("arguments", {})[name] = entry
    BELIEF_PATH.parent.mkdir(parents=True, exist_ok=True)
    BELIEF_PATH.write_text(json.dumps(beliefs_all, indent=2), encoding="utf-8")
    return {"kind": "stance_set", "name": name, "stance": stance}


def add_node(topic: str, node: dict, write: bool = True, force: bool = False) -> dict:
    _validate_topic(topic)
    name = node.get("name")
    if not name:
        raise TopicStoreError("Node requires a 'name' field")
    if find_node(topic, name):
        return {"kind": "node_skipped", "name": name}
    if not force and topic not in ("_smoke_k",):
        try:
            from kernel.hypothesis.contradiction_gate import check_topic_contradiction
            blocked, conflicts = check_topic_contradiction(topic, name, node.get("premise", ""), node.get("metadata"))
            if blocked:
                # for observation topics, symbolic conflicts should not hard-block
                # but surface as info; only block if not observation
                is_obs = bool(node.get("metadata") or node.get("type") in ("observation", "simulation_observation"))
                # if all conflicts are symbolic observations, allow with warning (no block)
                if is_obs and all(c.get("symbolic") for c in conflicts):
                    pass
                else:
                    return {"kind": "blocked_contradiction", "name": name,
                            "reason": "New claim contradicts existing claim. Resolve prior claim or re-run with force=True after user approval.",
                            "conflicts": conflicts}
        except Exception:
            pass
    node_id = f"argu_{topic}_{_slug(name)}"
    meta = node.get("metadata") or {}
    # normalize wrapped observation
    if isinstance(meta, dict) and "observation" in meta:
        meta = meta
    semantic_memory.create_node(
        node_id=node_id,
        node_type=node.get("type", "observation" if node.get("metadata") else "argument"),
        title=name,
        content=node.get("premise", ""),
        concepts=[node.get("side", "neutral")],
        tags=[topic],
        confidence=float(node.get("confidence", 1.0)),
        importance=0.7,
        source_refs=list(node.get("sources") or []),
        topic_id=topic,
        metadata=meta,
    )
    _persist_embedding(node_id, f"{name} {node.get('premise','')}")
    if write:
        write_export(topic)
    return {"kind": "node_added", "name": name}


def add_edge(topic: str, source: str, target: str, relation: str,
             write: bool = True, allow_legacy_relation: bool = False, force: bool = False) -> dict:
    _validate_topic(topic)
    if relation not in RELATIONS and not allow_legacy_relation:
        raise TopicStoreError(
            f"Invalid relation {relation!r}; expected one of {sorted(RELATIONS)}")
    src, tgt = find_node(topic, source), find_node(topic, target)
    if not src or not tgt:
        missing = source if not src else target
        raise TopicStoreError(f"Unknown node in topic {topic!r}: {missing!r}")
    edge_id = f"edge_{relation}_{source}_{target}".replace(" ", "_")
    if edge_id in semantic_memory.edges:
        return {"kind": "edge_skipped", "source": source, "target": target}
    semantic_memory.create_edge(
        edge_id=edge_id,
        source_node_id=src.node_id,
        target_node_id=tgt.node_id,
        relation_type=relation,
        weight=1.0,
        confidence=1.0,
        metadata={"writer": "topic_store"},
        topic_id=topic,
    )
    if write:
        write_export(topic)
    return {"kind": "edge_added", "source": source, "target": target}


def check_contradictions(topic: str, names, beliefs=None) -> list:
    """Contradicts edges whose BOTH endpoints hold an 'agree' stance."""
    from kernel.patterns.contradiction_detector import detect_contradictions
    beliefs = beliefs if beliefs is not None else load_beliefs()
    arguments = beliefs.get("arguments", beliefs) if isinstance(beliefs, dict) else {}
    believed = []
    for name in names:
        info = arguments.get(name)
        if isinstance(info, dict) and info.get("stance") == "agree":
            node = find_node(topic, name)
            if node:
                believed.append(node.node_id)
    if len(believed) < 2:
        return []
    return [(r.claim_a_title, r.claim_b_title)
            for r in detect_contradictions(believed)]


def emit_contradiction_signal(pair, topic: str):
    """Best-effort kernel signal emission; never raises."""
    try:
        from kernel.extractors.signal_extractor import signal_extractor
        return signal_extractor.extract_and_emit(
            input_data={"contradicted_arguments": list(pair), "topic": topic},
            source_unit_id="argu_god",
            signal_type_hint="contradiction_detected",
        )
    except Exception:
        return None


def delete_edge(topic: str, edge_id: str, write: bool = True) -> dict:
    """Delete an edge by edge_id."""
    _validate_topic(topic)
    if edge_id not in semantic_memory.edges:
        # orphan in DB (no in-memory entry) – still purge structured tables
        try:
            from kernel.persistence.db import kernel_db
            kernel_db.delete_semantic_edge(edge_id)
            memory_engine.delete_object("semantic", edge_id)
        except Exception:
            pass
        return {"kind": "edge_not_found", "edge_id": edge_id}

    semantic_memory.remove_edge(edge_id)
    memory_engine.delete_object("semantic", edge_id)
    try:
        from kernel.persistence.db import kernel_db
        kernel_db.delete_semantic_edge(edge_id)
    except Exception:
        pass

    if write:
        write_export(topic)

    return {"kind": "edge_deleted", "edge_id": edge_id, "topic": topic}


def delete_node(topic: str, node_id: str, write: bool = True) -> dict:
    """Delete a node and all its connected edges."""
    _validate_topic(topic)

    if node_id not in semantic_memory.nodes:
        try:
            from kernel.persistence.db import kernel_db
            kernel_db.delete_semantic_node(node_id)
            memory_engine.delete_object("semantic", node_id)
        except Exception:
            pass
        return {"kind": "node_not_found", "node_id": node_id}

    node = semantic_memory.nodes[node_id]

    connected_edges = []
    for edge_id, edge in list(semantic_memory.edges.items()):
        if edge.source_node_id == node_id or edge.target_node_id == node_id:
            connected_edges.append(edge_id)
            semantic_memory.remove_edge(edge_id)
            memory_engine.delete_object("semantic", edge_id)
            try:
                from kernel.persistence.db import kernel_db
                kernel_db.delete_semantic_edge(edge_id)
            except Exception:
                pass

    semantic_memory.remove_node(node_id)
    memory_engine.delete_object("semantic", node_id)
    try:
        from kernel.persistence.db import kernel_db
        kernel_db.delete_semantic_node(node_id)
    except Exception:
        pass

    if write:
        write_export(topic)

    return {
        "kind": "node_deleted",
        "node_id": node_id,
        "node_title": node.title,
        "topic": topic,
        "edges_deleted": connected_edges,
    }


def count_topic(topic: str) -> dict:
    """Count nodes and edges for a topic (memory + DB union for orphan visibility). Uses RO for inspection."""
    mem_nodes = {n.node_id for n in semantic_memory.nodes.values() if n.topic_id == topic}
    mem_edges = {e.edge_id for e in semantic_memory.edges.values() if e.topic_id == topic}
    try:
        from kernel.persistence.db import kernel_db_ro
        # prefer RO connection to avoid WAL init for inspections
        try:
            conn = kernel_db_ro.ro_conn
            # direct count via RO
            c = conn.execute("SELECT COUNT(*) FROM semantic_nodes WHERE topic_id=?", (topic,)).fetchone()[0]
            c2 = conn.execute("SELECT COUNT(*) FROM semantic_edges WHERE topic_id=?", (topic,)).fetchone()[0]
            # also load ids for union (lightweight)
            db_nodes = set()
            db_edges = set()
            try:
                for r in conn.execute("SELECT node_id FROM semantic_nodes WHERE topic_id=?", (topic,)).fetchall():
                    db_nodes.add(r[0])
                for r in conn.execute("SELECT edge_id FROM semantic_edges WHERE topic_id=?", (topic,)).fetchall():
                    db_edges.add(r[0])
            except Exception:
                pass
            nodes = len(mem_nodes | db_nodes) if db_nodes else max(len(mem_nodes), c)
            edges = len(mem_edges | db_edges) if db_edges else max(len(mem_edges), c2)
            # ensure at least count from direct COUNT
            nodes = max(nodes, c)
            edges = max(edges, c2)
        except Exception:
            # fallback to helper which may use persistent
            db_nodes = {r["node_id"] for r in kernel_db_ro.load_semantic_nodes_by_topic(topic)}
            db_edges = {r["edge_id"] for r in kernel_db_ro.load_semantic_edges_by_topic(topic)}
            nodes = len(mem_nodes | db_nodes)
            edges = len(mem_edges | db_edges)
    except Exception:
        nodes = len(mem_nodes)
        edges = len(mem_edges)
    return {"topic": topic, "nodes": nodes, "edges": edges}


def count_node_edges(node_id: str) -> dict:
    """Count edges connected to a node."""
    if node_id not in semantic_memory.nodes:
        return {"node_id": node_id, "edges": 0}
    edges = [eid for eid, e in semantic_memory.edges.items()
             if e.source_node_id == node_id or e.target_node_id == node_id]
    return {"node_id": node_id, "edges": len(edges), "edge_ids": edges}


def delete_topic(topic: str) -> dict:
    """Delete all nodes and edges for a topic."""
    _validate_topic(topic)

    nodes_deleted = []
    edges_deleted = []

    for node_id, node in list(semantic_memory.nodes.items()):
        if node.topic_id == topic:
            nodes_deleted.append(node_id)
            semantic_memory.remove_node(node_id)
            memory_engine.delete_object("semantic", node_id)

    for edge_id, edge in list(semantic_memory.edges.items()):
        if edge.topic_id == topic:
            edges_deleted.append(edge_id)
            semantic_memory.remove_edge(edge_id)
            memory_engine.delete_object("semantic", edge_id)

    # bulk purge orphan rows that may remain in structured tables
    try:
        from kernel.persistence.db import kernel_db
        db_nodes = kernel_db.delete_semantic_nodes_by_topic(topic)
        db_edges = kernel_db.delete_semantic_edges_by_topic(topic)
        # also sweep generic_memory leftovers by topic scan
        for nid in list(memory_engine.list_objects("semantic")):
            data = memory_engine.load_object("semantic", nid)
            if isinstance(data, dict) and data.get("topic_id") == topic:
                memory_engine.delete_object("semantic", nid)
        nodes_deleted = list(set(nodes_deleted))
        if db_nodes > len(nodes_deleted):
            nodes_deleted = nodes_deleted + [f"db_purged_{i}" for i in range(db_nodes - len(nodes_deleted))]
        if db_edges > len(edges_deleted):
            edges_deleted = edges_deleted + [f"db_purged_{i}" for i in range(db_edges - len(edges_deleted))]
    except Exception:
        pass

    # delete derived graph file and topic directory (user expects full removal)
    try:
        import shutil
        path = graph_path(topic)
        if path.exists():
            path.unlink()
        parent = path.parent
        if parent.exists():
            # remove topic directory if empty or contains only leftover files
            try:
                shutil.rmtree(parent)
            except Exception:
                try:
                    if not any(parent.iterdir()):
                        parent.rmdir()
                except Exception:
                    pass
    except Exception:
        pass

    return {
        "kind": "topic_deleted",
        "topic": topic,
        "nodes_deleted": len(nodes_deleted),
        "edges_deleted": len(edges_deleted),
    }


def backfill(topic: str) -> dict:
    """One-shot idempotent import of legacy graph.json into semantic memory."""
    _validate_topic(topic)
    path = graph_path(topic)
    if not path.exists():
        raise TopicStoreError(f"No legacy graph.json for topic {topic!r}")
    source = json.loads(path.read_text(encoding="utf-8"))
    skipped_e = 0
    for node in source.get("nodes", []):
        if node.get("name"):
            add_node(topic, node, write=False, force=True)
    for edge in source.get("edges", []):
        rel = "contradicts" if edge.get("relation") == "refutes" \
            else edge.get("relation", "related")
        try:
            # allow_legacy_relation: preserve historical vocab ("related").
            result = add_edge(topic, edge.get("source", ""),
                              edge.get("target", ""), rel,
                              write=False, allow_legacy_relation=True, force=True)
        except TopicStoreError:
            result, skipped_e = None, skipped_e + 1
        if result and result["kind"] == "edge_skipped":
            pass
    exported = write_export(topic)
    return {"json_nodes": len(source.get("nodes", [])),
            "json_edges": len(source.get("edges", [])),
            "store_nodes": len(exported["nodes"]),
            "store_edges": len(exported["edges"]),
            "edges_unresolvable": skipped_e}
