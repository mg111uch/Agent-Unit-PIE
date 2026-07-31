"""Command execution and sandboxing utilities."""

from __future__ import annotations

import re
import subprocess
from datetime import datetime

from agent_core.config import ALLOWED_COMMANDS, SANDBOX_ENABLED
from agent_core.workspace import WORKSPACE_ROOT, get_user_workspace_root


def log_output(message: str, end: str = "\n", flush: bool = False):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", end=end, flush=flush)


def extract_json(text: str):
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return match.group(0)
    return None


def _is_command_allowed(cmd: str) -> bool:
    first_word = cmd.strip().split()[0] if cmd.strip() else ""
    return first_word in ALLOWED_COMMANDS


def _format_subprocess_output(result: subprocess.CompletedProcess) -> str:
    output = result.stdout
    if result.stderr:
        output += f"\n[STDERR]: {result.stderr}"
    if result.returncode != 0:
        output += f"\n[Exit code: {result.returncode}]"
    return output or "(No output)"


def _run_sandboxed(cmd: str, timeout: int = 60) -> str:
    ws = get_user_workspace_root() or WORKSPACE_ROOT
    try:
        result = subprocess.run(
            ["docker", "run", "--rm", "--network", "none",
             "-v", f"{ws}:/workspace:ro",
             "-w", "/workspace",
             "python:3.11-slim",
             "sh", "-c", cmd],
            capture_output=True, text=True, timeout=timeout,
        )
        return _format_subprocess_output(result)
    except FileNotFoundError:
        return "Sandbox error: Docker not found. Set sandbox_enabled=false or install Docker."
    except subprocess.TimeoutExpired:
        return f"Sandbox command timed out after {timeout}s: {cmd}"
    except Exception as e:
        return f"Sandbox error: {e}"


def execute_command_raw(cmd: str) -> str:
    if isinstance(cmd, dict):
        cmd = (
            cmd.get("command")
            or cmd.get("cmd")
            or cmd.get("input")
            or next(iter(cmd.values()), "")
        )
    cmd = "" if cmd is None else str(cmd)

    if not _is_command_allowed(cmd):
        allowed = ", ".join(sorted(ALLOWED_COMMANDS))
        return f"Command not allowed. Allowed commands: {allowed}"

    if SANDBOX_ENABLED:
        return _run_sandboxed(cmd)

    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30
        )
        return _format_subprocess_output(result)
    except subprocess.TimeoutExpired:
        msg = f"Command timed out after 30 seconds: {cmd}"
        log_output(f"[ERROR] {msg}")
        return msg
    except Exception as e:
        msg = f"Error executing command '{cmd}': {str(e)}"
        log_output(f"[ERROR] {msg}")
        return msg
