# 📂 engine
Generated: 2026-07-21 18:31:40
Files: 8

---

F292│debate.py│348
D: ►F012,F239,F293,F294,F298,F299 ●agent_core,kernel,os,threading,typing,+4
F: _populate_semantic_memory(graph,topic)
   ↳Called by: F292:debate_step | Calls: F298:index_graph
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F292:debate_step]
F: _build_debate_question(argument,counter)→dict
   ↳Called by: F292:debate_step
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F292:debate_step]
F: _build_knowledge_context(topic)→dict
   ↳Called by: F292:_generate_next_question
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F292:_generate_next_question]
F: _check_novelty(text,threshold)→bool
   ↳Calls: F299:is_similar_to_any
F: _store_user_knowledge(argument_name,stance,confidence,topic,user_text)
   ↳Called by: F292:debate_step | Calls: F094:_get_collection,F298:_get_collection,F298:embed
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F292:debate_step]
F: _generate_next_question(topic,state,beliefs,graph,llm_input)→Any
   ↳Called by: F292:debate_step | Calls: F292:_get_untouched_knowledge,F294:get_best_counter,F293:get_next_argument
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F292:debate_step]
F: _get_untouched_knowledge(topic,state,beliefs)→Optional[dict]
   ↳Called by: F292:_generate_next_question
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F292:_generate_next_question]
F: debate_step(raw_input)→str
   ↳Calls: F316:_populate_semantic_memory,F297:load_beliefs,F292:_store_user_knowledge
---

F299│dedup.py│16
D: ►F298 ●numpy
F: cosine_similarity(a,b)
   ↳Called by: F299:is_similar_to_any
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F299:is_similar_to_any]
F: is_similar_to_any(candidate_text,existing_texts,threshold)
   ↳Called by: F292:_check_novelty,F292:_generate_next_question | Calls: F299:cosine_similarity,F298:embed
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F292:_check_novelty],[F292:_generate_next_question]
---

F295│expand.py│28
D: ►F293,F298 ●json,os
F: expand_topic(topic,new_nodes,new_edges)→dict
   ↳Calls: F293:load_graph,F298:index_graph
---

F293│loop.py│25
D: ●json,os
F: load_graph(topic)
   ↳Called by: F292:debate_step,F295:expand_topic
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F292:debate_step],[F295:expand_topic]
F: get_next_argument(topic,graph,state,beliefs)
   ↳Called by: F292:_generate_next_question
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F292:_generate_next_question]
---

F296│question_builder.py│1
---

F294│retriever.py│9
D: ●argu_god
F: get_best_counter(argument)
   ↳Called by: F292:_generate_next_question | Calls: F094:search_similar,F298:search_similar
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F292:_generate_next_question]
---

F297│storage.py│44
D: ●datetime,json,os
F: load_state()
   ↳Called by: F292:debate_step
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F292:debate_step]
F: save_state(state)
   ↳Called by: F292:debate_step
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F292:debate_step]
F: load_beliefs()
   ↳Called by: F292:debate_step
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F292:debate_step]
F: save_beliefs(data)
   ↳Called by: F292:debate_step
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F292:debate_step]
F: add_response(state,argument_name,choice,custom_text)
   ↳Called by: F292:debate_step
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F292:debate_step]
---

F298│vector_store.py│50
D: ●chromadb,functools,sentence_transformers
F: _get_client()
   ↳Called by: F298:_get_collection
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F298:_get_collection]
F: _get_collection()
   ↳Called by: F298:search_similar,F316:test_populates_vector_store,F298:index_graph | Calls: F298:_get_client
   ↳Impact: 🔴HIGH (4 dependents) | Breaks: [F298:search_similar],[F316:test_populates_vector_store],[F298:index_graph]
F: _get_model()
   ↳Called by: F298:embed
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F298:embed]
F: embed(text)
   ↳Called by: F298:search_similar,F299:is_similar_to_any,F298:index_graph | Calls: F298:_get_model,F094:_get_model
   ↳Impact: 🔴HIGH (4 dependents) | Breaks: [F298:search_similar],[F299:is_similar_to_any],[F298:index_graph]
F: index_graph(graph)
   ↳Called by: F292:_populate_semantic_memory,F316:_populate_semantic_memory,F295:expand_topic | Calls: F094:_get_collection,F298:_get_collection,F298:embed
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F292:_populate_semantic_memory],[F316:_populate_semantic_memory],[F295:expand_topic]
F: search_similar(argument,top_k)
   ↳Called by: F294:get_best_counter | Calls: F094:_get_collection,F298:_get_collection,F298:embed
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F294:get_best_counter]
---
