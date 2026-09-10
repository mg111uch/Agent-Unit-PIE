#!/usr/bin/env python3
"""Generic topic-graph CLI for external agents (kernel-backed).

Mutations go through kernel semantic_memory (SQLite, canonical) via
argu_god.engine.topic_store; graph.json under data/topics/ is regenerated
as a derived view. Adding a `contradicts` edge triggers kernel contradiction
detection against belief_state and emits a contradiction_detected signal.
"""

import argparse
import json
import sys
from pathlib import Path

_SCRIPTS = str(Path(__file__).resolve().parent)
_MODULES = (_SCRIPTS, str(Path(__file__).resolve().parents[1] / "codebase" / "modules"))
for _p in _MODULES:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from argu_god.engine import topic_store as ts  # noqa: E402
from argu_god.engine.topic_store import TopicStoreError  # noqa: E402


_DOCS_HINT = ("Docs: system_devpt_reports/kernel/usage.md | "
              "Agent loop: data/workflows/kernel_ops.md")


def build_parser():
    # default=SUPPRESS: without it a subparser's False default would
    # clobber flags given before the subcommand (e.g. `topic_ops.py
    # --dry-run add-node ...`).
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--dry-run", action="store_true",
                        default=argparse.SUPPRESS)
    common.add_argument("--json", action="store_true",
                        default=argparse.SUPPRESS)
    common.add_argument("--quiet", "-q", action="store_true",
                        default=argparse.SUPPRESS)

    p = argparse.ArgumentParser(
        description="Add/query nodes and edges in a topic graph "
                    "(stored in kernel semantic memory)",
        epilog=f"{_DOCS_HINT}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[common])
    sub = p.add_subparsers(dest="cmd", required=True)

    def topic_arg(sp):
        sp.add_argument("--topic", required=True)

    pn = sub.add_parser("add-node", parents=[common],
                        help="append a node (skips duplicates by name)")
    topic_arg(pn)
    pn.add_argument("--name", required=True)
    pn.add_argument("--premise", required=True)
    pn.add_argument("--side", default="argument",
                    choices=["decision", "argument", "pro", "con", "neutral"])
    pn.add_argument("--source", action="append", default=[], dest="sources")
    pn.add_argument("--confidence", type=float, default=1.0)
    pn.add_argument("--force", action="store_true", help="force add even if contradicts prior claim (requires user approval)")
    pn.add_argument("--type", dest="node_type", default=None, help="node_type: argument|observation|hypothesis (default argument, observation if --metadata given)")
    pn.add_argument("--metadata", default=None, help="JSON string for typed observation metadata, e.g. '{\"observation\":{\"metric\":\"population\",\"outcome\":\"COLLAPSED\"}}'")
    pn.add_argument("--stance", default=None, choices=["agree", "disagree", "neutral"],
                    help="record stance right away (default: agree for side=decision, none otherwise)")
    pn.add_argument("--supersedes", default=None, metavar="NAME",
                    help="bypass similarity gate as explicit refinement; marks NAME superseded (history kept)")
    pn.add_argument("--evidence", action="append", default=[], dest="evidence",
                    help="cross-topic pointer TOPIC:NAME (repeatable)")

    pe = sub.add_parser("add-edge", parents=[common],
                        help="append an edge (skips duplicate triples)")
    topic_arg(pe)
    pe.add_argument("--source", required=True)
    pe.add_argument("--target", required=True)
    pe.add_argument("--relation", required=True,
                    choices=["contradicts", "requires", "supports", "supersedes"])
    pe.add_argument("--force", action="store_true", help="force add even if contradicts prior claim")

    pn2 = sub.add_parser("neighbors", parents=[common],
                         help="in-topic edges + cross-topic evidence pointers for a node")
    topic_arg(pn2)
    pn2.add_argument("--name", required=True)

    pb = sub.add_parser("batch", parents=[common],
                        help="many nodes+edges in one process: --file JSON {topic?,nodes:[],edges:[]} (single hydrate)")
    pb.add_argument("--file", required=True)
    pb.add_argument("--topic", required=False, default=None)

    pl = sub.add_parser("list", parents=[common], help="list nodes")
    topic_arg(pl)
    pl.add_argument("--side")

    sub.add_parser("topics", parents=[common],
                   help="list all topic ids known to the kernel")

    ps = sub.add_parser("set-stance", parents=[common],
                        help="record agree/disagree/neutral for a node")
    topic_arg(ps)
    ps.add_argument("--name", required=True)
    ps.add_argument("--stance", required=True,
                    choices=["agree", "disagree", "neutral"])
    ps.add_argument("--confidence", type=float, default=0.9)

    sub.add_parser("doctor", parents=[common],
                   help="kernel health report (integrity, topics, logs)")

    pc = sub.add_parser("check", parents=[common],
                        help="check contradictions for claims (CLI wrapper for debate detector)")
    topic_arg(pc)
    pc.add_argument("--claims", required=True, help="comma-separated claim names, e.g. ClaimA,ClaimB")

    sub.add_parser("signals", parents=[common],
                   help="list contradiction_detected signals persisted in kernel episodic memory")

    pd = sub.add_parser("delete-node", parents=[common],
                        help="delete a node and all its connected edges by name")
    topic_arg(pd)
    pd.add_argument("--name", help="node name to delete")
    pd.add_argument("--node-id", help="node_id to delete")

    pe2 = sub.add_parser("delete-edge", parents=[common],
                         help="delete an edge by edge-id")
    topic_arg(pe2)
    pe2.add_argument("--edge-id", required=True)

    pt = sub.add_parser("delete-topic", parents=[common],
                        help="delete all nodes and edges for a topic")
    topic_arg(pt)

    return p


def _g(args, flag):
    return getattr(args, flag, False)


def _run_batch(args):
    """One hydrate, many mutations; single export per touched topic."""
    try:
        spec = json.loads(Path(args.file).read_text(encoding="utf-8"))
    except Exception as e:
        raise TopicStoreError(f"Invalid batch file: {e}")
    default_topic = getattr(args, "topic", None) or spec.get("topic")
    if _g(args, "dry_run"):
        n = len(spec.get("nodes", [])) + len(spec.get("edges", []))
        return [{"kind": "batch_dry_run", "topic": default_topic or "",
                 "ops": n}]
    changes, touched = [], set()
    for item in spec.get("nodes", []):
        t = item.get("topic") or default_topic
        if not t:
            raise TopicStoreError("batch node missing topic (no --topic and no item.topic)")
        res = ts.add_node(t, {"name": item["name"], "side": item.get("side", "argument"),
                              "premise": item.get("premise", ""),
                              "sources": item.get("sources", []),
                              "confidence": item.get("confidence", 1.0),
                              "metadata": item.get("metadata"),
                              "evidence": item.get("evidence", []),
                              "supersedes": item.get("supersedes"),
                              "type": item.get("type")},
                          write=False, force=item.get("force", False))
        if res.get("kind") == "node_added":
            stance = item.get("stance") or ("agree" if item.get("side") == "decision" else None)
            if stance:
                ts.set_stance(t, item["name"], stance)
        touched.add(t)
        changes.append({**res, "topic": t})
    for item in spec.get("edges", []):
        t = item.get("topic") or default_topic
        if not t:
            raise TopicStoreError("batch edge missing topic (no --topic and no item.topic)")
        res = ts.add_edge(t, item["source"], item["target"], item["relation"],
                          write=False, force=item.get("force", False))
        touched.add(t)
        changes.append({**res, "topic": t})
    for t in sorted(touched):
        ts.write_export(t)
    return changes


def run(args):
    # all CLI ops use RO hydrate to avoid persistent WAL creation on pure inspections
    # writes (add/delete) will still persist via semantic_memory -> memory_engine -> kernel_db (persistent)
    ts.hydrate(use_ro=True)
    if args.cmd == "signals":
        return [], _emit_signals(_g(args, "json"), _g(args, "quiet"))
    if args.cmd == "check":
        names = [n.strip() for n in args.claims.split(",") if n.strip()]
        contras = ts.check_contradictions(args.topic, names)
        _emit_check(contras, _g(args, "json"), _g(args, "quiet"))
        return contras, []
    # add-node may bootstrap a new topic; topics/doctor need no topic;
    # everything else requires the topic to exist
    if (args.cmd not in ("add-node", "batch", "topics", "doctor", "signals", "check", "delete-topic")
            and not ts.has_topic(args.topic)):
        raise TopicStoreError(f"Topic not found: {args.topic}")
    if args.cmd == "neighbors":
        nb = ts.neighbors(args.topic, args.name)
        if _g(args, "json"):
            print(json.dumps(nb))
        elif not _g(args, "quiet"):
            print(f"  {nb['topic']}:{nb['name']} [{nb['status']}]")
            for e in nb["out_edges"]:
                print(f"    --{e['relation']}--> {e['target']}")
            for e in nb["in_edges"]:
                print(f"    <--{e['relation']}-- {e['source']}")
            for c in nb["cites"]:
                print(f"    cites {c['topic']}:{c['node']}")
            for c in nb["cited_by"]:
                print(f"    cited_by {c['topic']}:{c['node']}")
        return [], [{"kind": "neighbors", "topic": args.topic, "name": args.name}]
    if args.cmd == "batch":
        return [], _run_batch(args)
    if args.cmd == "topics":
        return [], _emit_topics(_g(args, "json"), _g(args, "quiet"))
    if args.cmd == "delete-topic":
        if _g(args, "dry_run"):
            counts = ts.count_topic(args.topic)
            return [], [{"kind": "topic_dry_run", "topic": args.topic,
                         "nodes_to_delete": counts["nodes"], "edges_to_delete": counts["edges"]}]
        result = ts.delete_topic(args.topic)
        return [], [result]
    if args.cmd == "set-stance":
        if _g(args, "dry_run"):
            cur = ts.load_beliefs().get("arguments", {}).get(args.name, {})
            same = isinstance(cur, dict) and cur.get("stance") == args.stance
            return [], [{"kind": "stance_skipped" if same else "stance_set",
                         "name": args.name, "stance": args.stance}]
        return [], [ts.set_stance(args.topic, args.name, args.stance,
                                  float(args.confidence))]
    if args.cmd == "add-node":
        meta = None
        if getattr(args, "metadata", None):
            try:
                meta = json.loads(args.metadata)
            except Exception as e:
                raise TopicStoreError(f"Invalid --metadata JSON: {e}")
        node = {"name": args.name, "side": args.side, "premise": args.premise,
                "sources": list(args.sources),
                "confidence": float(args.confidence),
                "metadata": meta,
                "evidence": list(getattr(args, "evidence", []) or []),
                "supersedes": getattr(args, "supersedes", None),
                "type": getattr(args, "node_type", None) or ("observation" if meta else "argument")}
        if _g(args, "dry_run"):
            exists = ts.find_node(args.topic, args.name) is not None
            return [], [{"kind": "node_skipped" if exists else "node_added",
                          "name": args.name}]
        res = ts.add_node(args.topic, node, force=getattr(args, "force", False))
        if res.get("kind") == "blocked_contradiction":
            print(f"BLOCKED: {res['reason']}\nconflicts: {res['conflicts']}\nHint: resolve prior claim(s) or re-run with --force after user approval.", file=sys.stderr)
            return [], [res]
        # stance defaults to agree for decisions so contradicts edges can fire
        stance = getattr(args, "stance", None) or ("agree" if args.side == "decision" else None)
        if stance and res.get("kind") == "node_added":
            res["stance"] = ts.set_stance(args.topic, args.name, stance).get("stance")
        return [], [res]

    if args.cmd == "add-edge":
        if _g(args, "dry_run"):
            edge_id = f"edge_{args.relation}_{args.source}_{args.target}"
            known = all(ts.find_node(args.topic, n)
                        for n in (args.source, args.target))
            kind = "edge_added" if known and edge_id not in ts.semantic_memory.edges \
                else "edge_skipped"
            return [], [{"kind": kind, "source": args.source,
                         "target": args.target}]
        change = ts.add_edge(args.topic, args.source, args.target,
                             args.relation, force=getattr(args, "force", False))
        if change.get("kind") == "blocked_contradiction":
            print(f"BLOCKED: {change['reason']}\nconflicts: {change['conflicts']}", file=sys.stderr)
            return [], [change]
        contradictions = []
        if change["kind"] == "edge_added" and args.relation == "contradicts":
            contradictions = ts.check_contradictions(
                args.topic, (args.source, args.target))
        return contradictions, [change]

    if args.cmd == "delete-node":
        node_id = getattr(args, 'node_id', None)
        name = getattr(args, 'name', None)
        if not node_id and not name:
            raise TopicStoreError("Either --name or --node-id required")
        if name:
            node = ts.find_node(args.topic, name)
            if node:
                node_id = node.node_id
            else:
                raise TopicStoreError(f"Node not found in topic {args.topic}: {name}")
        if _g(args, "dry_run"):
            counts = ts.count_node_edges(node_id)
            return [], [{"kind": "node_dry_run", "node_id": node_id,
                         "topic": args.topic, "edges_to_delete": counts["edges"]}]
        result = ts.delete_node(args.topic, node_id)
        return [], [result]

    if args.cmd == "delete-edge":
        if _g(args, "dry_run"):
            return [], [{"kind": "edge_dry_run", "edge_id": args.edge_id, "topic": args.topic}]
        result = ts.delete_edge(args.topic, args.edge_id)
        return [], [result]

    from argu_god.engine.topic_store import export_graph
    nodes = [n for n in export_graph(args.topic)["nodes"]
             if not args.side or n.get("side") == args.side]
    emit_list(_g(args, "json"), nodes)
    return [], []


def emit_list(as_json, nodes):
    if as_json:
        print(json.dumps(nodes))
        return
    for n in nodes:
        side = f" [{n['side']}]" if n.get("side") else ""
        print(f"  {n['name']}{side}  {(n.get('premise') or '')[:80]}")
    print(f"{len(nodes)} node(s)")


def _emit_topics(as_json, quiet):
    topics_list = ts.list_topics()
    if as_json:
        print(json.dumps(topics_list))
    elif not quiet:
        for t in topics_list:
            print(f"  {t}")
        print(f"{len(topics_list)} topic(s)")
    return []


def _emit_signals(as_json, quiet):
    from kernel.memory.memory_engine import memory_engine
    try:
        ids = [i for i in memory_engine.list_objects_ro("episodic") if i.startswith("contradiction_detected_")]
    except Exception:
        ids = [i for i in memory_engine.list_objects("episodic") if i.startswith("contradiction_detected_")]
    if as_json:
        print(json.dumps(ids))
    elif not quiet:
        for i in ids[:20]:
            print(f"  {i}")
        print(f"{len(ids)} signal(s)")
    return [{"kind": "signals", "count": len(ids), "ids": ids}]


def _emit_check(contras, as_json, quiet):
    if as_json:
        print(json.dumps([list(c) for c in contras]))
        return
    if not quiet:
        if not contras:
            print("  no contradictions")
        for a, b in contras:
            print(f"  CONTRADICTION: {a} <-> {b}")
        print(f"{len(contras)} contradiction(s)")


def report(args, changes, contradictions):
    path = ts.graph_path(args.topic) if args.topic else None
    rel = path.relative_to(Path(__file__).resolve().parents[1]) if path else ""
    signals = []
    for pair in contradictions:
        sid = ts.emit_contradiction_signal(pair, args.topic)
        signals.append(sid)
    if _g(args, "json"):
        print(json.dumps({"graph": str(path) if path else None,
                          "dry_run": _g(args, "dry_run"),
                          "changes": changes,
                          "contradictions": [list(c) for c in contradictions],
                          "signal_ids": signals}, separators=(",", ":")))
        return
    if not _g(args, "quiet"):
        for c in changes:
            kind = c.get("kind", "")
            if kind == "node_dry_run":
                print(f"  {kind:20s} node={c.get('node_id')} topic={c.get('topic')} "
                      f"edges={c.get('edges_to_delete', 0)}")
            elif kind == "topic_dry_run":
                print(f"  {kind:20s} topic={c.get('topic')} "
                      f"nodes={c.get('nodes_to_delete', 0)} edges={c.get('edges_to_delete', 0)}")
            elif kind == "edge_dry_run":
                print(f"  {kind:20s} edge={c.get('edge_id')} topic={c.get('topic')}")
            elif kind == "topic_deleted":
                print(f"  {kind:20s} topic={c.get('topic')} "
                      f"nodes={c.get('nodes_deleted', 0)} edges={c.get('edges_deleted', 0)}")
            elif kind == "node_deleted":
                eds = c.get('edges_deleted', [])
                print(f"  {kind:20s} node={c.get('node_id')} topic={c.get('topic')} "
                      f"edges={len(eds) if isinstance(eds, list) else eds}")
            elif kind == "edge_deleted":
                print(f"  {kind:20s} edge={c.get('edge_id')} topic={c.get('topic')}")
            elif kind in ("edge_not_found", "node_not_found"):
                print(f"  {kind:20s} {c.get('edge_id') or c.get('node_id')} topic={c.get('topic','')}")
            else:
                label = c.get("name") or c.get("source") or c.get("topic") or c.get("node_id") or c.get("edge_id") or ""
                extra = f" -> {c['stance']}" if kind == "stance_set" else ""
                print(f"  {kind:12s} {label}{extra}")
        for pair, sid in zip(contradictions, signals):
            print(f"  CONTRADICTION: {pair[0]} <-> {pair[1]}  signal={sid}")
    verb = "Would record" if _g(args, "dry_run") else "Recorded"
    if _g(args, "dry_run"):
        added = 0
        for c in changes:
            k = c.get("kind", "")
            if k == "topic_dry_run":
                added += int(c.get("nodes_to_delete", 0) or 0) + int(c.get("edges_to_delete", 0) or 0)
            elif k in ("node_dry_run", "edge_dry_run"):
                added += 1
            elif k.endswith("_added") or k == "stance_set":
                added += 1
    else:
        added = 0
        for c in changes:
            k = c.get("kind", "")
            if k == "topic_deleted":
                nd = int(c.get("nodes_deleted", 0) or 0)
                ed = int(c.get("edges_deleted", 0) or 0)
                added += nd + ed if (nd + ed) else 0
            elif k in ("node_deleted", "edge_deleted"):
                added += 1
            elif k.endswith("_added") or k == "stance_set":
                added += 1
            elif k.endswith("_deleted"):
                added += 1
    print(f"{verb} {added} change(s) in {rel}")


def run_doctor(args) -> int:
    ts.hydrate(use_ro=True)
    from kernel.memory.memory_engine import memory_engine
    from kernel.memory.semantic_memory import semantic_memory
    from kernel.persistence.db import kernel_db_ro

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

    topics_out, issues = [], []
    if integrity != "ok":
        issues.append(f"db integrity: {integrity}")
    if logs_n > 200:
        issues.append(f"logs table has {logs_n} rows (>200) — "
                      f"run scripts/prune_kernel_logs.py --keep 200")
    for t in ts.list_topics():
        tnodes = [n for n in semantic_memory.nodes.values()
                  if n.topic_id == t]
        id2name = {n.node_id: n.title for n in tnodes}
        tedges = [e for e in semantic_memory.edges.values()
                  if e.topic_id == t]
        live = [e for e in tedges
                if e.source_node_id in id2name and e.target_node_id in id2name]
        dangling = len(tedges) - len(live)
        exported = ts.export_graph(t)
        path = ts.graph_path(t)
        disk = json.loads(path.read_text(encoding="utf-8")) \
            if path.exists() else None
        parity = ("no export" if disk is None else
                  ("match" if (len(disk["nodes"]), len(disk["edges"]))
                   == (len(exported["nodes"]), len(exported["edges"]))
                   else "STALE"))
        if dangling:
            issues.append(f"topic {t}: {dangling} dangling edge(s)")
        if parity == "STALE":
            issues.append(f"topic {t}: derived export stale — rerun "
                          f"scripts/backfill_topics.py {t}")
        topics_out.append({"topic": t, "nodes": len(tnodes),
                           "edges": len(live), "dangling": dangling,
                           "export": parity})

    report = {"db_integrity": integrity, "log_rows": logs_n,
              "contradiction_signals": signals, "topics": topics_out,
              "issues": issues, "docs": _DOCS_HINT}
    if _g(args, "json"):
        print(json.dumps(report, separators=(",", ":")))
    else:
        print("KERNEL DOCTOR")
        print(f"  db integrity : {integrity}")
        print(f"  log rows     : {logs_n}"
              f"{'  (>200: prune suggested)' if logs_n > 200 else ''}")
        print(f"  signals      : {signals} contradiction_detected_*")
        for t in topics_out:
            print(f"  topic {t['topic']}: {t['nodes']}n/{t['edges']}e | "
                  f"export={t['export']} | dangling={t['dangling']}")
        for i in issues:
            print(f"  ISSUE: {i}")
        print(f"  {_DOCS_HINT}")
        print(f"overall: {'ISSUES' if issues else 'OK'}")
    return 1 if issues else 0


def main():
    args = build_parser().parse_args()
    if args.cmd == "doctor":
        try:
            return run_doctor(args)
        except TopicStoreError as e:
            print(f"error: {e}\nhint: {_DOCS_HINT}", file=sys.stderr)
            return 1
    try:
        contradictions, changes = run(args)
    except TopicStoreError as e:
        print(f"error: {e}\nhint: {_DOCS_HINT}", file=sys.stderr)
        return 1
    if args.cmd not in ("list", "topics", "signals", "check"):
        report(args, changes, contradictions)
    return 0


if __name__ == "__main__":
    sys.exit(main())
