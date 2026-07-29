from __future__ import annotations

import json, os, re, subprocess
from pathlib import Path
from typing import Any

from agent_core.workspace import resolve, WORKSPACE_ROOT, PathEscapeError, to_relative, root_basename_hint
from agent_core.tools.undo_ops import save_checkpoint
from agent_core.config import CODEBASE_ROOT, EXCLUDE_DIRS
from kernel.persistence.db import kernel_db
from agent_core.tools.types import ToolResult

_exclude_set = set(EXCLUDE_DIRS)

_PLAN: list[dict] = []
_PLAN_FILE = "agent_plan.json"


def _load_plan() -> list[dict]:
    global _PLAN
    try:
        with open(_PLAN_FILE, "r") as f:
            _PLAN = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        _PLAN = []
    return _PLAN


def _save_plan():
    with open(_PLAN_FILE, "w") as f:
        json.dump(_PLAN, f, indent=2)


def todo_write(input_data: Any) -> str:
    global _PLAN
    _load_plan()
    data = json.loads(input_data) if isinstance(input_data, str) else input_data
    action = data.get("action", "create")

    if action == "create":
        items = data.get("items", [])
        _PLAN = [{"id": i + 1, "text": item, "done": False} for i, item in enumerate(items)]
        _save_plan()
        return f"[PLAN] Created {len(items)} tasks"

    elif action == "update":
        items = data.get("items", [])
        existing_ids = {t["id"] for t in _PLAN}
        next_id = max(existing_ids) + 1 if existing_ids else 1
        for item in items:
            _PLAN.append({"id": next_id, "text": item, "done": False})
            next_id += 1
        _save_plan()
        return f"[PLAN] Added {len(items)} tasks"

    elif action == "mark_done":
        ids = data.get("ids", [])
        for t in _PLAN:
            if t["id"] in ids:
                t["done"] = True
        _save_plan()
        return f"[PLAN] Marked {len(ids)} tasks done"

    elif action == "clear":
        _PLAN = []
        _save_plan()
        return "[PLAN] Cleared"

    return f"Error: Unknown action '{action}'"


def todo_read(_input: Any = None) -> str:
    _load_plan()
    if not _PLAN:
        return "(No plan set)"
    lines = ["Current plan:"]
    for t in _PLAN:
        status = "✓" if t["done"] else " "
        lines.append(f"  [{status}] {t['id']}. {t['text']}")
    return "\n".join(lines)

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


def _compute_diff(old_str: str, new_str: str) -> list[str]:
    """Compute a simple unified diff between old and new strings."""
    try:
        import difflib
        old_lines = old_str.splitlines(keepends=True)
        new_lines = new_str.splitlines(keepends=True)
        diff = list(difflib.unified_diff(old_lines, new_lines, n=3))
        return [l.rstrip() for l in diff[2:]] if len(diff) > 2 else []
    except Exception:
        return []


def _count_lines(path: str) -> int:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def read_file(path: str = "", **kwargs) -> ToolResult:
    path = kwargs.get("path") or kwargs.get("input") or kwargs.get("file") or path
    offset = int(kwargs.get("offset", 0))
    limit = kwargs.get("limit")
    if limit is not None:
        limit = int(limit)
    else:
        limit = 1000  # default: read up to 1000 lines per call
    line_numbers = kwargs.get("line_numbers", True)
    if isinstance(line_numbers, str):
        line_numbers = line_numbers.lower() in ("true", "1", "yes")
    try:
        full = resolve(path)
        rel = to_relative(full)
        try: kernel_db.record_file_access(rel, "read")
        except: pass
        if not os.path.exists(full):
            parent = os.path.dirname(full) or WORKSPACE_ROOT
            nearby = []
            if os.path.isdir(parent):
                nearby = sorted(os.listdir(parent))[:20]
            hint = root_basename_hint(path)
            return ToolResult(ok=False, message=(
                f"file not found: {path}\n"
                f"Resolved to: {rel} (workspace-relative)\n"
                f"Files in that directory: {nearby if nearby else '(directory does not exist)'}"
                f"{hint}"
            ))
        # Session cache: default reads only (no explicit offset/limit params)
        if not offset and kwargs.get("limit") is None:
            from agent_core.loop.session_state import get_session_state
            st = get_session_state()
            if st is not None:
                cached = st.get_cached_file(rel)
                if cached is not None:
                    return ToolResult(ok=True, data=f"[cached, unchanged]\n{cached}")
        result = _read_file_content(full, offset=offset, limit=limit, line_numbers=line_numbers)
        if result.ok and not offset and kwargs.get("limit") is None:
            from agent_core.loop.session_state import get_session_state
            st = get_session_state()
            if st is not None:
                st.put_file(rel, result.data)
        return result
    except PathEscapeError as e:
        return ToolResult(ok=False, message=str(e))
    except Exception as e:
        return ToolResult(ok=False, message=f"reading {path}: {e}")


def list_files(path: str = ".", **kwargs) -> ToolResult:
    path = kwargs.get("path") or kwargs.get("directory") or kwargs.get("dir") or kwargs.get("input") or path
    recursive = kwargs.get("recursive", False)
    if isinstance(recursive, str):
        recursive = recursive.lower() in ("true", "1", "yes")
    if not path:
        path = "."
    try:
        full = resolve(path)
        if not os.path.isdir(full):
            return ToolResult(ok=False, message=f"not a directory: {path}")
        rel = to_relative(full)
        from agent_core.loop.session_state import get_session_state
        st = get_session_state()
        if st is not None and rel in st.dir_cache:
            st.cache_hits += 1
            return ToolResult(ok=True, data=f"[cached listing]\n{st.dir_cache[rel]}")
        lines = []
        if recursive:
            for root, dirs, files in os.walk(full):
                dirs[:] = [d for d in sorted(dirs) if d not in _exclude_set]
                depth = os.path.relpath(root, full).count(os.sep)
                if root != full and depth > 3:
                    dirs[:] = []
                    continue
                rel_root = to_relative(root)
                indent = "  " * (0 if rel_root == "." else rel_root.count(os.sep) + 1)
                if rel_root != ".":
                    lines.append(f"{indent}{os.path.basename(root)}/")
                for fname in sorted(files):
                    lines.append(f"{indent}  {fname}")
        else:
            names = sorted(os.listdir(full))
            for name in names:
                child = os.path.join(full, name)
                if os.path.isdir(child):
                    if name not in _exclude_set:
                        lines.append(f"  {name}/")
                else:
                    lines.append(f"  {name}")
        data = "\n".join(lines) if lines else "(empty directory)"
        if st is not None:
            st.dir_cache[rel] = data
            st.cache_misses += 1
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
        if isinstance(input_data, str):
            input_data = json.loads(input_data)

        path = input_data.get("path")
        mode = input_data.get("mode")
        content = input_data.get("content", "")
        dry_run = input_data.get("dry_run", False)

        if not path or not mode:
            return ToolResult(ok=False, message="'path' and 'mode' are required")

        full_path = resolve(path)
        try: kernel_db.record_file_access(to_relative(full_path), mode)
        except: pass
        exists = os.path.exists(full_path)

        rel = to_relative(full_path)
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
                st.put_file(rel, content)
                st.record_edit(rel, f"create {len(content)} chars")
            return ToolResult(ok=True, data=f"[CREATE] {rel} ({len(content)} chars)")

        elif mode == "overwrite":
            ckpt_saved = save_checkpoint(path) if not dry_run else None
            _ensure_dir(full_path)
            if not dry_run:
                with open(full_path, "w") as f:
                    f.write(content)
            if st is not None and not dry_run:
                st.put_file(rel, content)
                st.record_edit(rel, f"overwrite {len(content)} chars")
            ckpt = " [checkpoint saved]" if ckpt_saved else ""
            return ToolResult(ok=True, data=f"[OVERWRITE] {rel} ({len(content)} chars){ckpt}")

        elif mode == "append":
            _ensure_dir(full_path)
            if not dry_run:
                with open(full_path, "a") as f:
                    f.write(content)
            if st is not None and not dry_run:
                st.mark_stale(rel)
                st.record_edit(rel, f"append +{len(content)} chars")
            return ToolResult(ok=True, data=f"[APPEND] {rel} (+{len(content)} chars)")

        else:
            return ToolResult(ok=False, message=f"Unknown mode '{mode}'")

    except PathEscapeError as e:
        return ToolResult(ok=False, message=str(e))
    except Exception as e:
        return ToolResult(ok=False, message=str(e))


def edit_file(input_data) -> ToolResult:
    try:
        data = json.loads(input_data) if isinstance(input_data, str) else input_data
        path, old, new = data["path"], data["old_string"], data["new_string"]
        full = resolve(path)
        rel = to_relative(full)
        try: kernel_db.record_file_access(rel, "edit")
        except: pass
        if not os.path.exists(full):
            parent = os.path.dirname(full) or WORKSPACE_ROOT
            nearby = []
            if os.path.isdir(parent):
                nearby = sorted(os.listdir(parent))[:20]
            hint = root_basename_hint(path)
            return ToolResult(ok=False, message=(
                f"file not found: {path}\n"
                f"Resolved to: {rel} (workspace-relative)\n"
                f"Files in that directory: {nearby if nearby else '(directory does not exist)'}"
                f"{hint}"
            ))
        with open(full, "r", encoding="utf-8") as f:
            content = f.read()
        count = content.count(old)
        if count == 0:
            return ToolResult(ok=False, message=(
                "old_string not found. Re-read the file with read_file "
                "(it shows exact line numbers/whitespace) and copy the text exactly."
            ))
        if count > 1:
            return ToolResult(ok=False, message=(
                f"old_string is not unique ({count} matches). "
                "Include more surrounding lines so the match is unambiguous."
            ))
        ckpt_saved = save_checkpoint(path)
        updated = content.replace(old, new, 1)
        with open(full, "w", encoding="utf-8") as f:
            f.write(updated)

        # Prefer full-file unified diff (context around the change)
        try:
            import difflib
            diff_lines = list(difflib.unified_diff(
                content.splitlines(), updated.splitlines(),
                fromfile=f"a/{rel}", tofile=f"b/{rel}", lineterm="", n=8,
            ))
            diff_section = "\n".join(diff_lines[:60])
            if len(diff_lines) > 60:
                diff_section += f"\n... ({len(diff_lines) - 60} more diff lines)"
        except Exception:
            diff_lines = _compute_diff(old, new)
            diff_section = "\n".join(diff_lines[:40]) if diff_lines else ""

        from agent_core.loop.session_state import get_session_state
        st = get_session_state()
        if st is not None:
            # Cache post-edit content so verify re-reads are free
            numbered = "\n".join(f"{i+1:>5}\t{line}" for i, line in enumerate(updated.splitlines()))
            st.put_file(rel, f"--- {rel} ---\n{numbered}")
            st.record_edit(rel, f"edit {len(old)}→{len(new)} chars")

        ckpt = " [checkpoint saved]" if ckpt_saved else ""
        result = (
            f"[EDIT] {rel}: replaced 1 occurrence ({len(new)} chars){ckpt}\n"
            f"Diff below IS verification — do not re-read solely to confirm this edit."
        )
        if diff_section:
            result += f"\n--- Diff ---\n{diff_section}"
        return ToolResult(ok=True, data=result)
    except PathEscapeError as e:
        return ToolResult(ok=False, message=str(e))
    except Exception as e:
        return ToolResult(ok=False, message=str(e))





def glob_search(pattern: str = "", **kwargs) -> ToolResult:
    """Find files matching a glob pattern (e.g. '**/*.py', 'src/**/*.ts')."""
    pattern = kwargs.get("pattern") or kwargs.get("glob") or kwargs.get("input") or pattern
    try:
        matches = sorted(Path(WORKSPACE_ROOT).rglob(pattern))
        relative = [str(Path(p).relative_to(WORKSPACE_ROOT)) for p in matches if p.is_file()]
        if not relative:
            return ToolResult(ok=True, data=f"No files match pattern: {pattern}")
        lines = [f"Files matching '{pattern}' ({len(relative)}):"]
        lines.extend(f"  {r}" for r in relative)
        return ToolResult(ok=True, data="\n".join(lines))
    except Exception as e:
        return ToolResult(ok=False, message=f"globbing '{pattern}': {e}")


def grep_search(input_data) -> ToolResult:
    """Search file contents by regex across the workspace.
    
    input_data = {"pattern": "...", "include": "*.py", "max_results": 50}
    Uses ripgrep (rg) if available, falls back to Python regex walk.
    """
    try:
        data = json.loads(input_data) if isinstance(input_data, str) else input_data
        pattern = data.get("pattern", "")
        include = data.get("include", "")
        max_results = int(data.get("max_results", 50))

        if not pattern:
            return ToolResult(ok=False, message="'pattern' is required")

        # Try ripgrep first (much faster)
        try:
            cmd = ["rg", "--no-heading", "--line-number", "-n"]
            if include:
                cmd.extend(["--glob", include])
            cmd.extend(["-m", str(max_results), pattern, WORKSPACE_ROOT])
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().splitlines()
                relative_lines = []
                for line in lines:
                    abs_path = line.split(":", 1)[0] if ":" in line else ""
                    if abs_path and abs_path.startswith(WORKSPACE_ROOT):
                        rel = os.path.relpath(abs_path, WORKSPACE_ROOT)
                        line = rel + line[len(abs_path):]
                    relative_lines.append(line)
                out = "\n".join(relative_lines[:max_results])
                if len(relative_lines) > max_results:
                    out += f"\n... ({len(relative_lines) - max_results} more matches)"
                return ToolResult(ok=True, data=out)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # Fallback: Python regex walk
        matches = []
        import fnmatch
        for root, dirs, files in os.walk(WORKSPACE_ROOT):
            dirs[:] = [d for d in sorted(dirs) if d not in _exclude_set]
            for fname in sorted(files):
                if include and not any(fnmatch.fnmatch(fname, pat.strip()) for pat in include.split(",")):
                    continue
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                        for i, line in enumerate(f, 1):
                            if re.search(pattern, line):
                                rel = os.path.relpath(fpath, WORKSPACE_ROOT)
                                matches.append(f"{rel}:{i}:{line.rstrip()[:200]}")
                                if len(matches) >= max_results:
                                    break
                except Exception:
                    continue
                if len(matches) >= max_results:
                    break

        if not matches:
            return ToolResult(ok=True, data=f"No matches for pattern: {pattern}")
        out = "\n".join(matches[:max_results])
        if len(matches) > max_results:
            out += f"\n... ({len(matches) - max_results} more matches)"
        return ToolResult(ok=True, data=out)
    except Exception as e:
        return ToolResult(ok=False, message=f"grep_search error: {e}")


