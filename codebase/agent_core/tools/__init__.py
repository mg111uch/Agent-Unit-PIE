import os, subprocess, re
from dataclasses import dataclass, asdict
from typing import Dict, Any, Callable, Optional

from agent_core.tools.file_ops import (
    read_file,
    read_file_range,
    list_files,
    write_to_file,
    edit_file,
    get_workspace_info,
    glob_search,
    grep_search,
)
from agent_core.tools.plan_ops import (
    todo_write,
    todo_read,
)
from agent_core.tools.test_ops import (
    run_tests,
)
from agent_core.tools.git_ops import (
    git_status,
    git_diff,
    git_commit,
    git_log,
)
from agent_core.tools.undo_ops import (
    undo_last_edit,
    checkpoint_info,
)
from agent_core.config import ALLOWED_COMMANDS, SANDBOX_ENABLED
from agent_core.workspace import WORKSPACE_ROOT, get_user_workspace_root
from agent_core.tools.kernel_ops import (
    KERNEL_AVAILABLE,
    kernel_retrieve,
    kernel_emit_signal,
    kernel_store_context,
    kernel_get_memory,
    kernel_create_event,
)
from agent_core.tools.sim_ops import (
    SIMULATION_AVAILABLE,
    simulation_run,
    simulation_compare,
    simulation_list,
    simulation_get_signals,
)
from agent_core.tools.registry import ToolRegistry, CAT_FILE, CAT_KERNEL, CAT_SIM, CAT_META, CAT_GIT
from agent_core.tools.schemas import TOOL_NAME_MAP

LOG_FILE = "tui_output.txt"


class ToolError(Exception):
    def __init__(self, error_type: str, message: str, suggestion: str = ""):
        self.error_type = error_type
        self.message = message
        self.suggestion = suggestion
        super().__init__(message)


@dataclass
class ToolResult:
    ok: bool
    data: str = ""
    error_type: str = ""
    message: str = ""
    suggestion: str = ""

    def to_string(self) -> str:
        if self.ok:
            return self.data
        parts = [f"Error: {self.message}"]
        if self.suggestion:
            parts.append(f"Suggestion: {self.suggestion}")
        return "\n".join(parts)

    def to_dict(self) -> dict:
        return asdict(self)


def tool_call(fn: Callable) -> Callable:
    """Wrap a tool function to catch ToolErrors and return structured ToolResult."""
    def wrapper(*args, **kwargs) -> ToolResult:
        try:
            result = fn(*args, **kwargs)
            if isinstance(result, ToolResult):
                return result
            text = str(result)
            # Many tools return "Error: ..." strings instead of raising
            if text.startswith("Error"):
                return ToolResult(ok=False, error_type="tool", message=text, data=text)
            return ToolResult(ok=True, data=text)
        except ToolError as e:
            return ToolResult(ok=False, error_type=e.error_type, message=e.message, suggestion=e.suggestion)
        except Exception as e:
            return ToolResult(ok=False, error_type="internal", message=str(e))
    return wrapper


def log_output(message: str, end: str = "\n", flush: bool = False):
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}"
    print(log_line, end=end, flush=flush)


def extract_json(text: str):
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return match.group(0)
    return None


def _is_command_allowed(cmd: str) -> bool:
    first_word = cmd.strip().split()[0] if cmd.strip() else ""
    return first_word in ALLOWED_COMMANDS


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
        output = result.stdout
        if result.stderr:
            output += f"\n[STDERR]: {result.stderr}"
        if result.returncode != 0:
            output += f"\n[Exit code: {result.returncode}]"
        return output or "(No output)"
    except FileNotFoundError:
        return "Sandbox error: Docker not found. Set sandbox_enabled=false or install Docker."
    except subprocess.TimeoutExpired:
        return f"Sandbox command timed out after {timeout}s: {cmd}"
    except Exception as e:
        return f"Sandbox error: {e}"


@tool_call
def execute_command_raw(cmd: str) -> str:
    # Native function calling often passes {"command": "..."}; text path may pass a plain string.
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
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        output = result.stdout
        if result.stderr:
            output += f"\n[STDERR]: {result.stderr}"
        if result.returncode != 0:
            output += f"\n[Exit code: {result.returncode}]"

        if result.returncode != 0 or result.stderr:
            try:
                with open(LOG_FILE, "w") as f:
                    f.write(output)
            except Exception:
                pass

        return output if output else "(No output)"
    except subprocess.TimeoutExpired:
        error_msg = f"Command timed out after 30 seconds: {cmd}"
        log_output(f"[ERROR] {error_msg}")
        return error_msg
    except Exception as e:
        error_msg = f"Error executing command '{cmd}': {str(e)}"
        log_output(f"[ERROR] {error_msg}")
        return error_msg


registry = ToolRegistry()


def _register_all():
    _tc = tool_call
    _reg = registry
    _s = TOOL_NAME_MAP

    # File tools
    _reg.register("read_file", _tc(read_file), schema=_s["read_file"],
        meta={"description": "Read file (returns line-numbered output; lists nearby files on error)",
              "input_format": "`\"path/to/file.txt\"` (string path relative to workspace)"},
        category=CAT_FILE)
    _reg.register("read_file_range", _tc(read_file_range), schema=_s["read_file_range"],
        meta={"description": "Read a portion of a file with 1-based offset and optional line limit",
              "input_format": "`{\"path\": \"...\", \"offset\": 1, \"limit\": 50}`"},
        category=CAT_FILE)
    _reg.register("list_files", _tc(list_files), schema=_s["list_files"],
        meta={"description": "List directory contents (recursive, depth-capped, skips noise dirs)",
              "input_format": "`\"path/to/dir\"` or `\".\"` (string)"},
        category=CAT_FILE)
    _reg.register("write_to_file", _tc(write_to_file), schema=_s["write_to_file"],
        meta={"description": "Create or overwrite a file (use edit_file for targeted edits)",
              "input_format": "`{\"path\": \"...\", \"mode\": \"create|overwrite|append\", \"content\": \"...\", \"dry_run\": false}`"},
        category=CAT_FILE)
    _reg.register("edit_file", _tc(edit_file), schema=_s["edit_file"],
        meta={"description": "Targeted replacement in an existing file (unique old_string \u2192 new_string)",
              "input_format": "`{\"path\": \"...\", \"old_string\": \"exact text\", \"new_string\": \"replacement\"}`"},
        category=CAT_FILE)
    _reg.register("get_workspace_info", _tc(get_workspace_info), schema=_s["get_workspace_info"],
        meta={"description": "Show workspace root and top-level entries for orientation",
              "input_format": "omit or `\"\"`"},
        category=CAT_FILE)
    _reg.register("execute_command", execute_command_raw, schema=_s["execute_command"],
        meta={"description": "Run a shell command in the workspace",
              "input_format": "`\"ls -la\"` (shell command string)"},
        category=CAT_FILE)
    _reg.register("glob_search", _tc(glob_search), schema=_s["glob_search"],
        meta={"description": "Find files matching a glob pattern (e.g. '**/*.py', 'src/**/*.ts')",
              "input_format": "`\"**/*.py\"` (glob pattern string)"},
        category=CAT_FILE)
    _reg.register("grep_search", _tc(grep_search), schema=_s["grep_search"],
        meta={"description": "Search file contents by regex across the workspace",
              "input_format": "`{\"pattern\": \"...\", \"include\": \"*.py\", \"max_results\": 50}`"},
        category=CAT_FILE)

    # Meta tools (planning, tests, undo)
    _reg.register("todo_write", _tc(todo_write), schema=_s["todo_write"],
        meta={"description": "Create/update a task plan with actions: create, update, mark_done, clear",
              "input_format": "`{\"action\": \"create|update|mark_done|clear\", \"items\": [\"...\"], \"ids\": [1, 2]}`"},
        category=CAT_META)
    _reg.register("todo_read", _tc(todo_read), schema=_s["todo_read"],
        meta={"description": "Read the current task plan",
              "input_format": "omit or `\"\"`"},
        category=CAT_META)
    _reg.register("run_tests", _tc(run_tests), schema=_s["run_tests"],
        meta={"description": "Discover and run tests (pytest or unittest); specify path, pattern, framework",
              "input_format": "`{\"pattern\": \"test_*.py\", \"path\": \"tests/\", \"framework\": \"pytest\", \"timeout\": 60}`"},
        category=CAT_META)
    _reg.register("undo_last_edit", _tc(undo_last_edit), schema=_s["undo_last_edit"],
        meta={"description": "Restore the most recent checkpoint for a file, or list latest checkpoints",
              "input_format": "`{\"path\": \"optional/file.py\"}` or omit to show latest checkpoint info"},
        category=CAT_META)
    _reg.register("checkpoint_info", _tc(checkpoint_info), schema=_s["checkpoint_info"],
        meta={"description": "List available checkpoints for undo",
              "input_format": "omit or `\"\"`"},
        category=CAT_META)

    # Git tools
    _reg.register("git_status", _tc(git_status), schema=_s["git_status"],
        meta={"description": "Show current git status (tracked/untracked/modified files)",
              "input_format": "omit or `\"\"`"},
        category=CAT_GIT)
    _reg.register("git_diff", _tc(git_diff), schema=_s["git_diff"],
        meta={"description": "Show git diff; optionally filter by path or show staged changes",
              "input_format": "`{\"path\": \"optional/path\", \"staged\": false}`"},
        category=CAT_GIT)
    _reg.register("git_commit", _tc(git_commit), schema=_s["git_commit"],
        meta={"description": "Commit staged changes with a message; optional add_all to stage everything first",
              "input_format": "`{\"message\": \"commit msg\", \"add_all\": true}`"},
        category=CAT_GIT)
    _reg.register("git_log", _tc(git_log), schema=_s["git_log"],
        meta={"description": "Show recent commit history (oneline format)",
              "input_format": "`{\"max_count\": 10}`"},
        category=CAT_GIT)

    # Kernel tools
    _reg.register("kernel_retrieve", _tc(kernel_retrieve), schema=_s["kernel_retrieve"],
        meta={"description": "Query kernel memory for relevant context from past sessions",
              "input_format": "`{\"query\": \"...\", \"limit\": 10}`"},
        category=CAT_KERNEL)
    _reg.register("kernel_emit_signal", _tc(kernel_emit_signal), schema=_s["kernel_emit_signal"],
        meta={"description": "Emit an observation/signal to the kernel for pattern detection",
              "input_format": "`{\"signal_type\": \"...\", \"value\": \"...\", ...}`"},
        category=CAT_KERNEL)
    _reg.register("kernel_store_context", _tc(kernel_store_context), schema=_s["kernel_store_context"],
        meta={"description": "Store important context in kernel memory for future retrieval",
              "input_format": "`{\"memory_type\": \"context\", \"content\": \"...\", \"importance\": 0.5, ...}`"},
        category=CAT_KERNEL)
    _reg.register("kernel_get_memory", _tc(kernel_get_memory), schema=_s["kernel_get_memory"],
        meta={"description": "Retrieve a specific memory by its ID",
              "input_format": "`{\"memory_id\": \"...\"}`"},
        category=CAT_KERNEL)
    _reg.register("kernel_create_event", _tc(kernel_create_event), schema=_s["kernel_create_event"],
        meta={"description": "Create an event in the kernel timeline",
              "input_format": "`{\"event_type\": \"action\", \"title\": \"...\", ...}`"},
        category=CAT_KERNEL)

    # Simulation tools
    _reg.register("simulation_run", _tc(simulation_run), schema=_s["simulation_run"],
        meta={"description": "Run a simulation with specified parameters",
              "input_format": "`{\"run_id\": \"...\", \"params\": {...}}`"},
        category=CAT_SIM)
    _reg.register("simulation_compare", _tc(simulation_compare), schema=_s["simulation_compare"],
        meta={"description": "Compare multiple simulation runs",
              "input_format": "`{\"run_ids\": [\"...\", \"...\"]}`"},
        category=CAT_SIM)
    _reg.register("simulation_list", _tc(simulation_list), schema=_s["simulation_list"],
        meta={"description": "List all previous simulation runs",
              "input_format": "omit or `\"\"`"},
        category=CAT_SIM)
    _reg.register("simulation_get_signals", _tc(simulation_get_signals), schema=_s["simulation_get_signals"],
        meta={"description": "Get signals emitted during a simulation run",
              "input_format": "`{\"run_id\": \"...\"}`"},
        category=CAT_SIM)


_register_all()

TOOLS: Dict[str, Callable] = registry.tools_dict
TOOL_META: Dict[str, Dict[str, str]] = registry.meta_dict
