"""
MCP server exposing PIE kernel + simulation tools via stdio transport.

Usage:
    pie-mcp                # stdio mode (for MCP clients like Claude Code)

Integration with Claude Code:
    claude --mcp-servers '{"pie-kernel-sim": {"command": "python", "args": ["-m", "agent_core.mcp_server"]}}'
"""

from __future__ import annotations

import asyncio
import importlib
import json
import logging
import os
import sys
from typing import Any

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolResult,
    ServerCapabilities,
    TextContent,
    Tool,
    ToolsCapability,
)

from agent_core.tools import registry
from agent_core.tools.registry import CAT_FILE, CAT_KERNEL, CAT_SIM, CAT_META, CAT_GIT, CAT_CODE_RAG

# Expose kernel + sim + code_rag + file tools (file tools include Read for MCP clients)
EXPOSED_CATEGORIES = [CAT_KERNEL, CAT_SIM, CAT_CODE_RAG, CAT_FILE]

# Hot-reload support: tracks file mtime_ns and only reloads when files change
_HOT_MODULES = {
    "agent_core.tools.sim_ops":    "agent_core/tools/sim_ops.py",
    "agent_core.tools.kernel_ops": "agent_core/tools/kernel_ops.py",
    "agent_core.tools.code_rag":   "agent_core/tools/code_rag.py",
    "agent_core.tools":            "agent_core/tools/__init__.py",
}
_mtime_cache: dict[str, int] = {}


def _do_reload():
    for mod_name in _HOT_MODULES:
        if mod_name in sys.modules:
            importlib.reload(sys.modules[mod_name])
    from agent_core.tools import _register_all
    _register_all()


def _reload_if_changed():
    """Reload modules when source file mtime_ns has changed."""
    codebase = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    changed = False
    for mod_name, rel_path in _HOT_MODULES.items():
        src = os.path.join(codebase, rel_path)
        try:
            st = os.stat(src)
            mtime_ns = st.st_mtime_ns
        except OSError:
            continue
        last = _mtime_cache.get(mod_name)
        if last is None or mtime_ns > last:
            _mtime_cache[mod_name] = mtime_ns
            changed = True
    if changed:
        _do_reload()


server = Server("pie-kernel-sim")


def _check_kernel_read(name: str, arguments: dict[str, Any] | None) -> str | None:
    """Return warning message if this is a Read call on a kernel file, else None."""
    if name not in ("read_file", "read_file_range"):
        return None
    if os.environ.get("OVERRIDE_KERNEL_READ") == "1":
        return None
    path = (arguments or {}).get("path", "")
    if not path:
        return None
    try:
        from agent_core.workspace import resolve, WORKSPACE_ROOT
        resolved = resolve(path)
        kernel_dir = os.path.join(WORKSPACE_ROOT, "kernel")
        if not resolved.startswith(kernel_dir):
            return None
        logging.warning(f"Read tool called on kernel file: {path} -> {resolved}")
        return (
            "WARNING: Use pie_file_api or pie_get_symbol instead of Read "
            "for indexed kernel files. See AGENTS.md for the Kernel Probing Rules.\n"
        )
    except Exception:
        return None


def _build_tool_list() -> list[Tool]:
    mcp_tools = registry.to_mcp_tools(categories=EXPOSED_CATEGORIES)
    return [Tool(**t) for t in mcp_tools]


@server.list_tools()
async def list_mcp_tools() -> list[Tool]:
    _reload_if_changed()
    return _build_tool_list()


@server.call_tool()
async def call_mcp_tool(name: str, arguments: dict[str, Any] | None) -> CallToolResult:
    _reload_if_changed()

    kernel_read_warning = _check_kernel_read(name, arguments)

    tools = registry.get_tools(categories=EXPOSED_CATEGORIES)
    if name not in tools:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Unknown tool: {name}")],
            isError=True,
        )

    try:
        fn = tools[name]
        result = fn(arguments or {})

        from agent_core.tools import ToolResult as TR
        if isinstance(result, TR):
            if result.ok:
                text = result.data
                if kernel_read_warning:
                    text = kernel_read_warning + text
                return CallToolResult(
                    content=[TextContent(type="text", text=text)]
                )
            else:
                return CallToolResult(
                    content=[TextContent(type="text", text=result.to_string())],
                    isError=True,
                )
        else:
            text = str(result)
            if kernel_read_warning:
                text = kernel_read_warning + text
            return CallToolResult(
                content=[TextContent(type="text", text=text)]
            )
    except Exception as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {e}")],
            isError=True,
        )


async def main():
    async with stdio_server() as (read, write):
        await server.run(
            read,
            write,
            InitializationOptions(
                server_name="pie-kernel-sim",
                server_version="0.1.0",
                capabilities=ServerCapabilities(
                    tools=ToolsCapability(listTools=True)
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
