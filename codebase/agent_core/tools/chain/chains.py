"""Data-only definitions of the initial hand-written tool chains."""

from __future__ import annotations

from agent_core.tools.chain.chain_spec import ChainSpec, Step
from agent_core.tools.registry import CAT_CODE_RAG, CAT_META, arr_p, str_p

_EDIT_ITEMS = {
    "type": "object",
    "properties": {
        "path": {"type": "string", "description": "File path relative to workspace root"},
        "old_string": {"type": "string", "description": "Exact existing text to replace"},
        "new_string": {"type": "string", "description": "Replacement text"},
        "replace_all": {"type": "boolean", "description": "If true, replace all occurrences"},
    },
    "additionalProperties": False,
}


CHAIN_SPECS = [
    ChainSpec(
        name="probe_module",
        category=CAT_META,
        description=(
            "Understand a module before editing, in one call: structure (file_skeleton) + "
            "import graph (who_imports) + optional symbol impact (find_impact when 'name' is "
            "given). Replaces 2-3 serial tool calls."
        ),
        params={
            "path": str_p("File path relative to workspace root", req=True),
            "name": str_p("Optional symbol name to also run find_impact on"),
        },
        steps=[
            Step(tool="file_skeleton", args={"paths": "$input.path"}),
            Step(tool="who_imports", args={"paths": "$input.path"}),
            Step(tool="find_impact", args={"name": "$input.name"}, optional=True),
        ],
        budget_tokens=16000,
    ),
    ChainSpec(
        name="orient_symbols",
        category=CAT_CODE_RAG,
        description=(
            "One-call context gather over the codebase atlas, hardcoding the CALIBRATE -> ORIENT "
            "-> META -> FETCH workflow: get_index_info, file_api(paths), get_symbols_meta(names), "
            "get_symbol(names). Use to orient on files + fetch exact symbols in one round trip."
        ),
        params={
            "paths": arr_p("string", "File paths to orient with file_api (any files, not just kernel)"),
            "names": arr_p("string", "Symbol names to fetch metadata then full source for"),
        },
        steps=[
            Step(tool="get_index_info", args={}),
            Step(tool="file_api", args={"paths": "$input.paths"}, optional=True),
            Step(tool="get_symbols_meta", args={"names": "$input.names"}, optional=True),
            Step(tool="get_symbol", args={"names": "$input.names"}, optional=True),
        ],
        budget_tokens=24000,
        step_cap_chars=12000,
    ),
    ChainSpec(
        name="doc_audit",
        category=CAT_META,
        description=(
            "Audit all system_devpt_reports in one call: freshness (stale stamps + broken "
            "citations), schema compliance, and inventory."
        ),
        params={},
        steps=[
            Step(tool="report_freshness", args={}),
            Step(tool="report_schema_check", args={}),
            Step(tool="report_inventory", args={}),
        ],
        budget_tokens=8000,
    ),
    ChainSpec(
        name="safe_edit",
        category=CAT_META,
        description=(
            "Validate then apply a batch of edits to ONE file and show the resulting diff: "
            "check_before_edit (read-only dry-run) -> edit_file(edits) -> file_diff(path). Use "
            "for multi-edit changes to a single file to avoid batch-failure recovery cycles."
        ),
        params={
            "path": str_p("File path relative to workspace root", req=True),
            "edits": {"t": "array", "desc": "Edits to apply to the file", "r": True, "items": _EDIT_ITEMS},
        },
        steps=[
            Step(tool="check_before_edit", args={"edits": "$input.edits"}),
            Step(tool="edit_file", args={"path": "$input.path", "edits": "$input.edits"}),
            Step(tool="file_diff", args={"path": "$input.path"}),
        ],
        budget_tokens=4000,
    ),
]
