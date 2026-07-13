import json, os, re, subprocess
from pathlib import Path

from agent_core.workspace import resolve, WORKSPACE_ROOT, PathEscapeError, to_relative
from agent_core.tools.undo_ops import save_checkpoint

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


def read_file(path: str) -> str:
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
        return _read_file_content(full)
    except PathEscapeError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error reading {path}: {e}"


def read_file_range(input_data) -> str:
    """Read a portion of a file with offset (1-based) and optional limit.
    
    input_data = {"path": "...", "offset": 1, "limit": 50}
    """
    try:
        data = json.loads(input_data) if isinstance(input_data, str) else input_data
        path = data.get("path", "")
        offset = int(data.get("offset", 0))
        limit = data.get("limit")
        if limit is not None:
            limit = int(limit)
        full = resolve(path)
        if not os.path.exists(full):
            return f"Error: file not found: {path}"
        return _read_file_content(full, offset=offset, limit=limit)
    except PathEscapeError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error reading {path}: {e}"


def list_files(path: str = ".") -> str:
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


def glob_search(pattern: str) -> str:
    """Find files matching a glob pattern (e.g. '**/*.py', 'src/**/*.ts')."""
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
