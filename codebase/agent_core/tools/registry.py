"""ToolRegistry: central registry for pluggable tool functions with category filtering,
schema export, and middleware support."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional


class ToolRegistry:
    """Central registry for tool functions, schemas, and metadata.

    Supports:
    - Category-based filtering (file, kernel, sim, meta, git)
    - Middleware wrapping (audit, rate-limit, redaction)
    - Multi-format schema export (provider-native, MCP)

    Usage:
        registry = ToolRegistry()
        registry.register("read_file", fn, schema={...}, meta={...}, category="file")
        tools = registry.get_tools(categories=["kernel", "sim"])
        schemas = registry.get_schemas(provider_name="gemini")
        mcp_tools = registry.to_mcp_tools()
    """

    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._schemas: Dict[str, dict] = {}
        self._meta: Dict[str, Dict[str, str]] = {}
        self._categories: Dict[str, str] = {}
        self._risk_levels: Dict[str, str] = {}
        self._middleware: List[Callable] = []

    def register(
        self,
        name: str,
        fn: Callable,
        *,
        schema: Optional[dict] = None,
        meta: Optional[Dict[str, str]] = None,
        category: str = "file",
        risk_level: str = "low",
    ):
        self._tools[name] = fn
        if schema:
            self._schemas[name] = schema
        if meta:
            self._meta[name] = meta
        self._categories[name] = category
        self._risk_levels[name] = risk_level

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
        """Add middleware that wraps each tool.
        middleware_fn receives (name, fn) and returns wrapped fn."""
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
