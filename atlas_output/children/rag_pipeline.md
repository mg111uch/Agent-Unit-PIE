# 📂 rag_pipeline
Generated: 2026-07-21 18:31:40
Files: 1

---

F017│ChunkEmbedChroma.py│238│⚡
D: ●chromadb,os,pprint,sentence_transformers,tree_sitter_python,+2
F: get_node_text(node,source_code_bytes)
   ↳Called by: F017:extract_python_chunks
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F017:extract_python_chunks]
   S: Extracts the text of a tree-sitter node.
F: extract_python_chunks(file_path)
   ↳Called by: F017:index_codebase_to_chromadb | Calls: F017:get_node_text
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F017:index_codebase_to_chromadb]
   S: Parses a Python file and extracts semantic chunks (functions, classes, docstrings).
   S: Returns a list of dictionaries, each representing a chunk.
F: generate_embedding(text)
   ↳Called by: F017:index_codebase_to_chromadb
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F017:index_codebase_to_chromadb]
   S: Generates an embedding for the given text.
F: index_codebase_to_chromadb(project_root_dir)
   ↳Calls: F017:generate_embedding,F017:extract_python_chunks
   S: Parses all Python files in a project, generates embeddings,
   S: and stores them in ChromaDB.
---
