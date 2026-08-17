"""Model-driven tool discovery: find_tool + get_tool_schema.

Registered under CAT_META and force-included in the loop's schema payload by
name (tool_catalog.SEARCH_TOOL_NAMES), so the model can discover and call any
enabled tool even when its schema was not sent this turn — execution runs
against the full registry.
"""

from __future__ import annotations

from agent_core.tools import registry
from agent_core.tools.tool_catalog import _records, enabled_tool_names, rank_tools

_MAX_RESULTS_DEFAULT = 8


def _render_params(params: list) -> str:
    parts = [f"{p['name']}:{p['type']}({'req' if p['required'] else 'opt'})" for p in params]
    return ", ".join(parts) if parts else "(none)"


def find_tool(input_data=None) -> str:
    """Lexical search over the enabled tool catalog (respects packs/mode)."""
    if isinstance(input_data, str):
        params = {"query": input_data}
    elif isinstance(input_data, dict):
        params = input_data
    else:
        params = {}
    queries = params.get("queries") or []
    if isinstance(queries, str):
        queries = [queries]
    query = params.get("query") or ""
    try:
        max_results = int(params.get("max_results") or _MAX_RESULTS_DEFAULT)
    except (TypeError, ValueError):
        max_results = _MAX_RESULTS_DEFAULT

    enabled = enabled_tool_names()
    if not query and not queries:
        queries = [""]
    qs = [query] + [str(q) for q in queries]

    seen: set[str] = set()
    ordered: list[str] = []
    for q in qs:
        q = (q or "").strip()
        ranked = sorted(enabled) if not q else rank_tools(q, enabled - seen)
        for name in ranked:
            if name in seen:
                continue
            seen.add(name)
            ordered.append(name)
            if len(ordered) >= max_results:
                break
        if len(ordered) >= max_results:
            break

    if not ordered:
        return (
            "No tools matched. Try broader keywords or a category name "
            "(e.g. 'code_rag', 'kernel', 'git', 'sim', 'observer'). "
            f"Enabled tools: {', '.join(sorted(enabled)) or '(none)'}."
        )
    recs = {r["name"]: r for r in _records()}
    lines = [f"found {len(ordered)} tool(s):"]
    for name in ordered:
        r = recs.get(name, {})
        desc = (r.get("description") or "").split(". ")[0]
        lines.append(f"- {name} [{r.get('category', '?')}]: {desc}")
        lines.append(f"    params: {_render_params(r.get('params', []))}")
    return "\n".join(lines)


def get_tool_schema(input_data=None) -> str:
    """Full JSON schema for named tools (bypasses pack filter; checks enabled)."""
    if isinstance(input_data, str):
        params = {"name": input_data}
    elif isinstance(input_data, dict):
        params = input_data
    else:
        params = {}
    names = params.get("names") or []
    if isinstance(names, str):
        names = [names]
    name = params.get("name")
    if name:
        names = [str(name)] + [str(n) for n in names]
    if not names:
        return "Usage: get_tool_schema(name='tool_name') or names=['a', 'b']. Find names with find_tool(query=...)."

    enabled = enabled_tool_names()
    blocks = []
    for n in names:
        n = str(n)
        if not registry.has_tool(n):
            blocks.append(f"'{n}' is not a registered tool. Use find_tool to search the catalog.")
            continue
        if n not in enabled:
            blocks.append(f"'{n}' exists but is not enabled (tool_packs / tool_mode).")
            continue
        schema = next((s for s in registry.schemas_list if s.get("name") == n), None)
        if schema is None:
            blocks.append(f"'{n}' has no schema.")
            continue
        import json

        blocks.append(f"{n} [{registry.get_category(n)}]:\n{json.dumps(schema, indent=2)}")
    return "\n\n".join(blocks)