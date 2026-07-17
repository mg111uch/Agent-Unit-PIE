from __future__ import annotations

from typing import Any, Dict, List


def _str_schema(description: str) -> dict:
    return {"type": "string", "description": description}


def _obj_schema(properties: dict, required: list[str] | None = None) -> dict:
    schema: dict[str, Any] = {
        "type": "object",
        "properties": properties,
        "additionalProperties": False,
    }
    if required:
        schema["required"] = required
    return schema


_TEST_OPS_SCHEMA = {
    "name": "run_tests",
    "description": "Discover and run tests in the workspace using pytest or unittest. Specify path to limit scope, pattern for file filter, or framework to override auto-detection.",
    "parameters": _obj_schema(
        properties={
            "pattern": _str_schema("Optional glob pattern to filter test files (e.g. 'test_*.py')"),
            "path": _str_schema("Optional directory path to search for tests (default: workspace root)"),
            "framework": _str_schema("Test framework: 'pytest' (default) or 'unittest'"),
            "timeout": {"type": "integer", "description": "Timeout in seconds (default 60)"},
        },
    ),
}


TOOL_SCHEMAS: List[Dict[str, Any]] = [
    {
        "name": "read_file",
        "description": "Read a file from the workspace (returns line-numbered output; lists nearby files on error)",
        "parameters": _obj_schema(
            properties={
                "path": _str_schema("Path to the file, relative to the workspace root"),
            },
            required=["path"],
        ),
    },
    {
        "name": "read_file_range",
        "description": "Read a portion of a file with 1-based offset and optional line limit",
        "parameters": _obj_schema(
            properties={
                "path": _str_schema("File path relative to workspace root"),
                "offset": {"type": "integer", "description": "1-based line number to start from (default 1)"},
                "limit": {"type": "integer", "description": "Max lines to return (default: entire file)"},
            },
            required=["path"],
        ),
    },
    {
        "name": "list_files",
        "description": "List directory contents (recursive, depth-capped, skips .git/node_modules/__pycache__)",
        "parameters": _obj_schema(
            properties={
                "path": _str_schema("Directory path relative to workspace root; use '.' for root"),
            },
        ),
    },
    {
        "name": "write_to_file",
        "description": "Create or overwrite a file. Use edit_file for targeted edits to existing files.",
        "parameters": _obj_schema(
            properties={
                "path": _str_schema("File path relative to workspace root"),
                "mode": _str_schema("One of: create (fails if exists), overwrite (replaces), append (adds to end)"),
                "content": _str_schema("File content to write"),
                "dry_run": {"type": "boolean", "description": "If true, validate without writing"},
            },
            required=["path", "mode"],
        ),
    },
    {
        "name": "edit_file",
        "description": "Replace exact old_string with new_string in an existing file. old_string must match exactly once.",
        "parameters": _obj_schema(
            properties={
                "path": _str_schema("File path relative to workspace root"),
                "old_string": _str_schema("Exact existing text to replace (whitespace-sensitive)"),
                "new_string": _str_schema("Replacement text"),
            },
            required=["path", "old_string", "new_string"],
        ),
    },
    {
        "name": "get_workspace_info",
        "description": "Show the workspace root path and top-level directory entries for orientation",
        "parameters": _obj_schema(
            properties={},
        ),
    },
    {
        "name": "execute_command",
        "description": "Run a shell command. Allowed: ls, cat, pwd, echo, python.",
        "parameters": _obj_schema(
            properties={
                "command": _str_schema("Shell command string to execute"),
            },
            required=["command"],
        ),
    },
    {
        "name": "glob_search",
        "description": "Find files matching a glob pattern (e.g. '**/*.py', 'src/**/*.ts')",
        "parameters": _obj_schema(
            properties={
                "pattern": _str_schema("Glob pattern to match files against, relative to workspace root"),
            },
            required=["pattern"],
        ),
    },
    {
        "name": "grep_search",
        "description": "Search file contents by regex across the workspace",
        "parameters": _obj_schema(
            properties={
                "pattern": _str_schema("Regex pattern to search for in file contents"),
                "include": _str_schema("Optional file glob filter (e.g. '*.py' or '*.{py,ts}')"),
                "max_results": {"type": "integer", "description": "Max results to return (default 50)"},
            },
            required=["pattern"],
        ),
    },
    {
        "name": "todo_write",
        "description": "Create/update a task plan. Actions: create (new plan), update (append), mark_done, clear",
        "parameters": _obj_schema(
            properties={
                "action": _str_schema("One of: create, update, mark_done, clear"),
                "items": {"type": "array", "items": {"type": "string"}, "description": "List of task descriptions (for create/update)"},
                "ids": {"type": "array", "items": {"type": "integer"}, "description": "Task IDs to mark done (for mark_done)"},
            },
            required=["action"],
        ),
    },
    {
        "name": "todo_read",
        "description": "Read the current task plan",
        "parameters": _obj_schema(properties={}),
    },
    {
        "name": "kernel_retrieve",
        "description": "Query kernel memory for relevant context from past sessions",
        "parameters": _obj_schema(
            properties={
                "query": _str_schema("Search query for retrieving relevant memories"),
                "limit": {"type": "integer", "description": "Maximum number of results to return (default 10)"},
            },
            required=["query"],
        ),
    },
    {
        "name": "kernel_emit_signal",
        "description": "Emit an observation/signal to the kernel for pattern detection and belief tracking",
        "parameters": _obj_schema(
            properties={
                "signal_type": _str_schema("Type of signal (e.g. observation, finding)"),
                "value": _str_schema("The signal value/content"),
                "title": _str_schema("Optional title for the signal"),
                "description": _str_schema("Optional longer description"),
                "category": _str_schema("Optional category (default: general)"),
                "confidence": {"type": "number", "description": "Confidence score 0-1 (default 1.0)"},
                "importance": {"type": "number", "description": "Importance score 0-1 (default 0.5)"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Optional tags"},
            },
            required=["value"],
        ),
    },
    {
        "name": "kernel_store_context",
        "description": "Store important context in kernel memory for future retrieval across sessions",
        "parameters": _obj_schema(
            properties={
                "memory_type": _str_schema("Type of memory (default: context)"),
                "content": _str_schema("The content/memory to store"),
                "importance": {"type": "number", "description": "Importance score 0-1 (default 0.5)"},
                "confidence": {"type": "number", "description": "Confidence score 0-1 (default 1.0)"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Optional tags"},
                "ttl_seconds": {"type": "integer", "description": "Time-to-live in seconds (default 3600)"},
            },
            required=["content"],
        ),
    },
    {
        "name": "kernel_get_memory",
        "description": "Retrieve a specific memory by its ID from kernel storage",
        "parameters": _obj_schema(
            properties={
                "memory_id": _str_schema("The ID of the memory to retrieve"),
            },
            required=["memory_id"],
        ),
    },
    {
        "name": "kernel_create_event",
        "description": "Create an event in the kernel timeline for tracking significant actions",
        "parameters": _obj_schema(
            properties={
                "event_type": _str_schema("Type of event (default: action)"),
                "title": _str_schema("Event title (required)"),
                "description": _str_schema("Optional event description"),
                "category": _str_schema("Optional category (default: general)"),
                "confidence": {"type": "number", "description": "Confidence 0-1 (default 1.0)"},
                "importance": {"type": "number", "description": "Importance 0-1 (default 0.5)"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Optional tags"},
            },
            required=["title"],
        ),
    },
    {
        "name": "simulation_run",
        "description": "Run a simulation with specified parameters and get results",
        "parameters": _obj_schema(
            properties={
                "run_id": _str_schema("Unique identifier for this simulation run"),
                "params": {
                    "type": "object",
                    "description": "Simulation parameters (e.g. years, initial_pop, grid_width)",
                    "additionalProperties": True,
                },
            },
            required=["run_id"],
        ),
    },
    {
        "name": "simulation_compare",
        "description": "Compare results from multiple simulation runs",
        "parameters": _obj_schema(
            properties={
                "run_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of run IDs to compare",
                },
            },
            required=["run_ids"],
        ),
    },
    {
        "name": "simulation_list",
        "description": "List all previous simulation runs",
        "parameters": _obj_schema(properties={}),
    },
    {
        "name": "simulation_get_signals",
        "description": "Get signals emitted during a simulation run",
        "parameters": _obj_schema(
            properties={
                "run_id": _str_schema("The run ID to retrieve signals from"),
            },
            required=["run_id"],
        ),
    },
    {
        "name": "ask_user_question",
        "description": "Ask the user for input, clarification, or a decision. Provide up to 3 options per question (a 4th 'custom answer' text input is always available). Can ask multiple questions at once — user answers them one by one.",
        "parameters": _obj_schema(
            properties={
                "questions": {
                    "type": "array",
                    "description": "Questions to ask. User answers them sequentially. Max 3 options each (custom text input is always added as the last option).",
                    "items": _obj_schema(
                        properties={
                            "question": _str_schema("The question text to display to the user"),
                            "options": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Up to 3 predefined answer choices. A custom text option is always appended.",
                                "maxItems": 3,
                            },
                        },
                        required=["question"],
                    ),
                    "minItems": 1,
                },
            },
            required=["questions"],
        ),
    },
    _TEST_OPS_SCHEMA,
    {
        "name": "git_status",
        "description": "Show git status of the workspace — modified, staged, untracked files",
        "parameters": _obj_schema(properties={}),
    },
    {
        "name": "git_diff",
        "description": "Show git diff of uncommitted changes. Optionally filter by path or show staged diff.",
        "parameters": _obj_schema(
            properties={
                "path": _str_schema("Optional file path to filter diff"),
                "staged": {"type": "boolean", "description": "If true, show staged diff (default false)"},
            },
        ),
    },
    {
        "name": "git_commit",
        "description": "Commit staged changes with a message. Set add_all=true to stage all changes first.",
        "parameters": _obj_schema(
            properties={
                "message": _str_schema("Commit message (required)"),
                "add_all": {"type": "boolean", "description": "If true, run git add -A before commit"},
            },
            required=["message"],
        ),
    },
    {
        "name": "git_log",
        "description": "Show recent commit history in oneline format",
        "parameters": _obj_schema(
            properties={
                "max_count": {"type": "integer", "description": "Max commits to show (default 10)"},
            },
        ),
    },
    {
        "name": "undo_last_edit",
        "description": "Restore the most recent checkpoint for a file, or list latest checkpoint info",
        "parameters": _obj_schema(
            properties={
                "path": _str_schema("Optional file path to undo; omit to show latest checkpoint"),
            },
        ),
    },
    {
        "name": "checkpoint_info",
        "description": "List available checkpoints for undo operations",
        "parameters": _obj_schema(properties={}),
    },
    # Code RAG tools
    {
        "name": "get_symbol",
        "description": (
            "PRIMARY lookup when the user names functions/classes. "
            "Batch: names=['func1','func2']. Returns full source, signature, docstring. "
            "Prefer this over search_symbols when exact names are known. "
            "On missing names, response includes missing_names — then search_symbols only for those."
        ),
        "parameters": _obj_schema(
            properties={
                "names": {"type": "array", "items": {"type": "string"}, "description": "Exact function/class names to look up in one batch (e.g. ['func1', 'func2'])."},
                "file_path": _str_schema("Optional file path to narrow all lookups to one file"),
            },
            required=["names"],
        ),
    },
    {
        "name": "search_symbols",
        "description": (
            "Metadata-only full-text search over symbol names/docstrings/code. "
            "Use when names are unknown or get_symbol returned missing_names (misspelling). "
            "Does NOT return full source — pick relevant names then call get_symbol. "
            "Do not use as the first step when the user already gave exact symbol names."
        ),
        "parameters": _obj_schema(
            properties={
                "query": _str_schema("Search query (supports FTS5 syntax, e.g. 'auth AND login', 'process_order')"),
                "type_filter": _str_schema("Optional filter: 'function', 'class', 'method', or 'file'"),
                "top_k": {"type": "integer", "description": "Number of results to return (default 10)"},
            },
            required=["query"],
        ),
    },
    {
        "name": "get_callers_callees",
        "description": "Show which functions call a given symbol (callers) and which functions it calls (callees). Uses recursive graph traversal up to the specified depth.",
        "parameters": _obj_schema(
            properties={
                "name": _str_schema("Function or class name to analyze"),
                "file_path": _str_schema("Optional file path to disambiguate"),
                "direction": _str_schema("Direction: 'callers', 'callees', or 'both' (default: 'both')"),
            },
            required=["name"],
        ),
    },
    {
        "name": "find_impact",
        "description": "Find all functions that would be affected by changing the given symbol. Lists everything that directly or transitively depends on it.",
        "parameters": _obj_schema(
            properties={
                "name": _str_schema("Function or class name to check impact for"),
                "file_path": _str_schema("Optional file path to disambiguate"),
            },
            required=["name"],
        ),
    },
    {
        "name": "debate_step",
        "description": "Present the next debate argument for a topic and get the user's response. Handles argument selection, user question, belief tracking, and contradiction detection in one call. Call repeatedly until done=true.",
        "parameters": _obj_schema(
            properties={
                "topic": _str_schema("Topic name to explore (e.g. 'theism_atheism')"),
            },
            required=["topic"],
        ),
    },
]

TOOL_NAME_MAP: Dict[str, dict] = {s["name"]: s for s in TOOL_SCHEMAS}


def schemas_for_provider(provider_type: str) -> List[Dict[str, Any]]:
    if provider_type == "gemini":
        return [{"function_declarations": TOOL_SCHEMAS}]
    return [
        {"type": "function", "function": s} for s in TOOL_SCHEMAS
    ]
