import json, os, re, subprocess
from pathlib import Path

from agent_core.workspace import resolve, WORKSPACE_ROOT, PathEscapeError, to_relative
from agent_core.tools.undo_ops import save_checkpoint
from agent_core.config import CODEBASE_ROOT

MAX_FILE_SIZE = 512 * 1024  # 512 KB


def _ensure_dir(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)


def _read_file_content(full: str, offset: int = 0, limit: int | None = None) -> str:
    with open(full, "r", encoding="utf-8") as f:
        lines = f.readlines()

    size = sum(len(l) for l in lines)
    if size > MAX_FILE_SIZE:
        return f"Error: file too large ({size // 1024} KB). Max is {MAX_FILE_SIZE // 1024} KB."

    if offset > 0 or limit is not None:
        start = max(0, offset - 1) if offset > 0 else 0
        end = start + limit if limit else len(lines)
        lines = lines[start:end]
        line_offset = start + 1
    else:
        line_offset = 1

    numbered = "\n".join(
        f"{i + line_offset:>5}\t{line.rstrip()}"
        for i, line in enumerate(lines)
    )
    total = size  # approximate
    header = f"--- {to_relative(full)} ---"
    if offset > 0 or limit is not None:
        header += f" (lines {line_offset}-{line_offset + len(lines) - 1} of ~{_count_lines(full)})"
    return f"{header}\n{numbered}"


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


def read_file(path: str = "", **kwargs) -> str:
    path = kwargs.get("path") or kwargs.get("input") or kwargs.get("file") or path
    offset = int(kwargs.get("offset", 0))
    limit = kwargs.get("limit")
    if limit is not None:
        limit = int(limit)
    try:
        full = resolve(path)
        if not os.path.exists(full):
            parent = os.path.dirname(full) or WORKSPACE_ROOT
            nearby = []
            if os.path.isdir(parent):
                nearby = sorted(os.listdir(parent))[:20]
            return (
                f"Error: file not found: {path}\n"
                f"Resolved to: {to_relative(full)} (workspace-relative)\n"
                f"Files in that directory: {nearby if nearby else '(directory does not exist)'}"
            )
        return _read_file_content(full, offset=offset, limit=limit)
    except PathEscapeError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error reading {path}: {e}"


def list_files(path: str = ".", **kwargs) -> str:
    path = kwargs.get("path") or kwargs.get("directory") or kwargs.get("dir") or kwargs.get("input") or path
    if not path:
        path = "."
    try:
        full = resolve(path)
        if not os.path.isdir(full):
            return f"Error: not a directory: {path}"
        lines = []
        for root, dirs, files in os.walk(full):
            dirs[:] = [d for d in sorted(dirs) if d not in (".git", "node_modules", "__pycache__", ".venv")]
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
        return "\n".join(lines) if lines else "(empty directory)"
    except PathEscapeError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error listing {path}: {e}"


def write_to_file(input_data) -> str:
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
            return "Error: 'path' and 'mode' are required"

        full_path = resolve(path)
        exists = os.path.exists(full_path)

        if mode == "create":
            if exists:
                return f"Error: File already exists: {to_relative(full_path)}"
            _ensure_dir(full_path)
            if not dry_run:
                with open(full_path, "w") as f:
                    f.write(content)
            return f"[CREATE] {to_relative(full_path)} ({len(content)} chars)"

        elif mode == "overwrite":
            ckpt_saved = save_checkpoint(path) if not dry_run else None
            _ensure_dir(full_path)
            if not dry_run:
                with open(full_path, "w") as f:
                    f.write(content)
            ckpt = " [checkpoint saved]" if ckpt_saved else ""
            return f"[OVERWRITE] {to_relative(full_path)} ({len(content)} chars){ckpt}"

        elif mode == "append":
            _ensure_dir(full_path)
            if not dry_run:
                with open(full_path, "a") as f:
                    f.write(content)
            return f"[APPEND] {to_relative(full_path)} (+{len(content)} chars)"

        else:
            return f"Error: Unknown mode '{mode}'"

    except PathEscapeError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error: {str(e)}"


def edit_file(input_data) -> str:
    try:
        data = json.loads(input_data) if isinstance(input_data, str) else input_data
        path, old, new = data["path"], data["old_string"], data["new_string"]
        full = resolve(path)
        if not os.path.exists(full):
            parent = os.path.dirname(full) or WORKSPACE_ROOT
            nearby = []
            if os.path.isdir(parent):
                nearby = sorted(os.listdir(parent))[:20]
            return (
                f"Error: file not found: {path}\n"
                f"Resolved to: {to_relative(full)} (workspace-relative)\n"
                f"Files in that directory: {nearby if nearby else '(directory does not exist)'}"
            )
        with open(full, "r", encoding="utf-8") as f:
            content = f.read()
        count = content.count(old)
        if count == 0:
            return (
                "Error: old_string not found. Re-read the file with read_file "
                "(it shows exact line numbers/whitespace) and copy the text exactly."
            )
        if count > 1:
            return (
                f"Error: old_string is not unique ({count} matches). "
                "Include more surrounding lines so the match is unambiguous."
            )
        ckpt_saved = save_checkpoint(path)
        updated = content.replace(old, new, 1)
        with open(full, "w", encoding="utf-8") as f:
            f.write(updated)

        diff_lines = _compute_diff(old, new)
        diff_section = "\n".join(diff_lines[:20]) if diff_lines else ""
        if len(diff_lines) > 20:
            diff_section += f"\n... ({len(diff_lines) - 20} more lines changed)"

        ckpt = " [checkpoint saved]" if ckpt_saved else ""
        result = f"[EDIT] {to_relative(full)}: replaced 1 occurrence ({len(new)} chars){ckpt}"
        if diff_section:
            result += f"\n--- Diff ---\n{diff_section}"
        return result
    except PathEscapeError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error: {e}"


def get_workspace_info(_input=None) -> str:
    entries = sorted(os.listdir(WORKSPACE_ROOT))
    return (
        f"Workspace root (use paths relative to this): {WORKSPACE_ROOT}\n"
        f"Top-level entries: {entries}\n"
        f"All file paths you pass to read_file / write_to_file / list_files / edit_file "
        f"must be relative to this root (e.g. 'src/main.py', not an absolute OS path)."
    )


def glob_search(pattern: str = "", **kwargs) -> str:
    """Find files matching a glob pattern (e.g. '**/*.py', 'src/**/*.ts')."""
    pattern = kwargs.get("pattern") or kwargs.get("glob") or kwargs.get("input") or pattern
    try:
        matches = sorted(Path(WORKSPACE_ROOT).rglob(pattern))
        relative = [str(Path(p).relative_to(WORKSPACE_ROOT)) for p in matches if p.is_file()]
        if not relative:
            return f"No files match pattern: {pattern}"
        lines = [f"Files matching '{pattern}' ({len(relative)}):"]
        lines.extend(f"  {r}" for r in relative)
        return "\n".join(lines)
    except Exception as e:
        return f"Error globbing '{pattern}': {e}"


def grep_search(input_data) -> str:
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
            return "Error: 'pattern' is required"

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
                return out
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # Fallback: Python regex walk
        matches = []
        for root, dirs, files in os.walk(WORKSPACE_ROOT):
            dirs[:] = [d for d in sorted(dirs) if d not in (".git", "node_modules", "__pycache__", ".venv")]
            for fname in sorted(files):
                if include and not fname.endswith(tuple(include.split(","))):
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
            return f"No matches for pattern: {pattern}"
        out = "\n".join(matches[:max_results])
        if len(matches) > max_results:
            out += f"\n... ({len(matches) - max_results} more matches)"
        return out
    except Exception as e:
        return f"Error grepping '{pattern}': {e}"


def read_section_tool(params: dict) -> str:
    if isinstance(params, str):
        try:
            params = json.loads(params)
        except json.JSONDecodeError:
            return "Error: invalid JSON input."
    path = params.get("path", "")
    if not path:
        return "Error: 'path' parameter is required."
    pattern = params.get("pattern", "")
    if not pattern:
        return "Error: 'pattern' (regex) parameter is required."
    context_lines = params.get("context_lines", 10)
    ignore_case = params.get("ignore_case", False)
    try:
        full = resolve(path)
        if not os.path.isfile(full):
            return f"Error: file not found: {path}"
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
            return json.dumps({
                "path": path,
                "pattern": pattern,
                "matches": [],
                "total_lines": len(lines),
            }, indent=2)
        return json.dumps({
            "path": path,
            "pattern": pattern,
            "match_count": len(matches),
            "total_lines": len(lines),
            "matches": matches,
        }, indent=2)
    except re.error as e:
        return f"Error: invalid regex pattern '{pattern}': {e}"
    except Exception as e:
        return f"Error reading '{path}': {e}"


def batch_edit_tool(params: dict) -> str:
    if isinstance(params, str):
        try:
            params = json.loads(params)
        except json.JSONDecodeError:
            return "Error: invalid JSON input."
    path = params.get("path", "")
    edits = params.get("edits", [])
    if not path:
        return "Error: 'path' parameter is required."
    if not edits or not isinstance(edits, list):
        return "Error: 'edits' (list) parameter is required."
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
    return json.dumps({"file": path, "edits": results, "summary": f"{ok_count}/{len(edits)} edits applied"}, indent=2)


def batch_read_tool(params: dict) -> str:
    if isinstance(params, str):
        try:
            params = json.loads(params)
        except json.JSONDecodeError:
            return "Error: invalid JSON input."
    paths = params.get("paths", []) if isinstance(params, dict) else []
    if not paths or not isinstance(paths, list):
        return "Error: 'paths' (list) parameter is required."
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
    return json.dumps({"files": results, "summary": counts}, indent=2)
