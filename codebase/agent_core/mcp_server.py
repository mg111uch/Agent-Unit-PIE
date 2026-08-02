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
import os
import sys
import time
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolResult,
    ServerCapabilities,
    ServerNotification,
    TextContent,
    Tool,
    ToolListChangedNotification,
    ToolsCapability,
)

from agent_core.tools import registry
from agent_core.tools.registry import CAT_FILE, CAT_KERNEL, CAT_SIM, CAT_META, CAT_GIT, CAT_CODE_RAG, CAT_OBSERVER, CAT_DEBATE, CAT_CHAIN
from agent_core.config import resolve_active_tool_packs
from agent_core.loop.executor import _normalize_tool_arg

# MCP exposure policy:
# - CAT_FILE never exposed (redundant with opencode built-ins)
# - CAT_META always exposed
# - other packs exposed only when enabled in config (tool_packs)
_META_ALWAYS_ON = {CAT_META}
_FILE_NEVER_EXPOSED = CAT_FILE


def _exposed_categories() -> list[str]:
    active = set(resolve_active_tool_packs())
    others = {CAT_KERNEL, CAT_SIM, CAT_GIT, CAT_CODE_RAG, CAT_OBSERVER, CAT_DEBATE, CAT_CHAIN} & active
    return sorted(_META_ALWAYS_ON | others)

# Hot-reload support: watches all .py files under agent_core/tools/
_WATCH_DIR = "agent_core/tools/"
_mtime_cache: dict[str, int] = {}
_RELOAD_POLL_INTERVAL = 2.0
_last_reload_check = 0.0


def _do_reload():
    prefix = "agent_core.tools"
    for mod_name in list(sys.modules.keys()):
        if mod_name.startswith(prefix):
            importlib.reload(sys.modules[mod_name])
    from agent_core.tools import _register_all
    _register_all()


def _reload_if_changed():
    """Reload all tool modules when any .py file under _WATCH_DIR changes."""
    global _last_reload_check
    now = time.monotonic()
    if now - _last_reload_check < _RELOAD_POLL_INTERVAL:
        return
    _last_reload_check = now
    codebase = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    watch_path = os.path.join(codebase, _WATCH_DIR)
    changed = False
    for py_file in Path(watch_path).rglob("*.py"):
        try:
            mtime_ns = os.stat(py_file).st_mtime_ns
        except OSError:
            continue
        last = _mtime_cache.get(str(py_file))
        if last is None or mtime_ns > last:
            _mtime_cache[str(py_file)] = mtime_ns
            changed = True
    if changed:
        _do_reload()


server = Server("pie-kernel-sim")


def _build_tool_list() -> list[Tool]:
    mcp_tools = registry.to_mcp_tools(categories=_exposed_categories())
    return [Tool(**t) for t in mcp_tools]


@server.list_tools()
async def list_mcp_tools() -> list[Tool]:
    _reload_if_changed()
    return _build_tool_list()


@server.call_tool()
async def call_mcp_tool(name: str, arguments: dict[str, Any] | None) -> CallToolResult:
    _reload_if_changed()

    reg_name = name

    # Built-in hot_reload — re-registers tools and notifies client
    if reg_name == "hot_reload":
        _do_reload()
        ctx = server.request_context
        await ctx.session.send_notification(
            ServerNotification(ToolListChangedNotification())
        )
        return CallToolResult(
            content=[TextContent(type="text", text="Tools reloaded. Client notified — new tools should appear.")]
        )

    tools = registry.get_tools(categories=_exposed_categories())
    if reg_name not in tools:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Unknown tool: {name}")],
            isError=True,
        )

    import time
    t0 = time.time()
    is_error = False
    result_text = ""
    try:
        fn = tools[reg_name]
        arg = _normalize_tool_arg(reg_name, arguments or {})
        result = fn(arg)

        from agent_core.tools.types import ToolResult as TR
        if isinstance(result, TR):
            if result.ok:
                text = result.data
                result_text = text
                return CallToolResult(
                    content=[TextContent(type="text", text=text)]
                )
            else:
                is_error = True
                result_text = result.to_string()
                return CallToolResult(
                    content=[TextContent(type="text", text=result_text)],
                    isError=True,
                )
        else:
            text = str(result)
            result_text = text
            return CallToolResult(
                content=[TextContent(type="text", text=text)]
            )
    except Exception as e:
        is_error = True
        result_text = f"Error: {e}"
        return CallToolResult(
            content=[TextContent(type="text", text=result_text)],
            isError=True,
        )
    finally:
        duration_ms = (time.time() - t0) * 1000
        try:
            from kernel.persistence.db import kernel_db
            kernel_db.record_tool_call(reg_name, duration_ms, is_error, len(result_text))
            if is_error:
                kernel_db.save_generic_memory(
                    memory_id=f"tool_failure_{reg_name}_{int(t0)}",
                    memory_type="tool_failure",
                    data={"tool": reg_name, "error": result_text[:500], "ts": t0, "args": str(arguments)[:200]},
                )
        except Exception:
            pass


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
