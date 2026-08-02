"""ToolRegistry: central registry for pluggable tool functions with category filtering,
schema export, and middleware support."""

from __future__ import annotations

import inspect
from typing import Any, Callable, Dict, List, Optional


_TYPE_HINT_MAP = {str: "string", int: "integer", float: "number", bool: "boolean"}


def _infer_type(annotation: Any) -> str:
    if annotation is inspect.Parameter.empty:
        return "string"
    origin = getattr(annotation, "__origin__", None)
    if origin is list:
        return "array"
    if origin is dict:
        return "object"
    return _TYPE_HINT_MAP.get(annotation, "string")


def derive_schema(fn: Callable, desc_overrides: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Derive schema params dict from function signature + type hints.
    
    Only includes parameters with simple types (str, int, float, bool, list).
    Descriptions come from desc_overrides or empty string.
    Required status is derived from whether param has a default.
    """
    sig = inspect.signature(fn)
    params = {}
    for name, param in sig.parameters.items():
        if name in ("self", "cls", "kwargs", "args"):
            continue
        if param.kind in (inspect.Parameter.VAR_KEYWORD, inspect.Parameter.VAR_POSITIONAL):
            continue
        ptype = _infer_type(param.annotation)
        desc = (desc_overrides or {}).get(name, "")
        req = param.default is inspect.Parameter.empty
        spec = {"t": ptype, "desc": desc, "r": req}
        if ptype == "array":
            spec["items"] = {"t": "string"}
        params[name] = spec
    return params


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
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._schemas: Dict[str, dict] = {}
        self._meta: Dict[str, Dict[str, str]] = {}
        self._categories: Dict[str, str] = {}
        self._risk_levels: Dict[str, str] = {}
        self._default_category: str | None = None
        self._middleware: List[Callable] = []
        self._lazy_loaders: Dict[str, Callable[[], None]] = {}

    def set_default_category(self, category: str):
        self._default_category = category

    def simple(self, name, fn, description, **kw):
        """Compact registration: pass param specs as keyword args.
        
        Usage:
            reg.simple("name", fn, "description",
                path=("string", "The path", True),   # (type, desc, required)
                limit=("integer", "Max lines"),       # (type, desc)
                flag=bool_p("Some flag"),             # or use existing helpers
            )
        """
        params = {}
        for k, v in kw.items():
            if isinstance(v, tuple):
                t, desc = v[0], v[1]
                req = v[2] if len(v) > 2 else False
                params[k] = {"t": t, "desc": desc, "r": req}
                if t == "array":
                    params[k]["items"] = {"t": "string"}
            elif isinstance(v, dict):
                params[k] = v
        self.register(name, fn, description=description, params=params)

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

    def register_lazy(self, category: str, loader: Callable[[], None]):
        """Register a loader that registers a category's tools on first access."""
        self._lazy_loaders[category] = loader

    def unregister(self, name: str) -> bool:
        """Remove a tool (used when a mined chain is superseded by a longer one)."""
        if name not in self._tools:
            return False
        self._tools.pop(name, None)
        self._schemas.pop(name, None)
        self._meta.pop(name, None)
        self._categories.pop(name, None)
        self._risk_levels.pop(name, None)
        return True

    def _materialize(self, categories: Optional[List[str]] = None):
        """Run pending lazy loaders. With categories=None, materialize everything."""
        if not self._lazy_loaders:
            return
        if categories is None:
            pending = list(self._lazy_loaders.keys())
        else:
            pending = [c for c in categories if c in self._lazy_loaders]
        for cat in pending:
            loader = self._lazy_loaders.pop(cat)
            try:
                loader()
            except Exception:
                self._lazy_loaders[cat] = loader
                raise

    @property
    def tools_dict(self) -> Dict[str, Callable]:
        self._materialize()
        result = dict(self._tools)
        for mw in self._middleware:
            result = {n: mw(n, fn) for n, fn in result.items()}
        return result

    @property
    def schemas_list(self) -> List[dict]:
        self._materialize()
        return list(self._schemas.values())

    @property
    def meta_dict(self) -> Dict[str, Dict[str, str]]:
        self._materialize()
        return dict(self._meta)

    def get_tools(self, categories: Optional[List[str]] = None, names: Optional[set] = None) -> Dict[str, Callable]:
        self._materialize(categories)
        if categories is None:
            result = self.tools_dict
        else:
            result = {
                n: fn for n, fn in self._tools.items()
                if self._categories.get(n) in categories
            }
            for mw in self._middleware:
                result = {n: mw(n, fn) for n, fn in result.items()}
        if names:
            result = {n: fn for n, fn in result.items() if n in names}
        return result

    def get_schemas(self, provider_name: Optional[str] = None, categories: Optional[List[str]] = None, names: Optional[set] = None) -> List[dict]:
        self._materialize(categories)
        schemas = self.schemas_list
        if categories is not None:
            schemas = [s for s in schemas if self._categories.get(s["name"]) in categories]
        if names:
            schemas = [s for s in schemas if s["name"] in names]
        if provider_name == "gemini":
            return [{"function_declarations": schemas}]
        return [{"type": "function", "function": s} for s in schemas]

    def to_mcp_tools(self, categories: Optional[List[str]] = None) -> List[dict]:
        self._materialize(categories)
        names = (
            list(self._tools.keys())
            if categories is None
            else [n for n in self._tools if self._categories.get(n) in categories]
        )
        return [
            {
                "name": name,
                "description": self._schemas.get(name, {}).get("description", ""),
                "inputSchema": self._schemas.get(name, {}).get(
                    "parameters", {"type": "object", "properties": {}}
                ),
            }
            for name in names
        ]

    def add_middleware(self, middleware_fn: Callable):
        self._middleware.append(middleware_fn)

    def get_category(self, name: str) -> str:
        self._materialize()
        return self._categories.get(name, "file")

    def has_tool(self, name: str) -> bool:
        self._materialize()
        return name in self._tools

    @property
    def tool_names(self) -> List[str]:
        self._materialize()
        return list(self._tools.keys())

    @property
    def tool_count(self) -> int:
        self._materialize()
        return len(self._tools)


CAT_FILE = "file"
CAT_KERNEL = "kernel"
CAT_SIM = "sim"
CAT_META = "meta"
CAT_GIT = "git"
CAT_CODE_RAG = "code_rag"
CAT_OBSERVER = "observer"
CAT_DEBATE = "debate"
CAT_CHAIN = "chain"
