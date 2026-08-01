import importlib
import os
import sys

# On hot-reload this module body re-executes. Reload submodules FIRST so the
# `from agent_core.tools.X import ...` statements below bind fresh objects.
# Skip infra modules: reloading them redefines classes (ToolRegistry, ToolResult),
# breaking isinstance/registry identity for consumers holding old references.
_SKIP_RELOAD = {__name__ + ".registry", __name__ + ".types"}
for _mod in list(sys.modules):
    if _mod.startswith(__name__ + ".") and _mod not in _SKIP_RELOAD:
        importlib.reload(sys.modules[_mod])

from typing import Callable

from agent_core.tools.exec_ops import (
    log_output,
    execute_command_raw,
)
from agent_core.tools.file_ops import (
    read_file,
    list_files,
    write_to_file,
    edit_file,
)
from agent_core.tools.meta_ops import (
    get_workspace_info,
    read_section_tool,
    check_path_exists,
    cross_file_edit,
    check_before_edit,
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
from agent_core.tools.kernel_ops import (
    KERNEL_AVAILABLE,
    kernel_retrieve,
    kernel_emit_signal,
    kernel_store_context,
    kernel_get_memory,
    kernel_create_event,
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
    batch_file_api_tool,
    report_inventory_tool,
    report_schema_check_tool,
    list_capabilities_tool,
    resolve_citations_tool,
)
from agent_core.tools.question_ops import ask_user_question, todo
from agent_core.tools.diff_ops import file_diff
from agent_core.tools.search_ops import glob_search, grep_search
from agent_core.tools.ast_ops import file_skeleton, who_imports
from agent_core.tools.context_dump import minimal_context_dump
from agent_core.tools.tool_introspect import tool_anatomy
from agent_core.tools.registry import (
    ToolRegistry, CAT_FILE, CAT_KERNEL, CAT_SIM, CAT_META, CAT_GIT, CAT_OBSERVER, CAT_CODE_RAG, CAT_DEBATE,
    str_p, int_p, float_p, bool_p, arr_p, obj_p, derive_schema,
)
from agent_core.tools.observer_ops import tool_stats, file_stats, user_reading_budget
from agent_core.config import SUBAGENT_TASK_ENABLED


PATHS_PARAM = {
    "paths": {"type": "array", "items": {"type": "string"}, "required": True,
              "description": "List of file paths relative to workspace root"},
}


from agent_core.tools.types import ToolError, ToolResult


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


_existing_registry = globals().get("registry")
registry = _existing_registry if hasattr(_existing_registry, "register") else ToolRegistry()


# =========================== Table-driven registration ===========================
# Spec: (name, fn, category, description, params[, wrap=False]).
# `wrap` defaults True — tools get the tc() ToolResult wrapper. debate/expand and
# hot_reload register raw callables (wrap=False).

_IMPL_INDEX: dict[str, tuple[str, int]] = {}


def _register(specs):
    for spec in specs:
        name, fn, cat, desc, params = spec[:5]
        wrap = spec[5] if len(spec) > 5 else True
        code = getattr(fn, "__code__", None)
        if code is not None:
            _IMPL_INDEX[name] = (code.co_filename, code.co_firstlineno)
        registry.register(name, tool_call(fn) if wrap else fn,
                          description=desc, params=params, category=cat)


_FILE_SPECS = [
    ("read_file", read_file, CAT_FILE,
     "Read file (returns line-numbered output; lists nearby files on error; set line_numbers=false to save tokens). Pass paths=[...] to batch-read multiple files in one call — the top-level offset/limit/line_numbers then apply to every file.",
     {"path": str_p("Path to the file, relative to the workspace root", req=True),
      "paths": arr_p("string", "Batch read: list of file paths to read in one call. offset/limit/line_numbers (top-level) apply to each file."),
      "offset": int_p("1-based line number to start from (default 1)"),
      "limit": int_p("Max lines to return (default: 1000; pass 0 for no limit)"),
      "line_numbers": bool_p("If true (default), prefix each line with line number. Set false to save tokens when only content is needed.")}),
    ("list_files", list_files, CAT_FILE,
     "List directory contents (shallow by default; set recursive=true for deep listing up to 3 levels; skips excluded dirs). For quick workspace orientation use get_workspace_info instead.",
     {"path": str_p("Directory path relative to workspace root; use '.' for root"),
      "recursive": bool_p("If true, list recursively up to 3 levels deep (default false — flat listing only)")}),
    ("write_to_file", write_to_file, CAT_FILE,
     "Create or overwrite a file (use edit_file for targeted edits)",
     {"path": str_p("File path relative to workspace root", req=True),
      "mode": str_p("One of: create (fails if exists), overwrite (replaces), append (adds to end)", req=True),
      "content": str_p("File content to write"),
      "dry_run": bool_p("If true, validate without writing")}),
    ("edit_file", edit_file, CAT_FILE,
     "Replace exact old_string with new_string in an existing file. old_string must match exactly once (or set replace_all=true). Pass edits=[...] to apply multiple replacements to the same file in one call — each edit is applied sequentially with checkpoint + cache parity.",
     {"path": str_p("File path relative to workspace root", req=True),
      "old_string": str_p("Exact existing text to replace (whitespace-sensitive)", req=True),
      "new_string": str_p("Replacement text", req=True),
      "replace_all": bool_p("If true, replace all occurrences of old_string (default false)"),
      "edits": {"t": "array", "desc": "List of edits to apply sequentially (use instead of single old_string/new_string)", "r": False,
                "items": {"type": "object", "properties": {
                    "old_string": {"type": "string", "description": "Exact text to replace"},
                    "new_string": {"type": "string", "description": "Replacement text"},
                    "replace_all": {"type": "boolean", "description": "If true, replace all occurrences (default: replace first only)"}},
                    "additionalProperties": False}}}),
    ("execute_command", execute_command_raw, CAT_FILE,
     "Run a shell command. Allowed: ls, cat, pwd, echo, python.",
     {"command": str_p("Shell command string to execute", req=True)}),
    ("glob_search", glob_search, CAT_FILE,
     "Find files matching a glob pattern (e.g. '**/*.py', 'src/**/*.ts')",
     derive_schema(glob_search, {"pattern": "Glob pattern to match files against, relative to workspace root"})),
    ("grep_search", grep_search, CAT_FILE,
     "Search file contents by regex across the workspace. Optionally pass context_lines=N to return N surrounding lines per match (default 0 — match lines only).",
     {"pattern": str_p("Regex pattern to search for in file contents", req=True),
      "include": str_p("Optional file glob filter (e.g. '*.py' or '*.{py,ts}')"),
      "context_lines": int_p("Lines of context before/after each match (default 0)"),
      "max_results": int_p("Max result lines to return (default 50)")}),
    ("todo", todo, CAT_FILE,
     "Manage a task plan. Actions: read (show current plan), create (new plan), update (append items), mark_done (complete tasks by id), clear.",
     {"action": str_p("One of: read, create, update, mark_done, clear", req=True),
      "items": arr_p("string", "List of task descriptions (for create/update)"),
      "ids": arr_p("integer", "Task IDs to mark done (for mark_done)")}),
    ("ask_user_question", ask_user_question, CAT_FILE,
     "Ask the user for input, clarification, or a decision. Provide up to 3 options per question (a 4th 'custom answer' text input is always available). Can ask multiple questions at once — user answers them one by one.",
     {"questions": {"t": "array", "desc": "Questions to ask. User answers them sequentially. Max 3 options each.", "r": True,
                    "items": {"type": "object", "properties": {
                        "question": {"type": "string", "description": "The question text"},
                        "options": {"type": "array", "items": {"type": "string"}, "description": "Up to 3 predefined answer choices"}},
                        "additionalProperties": False}}}),
]

if SUBAGENT_TASK_ENABLED:
    from agent_core.tools.subagent_ops import subagent_task
    _FILE_SPECS.append(("subagent_task", subagent_task, CAT_FILE,
        "Delegate an open-ended research or exploration task to a sub-agent. The sub-agent runs its own agent loop with full tool access and returns its final answer. Use this when exploration would consume significant context tokens or requires multiple rounds of search/grep/read.",
        {"task": str_p("The task description for the sub-agent to execute", req=True),
         "provider": str_p("Optional provider override (default: active provider)"),
         "model": str_p("Optional model override (default: active model)"),
         "max_steps": int_p("Max steps for sub-agent loop (default 15)")}))

_AST_SPECS = [
    ("file_skeleton", file_skeleton, CAT_META,
     "Compact structural map of a file via AST: imports (eager/lazy), globals, classes and functions with signatures + line ranges — ~10% of a full read. Atlas-free and always fresh, unlike file_api (atlas-indexed). Use for orientation before reading full files. Accepts a single path string or a list.",
     {"paths": arr_p("string", "Single path string or list of file paths (relative to workspace root) to skeletonize", req=True)}),
    ("who_imports", who_imports, CAT_META,
     "Module-level import graph for a file: what it imports (eager vs lazy) and which workspace files import it (resolved including relative imports). Complements symbol-level get_callers_callees. Use to find consumers/blast radius before editing. Accepts a single path string or a list.",
     {"paths": arr_p("string", "Single path string or list of file paths (relative to workspace root) to analyze", req=True)}),
]

_META_SPECS = [
    ("check_path_exists", check_path_exists, CAT_META,
     "Check if a file or directory exists at the given path (cheap — no file content read). Use this to verify existence before read_file or list_files calls.",
     derive_schema(check_path_exists, {"path": "Path to check, relative to workspace root"})),
    ("get_workspace_info", get_workspace_info, CAT_META,
     "Show workspace root and top-level entries for orientation",
     {}),
    ("file_diff", file_diff, CAT_META,
     "Show diff of uncommitted changes for a file vs checkpoint or git HEAD. Returns ~5 lines — use for lightweight edit verification instead of re-reading the full file.",
     {"path": str_p("File path relative to workspace root", req=True)}),
    ("read_section", read_section_tool, CAT_META,
     "Read a file section around a regex pattern match. Returns match line + context lines. Use instead of read_file when searching by content pattern.",
     {"path": str_p("File path relative to workspace root", req=True),
      "pattern": str_p("Regex pattern to search for within the file", req=True),
      "context_lines": int_p("Number of context lines before and after each match (default 10)"),
      "ignore_case": bool_p("If true, case-insensitive matching (default false)")}),
    ("undo_last_edit", undo_last_edit, CAT_META,
     "Restore the most recent checkpoint for a file, or list latest checkpoint info",
     {"path": str_p("Optional file path to undo; omit to show latest checkpoint")}),
    ("checkpoint_info", checkpoint_info, CAT_META,
     "List available checkpoints for undo operations",
     {}),
    ("cross_file_edit", cross_file_edit, CAT_META,
     "Apply edits across MULTIPLE files in one call — each entry has its own path. Unlike edit_file(edits=[...]) which is single-file only. input_data = {\"edits\": [{\"path\", \"old_string\", \"new_string\", optional replace_all}, ...]}. Returns per-edit status + summary.",
     {"edits": {"t": "array", "desc": "Edits to apply across files", "r": True,
                "items": {"type": "object", "properties": {
                    "path": {"type": "string", "description": "File path relative to workspace root"},
                    "old_string": {"type": "string", "description": "Exact existing text to replace"},
                    "new_string": {"type": "string", "description": "Replacement text"},
                    "replace_all": {"type": "boolean", "description": "If true, replace all occurrences (default: replace first only)"}},
                    "additionalProperties": False}}}),
    ("check_before_edit", check_before_edit, CAT_META,
     "Read-only dry-run: verify planned edit targets WOULD match exactly once BEFORE applying. Returns per-edit: OK (match at line N), NO MATCH (+ closest line), or MULTIPLE (match lines). Use before cross_file_edit or edit_file batches to avoid batch-failure recovery cycles. Does not modify files.",
     {"edits": {"t": "array", "desc": "Edit targets to validate", "r": True,
                "items": {"type": "object", "properties": {
                    "path": {"type": "string", "description": "File path relative to workspace root"},
                    "old_string": {"type": "string", "description": "Exact text the edit would look for"}},
                    "additionalProperties": False}}}),
    ("tool_anatomy", tool_anatomy, CAT_META,
     "Registry introspection. tool_anatomy(name='X') traces ONE tool: category, registration line (__init__.py), implementation file:line, mcp_expose, enabled_now, schema params, and every cross-file reference (prompt fragments, mock scenarios, tests, stepper._EDIT_TOOLS, audit._WRITE_TOOLS, session_state observers, mcp_server) plus merge/rename history. tool_anatomy() lists ALL tools grouped by category with impl + registration locations, resolved config, and a stale-reference scan (docs/mocks referencing unregistered names — e.g. renamed tools).",
     {"name": str_p("Tool name to trace in depth (omit for full inventory)"),
      "names": arr_p("string", "Batch: list of tool names to trace in one call"),
      "category": str_p("Filter inventory by category: file, meta, kernel, git, code_rag, observer, sim, debate"),
      "config": bool_p("If true, prepend resolved-config header in deep mode (always present in inventory)")}),
]

_GIT_SPECS = [
    ("git_status", git_status, CAT_GIT,
     "Show git status of the workspace — modified, staged, untracked files",
     {}),
    ("git_diff", git_diff, CAT_GIT,
     "Show git diff of uncommitted changes. Optionally filter by path or show staged diff.",
     {"path": str_p("Optional file path to filter diff"),
      "staged": bool_p("If true, show staged diff (default false)")}),
    ("git_commit", git_commit, CAT_GIT,
     "Commit staged changes with a message. Set add_all=true to stage all changes first.",
     {"message": str_p("Commit message (required)", req=True),
      "add_all": bool_p("If true, run git add -A before commit")}),
    ("git_log", git_log, CAT_GIT,
     "Show recent commit history in oneline format",
     {"max_count": int_p("Max commits to show (default 10)")}),
]

_CODE_RAG_SPECS = [
    ("get_symbol", get_symbol_tool, CAT_CODE_RAG,
     "PRIMARY lookup when the user names functions/classes. Batch: names=['func1','func2']. Returns full source, signature, docstring. Prefer this over search_symbols when exact names are known. On missing names, response includes missing_names — then search_symbols only for those.",
     {"names": arr_p("string", "Exact function/class names to look up in one batch (e.g. ['func1', 'func2']).", req=True),
      "file_path": str_p("Optional file path to narrow all lookups to one file")}),
    ("get_symbols_meta", get_symbols_meta_tool, CAT_CODE_RAG,
     "Batch metadata lookup for multiple function/class names. Returns signature, docstring, token_count, risk_level, line numbers — but NOT full source code. Use this to browse many definitions cheaply, then call get_symbol only for the ones worth fetching in full.",
     {"names": arr_p("string", "Exact function/class names to look up (e.g. ['func1', 'func2']).", req=True),
      "file_path": str_p("Optional file path to narrow all lookups to one file")}),
    ("search_symbols", search_symbols_tool, CAT_CODE_RAG,
     "Metadata-only full-text search over symbol names/docstrings/code. Use when names are unknown or get_symbol returned missing_names (misspelling). Does NOT return full source — pick relevant names then call get_symbol. Do not use as the first step when the user already gave exact symbol names.",
     {"query": str_p("Single search query (FTS5 syntax, e.g. 'auth AND login')"),
      "queries": arr_p("string", "Multiple queries to search and merge results (deduplicated) — use instead of calling search_symbols repeatedly"),
      "type_filter": str_p("Optional filter: 'function', 'class', 'method', or 'file'"),
      "top_k": int_p("Number of results per query (default 10)")}),
    ("get_callers_callees", get_callers_callees_tool, CAT_CODE_RAG,
     "Show which functions call a given symbol (callers) and which functions it calls (callees). Uses recursive graph traversal up to the specified depth.",
     {"name": str_p("Function or class name to analyze", req=True),
      "file_path": str_p("Optional file path to disambiguate"),
      "direction": str_p("Direction: 'callers', 'callees', or 'both' (default: 'both')")}),
    ("find_impact", find_impact_tool, CAT_CODE_RAG,
     "Find all functions that would be affected by changing the given symbol. Lists everything that directly or transitively depends on it.",
     {"name": str_p("Function or class name to check impact for", req=True),
      "file_path": str_p("Optional file path to disambiguate")}),
    ("get_index_info", get_index_info_tool, CAT_CODE_RAG,
     "Return real-time statistics about the indexed codebase (total symbols, call edges, token ranges, risk distribution). Use this once at the start of a session to calibrate token budget and batch sizes.",
     {}),
    ("file_api", file_api_tool, CAT_CODE_RAG,
     "Return the public API surface of a file: class names + method signatures (with docstring first line), module-level function signatures, and exported symbols — without any method bodies. Use for orientation before making changes.",
     {"path": str_p("File path relative to workspace root", req=True)}),
    ("call_chain", call_chain_tool, CAT_CODE_RAG,
     "Trace the shortest call chain from one function to any function in another module. Uses the existing call-edge index. Example: call_chain('detect_contradictions', 'kernel.semantic_memory').",
     {"start_fn": str_p("Starting function or class name", req=True),
      "end_module": str_p("Target module path substring (e.g. 'kernel.semantic_memory')", req=True),
      "file_path": str_p("Optional file path to disambiguate start_fn")}),
    ("compare_apis", compare_apis_tool, CAT_CODE_RAG,
     "Diff two files by method name + signature only, ignoring method bodies. Shows methods present in one but not the other, and signature mismatches.",
     {"path_a": str_p("First file path relative to workspace root", req=True),
      "path_b": str_p("Second file path relative to workspace root", req=True)}),
    ("symbols_by_file", symbols_by_file_tool, CAT_CODE_RAG,
     "List every symbol (class, function, global variable) in a file with its type, line range, risk level, and signature — without requiring exact names. Unlike search_symbols, this doesn't need a query — it returns everything in the file.",
     {"path": str_p("File path relative to workspace root", req=True)}),
    ("atlas_status", atlas_status_tool, CAT_CODE_RAG,
     "Show whether the codebase atlas is indexed, when it was last ingested, and how many files/symbols/call edges it contains. Call this first when you suspect the atlas is stale or missing.",
     {}),
    ("project_root", project_root_tool, CAT_CODE_RAG,
     "Return the project root and codebase root absolute paths. Useful for path resolution across scripts.",
     {}),
    ("report_freshness", report_freshness_tool, CAT_CODE_RAG,
     "Scan all system_devpt_reports/*.md files, parse their _Last verified date stamps, and flag any that are stale (file's last git change is newer than the stamp, or cited file:function() symbols no longer resolve in the atlas). Use this before relying on a status report for planning.",
     {}),
    ("batch_file_api", batch_file_api_tool, CAT_CODE_RAG,
     "Query the codebase atlas for the public API surface of multiple files in one call. Each file returns class names + method signatures, module-level function signatures, and exported symbols — without any method bodies. Use this instead of calling file_api sequentially for each file.",
     PATHS_PARAM),
    ("minimal_context_dump", minimal_context_dump, CAT_CODE_RAG,
     "Generate a compact context file for an external LLM by chaining existing atlas tools. Given a problem description and symbols, it resolves the blast radius, fetches only relevant symbol source (not whole files), includes API signatures for peripheral files, and writes one capped file. Prefer this over full-file dumps like copyContent.py.",
     {"problem_description": str_p("The problem or question that needs external LLM context", req=True),
      "symbol_names": arr_p("string", "Starting function/class names to investigate (blast radius is auto-resolved)", req=True),
      "file_paths": arr_p("string", "Optional peripheral file paths for API-surface-only inclusion"),
      "output_path": str_p("Optional output path (default: project_root/context_dump.txt)"),
      "max_tokens": int_p("Optional token budget cap (default: 8000)")}),
    ("extract_symbols_to_file", extract_symbols_to_file_tool, CAT_CODE_RAG,
     "Extract full source code of named symbols from the atlas into a single file. Fetches bodies only for the given symbols (not entire files), writes them to destination with headers. Use this instead of manually copying symbol source into a new file during refactoring.",
     {"names": arr_p("string", "Exact symbol names to extract", req=True),
      "destination": str_p("Output file path (relative to project root)", req=True),
      "file_path": str_p("Optional file path to disambiguate symbols")}),
    ("report_inventory", report_inventory_tool, CAT_CODE_RAG,
     "Scan all system_devpt_reports/ files and return per-file: path, role (status/roadmap/readme), line count, has _Last verified, citation count, empty flag. One call replaces multi-file find + head + partial reads.",
     {}),
    ("report_schema_check", report_schema_check_tool, CAT_CODE_RAG,
     "Check each status.md for schema compliance: missing sections, bullets without file:symbol() citations, roadmap language in status.",
     {}),
    ("list_capabilities", list_capabilities_tool, CAT_CODE_RAG,
     "Live dump of capability_claim/known_gap hypotheses from HypothesisEngine. Returns id, type, status, title, evidence_path, evidence_symbol. Optionally filter by type.",
     {"type": str_p("Optional filter: 'capability_claim' or 'known_gap'")}),
    ("resolve_citations", resolve_citations_tool, CAT_CODE_RAG,
     "Resolve a list of path:symbol() citations against the atlas database. Returns resolved/missing status for each. Wraps the same logic as validate_capabilities.py as an MCP tool.",
     {"citations": arr_p("string", "List of citations like ['file.py:func()', 'path/to/module.py:ClassName()']", req=True)}),
]

_OBSERVER_SPECS = [
    ("tool_stats", tool_stats, CAT_OBSERVER,
     "Show tool call statistics — counts, avg duration, error rate per tool. Most called first.",
     {}),
    ("file_stats", file_stats, CAT_OBSERVER,
     "Show most accessed files by read/write/edit operations. Most accessed first.",
     {"limit": int_p("Max files to return (default 20)")}),
    ("user_reading_budget", user_reading_budget, CAT_OBSERVER,
     "Track user reading budget. Call with record_lines=N to record N lines of LLM output. Returns current usage/budget/remaining. Alerts when <20% budget left.",
     {"record_lines": int_p("Number of LLM response lines to record for today's budget")}),
    ("hot_reload", lambda _: "Tools reloaded.", CAT_OBSERVER,
     "Hot-reload all tool modules and notify the client to refresh its tool list. No restart needed.",
     {}, False),
]


def _register_kernel_tools():
    from agent_core.tools.kernel_ops import kernel_reload
    from kernel.signals.belief_signal_handler import register_handlers
    register_handlers()
    _register([
        ("kernel_retrieve", kernel_retrieve, CAT_KERNEL,
         "Query kernel memory for relevant context from past sessions",
         {"query": str_p("Search query for retrieving relevant memories", req=True),
          "limit": int_p("Maximum number of results to return (default 10)")}),
        ("kernel_emit_signal", kernel_emit_signal, CAT_KERNEL,
         "Emit an observation/signal to the kernel for pattern detection and belief tracking",
         {"signal_type": str_p("Type of signal (e.g. observation, finding)"),
          "value": str_p("The signal value/content", req=True),
          "title": str_p("Optional title for the signal"),
          "description": str_p("Optional longer description"),
          "category": str_p("Optional category (default: general)"),
          "confidence": float_p("Confidence score 0-1 (default 1.0)"),
          "importance": float_p("Importance score 0-1 (default 0.5)"),
          "tags": arr_p("string", "Optional tags")}),
        ("kernel_store_context", kernel_store_context, CAT_KERNEL,
         "Store important context in kernel memory for future retrieval across sessions",
         {"memory_type": str_p("Type of memory (default: context)"),
          "content": str_p("The content/memory to store", req=True),
          "importance": float_p("Importance score 0-1 (default 0.5)"),
          "confidence": float_p("Confidence score 0-1 (default 1.0)"),
          "tags": arr_p("string", "Optional tags"),
          "ttl_seconds": int_p("Time-to-live in seconds (default 3600)")}),
        ("kernel_get_memory", kernel_get_memory, CAT_KERNEL,
         "Retrieve a specific memory by its ID from kernel storage",
         {"memory_id": str_p("The ID of the memory to retrieve", req=True)}),
        ("kernel_create_event", kernel_create_event, CAT_KERNEL,
         "Create an event in the kernel timeline for tracking significant actions",
         {"event_type": str_p("Type of event (default: action)"),
          "title": str_p("Event title (required)", req=True),
          "description": str_p("Optional event description"),
          "category": str_p("Optional category (default: general)"),
          "confidence": float_p("Confidence 0-1 (default 1.0)"),
          "importance": float_p("Importance 0-1 (default 0.5)"),
          "tags": arr_p("string", "Optional tags")}),
        ("kernel_reload", kernel_reload, CAT_KERNEL,
         "Reload tool modules from disk to pick up code changes without restart",
         {"modules": arr_p("string", "Optional list of module names to reload (default: all hot modules)")}),
    ])


def _register_debate_tools():
    try:
        from agent_core.tools.debate_ops import debate_step
        from agent_core.tools.expand_ops import expand_topic
    except ImportError as e:
        log_output(f"[tools] debate/expand_ops unavailable, skipping: {e}")
        return
    _register([
        ("debate_step", debate_step, CAT_DEBATE,
         "Present next debate argument for a topic and get user response. Handles argument selection, belief tracking, contradiction detection. When graph is exhausted, pass llm_generated to add a new argument.",
         {"topic": str_p("Topic name to explore (e.g. 'theism_atheism')", req=True),
          "llm_generated": {"t": "object", "desc": "New argument when graph is exhausted",
                            "properties": {"name": {"type": "string", "description": "Unique argument name"},
                                            "premise": {"type": "string", "description": "The argument premise"},
                                            "side": {"type": "string", "description": "One of: pro, con, neutral"}},
                            "additionalProperties": False}}, False),
        ("expand_topic", expand_topic, CAT_DEBATE,
         "Add new nodes and edges to a topic's argument graph. Validates no duplicate names, persists to graph.json, and re-indexes the vector store.",
         {"topic": str_p("Topic name to expand (e.g. 'theism_atheism')", req=True),
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
                            "additionalProperties": False}}}, False),
    ])


def _register_sim_tools():
    from agent_core.tools.sim_ops import (
        simulation_run, simulation_compare,
        simulation_list, simulation_get_signals,
    )
    _register([
        ("simulation_run", simulation_run, CAT_SIM,
         "Run a simulation with specified parameters and get results",
         {"run_id": str_p("Unique identifier for this simulation run", req=True),
          "params": obj_p("Simulation parameters (e.g. years, initial_pop, grid_width)", additionalProperties=True),
          "timeout": int_p("Max run time in seconds (omit for no limit)")}),
        ("simulation_compare", simulation_compare, CAT_SIM,
         "Compare results from multiple simulation runs",
         {"run_ids": arr_p("string", "List of run IDs to compare", req=True)}),
        ("simulation_list", simulation_list, CAT_SIM,
         "List all previous simulation runs",
         {}),
        ("simulation_get_signals", simulation_get_signals, CAT_SIM,
         "Get signals emitted during a simulation run",
         {"run_id": str_p("The run ID to retrieve signals from", req=True)}),
    ])


def _register_all():
    _register(_FILE_SPECS)
    _register(_AST_SPECS)
    _register(_META_SPECS)
    _register(_GIT_SPECS)
    _register_kernel_tools()
    _register(_CODE_RAG_SPECS)
    _register(_OBSERVER_SPECS)
    registry.register_lazy(CAT_DEBATE, _register_debate_tools)
    registry.register_lazy(CAT_SIM, _register_sim_tools)


_register_all()

# Hot-reload recovery: consumers (mcp_server, executor, engine, ...) captured the
# registry instance at import time. A reload that re-created the registry leaves them
# pointing at an orphaned instance, so rebind any module that holds a different one.
for _mod in list(sys.modules.values()):
    if _mod is None or _mod is sys.modules.get(__name__):
        continue
    _ref = getattr(_mod, "registry", None)
    if _ref is not None and _ref is not registry and hasattr(_ref, "register") and hasattr(_ref, "get_tools"):
        _mod.registry = registry


def __getattr__(name: str):
    """Lazy backward-compat aliases: materialize only when TOOLS/TOOL_META are accessed."""
    if name == "TOOLS":
        return registry.tools_dict
    if name == "TOOL_META":
        return registry.meta_dict
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
