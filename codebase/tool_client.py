#!/usr/bin/env python3
"""
Thin CLI to test code_rag agent tools directly (no server, no LLM).

Usage:
    python tool_client.py --atlas-dir <path> get_symbol <name>
    python tool_client.py --atlas-dir <path> search_symbols <query> [--type-filter function] [--top-k 10]
    python tool_client.py --atlas-dir <path> get_callers_callees <name> [--direction both]
    python tool_client.py --atlas-dir <path> find_impact <name>
    python tool_client.py --atlas-dir <path> index_info
    python tool_client.py --atlas-dir <path> --reindex get_symbol <name>

If CODEBASE_ATLAS_DIR env var is set, --atlas-dir can be omitted.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent_core.tools.code_rag import CodeRAG, _get_rag


def _resolve_rag(args) -> CodeRAG:
    atlas_dir = args.atlas_dir or os.environ.get("CODEBASE_ATLAS_DIR") or ""
    if not atlas_dir:
        ws = os.environ.get("AGENT_WORKSPACE_ROOT", os.getcwd())
        candidate = os.path.join(ws, "atlas_output")
        if os.path.isdir(candidate):
            atlas_dir = candidate
    if not atlas_dir or not os.path.isdir(atlas_dir):
        print("Error: atlas_output dir not found. Set CODEBASE_ATLAS_DIR env var or pass --atlas-dir.")
        sys.exit(1)
    rag = CodeRAG(atlas_dir)
    if args.reindex:
        db_path = rag.db_path
        if db_path.exists():
            db_path.unlink()
    rag.ensure_indexed()
    return rag


def cmd_get_symbol(rag, args):
    result = rag.get_symbol(args.name, args.file_path, args.parent_name)
    if result is None:
        print(f"Symbol '{args.name}' not found.")
        return
    if "matches" in result:
        print(f"Ambiguous: {len(result['matches'])} matches for '{args.name}':")
        for m in result["matches"]:
            print(f"  {m['symbol_name']} ({m['symbol_type']}) in {m['file_path']}")
        return
    print(f"Name:       {result['symbol_name']}")
    print(f"Type:       {result['symbol_type']}")
    print(f"File:       {result['file_path']}")
    print(f"Lines:      {result['start_line']}-{result['end_line']}")
    print(f"Parent:     {result['parent_name'] or '-'}")
    print(f"Signature:  {result['signature'] or '-'}")
    print(f"Risk:       {result['risk_level']}")
    if result.get("docstring"):
        print(f"Docstring:  {result['docstring'][:200]}")
    print("--- code ---")
    print(result.get("code", "") or "(no code)")


def cmd_search_symbols(rag, args):
    results = rag.search_symbols(args.query, args.type_filter, args.top_k)
    if not results:
        print(f"No results for '{args.query}'.")
        return
    print(f"{len(results)} results for '{args.query}':")
    for r in results:
        risk = r["risk_level"]
        print(f"  [{risk:>5}] {r['symbol_name']:30s} ({r['symbol_type']:>6})  {r['file_path']}")
        if r.get("signature"):
            print(f"         {r['signature']}")


def cmd_callers_callees(rag, args):
    result = rag.get_callers_callees(args.name, args.file_path, args.depth, args.direction)
    if "error" in result:
        print(result["error"])
        return
    print(f"Symbol: {result['symbol']['symbol_name']} ({result['symbol']['symbol_type']})")
    print(f"  in {result['symbol']['file_path']}")
    if args.direction in ("callers", "both"):
        print(f"\nCallers ({len(result['callers'])}):")
        for c in result["callers"] or []:
            print(f"  - {c['symbol_name']} in {c['file_path']}")
    if args.direction in ("callees", "both"):
        print(f"\nCallees ({len(result['callees'])}):")
        for c in result["callees"] or []:
            print(f"  - {c['symbol_name']} in {c['file_path']}")


def cmd_find_impact(rag, args):
    results = rag.find_impact(args.name, args.file_path)
    if not results:
        print(f"Nothing depends on '{args.name}'.")
        return
    print(f"{len(results)} dependents of '{args.name}':")
    for r in results:
        print(f"  [{r['risk_level']:>5}] {r['symbol_name']} ({r['symbol_type']}) in {r['file_path']}")


def cmd_index_info(rag, args):
    db_path = rag.db_path
    if db_path.exists():
        size = db_path.stat().st_size
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        cur = conn.execute("SELECT COUNT(*) FROM symbols")
        sym_count = cur.fetchone()[0]
        cur = conn.execute("SELECT COUNT(*) FROM call_edges")
        edge_count = cur.fetchone()[0]
        conn.close()
        print(f"DB:      {db_path}")
        print(f"Size:    {size / 1024:.0f} KB")
        print(f"Symbols: {sym_count}")
        print(f"Edges:   {edge_count}")
    else:
        print("No code_rag.db found — run a tool command first to index.")


def main():
    parser = argparse.ArgumentParser(description="Test code_rag agent tools")
    parser.add_argument("--atlas-dir", help="Path to atlas_output directory")
    parser.add_argument("--reindex", action="store_true", help="Re-index from scratch")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("get_symbol", help="Look up a function/class by name")
    p.add_argument("name")
    p.add_argument("--file-path", help="Disambiguate by file path")
    p.add_argument("--parent-name", help="Disambiguate by parent class")

    p = sub.add_parser("search_symbols", help="Full-text search across symbols")
    p.add_argument("query")
    p.add_argument("--type-filter", choices=["function", "class", "method", "file"], help="Filter by type")
    p.add_argument("--top-k", type=int, default=10)

    p = sub.add_parser("get_callers_callees", help="Show callers/callees of a function")
    p.add_argument("name")
    p.add_argument("--file-path", help="Disambiguate")
    p.add_argument("--depth", type=int, default=1)
    p.add_argument("--direction", choices=["callers", "callees", "both"], default="both")

    p = sub.add_parser("find_impact", help="Find all dependents of a symbol")
    p.add_argument("name")
    p.add_argument("--file-path", help="Disambiguate")

    p = sub.add_parser("index_info", help="Show indexing stats")

    args = parser.parse_args()
    rag = _resolve_rag(args)

    dispatch = {
        "get_symbol": cmd_get_symbol,
        "search_symbols": cmd_search_symbols,
        "get_callers_callees": cmd_callers_callees,
        "find_impact": cmd_find_impact,
        "index_info": cmd_index_info,
    }
    dispatch[args.command](rag, args)


if __name__ == "__main__":
    main()
