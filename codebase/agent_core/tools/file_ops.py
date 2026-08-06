from __future__ import annotations

import os
import subprocess
import sys

from agent_core.workspace import resolve, resolve_for_tool, PathEscapeError, to_relative, not_found_message
from agent_core.tools.undo_ops import save_checkpoint
from agent_core.config import EXCLUDE_DIRS, CODEBASE_ROOT, POST_EDIT_IMPORT_CHECK
from agent_core.tools.types import ToolResult, _parse_arg
from agent_core.tools.diff_ops import _render_unified_diff, _compute_diff


def _verify_python(full: str, rel: str) -> str:
    """Post-edit verification for .py files. Returns '[verify]' warning text or ''.

    Always py_compiles (fast, in-process). When the file is under agent_core/tools/
    and post_edit_import_check is enabled, also imports agent_core.tools in a
    subprocess to catch schema/registration errors. Warn-only — never fails the edit.
    """
    if not rel.endswith(".py"):
        return ""
    try:
        with open(full, "r", encoding="utf-8") as f:
            compile(f.read(), full, "exec")
    except SyntaxError as e:
        return f"[verify] {rel}: SYNTAX ERROR (line {e.lineno}): {e.msg}"
    except Exception as e:
        return f"[verify] {rel}: compile failed: {e}"
    if not (POST_EDIT_IMPORT_CHECK and rel.startswith("agent_core/tools/")):
        return ""
    try:
        r = subprocess.run(
            [sys.executable, "-c", "import agent_core.tools"],
            cwd=CODEBASE_ROOT, capture_output=True, text=True, timeout=15,
        )
        if r.returncode != 0:
            tail = "\n".join((r.stderr or r.stdout).splitlines()[-5:])
            return f"[verify] {rel}: import agent_core.tools FAILED:\n{tail}"
    except subprocess.TimeoutExpired:
        return f"[verify] {rel}: import check timed out (skipped)"
    except Exception as e:
        return f"[verify] {rel}: import check error: {e}"
    return ""


def _record_file_access(rel, mode):
    try:
        from kernel.persistence.db import kernel_db
        kernel_db.record_file_access(rel, mode)
    except Exception:
        pass

_exclude_set = set(EXCLUDE_DIRS)


def _ensure_dir(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)


def _read_file_content(full: str, offset: int = 0, limit: int = 1000, line_numbers: bool = True) -> ToolResult:
    with open(full, "r", encoding="utf-8") as f:
        lines = f.readlines()

    start = max(0, offset - 1) if offset > 0 else 0
    end = start + limit if limit else len(lines)
    lines = lines[start:end]
    line_offset = start + 1

    if line_numbers:
        numbered = "\n".join(
            f"{i + line_offset:>5}\t{line.rstrip()}"
            for i, line in enumerate(lines)
        )
    else:
        numbered = "\n".join(line.rstrip() for line in lines)
    header = f"--- {to_relative(full)} ---"
    header += f" (lines {line_offset}-{line_offset + len(lines) - 1} of ~{_count_lines(full)})"
    return ToolResult(ok=True, data=f"{header}\n{numbered}")


def _count_lines(path: str) -> int:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def _read_single(path, offset=0, limit=None, line_numbers=True) -> ToolResult:
    """Read one file. offset/limit follow single-path semantics: limit=None
    means 'not specified' (default 1000 lines, session-cache eligible)."""
    try:
        offset = int(offset or 0)
        if isinstance(line_numbers, str):
            line_numbers = line_numbers.lower() in ("true", "1", "yes")
        res = resolve_for_tool(path, expect="file")
        if not res.ok:
            return ToolResult(ok=False, message=res.message)
        full = res.full
        rel = res.rel
        _record_file_access(rel, "read")
        if not os.path.exists(full):
            return ToolResult(ok=False, message=not_found_message(path, full, rel))
        # Session cache: default reads only (no explicit offset/limit params)
        cache_eligible = (offset == 0 and limit is None)
        if cache_eligible:
            from agent_core.loop.session_state import get_session_state
            st = get_session_state()
            if st is not None:
                cached = st.get_cached_file(rel)
                if cached is not None:
                    # mtime staleness check (cheap stat, no content read)
                    disk_mtime = os.path.getmtime(full)
                    ent = st.file_cache.get(rel)
                    if ent and disk_mtime == ent.mtime:
                        line_count = cached.count("\n")
                        return ToolResult(ok=True, data=f"(cached: {line_count} lines, unchanged)")
                    # Disk changed — invalidate cache and fall through
                    st.mark_stale(rel)
        actual_limit = int(limit) if limit is not None else 1000
        result = _read_file_content(full, offset=offset, limit=actual_limit, line_numbers=line_numbers)
        if result.ok and cache_eligible:
            from agent_core.loop.session_state import get_session_state
            st = get_session_state()
            if st is not None:
                st.put_file(rel, result.data, mtime=os.path.getmtime(full))
        return result
    except PathEscapeError as e:
        return ToolResult(ok=False, message=str(e))
    except Exception as e:
        return ToolResult(ok=False, message=f"reading {path}: {e}")


def _read_many(paths, offset=0, limit=None, line_numbers=True) -> ToolResult:
    """Batch read. Each entry is a path string or {path, offset?, limit?, line_numbers?}.
    Top-level offset/limit/line_numbers act as defaults for entries that omit them."""
    if not paths or not isinstance(paths, list):
        return ToolResult(ok=False, message="'paths' (list) parameter is required.")
    blocks = []
    stats = {"ok": 0, "errors": 0}
    for entry in paths:
        if isinstance(entry, dict):
            p = entry.get("path", "")
            off, lim, ln = entry.get("offset", offset), entry.get("limit", limit), entry.get("line_numbers", line_numbers)
        else:
            p, off, lim, ln = entry, offset, limit, line_numbers
        if not p:
            stats["errors"] += 1
            blocks.append("--- (missing path) ---\nERROR: 'path' is required for each entry")
            continue
        res = _read_single(p, offset=off, limit=lim, line_numbers=ln)
        if res.ok:
            stats["ok"] += 1
            blocks.append(res.data)
        else:
            stats["errors"] += 1
            blocks.append(f"--- {p} ---\nERROR: {res.message}")
    return ToolResult(ok=stats["ok"] > 0, data="\n\n".join(blocks))


def read_file(path: str = "", **kwargs) -> ToolResult:
    path = kwargs.get("path") or kwargs.get("input") or kwargs.get("file") or path
    paths = kwargs.get("paths")
    offset = kwargs.get("offset", 0)
    limit = kwargs.get("limit")
    line_numbers = kwargs.get("line_numbers", True)
    if paths:
        return _read_many(paths, offset=offset, limit=limit, line_numbers=line_numbers)
    return _read_single(path, offset=offset, limit=limit, line_numbers=line_numbers)


def list_files(path: str = ".", **kwargs) -> ToolResult:
    path = kwargs.get("path") or kwargs.get("directory") or kwargs.get("dir") or kwargs.get("input") or path
    if not path:
        path = "."
    try:
        res = resolve_for_tool(path, expect="any")
        if not res.ok:
            return ToolResult(ok=False, message=res.message)
        full = res.full
        if os.path.isfile(full):
            parent = os.path.dirname(full) or full
            full = parent
        if not os.path.isdir(full):
            return ToolResult(ok=False, message=f"not a directory: {path}")
        names = [n for n in sorted(os.listdir(full)) if n not in _exclude_set]
        dir_names = [n for n in names if os.path.isdir(os.path.join(full, n))]
        lines = []
        for name in names:
            if name not in dir_names:
                lines.append(f"  {name}")
        for name in dir_names:
            lines.append(f"  {name}/")
            children = [c for c in sorted(os.listdir(os.path.join(full, name))) if c not in _exclude_set]
            for c in children[:5]:
                cpath = os.path.join(full, name, c)
                lines.append(f"    {c}/" if os.path.isdir(cpath) else f"    {c}")
            extra = len(children) - 5
            if extra > 0:
                lines.append(f"    ... {extra} more entries")
        total = len(lines)
        if total > 50:
            lines = lines[:50]
            lines.append(f"... {total - 50} more entries")
        data = "\n".join(lines) if lines else "(empty directory)"
        return ToolResult(ok=True, data=data)
    except PathEscapeError as e:
        return ToolResult(ok=False, message=str(e))
    except Exception as e:
        return ToolResult(ok=False, message=f"listing {path}: {e}")


def write_to_file(input_data) -> ToolResult:
    """Write to file with modes: create, overwrite, append.

    input_data = {
        "path": "relative/path.txt",
        "mode": "create|overwrite|append",
        "content": "string (optional)",
        "dry_run": false
    }

    For targeted edits on existing files, use edit_file instead.
    """
    try:
        input_data = _parse_arg(input_data, {})

        path = input_data.get("path")
        mode = input_data.get("mode")
        content = input_data.get("content", "")
        dry_run = input_data.get("dry_run", False)

        if not path or not mode:
            return ToolResult(ok=False, message="'path' and 'mode' are required")

        res = resolve_for_tool(path, expect="target" if mode == "create" else "file")
        if not res.ok:
            return ToolResult(ok=False, message=res.message)
        full_path = res.full
        _record_file_access(res.rel, mode)
        exists = os.path.exists(full_path)

        rel = res.rel
        from agent_core.loop.session_state import get_session_state
        st = get_session_state()

        if mode == "create":
            if exists:
                return ToolResult(ok=False, message=f"File already exists: {rel}")
            _ensure_dir(full_path)
            if not dry_run:
                with open(full_path, "w") as f:
                    f.write(content)
            if st is not None and not dry_run:
                st.put_file(rel, content, mtime=os.path.getmtime(full_path))
                st.record_edit(rel, f"create {len(content)} chars")
            verify = "" if dry_run else _verify_python(full_path, rel)
            return ToolResult(ok=True, data=f"[CREATE] {rel} ({len(content)} chars)"
                                          + (f"\n{verify}" if verify else ""))

        elif mode == "overwrite":
            ckpt_saved = save_checkpoint(full_path) if not dry_run else None
            _ensure_dir(full_path)
            if not dry_run:
                with open(full_path, "w") as f:
                    f.write(content)
            if st is not None and not dry_run:
                st.put_file(rel, content, mtime=os.path.getmtime(full_path))
                st.record_edit(rel, f"overwrite {len(content)} chars")
            ckpt = " [checkpoint saved]" if ckpt_saved else ""
            verify = "" if dry_run else _verify_python(full_path, rel)
            return ToolResult(ok=True, data=f"[OVERWRITE] {rel} ({len(content)} chars){ckpt}"
                                          + (f"\n{verify}" if verify else ""))

        elif mode == "append":
            _ensure_dir(full_path)
            if not dry_run:
                with open(full_path, "a") as f:
                    f.write(content)
            if st is not None and not dry_run:
                st.mark_stale(rel)
                st.record_edit(rel, f"append +{len(content)} chars")
            verify = "" if dry_run else _verify_python(full_path, rel)
            return ToolResult(ok=True, data=f"[APPEND] {rel} (+{len(content)} chars)"
                                          + (f"\n{verify}" if verify else ""))

        else:
            return ToolResult(ok=False, message=f"Unknown mode '{mode}'")

    except PathEscapeError as e:
        return ToolResult(ok=False, message=str(e))
    except Exception as e:
        return ToolResult(ok=False, message=str(e))


def _apply_single_edit(path, old, new, replace_all=False) -> ToolResult:
    try:
        res = resolve_for_tool(path, expect="file")
        if not res.ok:
            return ToolResult(ok=False, message=res.message)
        full = res.full
        rel = res.rel
        _record_file_access(rel, "edit")
        if not os.path.exists(full):
            return ToolResult(ok=False, message=not_found_message(path, full, rel))
        with open(full, "r", encoding="utf-8") as f:
            content = f.read()
        if not old:
            return ToolResult(ok=False, message="old_string is required.")
        count = content.count(old)
        if count == 0:
            return ToolResult(ok=False, message=(
                "old_string not found. Re-read the file with read_file "
                "(it shows exact line numbers/whitespace) and copy the text exactly."
            ))
        if count > 1 and not replace_all:
            return ToolResult(ok=False, message=(
                f"old_string is not unique ({count} matches). "
                "Include more surrounding lines so the match is unambiguous, or set replace_all=true."
            ))
        ckpt_saved = save_checkpoint(full)
        replacement_count = count if replace_all else 1
        updated = content.replace(old, new, replacement_count)
        with open(full, "w", encoding="utf-8") as f:
            f.write(updated)

        # Prefer full-file unified diff (context around the change)
        diff_section = _render_unified_diff(content, updated, rel=rel, n=8, max_lines=60)
        if not diff_section:
            fallback = _compute_diff(old, new)
            diff_section = "\n".join(fallback[:40]) if fallback else ""

        from agent_core.loop.session_state import get_session_state
        st = get_session_state()
        if st is not None:
            # Cache post-edit content so verify re-reads are free
            numbered = "\n".join(f"{i+1:>5}\t{line}" for i, line in enumerate(updated.splitlines()))
            st.put_file(rel, f"--- {rel} ---\n{numbered}", mtime=os.path.getmtime(full))
            st.record_edit(rel, f"edit {len(old)}→{len(new)} chars")

        ckpt = " [checkpoint saved]" if ckpt_saved else ""
        result = (
            f"[EDIT] {rel}: replaced {replacement_count} occurrence(s) ({len(new)} chars){ckpt}\n"
            f"Diff below IS verification — do not re-read solely to confirm this edit."
        )
        if diff_section:
            result += f"\n--- Diff ---\n{diff_section}"
        return ToolResult(ok=True, data=result)
    except PathEscapeError as e:
        return ToolResult(ok=False, message=str(e))
    except Exception as e:
        return ToolResult(ok=False, message=str(e))


def _apply_edits(path, edits) -> ToolResult:
    """Apply multiple edits to one file sequentially, each with checkpoint + cache parity."""
    if not path:
        return ToolResult(ok=False, message="'path' parameter is required.")
    if not edits or not isinstance(edits, list):
        return ToolResult(ok=False, message="'edits' (list) parameter is required.")
    results = []
    for edit in edits:
        if not isinstance(edit, dict):
            results.append(ToolResult(ok=False, message="expected an object with old_string/new_string"))
            continue
        old_str = edit.get("old_string", "")
        new_str = edit.get("new_string", "")
        replace_all = edit.get("replace_all", False)
        results.append(_apply_single_edit(path, old_str, new_str, replace_all=replace_all))
    ok_count = sum(1 for r in results if r.ok)
    lines = [
        f"[edit {i}] {r.data if r.ok else f'ERROR: {r.message}'}"
        for i, r in enumerate(results)
    ]
    lines.append(f"Summary: {ok_count}/{len(results)} edits applied")
    return ToolResult(ok=ok_count > 0, data="\n\n".join(lines))


def edit_file(input_data) -> ToolResult:
    try:
        data = _parse_arg(input_data)
        path = data.get("path", "")
        edits = data.get("edits")
        if edits is not None:
            result = _apply_edits(path, edits)
        else:
            old = data.get("old_string", "")
            new = data.get("new_string", "")
            replace_all = data.get("replace_all", False)
            result = _apply_single_edit(path, old, new, replace_all=replace_all)
        if result.ok and path:
            try:
                res = resolve_for_tool(path, expect="file")
                if res.ok:
                    verify = _verify_python(res.full, res.rel)
            except Exception:
                verify = ""
            if verify:
                result.data = f"{result.data}\n{verify}"
        return result
    except PathEscapeError as e:
        return ToolResult(ok=False, message=str(e))
    except Exception as e:
        return ToolResult(ok=False, message=str(e))
