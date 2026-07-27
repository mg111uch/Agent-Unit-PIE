# 📂 code_rag
Generated: 2026-07-27 19:23:22
Files: 3

---

F193│__init__.py│22
D: ●agent_core
---

F194│engine.py│375
D: ●agent_core,os,pathlib,sqlite3,typing
C: CodeRAG│[__init__,_get_conn,ensure_indexed,needs_index,get_symbol,get_symbols,search_symbols,_search_fts,get_callers_callees,get_symbols_meta,+8]
F: _resolve_path(path)→str
   ↳Called by: F192:symbols_by_file_tool,F192:file_api_tool,F185:minimal_context_dump
   ↳Impact: 🔴HIGH (5 dependents) | Breaks: [F192:symbols_by_file_tool],[F192:file_api_tool],[F185:minimal_context_dump]
F: _get_rag()→Optional[CodeRAG]
   ↳Called by: F192:symbols_by_file_tool,F192:extract_symbols_to_file_tool,F192:atlas_status_tool
   ↳Impact: 🔴HIGH (9 dependents) | Breaks: [F192:symbols_by_file_tool],[F192:extract_symbols_to_file_tool],[F192:atlas_status_tool]
C: CodeRAG│[__init__,_get_conn,ensure_indexed,needs_index,get_symbol,get_symbols,search_symbols,_search_fts,get_callers_callees,get_symbols_meta,+8]
   F: __init__(self,atlas_dir)
   F: _get_conn(self)→sqlite3.Connection
   F: ensure_indexed(self)→bool
   F: needs_index(self)→bool
   F: get_symbol(self,name,file_path,parent_name)→Any
   F: get_symbols(self,names,file_path)→Any
   F: search_symbols(self,query,type_filter,top_k,queries)→Any
   F: _search_fts(self,query,type_filter,top_k)→Any
   F: get_callers_callees(self,name,file_path,depth,direction)→Any
   F: get_symbols_meta(self,names,file_path)→Any
   F: find_impact(self,name,file_path)→Any
   F: batch_file_api(self,paths)→Any
   ↳Calls: F194:_resolve_path
   F: atlas_status(self)→Any
   F: get_index_info(self)→Any
   F: file_api(self,path)→Any
   F: call_chain(self,start_fn,end_module,file_path)→Any
   F: compare_apis(self,path_a,path_b)→Any
   F: symbols_by_file(self,path)→Any
---

F192│tools.py│377
D: ●agent_core,json,kernel,pathlib,subprocess,+4
F: _project_root()→Path
   ↳Called by: F192:project_root_tool,F192:extract_symbols_to_file_tool,F192:report_schema_check_tool
   ↳Impact: 🔴HIGH (7 dependents) | Breaks: [F192:project_root_tool],[F192:extract_symbols_to_file_tool],[F192:report_schema_check_tool]
F: _make_rag_tool(method)
   ↳Calls: F194:_resolve_path,F194:_get_rag
   S: Generate a tool that inits rag, calls *method*(**kwargs), returns JSON.
F: _post_search(results)
F: _post_callers_callees(result)
F: _post_impact(results)
F: _post_file_api(result)
   ↳Called by: F192:file_api_tool
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F192:file_api_tool]
F: _post_symbols_by_file(result,path)
   ↳Called by: F192:symbols_by_file_tool
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F192:symbols_by_file_tool]
F: _post_meta(symbols)
   ↳Called by: F192:get_symbols_meta_tool
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F192:get_symbols_meta_tool]
F: file_api_tool(params)
   ↳Calls: F192:_post_file_api,F194:_resolve_path,F194:_get_rag
F: symbols_by_file_tool(params)
   ↳Calls: F192:_post_symbols_by_file,F194:_resolve_path,F194:_get_rag
F: atlas_status_tool(params)
   ↳Calls: F194:_get_rag
F: get_symbols_meta_tool(params)
   ↳Calls: F192:_post_meta,F194:_get_rag
F: get_symbol_tool(params)→str
   ↳Calls: F194:_get_rag
F: project_root_tool(params)→str
   ↳Calls: F192:_project_root
F: extract_symbols_to_file_tool(params)→str
   ↳Calls: F192:_project_root,F194:_get_rag
F: report_freshness_tool(params)→str
   ↳Calls: F192:_project_root,F194:_get_rag
F: report_inventory_tool(params)→str
   ↳Calls: F192:_project_root
F: report_schema_check_tool(params)→str
   ↳Calls: F192:_project_root
F: list_capabilities_tool(params)→str
   ↳Calls: F192:_project_root
F: resolve_citations_tool(params)→str
   ↳Calls: F192:_project_root
---
