from __future__ import annotations

import os
import subprocess

from agent_core.workspace import resolve, to_relative, WORKSPACE_ROOT, PathEscapeError
from agent_core.tools.types import ToolResult, _parse_arg


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


def _render_unified_diff(old: str, new: str, rel: str = "", n: int = 3, max_lines: int = 60) -> str:
    """Render a capped unified diff with a/b headers; returns '' on any error."""
    try:
        import difflib
        kwargs = {}
        if rel:
            kwargs.update(fromfile=f"a/{rel}", tofile=f"b/{rel}", lineterm="")
        diff_lines = list(difflib.unified_diff(old.splitlines(), new.splitlines(), n=n, **kwargs))
    except Exception:
        return ""
    out = "\n".join(diff_lines[:max_lines])
    if len(diff_lines) > max_lines:
        out += f"\n... ({len(diff_lines) - max_lines} more diff lines)"
    return out


def file_diff(input_data) -> ToolResult:
    """Show diff of changes for a file vs checkpoint or git HEAD.
    Returns ~5 lines instead of full file — use for lightweight edit verification.
    """
    try:
        data = _parse_arg(input_data)
        path = data.get("path", "")
        if not path:
            return ToolResult(ok=False, message="'path' is required")
        full = resolve(path)
        rel = to_relative(full)
        if not os.path.exists(full):
            return ToolResult(ok=False, message=f"file not found: {path}")

        # 1. Checkpoint-based diff (shows what last edit_file changed)
        from agent_core.tools.undo_ops import _load_index, CHECKPOINT_DIR
        index = _load_index()
        for entry in reversed(index):
            if entry["file"] == rel:
                ckpt_full = os.path.join(CHECKPOINT_DIR, entry["checkpoint"])
                if os.path.exists(ckpt_full):
                    with open(ckpt_full, "r") as f:
                        old_content = f.read()
                    with open(full, "r") as f:
                        new_content = f.read()
                    if old_content == new_content:
                        return ToolResult(ok=True, data="(no diff, file matches checkpoint)")
                    return ToolResult(ok=True, data=_render_unified_diff(old_content, new_content, rel=rel, n=3, max_lines=30))
                break

        # 2. Fallback: git diff against HEAD
        try:
            r = subprocess.run(["git", "diff", "--", rel], capture_output=True, text=True, timeout=10, cwd=WORKSPACE_ROOT)
            diff_text = r.stdout.strip()
            if not diff_text:
                r = subprocess.run(["git", "diff", "--staged", "--", rel], capture_output=True, text=True, timeout=10, cwd=WORKSPACE_ROOT)
                diff_text = r.stdout.strip()
            if diff_text:
                lines = diff_text.splitlines()
                if len(lines) > 30:
                    diff_text = "\n".join(lines[:30]) + f"\n... ({len(lines) - 30} more lines)"
                return ToolResult(ok=True, data=diff_text)
            return ToolResult(ok=True, data="(no diff, file matches HEAD)")
        except Exception:
            return ToolResult(ok=True, data="(no checkpoint or git diff available)")
    except PathEscapeError as e:
        return ToolResult(ok=False, message=str(e))
    except Exception as e:
        return ToolResult(ok=False, message=f"file_diff error: {e}")
