# 📂 engine
Generated: 2026-07-23 14:15:38
Files: 9

---

F139│debate.py│306
D: ►F011,F140,F144,F145,F146,F147 ●datetime,json,kernel,threading,time,+4
F: _populate_semantic_memory(graph,topic)
   ↳Called by: F139:debate_step
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F139:debate_step]
   S: Deprecated — topics now write directly to SQLite via debate_expand/import_topic.
   S: Kept as no-op for backward compatibility during migration.
F: _build_debate_question(argument,counter)→dict
   ↳Called by: F139:debate_step
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F139:debate_step]
F: debate_step(raw_input)→str
   ↳Calls: F144:load_state,F144:load_beliefs,F144:add_response
F: debate_expand(topic,llm_output)→dict
   ↳Calls: F146:index_graph,F147:is_similar_to_any
   S: Generate new arguments via LLM and write directly to semantic_memory SQLite tables.
   S: Returns {node_id, name} on success, or {error: ...} on failure.
F: export_topic(topic_id)→dict
   S: Query semantic_memory for all nodes/edges with the given topic_id.
   S: Returns a JSON-serializable dict matching the old graph.json schema.
F: import_topic(data_dict,topic_id)→str
   S: Bulk-insert nodes/edges from a graph.json dict into semantic_memory.
   S: Returns the topic_id used (auto-generated if not provided).
---

F145│debate_helpers.py│158
D: ►F138,F140,F141,F147 ●datetime,kernel,modules,typing
F: _build_knowledge_context(topic)→dict
   ↳Called by: F145:_generate_next_question
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F145:_generate_next_question]
F: _check_novelty(text,threshold)→bool
   ↳Calls: F147:is_similar_to_any
F: _store_user_knowledge(argument_name,stance,confidence,topic,user_text)
   ↳Called by: F139:debate_step | Calls: F054:_get_collection,F146:_get_collection,F146:embed
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F139:debate_step]
F: _get_untouched_knowledge(topic,state,beliefs)→Optional[dict]
   ↳Called by: F145:_generate_next_question
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F145:_generate_next_question]
F: _generate_next_question(topic,state,beliefs,graph,llm_input)→Any
   ↳Called by: F139:debate_step | Calls: F145:_get_untouched_knowledge,F140:get_next_argument,F141:get_best_counter
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F139:debate_step]
---

F147│dedup.py│16
D: ►F146 ●numpy
F: cosine_similarity(a,b)
   ↳Called by: F147:is_similar_to_any
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F147:is_similar_to_any]
F: is_similar_to_any(candidate_text,existing_texts,threshold)
   ↳Called by: F145:_generate_next_question,F139:debate_expand,F145:_check_novelty | Calls: F147:cosine_similarity,F146:embed
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F145:_generate_next_question],[F139:debate_expand],[F145:_check_novelty]
---

F142│expand.py│28
D: ►F140,F146 ●json,os
F: expand_topic(topic,new_nodes,new_edges)→dict
   ↳Calls: F146:index_graph,F140:load_graph
---

F140│loop.py│28
D: ●json,os
F: load_graph(topic)
   ↳Called by: F139:debate_step,F142:expand_topic
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F139:debate_step],[F142:expand_topic]
F: get_next_argument(topic,graph,state,beliefs)
   ↳Called by: F145:_generate_next_question
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F145:_generate_next_question]
---

F143│question_builder.py│1
---

F141│retriever.py│9
D: ●argu_god
F: get_best_counter(argument)
   ↳Called by: F145:_generate_next_question | Calls: F054:search_similar,F146:search_similar
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F145:_generate_next_question]
---

F144│storage.py│48
D: ●datetime,json,os
F: load_state()
   ↳Called by: F139:debate_step
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F139:debate_step]
F: save_state(state)
   ↳Called by: F139:debate_step
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F139:debate_step]
F: load_beliefs()
   ↳Called by: F139:debate_step
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F139:debate_step]
F: save_beliefs(data)
   ↳Called by: F139:debate_step
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F139:debate_step]
F: add_response(state,argument_name,choice,custom_text)
   ↳Called by: F139:debate_step
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F139:debate_step]
---

F146│vector_store.py│60
D: ●chromadb,functools,hashlib,numpy,sentence_transformers
F: _get_client()
   ↳Called by: F146:_get_collection
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F146:_get_collection]
F: _get_collection()
   ↳Called by: F146:index_graph,F146:search_similar,F145:_store_user_knowledge | Calls: F146:_get_client
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F146:index_graph],[F146:search_similar],[F145:_store_user_knowledge]
F: _get_model()
   ↳Called by: F146:embed
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F146:embed]
F: embed(text)
   ↳Called by: F146:index_graph,F147:is_similar_to_any,F146:search_similar | Calls: F054:_get_model,F146:_get_model
   ↳Impact: 🔴HIGH (4 dependents) | Breaks: [F146:index_graph],[F147:is_similar_to_any],[F146:search_similar]
F: index_graph(graph)
   ↳Called by: F139:debate_expand,F142:expand_topic | Calls: F054:_get_collection,F146:_get_collection,F146:embed
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F139:debate_expand],[F142:expand_topic]
F: search_similar(argument,top_k)
   ↳Called by: F141:get_best_counter | Calls: F054:_get_collection,F146:_get_collection,F146:embed
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F141:get_best_counter]
---
