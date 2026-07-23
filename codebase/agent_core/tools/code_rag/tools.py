import json
import re
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

from agent_core.config import CODEBASE_ATLAS_DIR as _CONFIG_ATLAS_DIR, CODEBASE_ROOT as _CODEBASE_ROOT
from agent_core.tools.code_rag.engine import _get_rag, _resolve_path


BUDGET_TOKENS = 8000


def _project_root() -> Path:
    return Path(_CODEBASE_ROOT).parent


def get_symbol_tool(params: dict) -> str:
    rag = _get_rag()
    if rag is None:
        return "Codebase atlas not found. Run `python -m codebase_atlas.main --project-dir <path> --output-dir ./atlas_output --serve` to generate it."
    rag.ensure_indexed()
    names = params.get("names")
    if not names:
        single = params.get("name", "")
        if single:
            names = [single]
    if names:
        if isinstance(names, str):
            names = [names]
        file_path = params.get("file_path")
        symbols = rag.get_symbols(names, file_path)
        found_names = {s["symbol_name"] for s in symbols}
        missing_names = [n for n in names if n not in found_names]
        if not symbols:
            return json.dumps({
                "error": f"No symbols found for: {names}",
                "missing_names": list(names),
                "hint": "Use search_symbols with a fuzzy query for possible misspellings, then get_symbol only for the exact names you need.",
            }, indent=2)
        results = []
        total_tokens = 0
        truncated_names = []
        for sym in symbols:
            sym_tokens = sym.get("token_count", 0) or 0
            total_tokens += sym_tokens
            if total_tokens > BUDGET_TOKENS and results:
                truncated_names.append(sym["symbol_name"])
            else:
                results.append(sym)
        output: dict = {"symbols": results}
        if missing_names:
            output["missing_names"] = missing_names
            output["hint"] = (
                "Some names were not found (check spelling). "
                "Call search_symbols only for missing names, then get_symbol with corrected exact names."
            )
        if truncated_names:
            output["truncated_names"] = truncated_names
        return json.dumps(output, indent=2)
    return "Error: 'names' (list) or 'name' (string) parameter is required."


def get_symbols_meta_tool(params: dict) -> str:
    rag = _get_rag()
    if rag is None:
        return "Codebase atlas not found."
    rag.ensure_indexed()
    names = params.get("names", [])
    if isinstance(names, str):
        names = [names]
    if not names:
        return "Error: 'names' (list) parameter is required."
    file_path = params.get("file_path")
    symbols = rag.get_symbols_meta(names, file_path)
    for s in symbols:
        if s.get("docstring") and len(s["docstring"]) > 200:
            s["docstring"] = s["docstring"][:200] + "..."
    found_names = {s["symbol_name"] for s in symbols}
    missing_names = [n for n in names if n not in found_names]
    output = {"symbols": symbols}
    if missing_names:
        output["missing_names"] = missing_names
        output["hint"] = "Use search_symbols for misspelled names."
    return json.dumps(output, indent=2)


def search_symbols_tool(params: dict) -> str:
    rag = _get_rag()
    if rag is None:
        return "Codebase atlas not found. Run `python -m codebase_atlas.main --project-dir <path> --output-dir ./atlas_output --serve` to generate it."
    rag.ensure_indexed()
    query = params.get("query", "")
    if not query:
        return "Error: 'query' parameter is required."
    type_filter = params.get("type_filter")
    top_k = params.get("top_k", 10)
    results = rag.search_symbols(query, type_filter, top_k)
    if not results:
        return f"No symbols matching '{query}'."
    summary = []
    for r in results:
        summary.append({
            "symbol_name": r["symbol_name"],
            "symbol_type": r["symbol_type"],
            "file_path": r["file_path"],
            "parent_name": r["parent_name"],
            "start_line": r["start_line"],
            "end_line": r["end_line"],
            "risk_level": r["risk_level"],
        })
    return json.dumps({"results": summary}, indent=2)


def get_callers_callees_tool(params: dict) -> str:
    rag = _get_rag()
    if rag is None:
        return "Codebase atlas not found."
    rag.ensure_indexed()
    name = params.get("name", "")
    if not name:
        return "Error: 'name' parameter is required."
    file_path = params.get("file_path")
    depth = params.get("depth", 1)
    direction = params.get("direction", "both")
    result = rag.get_callers_callees(name, file_path, depth, direction)
    if "error" in result:
        return result["error"]
    summary = {
        "symbol": {
            "name": result["symbol"]["symbol_name"],
            "type": result["symbol"]["symbol_type"],
            "file_path": result["symbol"]["file_path"],
        },
        "callers": [
            {"name": c["symbol_name"], "file": c["file_path"], "type": c["symbol_type"]}
            for c in result["callers"]
        ],
        "callees": [
            {"name": c["symbol_name"], "file": c["file_path"], "type": c["symbol_type"]}
            for c in result["callees"]
        ],
    }
    return json.dumps(summary, indent=2)


def find_impact_tool(params: dict) -> str:
    rag = _get_rag()
    if rag is None:
        return "Codebase atlas not found."
    rag.ensure_indexed()
    name = params.get("name", "")
    if not name:
        return "Error: 'name' parameter is required."
    file_path = params.get("file_path")
    results = rag.find_impact(name, file_path)
    if not results:
        return f"Nothing depends on '{name}'."
    summary = [
        {"name": r["symbol_name"], "file": r["file_path"],
         "type": r["symbol_type"], "risk": r["risk_level"]}
        for r in results
    ]
    return json.dumps(summary, indent=2)


def get_index_info_tool(params: dict) -> str:
    rag = _get_rag()
    if rag is None:
        return "Codebase atlas not found."
    if not rag.ensure_indexed():
        return "Code RAG database not found or not indexed."
    info = rag.get_index_info()
    return json.dumps(info, indent=2)


def file_api_tool(params: dict) -> str:
    rag = _get_rag()
    if rag is None:
        return "Codebase atlas not found."
    if not rag.ensure_indexed():
        return "Code RAG database not found or not indexed."
    path = params.get("path", "")
    if not path:
        return "Error: 'path' parameter is required."
    resolved = _resolve_path(path)
    result = rag.file_api(resolved)
    if result["total_api_symbols"] == 0:
        return json.dumps({"file_path": resolved, "note": "No symbols found. File may not be indexed."}, indent=2)
    return json.dumps(result, indent=2)


def call_chain_tool(params: dict) -> str:
    rag = _get_rag()
    if rag is None:
        return "Codebase atlas not found."
    if not rag.ensure_indexed():
        return "Code RAG database not found or not indexed."
    start_fn = params.get("start_fn", "")
    end_module = params.get("end_module", "")
    if not start_fn or not end_module:
        return "Error: 'start_fn' and 'end_module' parameters are required."
    file_path = params.get("file_path")
    result = rag.call_chain(start_fn, end_module, file_path)
    if "error" in result:
        return result["error"]
    return json.dumps(result, indent=2)


def compare_apis_tool(params: dict) -> str:
    rag = _get_rag()
    if rag is None:
        return "Codebase atlas not found."
    if not rag.ensure_indexed():
        return "Code RAG database not found or not indexed."
    path_a = params.get("path_a", "")
    path_b = params.get("path_b", "")
    if not path_a or not path_b:
        return "Error: 'path_a' and 'path_b' parameters are required."
    result = rag.compare_apis(_resolve_path(path_a), _resolve_path(path_b))
    return json.dumps(result, indent=2)


def symbols_by_file_tool(params: dict) -> str:
    rag = _get_rag()
    if rag is None:
        return "Codebase atlas not found."
    if not rag.ensure_indexed():
        return "Code RAG database not found or not indexed."
    path = params.get("path", "")
    if not path:
        return "Error: 'path' parameter is required."
    resolved = _resolve_path(path)
    result = rag.symbols_by_file(resolved)
    if not result:
        return json.dumps({"file_path": resolved, "symbols": [], "note": "No symbols found for this file."}, indent=2)
    return json.dumps({"file_path": resolved, "symbols": result, "count": len(result)}, indent=2)


def atlas_status_tool(params: dict) -> str:
    rag = _get_rag()
    if rag is None:
        return "Codebase atlas not found. Run `python -m codebase_atlas.main` to generate it."
    if not rag.ensure_indexed():
        return json.dumps({"indexed": False, "atlas_db": str(rag.db_path)}, indent=2)
    status = rag.atlas_status()
    return json.dumps(status, indent=2)


def project_root_tool(params: dict) -> str:
    return json.dumps({
        "project_root": str(_project_root()),
        "codebase_root": _CODEBASE_ROOT,
        "atlas_dir": _CONFIG_ATLAS_DIR or "",
    }, indent=2)


def batch_file_api_tool(params: dict) -> str:
    rag = _get_rag()
    if rag is None:
        return "Codebase atlas not found."
    if not rag.ensure_indexed():
        return "Code RAG database not found or not indexed."
    paths = params.get("paths", [])
    if not paths or not isinstance(paths, list):
        return "Error: 'paths' (list) parameter is required."
    result = rag.batch_file_api(paths)
    return json.dumps(result, indent=2)


def extract_symbols_to_file_tool(params: dict) -> str:
    rag = _get_rag()
    if rag is None:
        return "Error: Codebase atlas not found."
    if not rag.ensure_indexed():
        return "Error: Atlas not indexed."
    names = params.get("names", [])
    if isinstance(names, str):
        names = [names]
    if not names:
        return "Error: 'names' (list) parameter is required."
    dest = params.get("destination", "")
    if not dest:
        return "Error: 'destination' (file path) parameter is required."
    file_path = params.get("file_path")
    symbols = rag.get_symbols(names, file_path)
    if not symbols:
        return json.dumps({
            "error": f"No symbols found: {names}",
            "hint": "Use search_symbols to find correct names.",
        }, indent=2)
    dest_path = Path(dest)
    if not dest_path.is_absolute():
        dest_path = _project_root() / dest_path
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    lines_written = 0
    written = []
    missing = []
    for sym in symbols:
        name = sym.get("symbol_name", "?")
        code = sym.get("code", "")
        if not code:
            missing.append(name)
            continue
        header = f"# === {name} ({sym.get('symbol_type', '?')}) — {sym.get('file_path', '?')} ==="
        if sym.get("signature"):
            header += f"\n# Signature: {sym['signature']}"
        block = f"\n\n{header}\n\n{code}\n"
        with open(dest_path, "a") as f:
            f.write(block)
        lines_written += code.count("\n") + 1
        written.append(name)
    return json.dumps({
        "destination": str(dest_path),
        "symbols_written": written,
        "total_lines": lines_written,
        "missing_code": missing if missing else None,
    }, indent=2)


def report_freshness_tool(params: dict) -> str:
    reports_dir = _project_root() / "system_devpt_reports"
    if not reports_dir.is_dir():
        return "Error: system_devpt_reports/ not found."
    date_re = re.compile(r'_Last verified:\s*(\d{4}-\d{2}-\d{2})_')
    citation_re = re.compile(r'`([\w./-]+\.py:\w+\(\))`')
    stale = []
    ok = []
    not_found = []
    for md_file in sorted(reports_dir.rglob("*.md")):
        rel = md_file.relative_to(_project_root())
        text = md_file.read_text(encoding="utf-8", errors="replace")
        m = date_re.search(text)
        if not m:
            not_found.append({"file": str(rel), "reason": "No _Last verified date stamp."})
            continue
        verified_str = m.group(1)
        try:
            verified_date = datetime.strptime(verified_str, "%Y-%m-%d").date()
        except ValueError:
            not_found.append({"file": str(rel), "reason": f"Unparseable date: {verified_str}"})
            continue
        try:
            result = subprocess.run(
                ["git", "log", "-1", "--format=%ai", "--", str(md_file)],
                capture_output=True, text=True, timeout=10,
                cwd=_project_root(),
            )
            if result.returncode == 0 and result.stdout.strip():
                last_change = datetime.strptime(result.stdout.strip().split()[0], "%Y-%m-%d").date()
                if last_change > verified_date:
                    stale.append({"file": str(rel), "last_verified": verified_str, "last_git_change": str(last_change)})
                    continue
        except Exception:
            pass
        citations = citation_re.findall(text)
        if not citations:
            ok.append({"file": str(rel), "last_verified": verified_str, "citations": 0})
            continue
        rag = _get_rag()
        if rag and rag.ensure_indexed():
            broken = []
            for cit in citations:
                parts = cit.split(":")
                func_part = parts[1].rstrip("()")
                sym = rag.get_symbol(func_part)
                if sym is None:
                    broken.append(cit)
            if broken:
                stale.append({"file": str(rel), "last_verified": verified_str, "broken_citations": broken})
                continue
        ok.append({"file": str(rel), "last_verified": verified_str, "citations": len(citations)})
    return json.dumps({"ok": ok, "stale": stale, "no_date_stamp": not_found}, indent=2)


def report_inventory_tool(params: dict) -> str:
    reports_dir = _project_root() / "system_devpt_reports"
    if not reports_dir.is_dir():
        return json.dumps({"error": "system_devpt_reports/ not found"})
    date_re = re.compile(r'_Last verified:\s*(\d{4}-\d{2}-\d{2})_')
    citation_re = re.compile(r'`([\w./-]+\.py:\w+\(\))`')
    entries = []
    for md_file in sorted(reports_dir.rglob("*.md")):
        rel = md_file.relative_to(_project_root())
        text = md_file.read_text(encoding="utf-8", errors="replace")
        lines = text.count("\n") + 1
        parent = md_file.parent.name
        fname = md_file.name
        if fname == "status.md":
            role = "status"
        elif fname == "roadmap.md":
            role = "roadmap"
        elif fname == "README.md":
            role = "readme"
        else:
            role = "other"
        has_stamp = bool(date_re.search(text))
        citations = len(citation_re.findall(text))
        is_empty = lines <= 1 and not text.strip()
        entries.append({
            "path": str(rel), "role": role, "module": parent,
            "lines": lines, "has_last_verified": has_stamp,
            "citations": citations, "empty": is_empty,
        })
    return json.dumps({"reports": entries, "count": len(entries)}, indent=2)


def report_schema_check_tool(params: dict) -> str:
    reports_dir = _project_root() / "system_devpt_reports"
    date_re = re.compile(r'_Last verified:\s*(\d{4}-\d{2}-\d{2})_')
    citation_re = re.compile(r'`([\w./-]+\.py:\w+\(\))`')
    roadmap_lang = re.compile(r'phase|completed|planned|roadmap|not implemented', re.I)
    results = []
    for md_file in sorted(reports_dir.glob("*/status.md")):
        rel = md_file.relative_to(_project_root())
        text = md_file.read_text(encoding="utf-8", errors="replace")
        issues = []
        if not date_re.search(text):
            issues.append("missing _Last verified")
        has_cap = "## Current Capability" in text
        has_gaps = "## Known Gaps" in text
        has_recent = "## Recent Changes" in text
        if not has_cap:
            issues.append("missing ## Current Capability")
        if not has_gaps:
            issues.append("missing ## Known Gaps")
        if not has_recent:
            issues.append("missing ## Recent Changes")
        bullets = [l for l in text.splitlines() if l.strip().startswith("- ")]
        bullets_with_citation = sum(1 for b in bullets if citation_re.search(b))
        bullets_no_citation = len(bullets) - bullets_with_citation
        if bullets_no_citation:
            issues.append(f"{bullets_no_citation} bullet(s) without citation")
        if roadmap_lang.search(text) and has_cap:
            issues.append("possible roadmap language in status")
        results.append({
            "file": str(rel), "issues": issues, "clean": len(issues) == 0,
        })
    return json.dumps({"reports": results}, indent=2)


def list_capabilities_tool(params: dict) -> str:
    try:
        import sys as _sys2
        _sys2.path.insert(0, str(_project_root()))
        _sys2.path.insert(0, str(_project_root() / "codebase"))
        _sys2.path.insert(0, str(_project_root() / "scripts"))
        from kernel.hypothesis.hypothesis_engine import hypothesis_engine
        from scripts.seed_hypotheses import seed_all
        seed_all(hypothesis_engine)
    except Exception as e:
        return json.dumps({"error": f"HypothesisEngine not available: {e}"})
    htype = params.get("type", "")
    hyps = hypothesis_engine.hypotheses.values()
    if htype:
        hyps = [h for h in hyps if h.hypothesis_type == htype]
    entries = []
    for h in sorted(hyps, key=lambda x: x.hypothesis_id):
        entries.append({
            "id": h.hypothesis_id,
            "type": h.hypothesis_type,
            "status": h.status,
            "title": h.title,
            "evidence_path": h.metadata.get("evidence_path", ""),
            "evidence_symbol": h.metadata.get("evidence_symbol", ""),
        })
    return json.dumps({
        "hypotheses": entries,
        "count": len(entries),
        "filter_type": htype or "all",
    }, indent=2)


def resolve_citations_tool(params: dict) -> str:
    citations = params.get("citations", [])
    if isinstance(citations, str):
        citations = [citations]
    if not citations:
        return json.dumps({"error": "Provide citations list e.g. ['file.py:func()']"})
    cit_re = re.compile(r'([\w./-]+\.py):(\w+)\(\)')
    results = []
    for cit in citations:
        m = cit_re.match(cit)
        if not m:
            results.append({"citation": cit, "valid": False, "error": "bad format"})
            continue
        filename, funcname = m.group(1), m.group(2)
        sys.path.insert(0, str(_project_root()))
        sys.path.insert(0, str(_project_root() / "codebase"))
        from scripts.lib.citations import resolve_symbol
        found, resolved_path = resolve_symbol(filename, funcname)
        results.append({
            "citation": cit,
            "valid": True,
            "resolved": found,
            "path": resolved_path or filename,
        })
    return json.dumps({"results": results}, indent=2)
