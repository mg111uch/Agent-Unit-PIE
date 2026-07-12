import os, json

from agent_core.workspace import resolve, WORKSPACE_ROOT, PathEscapeError, to_relative


def _ensure_dir(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)


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
        with open(full, "r", encoding="utf-8") as f:
            content = f.read()
        numbered = "\n".join(f"{i+1:>5}\t{line}" for i, line in enumerate(content.splitlines()))
        return f"--- {to_relative(full)} ---\n{numbered}"
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
            _ensure_dir(full_path)
            if not dry_run:
                with open(full_path, "w") as f:
                    f.write(content)
            return f"[OVERWRITE] {to_relative(full_path)} ({len(content)} chars)"

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
        updated = content.replace(old, new, 1)
        with open(full, "w", encoding="utf-8") as f:
            f.write(updated)
        return f"[EDIT] {to_relative(full)}: replaced 1 occurrence ({len(new)} chars)"
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
