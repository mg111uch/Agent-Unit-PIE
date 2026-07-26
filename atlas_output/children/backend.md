# 📂 backend
Generated: 2026-07-26 16:20:18
Files: 5

---

F094│__init__.py│0
---

F093│graph_builder.py│284
S: graph_builder.py
D: ►F076,F092 ●__future__,typing
C: GraphBuilder│[__init__,build_dependency_graph,build_call_graph,build_unified_graph,_add_file_nodes,_add_dependency_edges,_add_file_nodes_unified,_add_function_nodes_unified,_add_function_clusters,_add_function_nodes,+8]
   S: Builds GraphData from AtlasData.
C: GraphBuilder│[__init__,build_dependency_graph,build_call_graph,build_unified_graph,_add_file_nodes,_add_dependency_edges,_add_file_nodes_unified,_add_function_nodes_unified,_add_function_clusters,_add_function_nodes,+8]
   S: Builds GraphData from AtlasData.
   F: __init__(self,atlas_data)
   F: build_dependency_graph(self)→GraphData
      S: Build file-level dependency graph.
   F: build_call_graph(self)→GraphData
      S: Build function-level call graph.
   F: build_unified_graph(self)→GraphData
      S: Build a single unified graph with file-level dependency nodes
      S: and function-level call nodes nested inside them.
   F: _add_file_nodes(self,graph)→None
   F: _add_dependency_edges(self,graph)→None
   F: _add_file_nodes_unified(self,graph)→None
   F: _add_function_nodes_unified(self,graph)→None
   F: _add_function_clusters(self,graph)→None
   F: _add_function_nodes(self,graph)→None
   F: _add_call_edges(self,graph)→None
   F: _collect_call_graph_functions(self)
   F: _file_risk_level(self,file_info)→RiskLevel
   F: _function_risk_level(self,func)→RiskLevel
   F: _is_valid_file(self,file_ref)→bool
   F: _is_init_py(file_info)→bool
   F: _function_node_id(file_ref,func_name)→str
   F: _find_function(file_info,func_name)
---

F092│graph_models.py│155
S: graph_models.py
D: ●__future__,dataclasses,enum,typing
C: NodeType←str,Enum│[]
C: EdgeType←str,Enum│[]
C: RiskLevel←str,Enum│[]
C: GraphType←str,Enum│[]
C: GraphNode│[]
   S: Canonical graph node.
C: GraphEdge│[]
   S: Canonical graph edge.
C: GraphCluster│[]
   S: Logical grouping.
C: GraphData│[add_node,get_node,has_node,add_edge,get_edge,add_cluster,get_cluster,outgoing_edges,incoming_edges,neighbors,+3]
   S: Canonical graph representation.
C: NodeType←str,Enum│[]
C: EdgeType←str,Enum│[]
C: RiskLevel←str,Enum│[]
C: GraphType←str,Enum│[]
C: GraphNode│[]
   S: Canonical graph node.
C: GraphEdge│[]
   S: Canonical graph edge.
C: GraphCluster│[]
   S: Logical grouping.
C: GraphData│[add_node,get_node,has_node,add_edge,get_edge,add_cluster,get_cluster,outgoing_edges,incoming_edges,neighbors,+3]
   S: Canonical graph representation.
   F: add_node(self,node)→None
   F: get_node(self,node_id)→Optional[GraphNode]
   F: has_node(self,node_id)→bool
   F: add_edge(self,edge)→None
   F: get_edge(self,edge_id)→Optional[GraphEdge]
   F: add_cluster(self,cluster)→None
   F: get_cluster(self,cluster_id)→Optional[GraphCluster]
   F: outgoing_edges(self,node_id)→List[GraphEdge]
   F: incoming_edges(self,node_id)→List[GraphEdge]
   F: neighbors(self,node_id)→Set[str]
   F: node_count(self)→int
   F: edge_count(self)→int
   F: cluster_count(self)→int
---

F096│graph_serializer.py│389
S: graph_serializer.py
D: ►F092 ●__future__,dataclasses,json,pathlib,typing
C: GraphSerializer│[to_dict,to_nested_dict,to_json,save_json,from_dict,from_json,load_json,_node_to_dict,_node_from_dict,_edge_to_dict,+3]
C: GraphSerializer│[to_dict,to_nested_dict,to_json,save_json,from_dict,from_json,load_json,_node_to_dict,_node_from_dict,_edge_to_dict,+3]
   F: to_dict(cls,graph)→Any
   F: to_nested_dict(cls,graph)→Any
   F: to_json(cls,graph)→str
   F: save_json(cls,graph,output_path)→None
   F: from_dict(cls,data)→GraphData
   F: from_json(cls,json_text)→GraphData
   F: load_json(cls,input_path)→GraphData
   F: _node_to_dict(node)→Any
   F: _node_from_dict(data)→GraphNode
   F: _edge_to_dict(edge)→Any
   F: _edge_from_dict(data)→GraphEdge
   F: _cluster_to_dict(cluster)→Any
   F: _cluster_from_dict(data)→GraphCluster
---

F095│serve.py│236│⚡
D: ►F092,F096 ●__future__,flask,json,pathlib
F: _load_positions_with_meta(output_dir,graph_type)→Any
   ↳Called by: F095:_write_positions,F095:_build_app,F095:_merge_positions
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F095:_write_positions],[F095:_build_app],[F095:_merge_positions]
F: _merge_positions(graph,output_dir,graph_type)→None
   ↳Called by: F095:create_app | Calls: F095:_load_positions_with_meta
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F095:create_app]
   S: Overwrite node.x / node.y from saved positions file if it exists.
F: _write_positions(output_dir,graph_type,positions,project_id,child_offsets)→None
   ↳Called by: F095:_build_app | Calls: F095:_load_positions_with_meta
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F095:_build_app]
F: create_app(unified_graph,output_dir,project_id)→Flask
   ↳Called by: F079:main | Calls: F095:_build_app,F095:_merge_positions
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F079:main]
   S: Create app from a unified GraphData object.
F: _build_app(graph_json,output_dir,project_id)→Flask
   ↳Called by: F095:create_app | Calls: F095:_write_positions,F095:_load_positions_with_meta
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F095:create_app]
---
