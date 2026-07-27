# 📂 engine
Generated: 2026-07-27 19:23:22
Files: 9

---

F140│debate.py│306
D: ►F011,F141,F145,F146,F147,F148 ●agent_core,json,kernel,threading,time,+4
F: _populate_semantic_memory(graph,topic)
   ↳Called by: F140:debate_step
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F140:debate_step]
   S: Deprecated — topics now write directly to SQLite via debate_expand/import_topic.
   S: Kept as no-op for backward compatibility during migration.
F: _build_debate_question(argument,counter)→dict
   ↳Called by: F140:debate_step
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F140:debate_step]
F: debate_step(raw_input)→str
   ↳Calls: F011:emit_confidence_signal,F146:_generate_next_question,F011:emit_belief_signal
F: debate_expand(topic,llm_output)→dict
   ↳Calls: F148:is_similar_to_any,F147:index_graph
   S: Generate new arguments via LLM and write directly to semantic_memory SQLite tables.
   S: Returns {node_id, name} on success, or {error: ...} on failure.
F: export_topic(topic_id)→dict
   S: Query semantic_memory for all nodes/edges with the given topic_id.
   S: Returns a JSON-serializable dict matching the old graph.json schema.
F: import_topic(data_dict,topic_id)→str
   S: Bulk-insert nodes/edges from a graph.json dict into semantic_memory.
   S: Returns the topic_id used (auto-generated if not provided).
---

F146│debate_helpers.py│158
D: ►F139,F141,F142,F148 ●datetime,kernel,modules,typing
F: _build_knowledge_context(topic)→dict
   ↳Called by: F146:_generate_next_question
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F146:_generate_next_question]
F: _check_novelty(text,threshold)→bool
   ↳Calls: F148:is_similar_to_any
F: _store_user_knowledge(argument_name,stance,confidence,topic,user_text)
   ↳Called by: F140:debate_step | Calls: F147:embed,F147:_get_collection,F055:_get_collection
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F140:debate_step]
F: _get_untouched_knowledge(topic,state,beliefs)→Optional[dict]
   ↳Called by: F146:_generate_next_question
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F146:_generate_next_question]
F: _generate_next_question(topic,state,beliefs,graph,llm_input)→Any
   ↳Called by: F140:debate_step | Calls: F146:_get_untouched_knowledge,F148:is_similar_to_any,F142:get_best_counter
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F140:debate_step]
---

F148│dedup.py│16
D: ►F147 ●numpy
F: cosine_similarity(a,b)
   ↳Called by: F148:is_similar_to_any
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F148:is_similar_to_any]
F: is_similar_to_any(candidate_text,existing_texts,threshold)
   ↳Called by: F146:_check_novelty,F146:_generate_next_question,F140:debate_expand | Calls: F147:embed,F148:cosine_similarity
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F146:_check_novelty],[F146:_generate_next_question],[F140:debate_expand]
---

F143│expand.py│28
D: ►F141,F147 ●json,os
F: expand_topic(topic,new_nodes,new_edges)→dict
   ↳Calls: F147:index_graph,F141:load_graph
---

F141│loop.py│28
D: ●json,os
F: load_graph(topic)
   ↳Called by: F143:expand_topic,F140:debate_step
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F143:expand_topic],[F140:debate_step]
F: get_next_argument(topic,graph,state,beliefs)
   ↳Called by: F146:_generate_next_question
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F146:_generate_next_question]
---

F144│question_builder.py│1
---

F142│retriever.py│9
D: ●argu_god
F: get_best_counter(argument)
   ↳Called by: F146:_generate_next_question | Calls: F147:search_similar,F055:search_similar
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F146:_generate_next_question]
---

F145│storage.py│48
D: ●datetime,json,os
F: load_state()
   ↳Called by: F140:debate_step
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F140:debate_step]
F: save_state(state)
   ↳Called by: F140:debate_step
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F140:debate_step]
F: load_beliefs()
   ↳Called by: F140:debate_step
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F140:debate_step]
F: save_beliefs(data)
   ↳Called by: F140:debate_step
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F140:debate_step]
F: add_response(state,argument_name,choice,custom_text)
   ↳Called by: F140:debate_step
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F140:debate_step]
---

F147│vector_store.py│60
D: ●chromadb,functools,hashlib,numpy,sentence_transformers
F: _get_client()
   ↳Called by: F147:_get_collection
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F147:_get_collection]
F: _get_collection()
   ↳Called by: F147:index_graph,F147:search_similar,F146:_store_user_knowledge | Calls: F147:_get_client
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F147:index_graph],[F147:search_similar],[F146:_store_user_knowledge]
F: _get_model()
   ↳Called by: F147:embed
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F147:embed]
F: embed(text)
   ↳Called by: F148:is_similar_to_any,F147:index_graph,F147:search_similar | Calls: F147:_get_model,F055:_get_model
   ↳Impact: 🔴HIGH (4 dependents) | Breaks: [F148:is_similar_to_any],[F147:index_graph],[F147:search_similar]
F: index_graph(graph)
   ↳Called by: F143:expand_topic,F140:debate_expand | Calls: F147:embed,F147:_get_collection,F055:_get_collection
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F143:expand_topic],[F140:debate_expand]
F: search_similar(argument,top_k)
   ↳Called by: F142:get_best_counter | Calls: F147:embed,F147:_get_collection,F055:_get_collection
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F142:get_best_counter]
---
