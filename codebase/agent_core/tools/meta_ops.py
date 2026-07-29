from __future__ import annotations

import json, os, re
from pathlib import Path
from typing import Any

from agent_core.workspace import resolve, WORKSPACE_ROOT, PathEscapeError, to_relative, root_basename_hint
from agent_core.config import CODEBASE_ROOT, EXCLUDE_DIRS
from agent_core.tools.types import ToolResult

_exclude_set = set(EXCLUDE_DIRS)


def get_workspace_info(_input=None) -> ToolResult:
    from agent_core.loop.session_state import get_session_state
    st = get_session_state()
    if st is not None and st.workspace_root and st.top_level_entries is not None:
        st.cache_hits += 1
        entries = st.top_level_entries
        return ToolResult(ok=True, data=(
            f"[cached workspace info]\n"
            f"Workspace root (use paths relative to this): {st.workspace_root}\n"
            f"Top-level entries: {entries}\n"
            f"All file paths you pass to read_file / write_to_file / list_files / edit_file "
            f"must be relative to this root (e.g. 'src/main.py', not an absolute OS path)."
        ))
    entries = sorted(os.listdir(WORKSPACE_ROOT))
    if st is not None:
        st.set_workspace(WORKSPACE_ROOT, entries)
        st.cache_misses += 1
    return ToolResult(ok=True, data=(
        f"Workspace root (use paths relative to this): {WORKSPACE_ROOT}\n"
        f"Top-level entries: {entries}\n"
        f"All file paths you pass to read_file / write_to_file / list_files / edit_file "
        f"must be relative to this root (e.g. 'src/main.py', not an absolute OS path)."
    ))


def _find_matching_basenames(basename: str) -> list[str]:
    matches = set()
    for dirpath, dirnames, filenames in os.walk(WORKSPACE_ROOT):
        dirnames[:] = [d for d in dirnames if d not in _exclude_set and not d.startswith(".")]
        for name in filenames + dirnames:
            if name == basename:
                rel = os.path.relpath(os.path.join(dirpath, name), WORKSPACE_ROOT)
                matches.add(rel)
    return sorted(matches)[:15]


def check_path_exists(path: str = "", **kwargs) -> ToolResult:
    path = kwargs.get("path") or kwargs.get("input") or path
    if not path:
        return ToolResult(ok=False, message="No path provided")
    try:
        full = resolve(path)
        rel = to_relative(full)
        if os.path.exists(full):
            kind = "directory" if os.path.isdir(full) else "file"
            return ToolResult(ok=True, data=f"exists ({kind}): {rel}")
        hint = root_basename_hint(path)
        parent = os.path.dirname(full) or WORKSPACE_ROOT
        nearby = []
        if os.path.isdir(parent):
            nearby = sorted(os.listdir(parent))[:20]
        basename = os.path.basename(path.rstrip("/\\"))
        alt_matches = _find_matching_basenames(basename) if basename else []
        alt_block = ""
        if alt_matches:
            alt_block = "\nPaths with matching name found elsewhere:\n  " + "\n  ".join(alt_matches)
        return ToolResult(ok=False, message=(
            f"not found: {rel}\n"
            f"Resolved to: {full}\n"
            f"Files in parent directory: {nearby if nearby else '(parent does not exist)'}"
            f"{hint}"
            f"{alt_block}"
        ))
    except PathEscapeError as e:
        return ToolResult(ok=False, message=str(e))
    except Exception as e:
        return ToolResult(ok=False, message=f"checking path: {e}")


def batch_read_tool(params: dict) -> ToolResult:
    if isinstance(params, str):
        try:
            params = json.loads(params)
        except json.JSONDecodeError:
            return ToolResult(ok=False, message="invalid JSON input.")
    paths = params.get("paths", []) if isinstance(params, dict) else []
    if not paths or not isinstance(paths, list):
        return ToolResult(ok=False, message="'paths' (list) parameter is required.")
    codebase = Path(CODEBASE_ROOT)
    results = {}
    for p in paths:
        resolved = (codebase / p) if not Path(p).is_absolute() else Path(p)
        kernel_dir = codebase / "kernel"
        is_kernel = False
        try:
            is_kernel = kernel_dir in resolved.parents
        except ValueError:
            pass
        if not resolved.exists():
            results[p] = {"error": "File not found."}
            continue
        if resolved.is_dir():
            results[p] = {"error": "Path is a directory. Use glob_search or list_files instead."}
            continue
        content = resolved.read_text(encoding="utf-8", errors="replace")
        lines = content.split("\n")
        entry = {"lines": len(lines), "content": content}
        if is_kernel:
            entry["warning"] = "Prefer file_api or symbols_by_file for kernel files — this is a raw file read."
        results[p] = entry
    counts = {"ok": sum(1 for v in results.values() if "content" in v), "errors": sum(1 for v in results.values() if "error" in v)}
    return ToolResult(ok=True, data=json.dumps({"files": results, "summary": counts}, separators=(",", ":")))


def read_section_tool(params: dict) -> ToolResult:
    if isinstance(params, str):
        try:
            params = json.loads(params)
        except json.JSONDecodeError:
            return ToolResult(ok=False, message="invalid JSON input.")
    path = params.get("path", "")
    if not path:
        return ToolResult(ok=False, message="'path' parameter is required.")
    pattern = params.get("pattern", "")
    if not pattern:
        return ToolResult(ok=False, message="'pattern' (regex) parameter is required.")
    context_lines = params.get("context_lines", 10)
    ignore_case = params.get("ignore_case", False)
    try:
        full = resolve(path)
        if not os.path.isfile(full):
            return ToolResult(ok=False, message=f"file not found: {path}")
        flags = re.IGNORECASE if ignore_case else 0
        compiled = re.compile(pattern, flags)
        with open(full, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        matches = []
        for i, line in enumerate(lines):
            if compiled.search(line):
                start = max(0, i - context_lines)
                end = min(len(lines), i + context_lines + 1)
                block = "".join(
                    f"{j+1:>6}: {lines[j]}"
                    for j in range(start, end)
                )
                matches.append({
                    "match_line": i + 1,
                    "matched_text": line.rstrip()[:200],
                    "context": f"Lines {start+1}-{end} (match at {i+1}):\n{block}",
                })
        if not matches:
            return ToolResult(ok=True, data=json.dumps({
                "path": path,
                "pattern": pattern,
                "matches": [],
                "total_lines": len(lines),
            }, separators=(",", ":")))
        return ToolResult(ok=True, data=json.dumps({
            "path": path,
            "pattern": pattern,
            "match_count": len(matches),
            "total_lines": len(lines),
            "matches": matches,
        }, separators=(",", ":")))
    except re.error as e:
        return ToolResult(ok=False, message=f"invalid regex pattern '{pattern}': {e}")
    except Exception as e:
        return ToolResult(ok=False, message=f"reading '{path}': {e}")


def batch_edit_tool(params: dict) -> ToolResult:
    if isinstance(params, str):
        try:
            params = json.loads(params)
        except json.JSONDecodeError:
            return ToolResult(ok=False, message="invalid JSON input.")
    path = params.get("path", "")
    edits = params.get("edits", [])
    if not path:
        return ToolResult(ok=False, message="'path' parameter is required.")
    if not edits or not isinstance(edits, list):
        return ToolResult(ok=False, message="'edits' (list) parameter is required.")
    results = []
    for i, edit in enumerate(edits):
        old_str = edit.get("old_string", "")
        new_str = edit.get("new_string", "")
        if not old_str:
            results.append({"edit": i, "status": "error", "message": "old_string is required"})
            continue
        try:
            full = resolve(path)
            if not os.path.exists(full):
                results.append({"edit": i, "status": "error", "message": "file not found"})
                continue
            with open(full, "r", encoding="utf-8") as f:
                content = f.read()
            count = content.count(old_str)
            if count == 0:
                results.append({"edit": i, "status": "error", "message": "old_string not found"})
                continue
            if count > 1 and not edit.get("replace_all"):
                results.append({"edit": i, "status": "error", "message": f"old_string has {count} matches — set replace_all=true or refine"})
                continue
            replacement_count = count if edit.get("replace_all") else 1
            updated = content.replace(old_str, new_str, replacement_count)
            with open(full, "w", encoding="utf-8") as f:
                f.write(updated)
            results.append({"edit": i, "status": "ok", "replaced": replacement_count})
        except Exception as e:
            results.append({"edit": i, "status": "error", "message": str(e)})
    ok_count = sum(1 for r in results if r["status"] == "ok")
    return ToolResult(ok=True, data=json.dumps({"file": path, "edits": results, "summary": f"{ok_count}/{len(edits)} edits applied"}, separators=(",", ":")))
