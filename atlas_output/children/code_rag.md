# 📂 code_rag
Generated: 2026-07-23 14:15:38
Files: 3

---

F189│__init__.py│18
D: ●agent_core
---

F190│engine.py│358
D: ●agent_core,os,pathlib,sqlite3,typing
C: CodeRAG│[__init__,_get_conn,ensure_indexed,needs_index,get_symbol,get_symbols,search_symbols,get_callers_callees,get_symbols_meta,find_impact,+7]
F: _resolve_path(path)→str
   ↳Called by: F188:symbols_by_file_tool,F188:file_api_tool,F188:compare_apis_tool
   ↳Impact: 🔴HIGH (5 dependents) | Breaks: [F188:symbols_by_file_tool],[F188:file_api_tool],[F188:compare_apis_tool]
F: _get_rag()→Optional[CodeRAG]
   ↳Called by: F188:get_symbol_tool,F188:get_symbols_meta_tool,F188:get_index_info_tool
   ↳Impact: 🔴HIGH (15 dependents) | Breaks: [F188:get_symbol_tool],[F188:get_symbols_meta_tool],[F188:get_index_info_tool]
C: CodeRAG│[__init__,_get_conn,ensure_indexed,needs_index,get_symbol,get_symbols,search_symbols,get_callers_callees,get_symbols_meta,find_impact,+7]
   F: __init__(self,atlas_dir)
   F: _get_conn(self)→sqlite3.Connection
   F: ensure_indexed(self)→bool
   F: needs_index(self)→bool
   F: get_symbol(self,name,file_path,parent_name)→Any
   F: get_symbols(self,names,file_path)→Any
   F: search_symbols(self,query,type_filter,top_k)→Any
   F: get_callers_callees(self,name,file_path,depth,direction)→Any
   F: get_symbols_meta(self,names,file_path)→Any
   F: find_impact(self,name,file_path)→Any
   F: batch_file_api(self,paths)→Any
   ↳Calls: F190:_resolve_path
   F: atlas_status(self)→Any
   F: get_index_info(self)→Any
   F: file_api(self,path)→Any
   F: call_chain(self,start_fn,end_module,file_path)→Any
   F: compare_apis(self,path_a,path_b)→Any
   F: symbols_by_file(self,path)→Any
---

F188│tools.py│339
D: ●datetime,json,pathlib,re,subprocess,+2
F: _project_root()→Path
   ↳Called by: F188:extract_symbols_to_file_tool,F188:project_root_tool,F188:report_freshness_tool
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F188:extract_symbols_to_file_tool],[F188:project_root_tool],[F188:report_freshness_tool]
F: get_symbol_tool(params)→str
   ↳Calls: F190:_get_rag
F: get_symbols_meta_tool(params)→str
   ↳Calls: F190:_get_rag
F: search_symbols_tool(params)→str
   ↳Calls: F190:_get_rag
F: get_callers_callees_tool(params)→str
   ↳Calls: F190:_get_rag
F: find_impact_tool(params)→str
   ↳Calls: F190:_get_rag
F: get_index_info_tool(params)→str
   ↳Calls: F190:_get_rag
F: file_api_tool(params)→str
   ↳Calls: F190:_resolve_path,F190:_get_rag
F: call_chain_tool(params)→str
   ↳Calls: F190:_get_rag
F: compare_apis_tool(params)→str
   ↳Calls: F190:_resolve_path,F190:_get_rag
F: symbols_by_file_tool(params)→str
   ↳Calls: F190:_resolve_path,F190:_get_rag
F: atlas_status_tool(params)→str
   ↳Calls: F190:_get_rag
F: project_root_tool(params)→str
   ↳Calls: F188:_project_root
F: batch_file_api_tool(params)→str
   ↳Calls: F190:_get_rag
F: extract_symbols_to_file_tool(params)→str
   ↳Calls: F188:_project_root,F190:_get_rag
F: report_freshness_tool(params)→str
   ↳Calls: F188:_project_root,F190:_get_rag
---
