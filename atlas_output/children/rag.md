# 📂 rag
Generated: 2026-07-23 14:15:38
Files: 2

---

F099│__init__.py│0
---

F098│db.py│220
S: Code RAG database operations — schema init, symbol insertion, call edges.
D: ►F148 ●agent_tools,pathlib,sqlite3,sys,typing
F: init_schema(conn)
   ↳Called by: F078:generate_atlas
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F078:generate_atlas]
F: insert_function(conn,file_path,func,parent_name,name_to_id)→int
   ↳Called by: F098:insert_file_symbols
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F098:insert_file_symbols]
F: insert_class(conn,file_path,cls,name_to_id)→int
   ↳Called by: F098:insert_file_symbols
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F098:insert_file_symbols]
F: insert_file_as_symbol(conn,file_path,name_to_id)→int
   ↳Called by: F098:insert_file_symbols
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F098:insert_file_symbols]
F: insert_file_symbols(conn,file_path,file_info,name_to_id)
   ↳Called by: F078:generate_atlas | Calls: F098:insert_class,F098:insert_file_as_symbol,F098:insert_function
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F078:generate_atlas]
F: update_from_graph(conn,unified_graph,name_to_id)
   ↳Called by: F078:generate_atlas
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F078:generate_atlas]
   S: Update risk/entry levels and insert call edges from graph data.
---
