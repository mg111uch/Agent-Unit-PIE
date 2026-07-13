"""Git operation tools: status, diff, commit — behind config flag."""

from __future__ import annotations

import os
import subprocess

from agent_core.config import GIT_TOOLS_ENABLED
from agent_core.workspace import WORKSPACE_ROOT, to_relative


def _check_git_enabled() -> str | None:
    if not GIT_TOOLS_ENABLED:
        return "Git tools are disabled. Set git_tools_enabled: true in config.json to enable."
    if not os.path.isdir(os.path.join(WORKSPACE_ROOT, ".git")):
        return "Not a git repository (no .git directory found in workspace root)."
    return None


def _run_git(args: list[str], timeout: int = 30) -> str:
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=WORKSPACE_ROOT,
        )
        output = result.stdout
        if result.stderr:
            output += f"\n[STDERR]\n{result.stderr}"
        if result.returncode != 0:
            output += f"\n[Exit code: {result.returncode}]"
        return output if output else "(No output)"
    except FileNotFoundError:
        return "git not found. Install git or check PATH."
    except subprocess.TimeoutExpired:
        return f"Git command timed out after {timeout}s."
    except Exception as e:
        return f"Error running git: {e}"


def git_status(input_data=None) -> str:
    """Show git status of the workspace."""
    error = _check_git_enabled()
    if error:
        return error
    return _run_git(["status"])


def git_diff(input_data=None) -> str:
    """Show git diff of uncommitted changes.

    input_data = {"path": "optional/path", "staged": false}
    """
    try:
        import json
        path = ""
        staged = False
        if isinstance(input_data, str) and input_data.strip():
            data = json.loads(input_data) if input_data.strip() else {}
            path = data.get("path", "")
            staged = data.get("staged", False)
        elif isinstance(input_data, dict):
            path = input_data.get("path", "")
            staged = input_data.get("staged", False)
    except Exception:
        path = ""
        staged = False

    error = _check_git_enabled()
    if error:
        return error

    args = ["diff"]
    if staged:
        args.append("--staged")
    if path:
        args.append("--")
        args.append(path)
    return _run_git(args)


def git_commit(input_data) -> str:
    """Commit staged changes with a message.

    input_data = {
        "message": "commit message",
        "add_all": true      # optional: git add -A before commit
    }
    """
    try:
        if isinstance(input_data, str):
            import json
            data = json.loads(input_data)
        else:
            data = input_data
        message = data.get("message", "")
        add_all = data.get("add_all", False)
        if not message:
            return "Error: 'message' is required for git commit"
    except Exception:
        return "Error: 'message' is required for git commit"

    error = _check_git_enabled()
    if error:
        return error

    if add_all:
        add_result = _run_git(["add", "-A"])
        if "Exit code:" in add_result and "Exit code: 0" not in add_result:
            return f"git add failed:\n{add_result}"

    return _run_git(["commit", "-m", message])


def git_log(input_data=None) -> str:
    """Show recent git log.

    input_data = {"max_count": 10}
    """
    try:
        max_count = 10
        if isinstance(input_data, str) and input_data.strip():
            import json
            data = json.loads(input_data)
            max_count = int(data.get("max_count", 10))
        elif isinstance(input_data, dict):
            max_count = int(input_data.get("max_count", 10))
    except Exception:
        max_count = 10

    error = _check_git_enabled()
    if error:
        return error
    return _run_git(["log", f"--max-count={max_count}", "--oneline"])
