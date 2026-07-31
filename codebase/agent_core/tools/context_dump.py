import os
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

from agent_core.config import CODEBASE_ROOT
from agent_core.tools.code_rag.engine import _get_rag, _resolve_path

DEFAULT_TOKEN_BUDGET = 20000
DEFAULT_OUTPUT = os.path.join(os.path.dirname(CODEBASE_ROOT), "context_dump.txt")


def _add_section(header: str, body: str, sections: list, max_tokens: int, used_tokens: int) -> int:
    block = f"{header}\n{body}\n"
    tok = len(block) // 4
    if used_tokens + tok > max_tokens:
        return -1
    sections.append(block)
    return used_tokens + tok


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
    graph = {}

    if problem:
        used_tokens = _add_section("=" * 60, "", sections, max_tokens, used_tokens)
        used_tokens = _add_section("PROBLEM DESCRIPTION", "", sections, max_tokens, used_tokens)
        used_tokens = _add_section("", problem, sections, max_tokens, used_tokens)
        used_tokens = _add_section("", "", sections, max_tokens, used_tokens)

    if symbol_names:
        if isinstance(symbol_names, str):
            symbol_names = [symbol_names]
        used_tokens = _add_section("=" * 60, "", sections, max_tokens, used_tokens)
        used_tokens = _add_section("BLAST RADIUS ANALYSIS", "", sections, max_tokens, used_tokens)
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
        used_tokens = _add_section("", f"Starting symbols: {', '.join(symbol_names)}", sections, max_tokens, used_tokens)
        used_tokens = _add_section("", f"Blast radius: {len(blast)} symbols across call graph", sections, max_tokens, used_tokens)
        for name, edges in graph.items():
            c_str = ", ".join(edges["callers"]) or "(none)"
            e_str = ", ".join(edges["callees"]) or "(none)"
            used_tokens = _add_section("", f"  {name}: called by [{c_str}], calls [{e_str}]", sections, max_tokens, used_tokens)

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
                result = _add_section(header_line, f"```\n{code}\n```", sections, max_tokens, used_tokens)
                if result < 0:
                    warnings.append(f"Token budget reached, skipped {sn}")
                    break
                used_tokens = result
                total_symbols += 1
            else:
                used_tokens = _add_section(header_line, "(source not indexed)", sections, max_tokens, used_tokens)

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
            result = _add_section("", "\n".join(api_lines), sections, max_tokens, used_tokens)
            if result < 0:
                continue
            used_tokens = result
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
    used_tokens = _add_section("=" * 60, "", sections, max_tokens, used_tokens)
    _add_section("SUMMARY", json.dumps(summary, indent=2), sections, max_tokens, used_tokens)

    try:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w") as f:
            f.write("\n".join(sections))
    except OSError as e:
        return f"Error writing output: {e}"

    return json.dumps(summary, separators=(",", ":"))
