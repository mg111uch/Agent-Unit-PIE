# 📂 persistence
Generated: 2026-07-21 18:31:40
Files: 2

---

F062│__init__.py│0
---

F061│db.py│465
D: ●__future__,kernel,pathlib,time,typing,+2
C: KernelDB│[__init__,conn,_init_db,close,insert_log,query_logs,save_semantic_node,load_semantic_node,load_all_semantic_nodes,search_semantic_nodes,+21]
C: KernelDB│[__init__,conn,_init_db,close,insert_log,query_logs,save_semantic_node,load_semantic_node,load_all_semantic_nodes,search_semantic_nodes,+21]
   F: __init__(self,db_path)
   F: conn(self)→sqlite3.Connection
   F: _init_db(self)
   F: close(self)
   F: insert_log(self,level,module,message,context)→int
   F: query_logs(self,level,module,limit,offset)→Any
   F: save_semantic_node(self,node_id,node_type,title,content,concepts,tags,importance,confidence,created_at,updated_at)
   F: load_semantic_node(self,node_id)→Any
   F: load_all_semantic_nodes(self)→Any
   F: search_semantic_nodes(self,query,limit)→Any
   F: _row_to_node(row)→Any
   F: save_semantic_edge(self,edge_id,source_node_id,target_node_id,relation_type,weight,confidence,created_at)
   F: load_semantic_edge(self,edge_id)→Any
   F: get_edges_by_type(self,relation_type)→Any
   F: load_all_semantic_edges(self)→Any
   F: save_pattern(self,pattern_id,pattern_type,category,title,description,source_ids,confidence,importance,created_at)
   F: load_pattern(self,pattern_id)→Any
   F: list_patterns(self,pattern_type)→Any
   F: save_hypothesis(self,hypothesis_id,title,description,hypothesis_type,category,confidence,status,supporting,contradicting,created_at,updated_at)
   F: load_hypothesis(self,hypothesis_id)→Any
---
