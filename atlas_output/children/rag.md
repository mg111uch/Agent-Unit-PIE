# 📂 rag
Generated: 2026-07-21 18:31:40
Files: 2

---

F252│__init__.py│0
---

F251│db.py│220
S: Code RAG database operations — schema init, symbol insertion, call edges.
D: ►F300 ●agent_tools,pathlib,sqlite3,sys,typing
F: init_schema(conn)
   ↳Called by: F209:generate_atlas
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F209:generate_atlas]
F: insert_function(conn,file_path,func,parent_name,name_to_id)→int
   ↳Called by: F251:insert_file_symbols | Calls: F040:count_tokens_string
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F251:insert_file_symbols]
F: insert_class(conn,file_path,cls,name_to_id)→int
   ↳Called by: F251:insert_file_symbols | Calls: F040:count_tokens_string
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F251:insert_file_symbols]
F: insert_file_as_symbol(conn,file_path,name_to_id)→int
   ↳Called by: F251:insert_file_symbols | Calls: F040:count_tokens_string
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F251:insert_file_symbols]
F: insert_file_symbols(conn,file_path,file_info,name_to_id)
   ↳Called by: F209:generate_atlas | Calls: F251:insert_function,F251:insert_file_as_symbol,F251:insert_class
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F209:generate_atlas]
F: update_from_graph(conn,unified_graph,name_to_id)
   ↳Called by: F209:generate_atlas
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F209:generate_atlas]
   S: Update risk/entry levels and insert call edges from graph data.
---
