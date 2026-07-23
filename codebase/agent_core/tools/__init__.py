import os, subprocess, re
from dataclasses import dataclass, asdict
from typing import Dict, Any, Callable, Optional

from agent_core.tools.file_ops import (
    read_file,
    list_files,
    write_to_file,
    edit_file,
    get_workspace_info,
    glob_search,
    grep_search,
    batch_read_tool,
    read_section_tool,
    batch_edit_tool,
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
from agent_core.tools.code_rag import (
    get_symbol_tool,
    get_symbols_meta_tool,
    search_symbols_tool,
    get_callers_callees_tool,
    find_impact_tool,
    get_index_info_tool,
    file_api_tool,
    call_chain_tool,
    compare_apis_tool,
    symbols_by_file_tool,
    atlas_status_tool,
    project_root_tool,
    report_freshness_tool,
    extract_symbols_to_file_tool,
)
from agent_core.tools.question_ops import ask_user_question
from agent_core.tools.debate_ops import debate_step
from agent_core.tools.expand_ops import expand_topic
from agent_core.tools.context_dump import minimal_context_dump
from agent_core.tools.registry import (
    ToolRegistry, CAT_FILE, CAT_KERNEL, CAT_SIM, CAT_META, CAT_GIT, CAT_CODE_RAG,
    str_p, int_p, float_p, bool_p, arr_p, obj_p,
)


PATHS_PARAM = {
    "paths": {"type": "array", "items": {"type": "string"}, "required": True,
              "description": "List of file paths relative to workspace root"},
}

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


registry = ToolRegistry(mcp_prefix="")


def _register_file_tools(reg, tc):
    reg.set_default_category(CAT_FILE)
    from agent_core.tools.file_ops import batch_read_tool, read_section_tool, batch_edit_tool

    reg.register("read_file", tc(read_file),
        description="Read file (returns line-numbered output; lists nearby files on error)",
        params={"path": str_p("Path to the file, relative to the workspace root", req=True),
                "offset": int_p("1-based line number to start from (default 1)"),
                "limit": int_p("Max lines to return (default: entire file)")},
        mcp_expose=False)
    reg.register("list_files", tc(list_files),
        description="List directory contents (recursive, depth-capped, skips noise dirs)",
        params={"path": str_p("Directory path relative to workspace root; use '.' for root")})
    reg.register("write_to_file", tc(write_to_file),
        description="Create or overwrite a file (use edit_file for targeted edits)",
        params={"path": str_p("File path relative to workspace root", req=True),
                "mode": str_p("One of: create (fails if exists), overwrite (replaces), append (adds to end)", req=True),
                "content": str_p("File content to write"),
                "dry_run": bool_p("If true, validate without writing")},
        mcp_expose=False)
    reg.register("edit_file", tc(edit_file),
        description="Replace exact old_string with new_string in an existing file. old_string must match exactly once.",
        params={"path": str_p("File path relative to workspace root", req=True),
                "old_string": str_p("Exact existing text to replace (whitespace-sensitive)", req=True),
                "new_string": str_p("Replacement text", req=True)},
        mcp_expose=False)
    reg.register("get_workspace_info", tc(get_workspace_info),
        description="Show workspace root and top-level entries for orientation",
        params={})
    reg.register("execute_command", execute_command_raw,
        description="Run a shell command. Allowed: ls, cat, pwd, echo, python.",
        params={"command": str_p("Shell command string to execute", req=True)},
        mcp_expose=False)
    reg.register("glob_search", tc(glob_search),
        description="Find files matching a glob pattern (e.g. '**/*.py', 'src/**/*.ts')",
        params={"pattern": str_p("Glob pattern to match files against, relative to workspace root", req=True)},
        mcp_expose=False)
    reg.register("grep_search", tc(grep_search),
        description="Search file contents by regex across the workspace",
        params={"pattern": str_p("Regex pattern to search for in file contents", req=True),
                "include": str_p("Optional file glob filter (e.g. '*.py' or '*.{py,ts}')"),
                "max_results": int_p("Max results to return (default 50)")},
        mcp_expose=False)
    reg.register("batch_read", tc(batch_read_tool),
        description="Read multiple non-kernel files at once. Saves token overhead vs sequential Read calls. Warns on kernel files.",
        params=PATHS_PARAM)
    reg.register("read_section", tc(read_section_tool),
        description="Read a file section around a regex pattern match. Returns match line + context lines. Use instead of read_file when searching by content pattern.",
        params={"path": str_p("File path relative to workspace root", req=True),
                "pattern": str_p("Regex pattern to search for within the file", req=True),
                "context_lines": int_p("Number of context lines before and after each match (default 10)"),
                "ignore_case": bool_p("If true, case-insensitive matching (default false)")})
    reg.register("batch_edit", tc(batch_edit_tool),
        description="Apply multiple string replacements to a file in one call. Each edit is applied sequentially.",
        params={"path": str_p("File path relative to workspace root", req=True),
                "edits": {"t": "array", "desc": "List of edits to apply sequentially", "r": True,
                          "items": {"type": "object", "properties": {
                              "old_string": {"type": "string", "description": "Exact text to replace"},
                              "new_string": {"type": "string", "description": "Replacement text"},
                              "replace_all": {"type": "boolean", "description": "If true, replace all occurrences (default: replace first only)"}},
                          "additionalProperties": False}}})


def _register_meta_tools(reg, tc):
    reg.set_default_category(CAT_META)

    reg.register("todo_write", tc(todo_write),
        description="Create/update a task plan. Actions: create (new plan), update (append), mark_done, clear",
        params={"action": str_p("One of: create, update, mark_done, clear", req=True),
                "items": arr_p("string", "List of task descriptions (for create/update)"),
                "ids": arr_p("integer", "Task IDs to mark done (for mark_done)")})
    reg.register("todo_read", tc(todo_read),
        description="Read the current task plan",
        params={})
    reg.register("run_tests", tc(run_tests),
        description="Discover and run tests in the workspace using pytest or unittest. Specify path to limit scope, pattern for file filter, or framework to override auto-detection.",
        params={"pattern": str_p("Optional glob pattern to filter test files (e.g. 'test_*.py')"),
                "path": str_p("Optional directory path to search for tests (default: workspace root)"),
                "framework": str_p("Test framework: 'pytest' (default) or 'unittest'"),
                "timeout": int_p("Timeout in seconds (default 60)")})
    reg.register("undo_last_edit", tc(undo_last_edit),
        description="Restore the most recent checkpoint for a file, or list latest checkpoint info",
        params={"path": str_p("Optional file path to undo; omit to show latest checkpoint")})
    reg.register("checkpoint_info", tc(checkpoint_info),
        description="List available checkpoints for undo operations",
        params={})
    reg.register("ask_user_question", tc(ask_user_question),
        description="Ask the user for input, clarification, or a decision. Provide up to 3 options per question (a 4th 'custom answer' text input is always available). Can ask multiple questions at once — user answers them one by one.",
        params={"questions": {"t": "array", "desc": "Questions to ask. User answers them sequentially. Max 3 options each.", "r": True,
                              "items": {"type": "object", "properties": {
                                  "question": {"type": "string", "description": "The question text"},
                                  "options": {"type": "array", "items": {"type": "string"}, "description": "Up to 3 predefined answer choices"}},
                              "additionalProperties": False}}})
    reg.register("debate_step", debate_step,
        description="Present next debate argument for a topic and get user response. Handles argument selection, belief tracking, contradiction detection. When graph is exhausted, pass llm_generated to add a new argument.",
        params={"topic": str_p("Topic name to explore (e.g. 'theism_atheism')", req=True),
                "llm_generated": {"t": "object", "desc": "New argument when graph is exhausted",
                                  "properties": {"name": {"type": "string", "description": "Unique argument name"},
                                                  "premise": {"type": "string", "description": "The argument premise"},
                                                  "side": {"type": "string", "description": "One of: pro, con, neutral"}},
                                  "additionalProperties": False}})
    reg.register("expand_topic", expand_topic,
        description="Add new nodes and edges to a topic's argument graph. Validates no duplicate names, persists to graph.json, and re-indexes the vector store.",
        params={"topic": str_p("Topic name to expand (e.g. 'theism_atheism')", req=True),
                "new_nodes": {"t": "array", "desc": "New argument nodes to add", "r": True,
                              "items": {"type": "object", "properties": {
                                  "name": {"type": "string", "description": "Unique argument name"},
                                  "premise": {"type": "string", "description": "The argument premise"},
                                  "side": {"type": "string", "description": "Side: pro, con, or neutral"}},
                              "additionalProperties": False}},
                "new_edges": {"t": "array", "desc": "New edges between arguments",
                              "items": {"type": "object", "properties": {
                                  "source": {"type": "string", "description": "Source argument name"},
                                  "target": {"type": "string", "description": "Target argument name"},
                                  "relation": {"type": "string", "description": "Edge relation (e.g. refutes, supports)"}},
                              "additionalProperties": False}}})


def _register_git_tools(reg, tc):
    reg.set_default_category(CAT_GIT)

    reg.register("git_status", tc(git_status),
        description="Show git status of the workspace — modified, staged, untracked files",
        params={})
    reg.register("git_diff", tc(git_diff),
        description="Show git diff of uncommitted changes. Optionally filter by path or show staged diff.",
        params={"path": str_p("Optional file path to filter diff"),
                "staged": bool_p("If true, show staged diff (default false)")})
    reg.register("git_commit", tc(git_commit),
        description="Commit staged changes with a message. Set add_all=true to stage all changes first.",
        params={"message": str_p("Commit message (required)", req=True),
                "add_all": bool_p("If true, run git add -A before commit")})
    reg.register("git_log", tc(git_log),
        description="Show recent commit history in oneline format",
        params={"max_count": int_p("Max commits to show (default 10)")})


def _register_kernel_tools(reg, tc):
    reg.set_default_category(CAT_KERNEL)
    from agent_core.tools.kernel_ops import (
        kernel_retrieve, kernel_emit_signal, kernel_reload,
        kernel_store_context, kernel_get_memory, kernel_create_event,
    )

    reg.register("kernel_retrieve", tc(kernel_retrieve),
        description="Query kernel memory for relevant context from past sessions",
        params={"query": str_p("Search query for retrieving relevant memories", req=True),
                "limit": int_p("Maximum number of results to return (default 10)")})
    reg.register("kernel_emit_signal", tc(kernel_emit_signal),
        description="Emit an observation/signal to the kernel for pattern detection and belief tracking",
        params={"signal_type": str_p("Type of signal (e.g. observation, finding)"),
                "value": str_p("The signal value/content", req=True),
                "title": str_p("Optional title for the signal"),
                "description": str_p("Optional longer description"),
                "category": str_p("Optional category (default: general)"),
                "confidence": float_p("Confidence score 0-1 (default 1.0)"),
                "importance": float_p("Importance score 0-1 (default 0.5)"),
                "tags": arr_p("string", "Optional tags")})
    reg.register("kernel_store_context", tc(kernel_store_context),
        description="Store important context in kernel memory for future retrieval across sessions",
        params={"memory_type": str_p("Type of memory (default: context)"),
                "content": str_p("The content/memory to store", req=True),
                "importance": float_p("Importance score 0-1 (default 0.5)"),
                "confidence": float_p("Confidence score 0-1 (default 1.0)"),
                "tags": arr_p("string", "Optional tags"),
                "ttl_seconds": int_p("Time-to-live in seconds (default 3600)")})
    reg.register("kernel_get_memory", tc(kernel_get_memory),
        description="Retrieve a specific memory by its ID from kernel storage",
        params={"memory_id": str_p("The ID of the memory to retrieve", req=True)})
    reg.register("kernel_create_event", tc(kernel_create_event),
        description="Create an event in the kernel timeline for tracking significant actions",
        params={"event_type": str_p("Type of event (default: action)"),
                "title": str_p("Event title (required)", req=True),
                "description": str_p("Optional event description"),
                "category": str_p("Optional category (default: general)"),
                "confidence": float_p("Confidence 0-1 (default 1.0)"),
                "importance": float_p("Importance 0-1 (default 0.5)"),
                "tags": arr_p("string", "Optional tags")})
    reg.register("kernel_reload", tc(kernel_reload),
        description="Reload tool modules from disk to pick up code changes without restart",
        params={"modules": arr_p("string", "Optional list of module names to reload (default: all hot modules)")})


def _register_sim_tools(reg, tc):
    reg.set_default_category(CAT_SIM)
    from agent_core.tools.sim_ops import (
        simulation_run, simulation_compare,
        simulation_list, simulation_get_signals,
    )

    reg.register("simulation_run", tc(simulation_run),
        description="Run a simulation with specified parameters and get results",
        params={"run_id": str_p("Unique identifier for this simulation run", req=True),
                "params": obj_p("Simulation parameters (e.g. years, initial_pop, grid_width)", additionalProperties=True),
                "timeout": int_p("Max run time in seconds (omit for no limit)")})
    reg.register("simulation_compare", tc(simulation_compare),
        description="Compare results from multiple simulation runs",
        params={"run_ids": arr_p("string", "List of run IDs to compare", req=True)})
    reg.register("simulation_list", tc(simulation_list),
        description="List all previous simulation runs",
        params={})
    reg.register("simulation_get_signals", tc(simulation_get_signals),
        description="Get signals emitted during a simulation run",
        params={"run_id": str_p("The run ID to retrieve signals from", req=True)})


def _register_code_rag_tools(reg, tc):
    reg.set_default_category(CAT_CODE_RAG)
    from agent_core.tools.code_rag import (
        get_symbol_tool, get_symbols_meta_tool,
        search_symbols_tool, get_callers_callees_tool, find_impact_tool,
        get_index_info_tool,
        file_api_tool, call_chain_tool, compare_apis_tool, symbols_by_file_tool,
        atlas_status_tool, project_root_tool,         report_freshness_tool,
        batch_file_api_tool, extract_symbols_to_file_tool,
        report_inventory_tool,
        report_schema_check_tool,
        list_capabilities_tool,
        resolve_citations_tool,
    )

    reg.register("get_symbol", tc(get_symbol_tool),
        description="PRIMARY lookup when the user names functions/classes. Batch: names=['func1','func2']. Returns full source, signature, docstring. Prefer this over search_symbols when exact names are known. On missing names, response includes missing_names — then search_symbols only for those.",
        params={"names": arr_p("string", "Exact function/class names to look up in one batch (e.g. ['func1', 'func2']).", req=True),
                "file_path": str_p("Optional file path to narrow all lookups to one file")})
    reg.register("get_symbols_meta", tc(get_symbols_meta_tool),
        description="Batch metadata lookup for multiple function/class names. Returns signature, docstring, token_count, risk_level, line numbers — but NOT full source code. Use this to browse many definitions cheaply, then call get_symbol only for the ones worth fetching in full.",
        params={"names": arr_p("string", "Exact function/class names to look up (e.g. ['func1', 'func2']).", req=True),
                "file_path": str_p("Optional file path to narrow all lookups to one file")})
    reg.register("search_symbols", tc(search_symbols_tool),
        description="Metadata-only full-text search over symbol names/docstrings/code. Use when names are unknown or get_symbol returned missing_names (misspelling). Does NOT return full source — pick relevant names then call get_symbol. Do not use as the first step when the user already gave exact symbol names.",
        params={"query": str_p("Search query (supports FTS5 syntax, e.g. 'auth AND login', 'process_order')", req=True),
                "type_filter": str_p("Optional filter: 'function', 'class', 'method', or 'file'"),
                "top_k": int_p("Number of results to return (default 10)")})
    reg.register("get_callers_callees", tc(get_callers_callees_tool),
        description="Show which functions call a given symbol (callers) and which functions it calls (callees). Uses recursive graph traversal up to the specified depth.",
        params={"name": str_p("Function or class name to analyze", req=True),
                "file_path": str_p("Optional file path to disambiguate"),
                "direction": str_p("Direction: 'callers', 'callees', or 'both' (default: 'both')")})
    reg.register("find_impact", tc(find_impact_tool),
        description="Find all functions that would be affected by changing the given symbol. Lists everything that directly or transitively depends on it.",
        params={"name": str_p("Function or class name to check impact for", req=True),
                "file_path": str_p("Optional file path to disambiguate")})
    reg.register("get_index_info", tc(get_index_info_tool),
        description="Return real-time statistics about the indexed codebase (total symbols, call edges, token ranges, risk distribution). Use this once at the start of a session to calibrate token budget and batch sizes.",
        params={})
    reg.register("file_api", tc(file_api_tool),
        description="Return the public API surface of a file: class names + method signatures (with docstring first line), module-level function signatures, and exported symbols — without any method bodies. Use for orientation before making changes.",
        params={"path": str_p("File path relative to workspace root", req=True)})
    reg.register("call_chain", tc(call_chain_tool),
        description="Trace the shortest call chain from one function to any function in another module. Uses the existing call-edge index. Example: call_chain('detect_contradictions', 'kernel.semantic_memory').",
        params={"start_fn": str_p("Starting function or class name", req=True),
                "end_module": str_p("Target module path substring (e.g. 'kernel.semantic_memory')", req=True),
                "file_path": str_p("Optional file path to disambiguate start_fn")})
    reg.register("compare_apis", tc(compare_apis_tool),
        description="Diff two files by method name + signature only, ignoring method bodies. Shows methods present in one but not the other, and signature mismatches.",
        params={"path_a": str_p("First file path relative to workspace root", req=True),
                "path_b": str_p("Second file path relative to workspace root", req=True)})
    reg.register("symbols_by_file", tc(symbols_by_file_tool),
        description="List every symbol (class, function, global variable) in a file with its type, line range, risk level, and signature — without requiring exact names. Unlike search_symbols, this doesn't need a query — it returns everything in the file.",
        params={"path": str_p("File path relative to workspace root", req=True)})
    reg.register("atlas_status", tc(atlas_status_tool),
        description="Show whether the codebase atlas is indexed, when it was last ingested, and how many files/symbols/call edges it contains. Call this first when you suspect the atlas is stale or missing.",
        params={})
    reg.register("project_root", tc(project_root_tool),
        description="Return the project root and codebase root absolute paths. Useful for path resolution across scripts.",
        params={})
    reg.register("report_freshness", tc(report_freshness_tool),
        description="Scan all system_devpt_reports/*.md files, parse their _Last verified date stamps, and flag any that are stale (file's last git change is newer than the stamp, or cited file:function() symbols no longer resolve in the atlas). Use this before relying on a status report for planning.",
        params={})
    reg.register("batch_file_api", tc(batch_file_api_tool),
        description="Query the codebase atlas for the public API surface of multiple files in one call. Each file returns class names + method signatures, module-level function signatures, and exported symbols — without any method bodies. Use this instead of calling file_api sequentially for each file.",
        params=PATHS_PARAM)
    reg.register("minimal_context_dump", tc(minimal_context_dump),
        description="Generate a compact context file for an external LLM by chaining existing atlas tools. Given a problem description and symbols, it resolves the blast radius, fetches only relevant symbol source (not whole files), includes API signatures for peripheral files, and writes one capped file. Prefer this over full-file dumps like copyContent.py.",
        params={"problem_description": str_p("The problem or question that needs external LLM context", req=True),
                "symbol_names": arr_p("string", "Starting function/class names to investigate (blast radius is auto-resolved)", req=True),
                "file_paths": arr_p("string", "Optional peripheral file paths for API-surface-only inclusion"),
                "output_path": str_p("Optional output path (default: project_root/context_dump.txt)"),
                "max_tokens": int_p("Optional token budget cap (default: 8000)")})
    reg.register("extract_symbols_to_file", tc(extract_symbols_to_file_tool),
        description="Extract full source code of named symbols from the atlas into a single file. Fetches bodies only for the given symbols (not entire files), writes them to destination with headers. Use this instead of manually copying symbol source into a new file during refactoring.",
        params={"names": arr_p("string", "Exact symbol names to extract", req=True),
                "destination": str_p("Output file path (relative to project root)", req=True),
                "file_path": str_p("Optional file path to disambiguate symbols")})
    reg.register("report_inventory", tc(report_inventory_tool),
        description="Scan all system_devpt_reports/ files and return per-file: path, role (status/roadmap/readme), line count, has _Last verified, citation count, empty flag. One call replaces multi-file find + head + partial reads.",
        params={})
    reg.register("report_schema_check", tc(report_schema_check_tool),
        description="Check each status.md for schema compliance: missing sections, bullets without file:symbol() citations, roadmap language in status.",
        params={})
    reg.register("list_capabilities", tc(list_capabilities_tool),
        description="Live dump of capability_claim/known_gap hypotheses from HypothesisEngine. Returns id, type, status, title, evidence_path, evidence_symbol. Optionally filter by type.",
        params={"type": str_p("Optional filter: 'capability_claim' or 'known_gap'")})
    reg.register("resolve_citations", tc(resolve_citations_tool),
        description="Resolve a list of path:symbol() citations against the atlas database. Returns resolved/missing status for each. Wraps the same logic as validate_capabilities.py as an MCP tool.",
        params={"citations": arr_p("string", "List of citations like ['file.py:func()', 'path/to/module.py:ClassName()']", req=True)})


def _register_all():
    _tc = tool_call
    _reg = registry
    _register_file_tools(_reg, _tc)
    _register_meta_tools(_reg, _tc)
    _register_git_tools(_reg, _tc)
    _register_kernel_tools(_reg, _tc)
    _register_sim_tools(_reg, _tc)
    _register_code_rag_tools(_reg, _tc)


_register_all()

TOOLS: Dict[str, Callable] = registry.tools_dict
TOOL_META: Dict[str, Dict[str, str]] = registry.meta_dict
