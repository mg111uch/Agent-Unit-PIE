# 📂 persistence
Generated: 2026-07-23 14:15:38
Files: 2

---

F022│__init__.py│0
---

F021│db.py│492
D: ●__future__,json,kernel,pathlib,time,+2
C: KernelDB│[__init__,conn,_init_db,close,insert_log,query_logs,save_semantic_node,load_semantic_node,load_all_semantic_nodes,load_semantic_nodes_by_topic,+23]
C: KernelDB│[__init__,conn,_init_db,close,insert_log,query_logs,save_semantic_node,load_semantic_node,load_all_semantic_nodes,load_semantic_nodes_by_topic,+23]
   F: __init__(self,db_path)
   F: conn(self)→sqlite3.Connection
   F: _init_db(self)
   F: close(self)
   F: insert_log(self,level,module,message,context)→int
   F: query_logs(self,level,module,limit,offset)→Any
   F: save_semantic_node(self,node_id,node_type,title,content,concepts,tags,importance,confidence,created_at,updated_at,topic_id)
   F: load_semantic_node(self,node_id)→Any
   F: load_all_semantic_nodes(self)→Any
   F: load_semantic_nodes_by_topic(self,topic_id)→Any
   F: search_semantic_nodes(self,query,limit)→Any
   F: _row_to_node(row)→Any
   F: save_semantic_edge(self,edge_id,source_node_id,target_node_id,relation_type,weight,confidence,created_at,topic_id)
   F: load_semantic_edge(self,edge_id)→Any
   F: get_edges_by_type(self,relation_type)→Any
   F: load_all_semantic_edges(self)→Any
   F: load_semantic_edges_by_topic(self,topic_id)→Any
   F: save_pattern(self,pattern_id,pattern_type,category,title,description,source_ids,confidence,importance,created_at)
   F: load_pattern(self,pattern_id)→Any
   F: list_patterns(self,pattern_type)→Any
---
