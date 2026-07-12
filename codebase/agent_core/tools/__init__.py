import os, subprocess, re
from typing import Dict, Any, Callable

from agent_core.tools.file_ops import (
    read_file,
    list_files,
    write_to_file,
    edit_file,
    get_workspace_info,
)
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

LOG_FILE = "tui_output.txt"
ALLOWED_COMMANDS = ["ls", "cat", "pwd", "echo", "python"]


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


def execute_command(cmd: str) -> str:
    if not any(cmd.startswith(c) for c in ALLOWED_COMMANDS):
        return "Command not allowed"
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


TOOLS: Dict[str, Callable] = {
    "read_file": read_file,
    "list_files": list_files,
    "write_to_file": write_to_file,
    "edit_file": edit_file,
    "get_workspace_info": get_workspace_info,
    "execute_command": execute_command,
    "kernel_retrieve": kernel_retrieve,
    "kernel_emit_signal": kernel_emit_signal,
    "kernel_store_context": kernel_store_context,
    "kernel_get_memory": kernel_get_memory,
    "kernel_create_event": kernel_create_event,
    "simulation_run": simulation_run,
    "simulation_compare": simulation_compare,
    "simulation_list": simulation_list,
    "simulation_get_signals": simulation_get_signals,
}
