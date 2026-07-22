import os
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

from agent_core.config import CODEBASE_ROOT
from agent_core.tools.code_rag.engine import _get_rag, _resolve_path

DEFAULT_TOKEN_BUDGET = 20000
DEFAULT_OUTPUT = os.path.join(os.path.dirname(CODEBASE_ROOT), "context_dump.txt")


def _rough_token_count(text: str) -> int:
    return len(text) // 4


def _collect_blast_radius(rag, names: List[str], output: Dict[str, Any]) -> None:
    seen: set = set()
    for name in names:
        if name in seen:
            continue
        cc = rag.get_callers_callees(name)
        if "error" in cc:
            output.setdefault("warnings", []).append(cc["error"])
            continue
        for group in ("callers", "callees"):
            for sym in cc.get(group, []):
                sn = sym["symbol_name"]
                if sn not in seen and sn != name:
                    seen.add(sn)
        seen.add(name)
    return list(seen)


def minimal_context_dump(params: dict) -> str:
    rag = _get_rag()
    if rag is None:
        return "Error: Codebase atlas not found. Run atlas generation first."
    if not rag.ensure_indexed():
        return "Error: Atlas not indexed."

    problem = params.get("problem_description", "")
    symbol_names = params.get("symbol_names") or params.get("names") or []
    file_paths = params.get("file_paths") or params.get("file_path") or []
    output_path = params.get("output_path") or DEFAULT_OUTPUT
    max_tokens = params.get("max_tokens") or DEFAULT_TOKEN_BUDGET

    sections: List[str] = []
    used_tokens = 0
    total_symbols = 0
    peripheral_files = 0
    warnings: List[str] = []
    graph = {}  # symbol -> {callers, callees}

    def _add_section(header: str, body: str) -> bool:
        nonlocal used_tokens
        block = f"{header}\n{body}\n"
        tok = _rough_token_count(block)
        if used_tokens + tok > max_tokens:
            return False
        sections.append(block)
        used_tokens += tok
        return True

    if problem:
        _add_section("=" * 60, "")
        _add_section("PROBLEM DESCRIPTION", "")
        _add_section("", problem)
        _add_section("", "")

    if symbol_names:
        if isinstance(symbol_names, str):
            symbol_names = [symbol_names]
        _add_section("=" * 60, "")
        _add_section("BLAST RADIUS ANALYSIS", "")
        blast = set()
        for name in symbol_names:
            cc = rag.get_callers_callees(name)
            if "error" in cc:
                warnings.append(cc["error"])
                continue
            callers = [s["symbol_name"] for s in cc.get("callers", [])]
            callees = [s["symbol_name"] for s in cc.get("callees", [])]
            graph[name] = {"callers": callers, "callees": callees}
            blast.add(name)
            blast.update(callers)
            blast.update(callees)
        _add_section("", f"Starting symbols: {', '.join(symbol_names)}")
        _add_section("", f"Blast radius: {len(blast)} symbols across call graph")
        for name, edges in graph.items():
            c_str = ", ".join(edges["callers"]) or "(none)"
            e_str = ", ".join(edges["callees"]) or "(none)"
            _add_section("", f"  {name}: called by [{c_str}], calls [{e_str}]")

        symbols_data = rag.get_symbols(list(blast))
        for sym in symbols_data:
            sn = sym.get("symbol_name", "?")
            st = sym.get("symbol_type", "?")
            fp = sym.get("file_path", "?")
            sig = sym.get("signature", "")
            code = sym.get("source_code") or sym.get("code", "")
            header_line = f"## {sn} ({st}) — {fp}"
            if sig and sig not in code:
                header_line += f"\n```\n{sig}\n```"
            if code:
                if not _add_section(header_line, f"```\n{code}\n```"):
                    warnings.append(f"Token budget reached, skipped {sn}")
                    break
                total_symbols += 1
            else:
                _add_section(header_line, "(source not indexed)")

    if file_paths:
        if isinstance(file_paths, str):
            file_paths = [file_paths]
        for fp in file_paths:
            resolved = _resolve_path(fp)
            api = rag.file_api(resolved)
            if api["total_api_symbols"] == 0:
                continue
            api_lines = [f"## API: {fp}"]
            for f in api.get("functions", []):
                api_lines.append(f"  def {f['symbol_name']}{f.get('signature', '()')}")
                if f.get("docstring_first_line"):
                    api_lines.append(f"    {f['docstring_first_line']}")
            for cls in api.get("classes", []):
                api_lines.append(f"  class {cls['class_name']}:")
                for m in cls.get("methods", []):
                    api_lines.append(f"    def {m['symbol_name']}{m.get('signature', '()')}")
                    if m.get("docstring_first_line"):
                        api_lines.append(f"      {m['docstring_first_line']}")
            if _add_section("", "\n".join(api_lines)):
                peripheral_files += 1

    summary = {
        "sections": len(sections),
        "symbols_included": total_symbols,
        "peripheral_files": peripheral_files,
        "estimated_tokens": used_tokens,
        "budget": max_tokens,
        "output_file": output_path,
    }
    if warnings:
        summary["warnings"] = warnings
    _add_section("=" * 60, "")
    _add_section("SUMMARY", json.dumps(summary, indent=2))

    try:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w") as f:
            f.write("\n".join(sections))
    except OSError as e:
        return f"Error writing output: {e}"

    return json.dumps(summary, indent=2)
