import json
import re
import subprocess
import sys
from pathlib import Path
from datetime import datetime

from agent_core.config import CODEBASE_ATLAS_DIR as _CONFIG_ATLAS_DIR, CODEBASE_ROOT as _CODEBASE_ROOT
from agent_core.tools.code_rag.engine import _get_rag, _resolve_path


BUDGET_TOKENS = 8000


def _project_root() -> Path:
    return Path(_CODEBASE_ROOT).parent


# ── Factory ──────────────────────────────────────────────────────────

_NO_ATLAS_LONG = (
    "Codebase atlas not found. "
)


def _make_rag_tool(method, *, required=None, optional=None, resolve=(), post=None, err_no_atlas=None):
    """Generate a tool that inits rag, calls *method*(**kwargs), returns JSON."""
    def fn(params):
        rag = _get_rag()
        if rag is None:
            return err_no_atlas or "Codebase atlas not found."
        if not rag.ensure_indexed():
            return "Code RAG database not found or not indexed."
        kwargs = {}
        for k in (required or []):
            v = params.get(k)
            if v is None:
                return f"Error: '{k}' parameter is required."
            kwargs[k] = _resolve_path(v) if k in resolve else v
        for k in (optional or []):
            if k in params:
                kwargs[k] = _resolve_path(params[k]) if k in resolve else params[k]
        result = getattr(rag, method)(**kwargs)
        if isinstance(result, str) and ("Error" in result or "not found" in result):
            return result
        if post:
            result = post(result)
            if isinstance(result, str):
                return result
        return json.dumps(result, separators=(",", ":"))
    fn.__name__ = f"{method}_tool"
    return fn


# ── Post-processors ──────────────────────────────────────────────────

def _post_search(results):
    if not results:
        return f"No symbols matching the query."
    return {"results": [
        {k: r[k] for k in ("symbol_name","symbol_type","file_path","parent_name","start_line","end_line","risk_level")}
        for r in results
    ]}

def _post_callers_callees(result):
    if "error" in result:
        return result["error"]
    return {
        "symbol": {"name": result["symbol"]["symbol_name"], "type": result["symbol"]["symbol_type"], "file_path": result["symbol"]["file_path"]},
        "callers": [{"name": c["symbol_name"], "file": c["file_path"], "type": c["symbol_type"]} for c in result["callers"]],
        "callees": [{"name": c["symbol_name"], "file": c["file_path"], "type": c["symbol_type"]} for c in result["callees"]],
    }

def _post_impact(results):
    if not results:
        return "Nothing depends on the given symbol."
    return [{"name": r["symbol_name"], "file": r["file_path"], "type": r["symbol_type"], "risk": r["risk_level"]} for r in results]

def _post_file_api(result):
    if result.get("total_api_symbols", 0) == 0:
        return {"file_path": result.get("file_path", ""), "note": "No symbols found. File may not be indexed."}
    return result

def _post_symbols_by_file(result, path):
    if not result:
        return {"file_path": path, "symbols": [], "note": "No symbols found for this file."}
    return {"file_path": path, "symbols": result, "count": len(result)}

def _post_meta(symbols):
    for s in symbols:
        if s.get("docstring") and len(s["docstring"]) > 200:
            s["docstring"] = s["docstring"][:200] + "..."
    return {"symbols": symbols}


# ── Factory-generated tools (7) ──────────────────────────────────────

get_index_info_tool = _make_rag_tool("get_index_info")
call_chain_tool = _make_rag_tool("call_chain", required=["start_fn","end_module"], optional=["file_path"])
compare_apis_tool = _make_rag_tool("compare_apis", required=["path_a","path_b"], resolve=["path_a","path_b"])
search_symbols_tool = _make_rag_tool("search_symbols", required=[], optional=["query","queries","type_filter","top_k"], post=_post_search, err_no_atlas=_NO_ATLAS_LONG)
get_callers_callees_tool = _make_rag_tool("get_callers_callees", required=["name"], optional=["file_path","depth","direction"], post=_post_callers_callees)
find_impact_tool = _make_rag_tool("find_impact", required=["name"], optional=["file_path"], post=_post_impact)


# ── Semi-factory helpers (resolve + post) ────────────────────────────

def file_api_tool(params):
    rag = _get_rag()
    if rag is None:
        return "Codebase atlas not found."
    if not rag.ensure_indexed():
        return "Code RAG database not found or not indexed."
    paths = params.get("paths")
    if isinstance(paths, str):
        paths = [paths]
    single = params.get("path")
    if single:
        paths = [single] + (paths or [])
    if not paths:
        return "Error: 'path' (string) or 'paths' (list) parameter is required."
    result = rag.file_api(paths)
    posted = {k: _post_file_api(v) for k, v in result["files"].items()}
    if len(paths) == 1:
        return json.dumps(posted[paths[0]], separators=(",", ":"))
    return json.dumps({"files": posted, "total": len(paths)}, separators=(",", ":"))

def symbols_by_file_tool(params):
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
    return json.dumps(_post_symbols_by_file(result, resolved), separators=(",", ":"))

def atlas_status_tool(params):
    rag = _get_rag()
    if rag is None:
        return _NO_ATLAS_LONG
    if not rag.ensure_indexed():
        return json.dumps({"indexed": False, "atlas_db": str(rag.db_path)}, separators=(",", ":"))
    return json.dumps(rag.atlas_status(), separators=(",", ":"))

def get_symbols_meta_tool(params):
    rag = _get_rag()
    if rag is None:
        return "Codebase atlas not found."
    if not rag.ensure_indexed():
        return "Code RAG database not found or not indexed."
    names = params.get("names", [])
    if isinstance(names, str):
        names = [names]
    if not names:
        return "Error: 'names' (list) parameter is required."
    file_path = params.get("file_path")
    symbols = rag.get_symbols_meta(names, file_path)
    found = {s["symbol_name"] for s in symbols}
    missing = [n for n in names if n not in found]
    out = _post_meta(symbols)
    if missing:
        out["missing_names"] = missing
        out["hint"] = "Use search_symbols for misspelled names."
    return json.dumps(out, separators=(",", ":"))


# ── Special-case tools (8) ──────────────────────────────────────────

def get_symbol_tool(params: dict) -> str:
    rag = _get_rag()
    if rag is None:
        return _NO_ATLAS_LONG
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
            }, separators=(",", ":"))
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
        return json.dumps(output, separators=(",", ":"))
    return "Error: 'names' (list) or 'name' (string) parameter is required."


def project_root_tool(params: dict) -> str:
    return json.dumps({
        "project_root": str(_project_root()),
        "codebase_root": _CODEBASE_ROOT,
        "atlas_dir": _CONFIG_ATLAS_DIR or "",
    }, separators=(",", ":"))


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
        }, separators=(",", ":"))
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
        "destination": str(dest_path), "symbols_written": written,
        "total_lines": lines_written, "missing_code": missing if missing else None,
    }, separators=(",", ":"))


# ── Report tools (3) ─────────────────────────────────────────────────


def _iter_reports(pattern: str = "*.md"):
    """Yield (md_path, relative_path, file_text) for matching .md files in system_devpt_reports/."""
    reports_dir = _project_root() / "system_devpt_reports"
    if not reports_dir.is_dir():
        return
    for md_file in sorted(reports_dir.rglob(pattern)):
        rel = md_file.relative_to(_project_root())
        text = md_file.read_text(encoding="utf-8", errors="replace")
        yield md_file, rel, text


def report_freshness_tool(params: dict) -> str:
    date_re = re.compile(r'_Last verified:\s*(\d{4}-\d{2}-\d{2})_')
    citation_re = re.compile(r'`([\w./-]+\.py:\w+\(\))`')
    stale = []; ok = []; not_found = []
    for md_file, rel, text in _iter_reports():
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
                capture_output=True, text=True, timeout=10, cwd=_project_root(),
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
                func_part = cit.split(":")[1].rstrip("()")
                sym = rag.get_symbol(func_part)
                if sym is None:
                    broken.append(cit)
            if broken:
                stale.append({"file": str(rel), "last_verified": verified_str, "broken_citations": broken})
                continue
        ok.append({"file": str(rel), "last_verified": verified_str, "citations": len(citations)})
    return json.dumps({"ok": ok, "stale": stale, "no_date_stamp": not_found}, separators=(",", ":"))


def report_inventory_tool(params: dict) -> str:
    date_re = re.compile(r'_Last verified:\s*(\d{4}-\d{2}-\d{2})_')
    citation_re = re.compile(r'`([\w./-]+\.py:\w+\(\))`')
    entries = []
    for md_file, rel, text in _iter_reports():
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
        entries.append({
            "path": str(rel), "role": role, "module": parent,
            "lines": lines, "has_last_verified": bool(date_re.search(text)),
            "citations": len(citation_re.findall(text)), "empty": lines <= 1 and not text.strip(),
        })
    return json.dumps({"reports": entries, "count": len(entries)}, separators=(",", ":"))


def report_schema_check_tool(params: dict) -> str:
    date_re = re.compile(r'_Last verified:\s*(\d{4}-\d{2}-\d{2})_')
    citation_re = re.compile(r'`([\w./-]+\.py:\w+\(\))`')
    roadmap_lang = re.compile(r'phase|completed|planned|roadmap|not implemented', re.I)
    results = []
    for md_file, rel, text in _iter_reports("*/status.md"):
        issues = []
        if not date_re.search(text):
            issues.append("missing _Last verified")
        if "## Current Capability" not in text:
            issues.append("missing ## Current Capability")
        if "## Known Gaps" not in text:
            issues.append("missing ## Known Gaps")
        if "## Recent Changes" not in text:
            issues.append("missing ## Recent Changes")
        bullets = [l for l in text.splitlines() if l.strip().startswith("- ")]
        nc = sum(1 for b in bullets if not citation_re.search(b))
        if nc:
            issues.append(f"{nc} bullet(s) without citation")
        if roadmap_lang.search(text) and "## Current Capability" in text:
            issues.append("possible roadmap language in status")
        results.append({"file": str(rel), "issues": issues, "clean": len(issues) == 0})
    return json.dumps({"reports": results}, separators=(",", ":"))


# ── Hypothesis / Citation tools (2) ─────────────────────────────────

def list_capabilities_tool(params: dict) -> str:
    try:
        _sys2 = sys
        _sys2.path.insert(0, str(_project_root()))
        _sys2.path.insert(0, str(_project_root() / "codebase"))
        _sys2.path.insert(0, str(_project_root() / "scripts"))
        from kernel.hypothesis.hypothesis_engine import hypothesis_engine
        from scripts.seed_hypotheses import seed_all
        if not hypothesis_engine.hypotheses:
            seed_all(hypothesis_engine)
    except Exception as e:
        return json.dumps({"error": f"HypothesisEngine not available: {e}"})
    htype = params.get("type", "")
    hyps = hypothesis_engine.hypotheses.values()
    if htype:
        hyps = [h for h in hyps if h.hypothesis_type == htype]
    entries = [{
        "id": h.hypothesis_id, "type": h.hypothesis_type, "status": h.status,
        "title": h.title, "evidence_path": h.metadata.get("evidence_path", ""),
        "evidence_symbol": h.metadata.get("evidence_symbol", ""),
    } for h in sorted(hyps, key=lambda x: x.hypothesis_id)]
    return json.dumps({"hypotheses": entries, "count": len(entries), "filter_type": htype or "all"}, separators=(",", ":"))


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
        results.append({"citation": cit, "valid": True, "resolved": found, "path": resolved_path or filename})
    return json.dumps({"results": results}, separators=(",", ":"))
