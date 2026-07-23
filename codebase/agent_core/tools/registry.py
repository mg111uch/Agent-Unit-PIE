"""ToolRegistry: central registry for pluggable tool functions with category filtering,
schema export, and middleware support."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional


def _build_params_schema(params: dict) -> dict:
    type_map = {"str": "string", "int": "integer", "float": "number", "bool": "boolean"}
    props = {}
    required = []
    for key, spec in params.items():
        raw_type = spec.get("t") or spec.get("type") or "string"
        json_type = type_map.get(raw_type, raw_type)
        desc = spec.get("desc") or spec.get("description") or ""
        prop = {"type": json_type, "description": desc}
        if json_type == "array":
            items_spec = spec.get("items")
            if items_spec:
                items = dict(items_spec)
                raw_item_t = items.pop("t", None) or items.pop("type", None)
                if raw_item_t:
                    items["type"] = type_map.get(raw_item_t, raw_item_t)
                prop["items"] = items
            for constraint_key in ("minItems", "maxItems"):
                if constraint_key in spec:
                    prop[constraint_key] = spec[constraint_key]
        if json_type == "object":
            obj_props = spec.get("properties")
            if obj_props:
                prop["properties"] = obj_props
            prop["additionalProperties"] = spec.get("additionalProperties", False)
        elif spec.get("additionalProperties"):
            prop["additionalProperties"] = spec["additionalProperties"]
        props[key] = prop
        if spec.get("r") or spec.get("required"):
            required.append(key)
    return {"type": "object", "properties": props, "required": required, "additionalProperties": False}


def _auto_input_format(params: dict) -> str:
    parts = []
    for key in params:
        parts.append(f"\"{key}\": ...")
    if not parts:
        return "omit or `{}`"
    return "`{" + ", ".join(parts) + "}`"


def str_p(desc, *, req=False):
    return {"t": "string", "desc": desc, "r": req}

def int_p(desc, *, req=False):
    return {"t": "integer", "desc": desc, "r": req}

def float_p(desc, *, req=False):
    return {"t": "number", "desc": desc, "r": req}

def bool_p(desc, *, req=False):
    return {"t": "boolean", "desc": desc, "r": req}

def arr_p(item_t, desc, *, req=False, minItems=None, maxItems=None):
    spec = {"t": "array", "desc": desc, "items": {"t": item_t}, "r": req}
    if minItems is not None:
        spec["minItems"] = minItems
    if maxItems is not None:
        spec["maxItems"] = maxItems
    return spec

def obj_p(desc, *, properties=None, additionalProperties=False, req=False):
    spec = {"t": "object", "desc": desc, "additionalProperties": additionalProperties, "r": req}
    if properties:
        spec["properties"] = properties
    return spec


class ToolRegistry:
    def __init__(self, mcp_prefix: str = ""):
        self._tools: Dict[str, Callable] = {}
        self._schemas: Dict[str, dict] = {}
        self._meta: Dict[str, Dict[str, str]] = {}
        self._categories: Dict[str, str] = {}
        self._risk_levels: Dict[str, str] = {}
        self._mcp_expose: Dict[str, bool] = {}
        self._mcp_prefix = mcp_prefix
        self._default_category: str | None = None
        self._middleware: List[Callable] = []

    def set_default_category(self, category: str):
        self._default_category = category

    def register(
        self,
        name: str,
        fn: Callable,
        *,
        description: str = "",
        params: Optional[dict] = None,
        input_format: str = "",
        schema: Optional[dict] = None,
        meta: Optional[Dict[str, str]] = None,
        category: Optional[str] = None,
        risk_level: str = "low",
        mcp_expose: bool = True,
    ):
        if category is None:
            category = self._default_category or "file"
        self._tools[name] = fn

        if schema is None and params is not None:
            schema = {
                "name": name,
                "description": description,
                "parameters": _build_params_schema(params),
            }
        if schema:
            self._schemas[name] = schema

        if meta is None:
            meta = {"description": description, "input_format": input_format or _auto_input_format(params or {})}
        if meta:
            self._meta[name] = meta

        self._categories[name] = category
        self._risk_levels[name] = risk_level
        self._mcp_expose[name] = mcp_expose

    @property
    def tools_dict(self) -> Dict[str, Callable]:
        result = dict(self._tools)
        for mw in self._middleware:
            result = {n: mw(n, fn) for n, fn in result.items()}
        return result

    @property
    def schemas_list(self) -> List[dict]:
        return list(self._schemas.values())

    @property
    def meta_dict(self) -> Dict[str, Dict[str, str]]:
        return dict(self._meta)

    def get_tools(self, categories: Optional[List[str]] = None) -> Dict[str, Callable]:
        if categories is None:
            return self.tools_dict
        result = {
            n: fn for n, fn in self._tools.items()
            if self._categories.get(n) in categories
        }
        for mw in self._middleware:
            result = {n: mw(n, fn) for n, fn in result.items()}
        return result

    def get_schemas(self, provider_name: Optional[str] = None) -> List[dict]:
        if provider_name == "gemini":
            return [{"function_declarations": self.schemas_list}]
        return [{"type": "function", "function": s} for s in self.schemas_list]

    def to_mcp_tools(self, categories: Optional[List[str]] = None) -> List[dict]:
        names = (
            list(self._tools.keys())
            if categories is None
            else [n for n in self._tools if self._categories.get(n) in categories]
        )
        prefix = self._mcp_prefix
        return [
            {
                "name": prefix + name,
                "description": self._schemas.get(name, {}).get("description", ""),
                "inputSchema": self._schemas.get(name, {}).get(
                    "parameters", {"type": "object", "properties": {}}
                ),
            }
            for name in names
            if self._mcp_expose.get(name, True)
        ]

    def add_middleware(self, middleware_fn: Callable):
        self._middleware.append(middleware_fn)

    def get_category(self, name: str) -> str:
        return self._categories.get(name, "file")

    def has_tool(self, name: str) -> bool:
        return name in self._tools

    @property
    def tool_names(self) -> List[str]:
        return list(self._tools.keys())

    @property
    def tool_count(self) -> int:
        return len(self._tools)


CAT_FILE = "file"
CAT_KERNEL = "kernel"
CAT_SIM = "sim"
CAT_META = "meta"
CAT_GIT = "git"
CAT_CODE_RAG = "code_rag"
