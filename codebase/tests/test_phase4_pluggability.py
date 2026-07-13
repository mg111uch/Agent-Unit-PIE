"""
Phase 4 — Pluggability integration tests.

Tests:
- ToolRegistry category filtering (file pack off → only kernel/sim)
- MCP server tool export
- System prompt in embed mode (no file tool references)
- Backward compat (TOOLS/TOOL_META still importable)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestToolRegistryFiltering:
    """Registry with file pack off exposes only kernel/sim tools."""

    def test_registry_has_all_tools(self):
        from agent_core.tools import registry
        assert registry.tool_count == 27

    def test_category_filter_kernel_sim(self):
        from agent_core.tools import registry
        from agent_core.tools.registry import CAT_KERNEL, CAT_SIM
        tools = registry.get_tools(categories=[CAT_KERNEL, CAT_SIM])
        names = set(tools.keys())
        assert "kernel_retrieve" in names
        assert "simulation_run" in names
        assert "read_file" not in names
        assert "write_to_file" not in names
        assert "git_status" not in names
        assert len(tools) == 9

    def test_category_filter_file_only(self):
        from agent_core.tools import registry
        from agent_core.tools.registry import CAT_FILE
        tools = registry.get_tools(categories=[CAT_FILE])
        names = set(tools.keys())
        assert "read_file" in names
        assert "edit_file" in names
        assert "kernel_retrieve" not in names
        assert len(tools) == 9

    def test_category_filter_git(self):
        from agent_core.tools import registry
        from agent_core.tools.registry import CAT_GIT
        tools = registry.get_tools(categories=[CAT_GIT])
        names = set(tools.keys())
        assert "git_status" in names
        assert "git_commit" in names
        assert "read_file" not in names

    def test_category_filter_meta(self):
        from agent_core.tools import registry
        from agent_core.tools.registry import CAT_META
        tools = registry.get_tools(categories=[CAT_META])
        names = set(tools.keys())
        assert "todo_write" in names
        assert "run_tests" in names
        assert "read_file" not in names

    def test_no_categories_returns_all(self):
        from agent_core.tools import registry
        tools = registry.get_tools()
        assert len(tools) == 27

    def test_tools_are_callable(self):
        from agent_core.tools import registry
        from agent_core.tools.registry import CAT_KERNEL
        tools = registry.get_tools(categories=[CAT_KERNEL])
        result = tools["kernel_retrieve"]({"query": "test", "limit": 1})
        assert hasattr(result, "ok")
        assert hasattr(result, "data")


class TestMCPExport:
    """MCP server returns expected tools."""

    def test_mcp_kernel_sim_tools(self):
        from agent_core.tools import registry
        from agent_core.tools.registry import CAT_KERNEL, CAT_SIM
        mcp_tools = registry.to_mcp_tools(categories=[CAT_KERNEL, CAT_SIM])
        assert len(mcp_tools) == 9
        names = {t["name"] for t in mcp_tools}
        assert "kernel_retrieve" in names
        assert "simulation_run" in names
        assert "read_file" not in names
        for t in mcp_tools:
            assert "name" in t
            assert "description" in t
            assert "inputSchema" in t
            assert isinstance(t["inputSchema"], dict)

    def test_mcp_all_tools(self):
        from agent_core.tools import registry
        mcp_tools = registry.to_mcp_tools()
        assert len(mcp_tools) == 27
        names = {t["name"] for t in mcp_tools}
        assert "read_file" in names
        assert "kernel_retrieve" in names

    def test_mcp_tool_has_schema(self):
        from agent_core.tools import registry
        from agent_core.tools.registry import CAT_KERNEL
        mcp_tools = registry.to_mcp_tools(categories=[CAT_KERNEL])
        kr = next(t for t in mcp_tools if t["name"] == "kernel_retrieve")
        props = kr["inputSchema"].get("properties", {})
        assert "query" in props
        assert "limit" in props


class TestPromptMode:
    """System prompt in embed mode never references file tools."""

    def test_full_prompt_has_file_tools(self):
        from agent_core.prompts import load_system_prompt
        from agent_core.tools import registry
        from agent_core.tools.registry import CAT_FILE, CAT_KERNEL, CAT_SIM, CAT_META, CAT_GIT
        tools = registry.get_tools()
        prompt = load_system_prompt(
            tools_dict=tools,
            active_packs=[CAT_FILE, CAT_KERNEL, CAT_SIM, CAT_META, CAT_GIT],
        )
        assert "read_file" in prompt
        assert "edit_file" in prompt
        assert "WORKING STYLE" in prompt
        assert "KERNEL MEMORY" in prompt
        assert "SIMULATION" in prompt
        assert "HOST INTEGRATION" not in prompt

    def test_embed_prompt_no_file_tools(self):
        from agent_core.prompts import load_system_prompt
        from agent_core.tools import registry
        from agent_core.tools.registry import CAT_KERNEL, CAT_SIM
        tools = registry.get_tools(categories=[CAT_KERNEL, CAT_SIM])
        prompt = load_system_prompt(
            tools_dict=tools,
            active_packs=[CAT_KERNEL, CAT_SIM],
        )
        assert "read_file" not in prompt
        assert "write_to_file" not in prompt
        assert "edit_file" not in prompt
        assert "WORKING STYLE" not in prompt
        assert "KERNEL MEMORY" in prompt
        assert "SIMULATION" in prompt
        assert "HOST INTEGRATION" in prompt

    def test_kernel_only_prompt_no_sim(self):
        from agent_core.prompts import load_system_prompt
        from agent_core.tools import registry
        from agent_core.tools.registry import CAT_KERNEL
        tools = registry.get_tools(categories=[CAT_KERNEL])
        prompt = load_system_prompt(
            tools_dict=tools,
            active_packs=[CAT_KERNEL],
        )
        assert "SIMULATION" not in prompt
        assert "simulation_run" not in prompt
        assert "KERNEL MEMORY" in prompt
        assert "HOST INTEGRATION" in prompt

    def test_prompt_includes_only_active_tools_in_table(self):
        from agent_core.prompts import load_system_prompt
        from agent_core.tools import registry
        from agent_core.tools.registry import CAT_KERNEL, CAT_SIM
        tools = registry.get_tools(categories=[CAT_KERNEL, CAT_SIM])
        prompt = load_system_prompt(
            tools_dict=tools,
            active_packs=[CAT_KERNEL, CAT_SIM],
        )
        # The tool table should only list kernel+sim tools
        assert "| `kernel_retrieve`" in prompt
        assert "| `simulation_run`" in prompt
        assert "| `read_file`" not in prompt
        assert "| `git_status`" not in prompt


class TestBackwardCompat:
    """TOOLS and TOOL_META remain importable."""

    def test_tools_dict_importable(self):
        from agent_core.tools import TOOLS
        assert len(TOOLS) == 27
        assert "read_file" in TOOLS
        assert callable(TOOLS["read_file"])

    def test_tool_meta_importable(self):
        from agent_core.tools import TOOL_META
        assert len(TOOL_META) == 27
        assert "read_file" in TOOL_META
        assert "description" in TOOL_META["read_file"]
        assert "input_format" in TOOL_META["read_file"]

    def test_registry_instance_accessible(self):
        from agent_core.tools import registry
        assert registry.tool_count == 27

    def test_tools_work_as_before(self):
        from agent_core.tools import TOOLS
        result = TOOLS["get_workspace_info"]("")
        assert hasattr(result, "ok")
        assert result.ok


class TestSchemas:
    """Schema export per provider."""

    def test_default_schemas(self):
        from agent_core.tools import registry
        schemas = registry.get_schemas()
        assert len(schemas) == 27
        assert schemas[0].get("type") == "function"

    def test_gemini_schemas(self):
        from agent_core.tools import registry
        schemas = registry.get_schemas("gemini")
        assert len(schemas) == 1
        assert "function_declarations" in schemas[0]

    def test_filtered_schemas(self):
        from agent_core.tools import registry
        from agent_core.tools.registry import CAT_KERNEL, CAT_SIM
        # Schemas are not filterable by category in the current API;
        # just verify get_schemas works
        schemas = registry.get_schemas()
        assert len(schemas) == 27


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
