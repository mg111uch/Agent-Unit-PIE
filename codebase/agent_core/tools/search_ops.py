from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from agent_core.workspace import WORKSPACE_ROOT, get_user_workspace_root
from agent_core.config import EXCLUDE_DIRS
from agent_core.tools.types import ToolResult, _parse_arg

_exclude_set = set(EXCLUDE_DIRS)
_RG_AVAILABLE: bool | None = None


def _normalize_pattern(pattern: str) -> str:
    """Strip a leading workspace-root basename prefix from a glob pattern."""
    root = get_user_workspace_root() or WORKSPACE_ROOT
    base = os.path.basename(root)
    cleaned = pattern.lstrip("/\\")
    if cleaned == base or cleaned.startswith(base + "/"):
        alt = cleaned[len(base):].lstrip("/\\")
        if not alt:
            alt = "**"
        return alt
    return pattern


def glob_search(pattern: str = "", **kwargs) -> ToolResult:
    """Find files matching a glob pattern (e.g. '**/*.py', 'src/**/*.ts')."""
    pattern = kwargs.get("pattern") or kwargs.get("glob") or kwargs.get("input") or pattern
    try:
        pattern = _normalize_pattern(pattern)
        matches = sorted(Path(WORKSPACE_ROOT).rglob(pattern))
        relative = []
        for p in matches:
            if not p.is_file():
                continue
            rel = str(p.relative_to(WORKSPACE_ROOT))
            parts = rel.split(os.sep)
            if any(part in _exclude_set for part in parts):
                continue
            relative.append(rel)
        if not relative:
            return ToolResult(ok=True, data=f"No files match pattern: {pattern}")
        lines = [f"Files matching '{pattern}' ({len(relative)}):"]
        lines.extend(f"  {r}" for r in relative)
        return ToolResult(ok=True, data="\n".join(lines))
    except Exception as e:
        return ToolResult(ok=False, message=f"globbing '{pattern}': {e}")


def _relativize_line(line: str) -> str:
    """Rewrite a leading WORKSPACE_ROOT path to relative in an rg line.

    Handles both match lines (`path:12:content`) and context lines
    (`path:12-content` / `path-12-content`).
    """
    m = re.match(r"^(.*?)[:\-]\d+[:\-]", line)
    if m and m.group(1).startswith(WORKSPACE_ROOT):
        rel = os.path.relpath(m.group(1), WORKSPACE_ROOT)
        return rel + line[len(m.group(1)):]
    return line


def grep_search(input_data) -> ToolResult:
    """Search file contents by regex across the workspace.
    
    input_data = {"pattern": "...", "include": "*.py", "context_lines": 2, "max_results": 50}
    context_lines>0 returns that many surrounding lines per match (opt-in, default 0).
    Uses ripgrep (rg) if available, falls back to Python regex walk.
    """
    try:
        data = _parse_arg(input_data)
        pattern = data.get("pattern", "")
        include = data.get("include", "")
        context_lines = max(0, int(data.get("context_lines", 0)))
        max_results = int(data.get("max_results", 50))

        if not pattern:
            return ToolResult(ok=False, message="'pattern' is required")

        # Try ripgrep first (much faster)
        global _RG_AVAILABLE
        if _RG_AVAILABLE is None:
            try:
                subprocess.run(["rg", "--version"], capture_output=True, timeout=5)
                _RG_AVAILABLE = True
            except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
                _RG_AVAILABLE = False
        if _RG_AVAILABLE:
            try:
                cmd = ["rg", "--no-heading", "--line-number", "-n"]
                if include:
                    cmd.extend(["--glob", include])
                for d in EXCLUDE_DIRS:
                    cmd.extend(["--glob", f"!{d}/**", "--glob", f"!{d}"])
                if context_lines > 0:
                    cmd.extend(["-C", str(context_lines)])
                cmd.extend(["-m", str(max_results), pattern, WORKSPACE_ROOT])
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if result.returncode == 0 and result.stdout.strip():
                    relative_lines = [_relativize_line(line) for line in result.stdout.strip().splitlines()]
                    out = "\n".join(relative_lines[:max_results])
                    if len(relative_lines) > max_results:
                        out += f"\n... ({len(relative_lines) - max_results} more lines)"
                    return ToolResult(ok=True, data=out)
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass

        # Fallback: Python regex walk
        matches = []
        import fnmatch
        pattern_re = re.compile(pattern)
        for root, dirs, files in os.walk(WORKSPACE_ROOT):
            dirs[:] = [d for d in sorted(dirs) if d not in _exclude_set]
            for fname in sorted(files):
                if include and not any(fnmatch.fnmatch(fname, pat.strip()) for pat in include.split(",")):
                    continue
                fpath = os.path.join(root, fname)
                try:
                    rel = os.path.relpath(fpath, WORKSPACE_ROOT)
                    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                        if context_lines > 0:
                            lines = f.readlines()
                            for i, line in enumerate(lines):
                                if not pattern_re.search(line):
                                    continue
                                start = max(0, i - context_lines)
                                end = min(len(lines), i + context_lines + 1)
                                for j in range(start, end):
                                    sep = ":" if j == i else "-"
                                    matches.append(f"{rel}:{j+1}{sep}{lines[j].rstrip()[:200]}")
                                if len(matches) >= max_results:
                                    break
                        else:
                            for i, line in enumerate(f, 1):
                                if pattern_re.search(line):
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
            out += f"\n... ({len(matches) - max_results} more lines)"
        return ToolResult(ok=True, data=out)
    except Exception as e:
        return ToolResult(ok=False, message=f"grep_search error: {e}")
