from __future__ import annotations

import json, os, re

from agent_core.workspace import resolve, WORKSPACE_ROOT, PathEscapeError, to_relative, root_basename_hint
from agent_core.config import EXCLUDE_DIRS
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
