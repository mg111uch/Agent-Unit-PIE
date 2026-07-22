# 📂 tests
Generated: 2026-07-21 18:31:40
Files: 3

---

F314│__init__.py│1
S: Tests package for agent Phase 1
---

F315│agent_test.py│138│⚡
S: Tests for agent kernel integration.
D: ●agent_core,kernel,os,pytest,sys,+1
C: TestKernelImports│[test_kernel_imports]
   S: Test kernel modules import
C: TestToolRegistry│[test_all_tools_registered]
   S: Test tool registration
C: TestKernelConfig│[test_kernel_config]
   S: Test kernel configuration
C: TestKernelRetrieval│[retrieval,test_search,test_retrieve_patterns,test_retrieve_timeline,test_memory_summary,test_kernel_retrieve_tool]
   S: Integration tests for kernel retrieval
C: TestSignalEngine│[signal_eng,kernel_avail,test_create_signal,test_emit_signal_tool]
   S: Integration tests for signal engine
C: TestWorkingMemory│[kernel_avail,test_store_context]
   S: Integration tests for working memory
C: TestEventEngine│[kernel_avail,test_create_event]
   S: Integration tests for event engine
C: TestPhase3Tools│[kernel_avail,test_all_tools_callable]
   S: Tests for Phase 3 tools
C: TestKernelImports│[test_kernel_imports]
   S: Test kernel modules import
   F: test_kernel_imports(self)
      S: Verify kernel modules can be imported
C: TestToolRegistry│[test_all_tools_registered]
   S: Test tool registration
   F: test_all_tools_registered(self)
      S: Verify all required tools are registered
C: TestKernelConfig│[test_kernel_config]
   S: Test kernel configuration
   F: test_kernel_config(self)
      S: Verify kernel config flags
C: TestKernelRetrieval│[retrieval,test_search,test_retrieve_patterns,test_retrieve_timeline,test_memory_summary,test_kernel_retrieve_tool]
   S: Integration tests for kernel retrieval
   F: retrieval(self)
   F: test_search(self,retrieval)
   F: test_retrieve_patterns(self,retrieval)
   F: test_retrieve_timeline(self,retrieval)
   F: test_memory_summary(self,retrieval)
   F: test_kernel_retrieve_tool(self)
C: TestSignalEngine│[signal_eng,kernel_avail,test_create_signal,test_emit_signal_tool]
   S: Integration tests for signal engine
   F: signal_eng(self)
   F: kernel_avail(self)
   F: test_create_signal(self,signal_eng)
   F: test_emit_signal_tool(self,kernel_avail)
C: TestWorkingMemory│[kernel_avail,test_store_context]
   S: Integration tests for working memory
   F: kernel_avail(self)
   F: test_store_context(self,kernel_avail)
C: TestEventEngine│[kernel_avail,test_create_event]
   S: Integration tests for event engine
   F: kernel_avail(self)
   F: test_create_event(self,kernel_avail)
C: TestPhase3Tools│[kernel_avail,test_all_tools_callable]
   S: Tests for Phase 3 tools
   F: kernel_avail(self)
   F: test_all_tools_callable(self,kernel_avail)
---

F313│test_tool_pluggability.py│197│⚡
S: Phase 4 — Pluggability integration tests.
D: ●agent_core,os,pytest,sys
C: TestToolRegistryFiltering│[test_registry_has_all_tools,test_category_filter_kernel_sim,test_category_filter_file_only,test_category_filter_git,test_category_filter_meta,test_no_categories_returns_all,test_tools_are_callable]
   S: Registry with file pack off exposes only kernel/sim tools.
C: TestMCPExport│[test_mcp_kernel_sim_tools,test_mcp_all_tools,test_mcp_tool_has_schema]
   S: MCP server returns expected tools.
C: TestPromptMode│[test_full_prompt_has_file_tools,test_embed_prompt_no_file_tools,test_kernel_only_prompt_no_sim,test_prompt_includes_only_active_tools_in_table]
   S: System prompt in embed mode never references file tools.
C: TestBackwardCompat│[test_tools_dict_importable,test_tool_meta_importable,test_registry_instance_accessible,test_tools_work_as_before]
   S: TOOLS and TOOL_META remain importable.
C: TestSchemas│[test_default_schemas,test_gemini_schemas,test_filtered_schemas]
   S: Schema export per provider.
C: TestToolRegistryFiltering│[test_registry_has_all_tools,test_category_filter_kernel_sim,test_category_filter_file_only,test_category_filter_git,test_category_filter_meta,test_no_categories_returns_all,test_tools_are_callable]
   S: Registry with file pack off exposes only kernel/sim tools.
   F: test_registry_has_all_tools(self)
   F: test_category_filter_kernel_sim(self)
   F: test_category_filter_file_only(self)
   F: test_category_filter_git(self)
   F: test_category_filter_meta(self)
   F: test_no_categories_returns_all(self)
   F: test_tools_are_callable(self)
C: TestMCPExport│[test_mcp_kernel_sim_tools,test_mcp_all_tools,test_mcp_tool_has_schema]
   S: MCP server returns expected tools.
   F: test_mcp_kernel_sim_tools(self)
   F: test_mcp_all_tools(self)
   F: test_mcp_tool_has_schema(self)
C: TestPromptMode│[test_full_prompt_has_file_tools,test_embed_prompt_no_file_tools,test_kernel_only_prompt_no_sim,test_prompt_includes_only_active_tools_in_table]
   S: System prompt in embed mode never references file tools.
   F: test_full_prompt_has_file_tools(self)
   ↳Calls: F323:load_system_prompt
   F: test_embed_prompt_no_file_tools(self)
   ↳Calls: F323:load_system_prompt
   F: test_kernel_only_prompt_no_sim(self)
   ↳Calls: F323:load_system_prompt
   F: test_prompt_includes_only_active_tools_in_table(self)
   ↳Calls: F323:load_system_prompt
C: TestBackwardCompat│[test_tools_dict_importable,test_tool_meta_importable,test_registry_instance_accessible,test_tools_work_as_before]
   S: TOOLS and TOOL_META remain importable.
   F: test_tools_dict_importable(self)
   F: test_tool_meta_importable(self)
   F: test_registry_instance_accessible(self)
   F: test_tools_work_as_before(self)
C: TestSchemas│[test_default_schemas,test_gemini_schemas,test_filtered_schemas]
   S: Schema export per provider.
   F: test_default_schemas(self)
   F: test_gemini_schemas(self)
   F: test_filtered_schemas(self)
---
