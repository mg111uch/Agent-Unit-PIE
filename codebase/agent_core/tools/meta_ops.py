from __future__ import annotations

import json, os, re

from agent_core.workspace import resolve, resolve_for_tool, WORKSPACE_ROOT, PathEscapeError, to_relative, root_basename_hint
from agent_core.config import EXCLUDE_DIRS
from agent_core.tools.types import ToolResult, _parse_arg

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
        res = resolve_for_tool(path, expect="file")
        if not res.ok:
            return ToolResult(ok=False, message=res.message)
        full = res.full
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


def cross_file_edit(input_data) -> ToolResult:
    """Apply edits across multiple files in one call (reuses _apply_single_edit).

    input_data = {"edits": [{"path": "...", "old_string": "...", "new_string": "...",
                             "replace_all": false}, ...]}
    """
    try:
        data = _parse_arg(input_data, {})
        edits = data.get("edits")
        if not edits or not isinstance(edits, list):
            return ToolResult(ok=False, message="'edits' (list of {path, old_string, new_string}) is required.")
        from agent_core.tools.file_ops import _apply_single_edit, _verify_python
        results = []
        ok_count = 0
        applied_py_paths = []
        for i, e in enumerate(edits):
            if not isinstance(e, dict):
                results.append(f"[edit {i}] ERROR: expected an object with path/old_string/new_string")
                continue
            path = e.get("path", "")
            old = e.get("old_string", "")
            new = e.get("new_string", "")
            replace_all = e.get("replace_all", False)
            if not path or not old:
                results.append(f"[edit {i}] ERROR: 'path' and 'old_string' are required")
                continue
            r = _apply_single_edit(path, old, new, replace_all=replace_all)
            if r.ok:
                ok_count += 1
                if path.endswith(".py") and path not in applied_py_paths:
                    applied_py_paths.append(path)
            results.append(f"[edit {i}] {r.data if r.ok else f'ERROR: {r.message}'}")
        verify_lines = []
        for path in applied_py_paths:
            try:
                res = resolve_for_tool(path, expect="file")
                v = _verify_python(res.full, res.rel) if res.ok else ""
            except Exception:
                v = ""
            if v:
                verify_lines.append(v)
        if verify_lines:
            results.append("[verify]\n" + "\n".join(verify_lines))
        results.append(f"Summary: {ok_count}/{len(edits)} edits applied")
        return ToolResult(ok=ok_count > 0, data="\n\n".join(results))
    except Exception as e:
        return ToolResult(ok=False, message=f"cross_file_edit error: {e}")


def _find_match_lines(content: str, old: str) -> list[int]:
    if "\n" in old:
        idx = content.find(old)
        if idx < 0:
            return []
        return [content[:idx].count("\n") + 1]
    return [i + 1 for i, line in enumerate(content.splitlines()) if old in line]


def _closest_line(content: str, old: str):
    tokens = [t for t in old.split() if len(t) >= 3]
    if not tokens:
        return None
    token = tokens[0]
    for i, line in enumerate(content.splitlines()):
        if token in line:
            return i + 1, line.strip()[:120]
    return None


def check_before_edit(input_data) -> ToolResult:
    """Read-only: verify planned edits would match exactly once BEFORE applying.

    input_data = {"edits": [{"path": "...", "old_string": "..."}, ...]}
    (also accepts a single {"path", "old_string"}).
    Returns per-edit: OK (match line), NO MATCH (+ closest line), or MULTIPLE (line list).
    """
    try:
        data = _parse_arg(input_data, {})
        if "edits" in data:
            edits = data["edits"]
        elif data.get("path") and data.get("old_string"):
            edits = [{"path": data["path"], "old_string": data["old_string"]}]
        else:
            edits = None
        if not edits or not isinstance(edits, list):
            return ToolResult(ok=False, message="'edits' (list of {path, old_string}) is required.")
        results = []
        ok_count = 0
        for i, e in enumerate(edits):
            if not isinstance(e, dict):
                results.append(f"[edit {i}] ERROR: expected an object with path/old_string")
                continue
            path = e.get("path", "")
            old = e.get("old_string", "")
            if not path or not old:
                results.append(f"[edit {i}] ERROR: 'path' and 'old_string' are required")
                continue
            try:
                res = resolve_for_tool(path, expect="file")
                if not res.ok:
                    results.append(f"[edit {i}] ERROR: {res.message}")
                    continue
                full = res.full
            except PathEscapeError as err:
                results.append(f"[edit {i}] ERROR: {err}")
                continue
            if not os.path.isfile(full):
                results.append(f"[edit {i}] ERROR: file not found: {path}")
                continue
            with open(full, "r", encoding="utf-8") as f:
                content = f.read()
            lines = _find_match_lines(content, old)
            if len(lines) == 1:
                ok_count += 1
                results.append(f"[edit {i}] OK — 1 match at line {lines[0]}  ({path})")
            elif not lines:
                close = _closest_line(content, old)
                hint = f"  closest: line {close[0]}: \"{close[1]}\"" if close else ""
                results.append(f"[edit {i}] NO MATCH{hint}  ({path})")
            else:
                results.append(f"[edit {i}] MULTIPLE ({len(lines)} matches at lines {', '.join(map(str, lines))})  ({path})")
        results.append(f"Summary: {ok_count}/{len(edits)} edits would match exactly once")
        return ToolResult(ok=ok_count > 0, data="\n\n".join(results))
    except Exception as e:
        return ToolResult(ok=False, message=f"check_before_edit error: {e}")
