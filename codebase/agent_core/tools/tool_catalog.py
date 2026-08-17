"""Per-turn tool catalog builder + shared tool-search scoring.

build_catalog() is the single chokepoint for which tool schemas go into the
model's ``tools=`` payload each turn. With tool_search enabled it sends a small
always-on base set plus a lexically-ranked top-k of enabled tools; the
find_tool/get_tool_schema tools (tool_search.py) let the model fetch more on
demand. Execution is decoupled from schemas (dispatch_step runs against the
full registry), so any discovered tool can be called by name without
re-injecting its schema.
"""

from __future__ import annotations

import difflib
import re
from typing import Optional, Set

from agent_core.config import (
    TOOL_GROUP_ROUTING,
    TOOL_SEARCH_BASE_TOOLS,
    TOOL_SEARCH_ENABLED,
    TOOL_SEARCH_FALLBACK,
    TOOL_SEARCH_TOP_K,
    resolve_active_tool_packs,
)
from agent_core.tools import registry
from agent_core.tools.tool_groups import select_tools_for_request

# Always-available discovery tools (CAT_META). Force-included in the loop
# catalog by name, independent of pack filtering, so the model can always find
# and call any enabled tool even when its schema was not sent this turn.
SEARCH_TOOL_NAMES = ("find_tool", "get_tool_schema")

_WORD_RE = re.compile(r"[a-z0-9_]+")


def _tokens(text: str) -> Set[str]:
    return set(_WORD_RE.findall((text or "").lower()))


def enabled_tool_names(active_names: Optional[set] = None) -> Set[str]:
    """Tools visible right now: category in active packs AND mode-allowed."""
    cats = resolve_active_tool_packs()
    if cats:
        names = set(registry.get_tools(categories=cats))
    else:
        names = set(registry.tool_names)
    if active_names:
        names &= set(active_names)
    return names


def _schema_props(name: str) -> tuple[dict, list]:
    for s in registry.schemas_list:
        if s.get("name") == name:
            params = s.get("parameters") or {}
            return params.get("properties") or {}, params.get("required") or []
    return {}, []


_search_cache: dict = {"sig": None, "records": []}


def _records() -> list[dict]:
    """Lazy search index over the full registry, invalidated on tool changes."""
    names = sorted(registry.tool_names)
    sig = tuple(names)
    if _search_cache["sig"] == sig and _search_cache["records"]:
        return _search_cache["records"]
    recs = []
    for name in names:
        meta = registry.meta_dict.get(name) or {}
        props, req = _schema_props(name)
        params = [
            {"name": k, "type": v.get("type") or "?", "required": k in req}
            for k, v in props.items()
        ]
        recs.append({
            "name": name,
            "category": registry.get_category(name),
            "description": str(meta.get("description", "") or ""),
            "input_format": str(meta.get("input_format", "") or ""),
            "params": params,
        })
    _search_cache.update(sig=sig, records=recs)
    return recs


def _score(query_tokens: Set[str], rec: dict) -> float:
    name = rec["name"].lower()
    q = " ".join(sorted(query_tokens))
    score = 0.0
    if query_tokens & set(name.split("_")):
        score += 4.0
    if q and q in name:
        score += 6.0
    ratio = difflib.SequenceMatcher(None, q, name).ratio()
    if ratio > 0.55:
        score += 3.0 * ratio
    if query_tokens & set(rec["category"].lower().split("_")):
        score += 2.0
    if query_tokens:
        hay = _tokens(rec["description"]) | _tokens(rec["input_format"])
        for p in rec["params"]:
            hay |= _tokens(p["name"])
        overlap = len(query_tokens & hay)
        if overlap:
            score += 0.5 * overlap
    return score


def rank_tools(query: str, candidates: Set[str]) -> list[str]:
    """Score candidate tools against a query, highest first (score > 0 only)."""
    qt = _tokens(query)
    scored = []
    for r in _records():
        n = r["name"]
        if n not in candidates:
            continue
        s = _score(qt, r)
        if s > 0:
            scored.append((n, s))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [n for n, _s in scored]


def _name_of(schema: dict) -> str:
    fn = schema.get("function")
    if isinstance(fn, dict):
        return fn.get("name", "")
    return schema.get("name", "")


def _filter_names(schemas: list, provider: Optional[str], names: set) -> list:
    out = []
    for s in schemas:
        if provider == "gemini":
            kept = [d for d in (s.get("function_declarations") or []) if _name_of(d) in names]
            if kept:
                out.append({"function_declarations": kept})
        elif _name_of(s) in names:
            out.append(s)
    return out


def build_catalog(
    provider: Optional[str],
    user_input: str,
    tool_categories: Optional[list] = None,
    active_names: Optional[set] = None,
) -> list:
    """Return the provider-formatted schema list for this turn's tools payload."""
    active_names = set(active_names) if active_names else None

    if not TOOL_SEARCH_ENABLED:
        schemas = registry.get_schemas(
            provider_name=provider, categories=tool_categories,
            names=active_names or None,
        )
        if schemas and TOOL_GROUP_ROUTING:
            filtered = _filter_names(schemas, provider, select_tools_for_request(user_input))
            if filtered:
                schemas = filtered
        return schemas

    enabled = enabled_tool_names(active_names)
    base = (set(TOOL_SEARCH_BASE_TOOLS) & enabled) | set(SEARCH_TOOL_NAMES)
    selected = set(base)
    picked = rank_tools(user_input, enabled - base)
    if picked:
        selected |= set(picked[:TOOL_SEARCH_TOP_K])
    elif TOOL_SEARCH_FALLBACK == "full":
        selected |= enabled
    return registry.get_schemas(provider_name=provider, names=selected)