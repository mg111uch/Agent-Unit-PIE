"""Git-backed lineage helpers — Phase 0 refactor.

RO only: `git rev-parse`, `diff --name-only`, `branch --show-current`.
Fallback to compute_code_hash when not in git repo or git unavailable.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List, Optional

from kernel.schemas.simulation_schema import compute_code_hash
from kernel.utils.logger import get_child_logger

logger = get_child_logger("git_version")

_GIT_ROOT = Path(__file__).resolve().parents[2]  # workspace root (Agentic_Unit_PIE)
_SIM_ROOT = _GIT_ROOT / "codebase" / "modules" / "simulators"


def _run_git(args: List[str], cwd: Optional[Path] = None) -> Optional[str]:
    try:
        res = subprocess.run(
            ["git"] + args,
            cwd=str(cwd or _GIT_ROOT),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if res.returncode != 0:
            return None
        return res.stdout.strip()
    except Exception:
        return None


def is_git_repo() -> bool:
    return _run_git(["rev-parse", "--is-inside-work-tree"]) == "true"


def current_commit(short: bool = True) -> Optional[str]:
    fmt = "--short" if short else ""
    args = ["rev-parse", "--short" if short else "HEAD"]
    # git rev-parse --short HEAD
    if short:
        out = _run_git(["rev-parse", "--short", "HEAD"])
    else:
        out = _run_git(["rev-parse", "HEAD"])
    return out or None


def parent_commit(commit: str) -> Optional[str]:
    out = _run_git(["rev-parse", f"{commit}^"])
    return out or None


def current_branch() -> Optional[str]:
    out = _run_git(["branch", "--show-current"])
    return out or "detached"


def diff_files(from_commit: str, to_commit: str = "HEAD", paths: Optional[List[str]] = None) -> List[str]:
    args = ["diff", "--name-only", f"{from_commit}..{to_commit}"]
    if paths:
        args += ["--"] + paths
    out = _run_git(args)
    if not out:
        return []
    return [l.strip() for l in out.splitlines() if l.strip()]


def diff_sim_files(sim_name: str, from_commit: str, to_commit: str = "HEAD") -> List[str]:
    try:
        from kernel.simulator_registry import sim_patterns
        paths = sim_patterns(sim_name)
        return diff_files(from_commit, to_commit, paths=paths)
    except Exception:
        return diff_files(from_commit, to_commit)


def sim_commit(sim_name: str, short: bool = True) -> Optional[str]:
    """Last commit touching aSimulator's directory (scoped). Returns None if none."""
    try:
        from kernel.simulator_registry import sim_patterns
        paths = sim_patterns(sim_name)
        args = ["log", "-1", "--pretty=%H" if not short else "--pretty=%h", "--"] + paths
        out = _run_git(args)
        # Do NOT fallback to global HEAD — keeps per-sim isolation
        return out or None
    except Exception:
        return None


def diff_files_uncommitted() -> List[str]:
    out = _run_git(["status", "--porcelain"])
    if not out:
        return []
    files: List[str] = []
    for line in out.splitlines():
        parts = line.strip().split()
        if parts:
            files.append(parts[-1])
    return files


def git_commit_message(commit: str) -> str:
    out = _run_git(["log", "-1", "--pretty=%s", commit])
    return out or ""


def current_code_hash_fallback() -> str:
    try:
        return compute_code_hash(_SIM_ROOT)
    except Exception:
        return "unknown"


def current_version_id(sim_name: Optional[str] = None) -> str:
    """Preferred version_id scoped to simulator if given."""
    if sim_name:
        c = sim_commit(sim_name, short=True)
        if c:
            return f"{sim_name}@{c}"
        # no history for this sim → hash-based isolated version
        return f"{sim_name}@V1_{current_code_hash_fallback()[:7]}"
    if is_git_repo():
        c = current_commit(short=True)
        if c:
            return c
    return f"Vhash_{current_code_hash_fallback()[:7]}"
