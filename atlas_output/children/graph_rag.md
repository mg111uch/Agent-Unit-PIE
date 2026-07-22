# 📂 graph_rag
Generated: 2026-07-21 18:31:40
Files: 2

---

F018│graph_db.py│324│⚡
D: ●ast,inspect,os,sqlite3,typing
C: CodeGraphDB│[__init__,init_db,add_node,add_edge,get_node_by_name,get_neighbors,search_nodes,get_graph_context,clear_db]
   S: SQLite-based graph database for codebase analysis and GraphRAG context retrieval.
C: CodeAnalyzer←ast.NodeVisitor│[__init__,visit_ClassDef,visit_FunctionDef,visit_Call,visit_Import,visit_ImportFrom]
   S: AST visitor to analyze code and build graph.
F: analyze_codebase(db,directory)
   ↳Called by: F019:reanalyze_codebase
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F019:reanalyze_codebase]
   S: Analyze the codebase and populate the graph database.
C: CodeGraphDB│[__init__,init_db,add_node,add_edge,get_node_by_name,get_neighbors,search_nodes,get_graph_context,clear_db]
   S: SQLite-based graph database for codebase analysis and GraphRAG context retrieval.
   F: __init__(self,db_path)
      S: Initialize the graph database.
   F: init_db(self)
      S: Initialize database tables.
   F: add_node(self,name,node_type,file_path,line_start,line_end,content,metadata)→int
      S: Add a node to the graph.
   F: add_edge(self,source_id,target_id,relationship_type,metadata)→int
      S: Add an edge between two nodes.
   F: get_node_by_name(self,name,file_path)→Any
      S: Get a node by name and optionally file path.
   F: get_neighbors(self,node_id,relationship_type)→Any
      S: Get neighboring nodes connected by edges.
   F: search_nodes(self,query,node_type)→Any
      S: Search nodes by name or content.
   F: get_graph_context(self,node_name,depth)→Any
      S: Get graph context around a node for RAG.
   F: clear_db(self)
      S: Clear all data from the database.
C: CodeAnalyzer←ast.NodeVisitor│[__init__,visit_ClassDef,visit_FunctionDef,visit_Call,visit_Import,visit_ImportFrom]
   S: AST visitor to analyze code and build graph.
   F: __init__(self,db,file_path,module_id)
   F: visit_ClassDef(self,node)
      S: Handle class definitions.
   F: visit_FunctionDef(self,node)
      S: Handle function definitions.
   F: visit_Call(self,node)
      S: Handle function calls.
   F: visit_Import(self,node)
      S: Handle import statements.
   F: visit_ImportFrom(self,node)
      S: Handle from import statements.
---

F019│graph_visualizer.py│181│⚡
D: ►F018 ●fastapi,pydantic,sqlite3,typing,uvicorn,+1
C: NodeResponse←BaseModel│[]
C: EdgeResponse←BaseModel│[]
C: GraphDataResponse←BaseModel│[]
C: SearchRequest←BaseModel│[]
C: ContextRequest←BaseModel│[]
F: root()
   S: Serve the main visualization page.
F: api_root()
   S: Root endpoint with API information.
F: get_graph_data()
   S: Get all nodes and edges in the graph.
F: search_nodes(request)
   S: Search for nodes by name or content.
F: get_node_neighbors(node_id,relationship_type)
   S: Get neighbors of a specific node.
F: get_graph_context(request)
   S: Get graph context around a node for GraphRAG.
F: get_graph_stats()
   S: Get statistics about the graph database.
F: reanalyze_codebase()
   ↳Calls: F018:analyze_codebase
   S: Re-analyze the codebase and update the graph database.
C: NodeResponse←BaseModel│[]
C: EdgeResponse←BaseModel│[]
C: GraphDataResponse←BaseModel│[]
C: SearchRequest←BaseModel│[]
C: ContextRequest←BaseModel│[]
---
