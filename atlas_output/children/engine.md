# 📂 engine
Generated: 2026-07-17 18:00:11
Files: 7

---

F005│analyzer.py│14
F: detect_contradictions(beliefs,graph)
---

F008│kernel_bridge.py│418
D: ●datetime,json,kernel,os,uuid,+1
F: _get_session_path(session_id)
   ↳Called by: F008:save_debate_session,F008:load_debate_session
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F008:save_debate_session],[F008:load_debate_session]
F: save_debate_session(topic,state,beliefs,session_id)→str
   ↳Calls: F008:_get_session_path
   S: Save debate session state.
F: load_debate_session(session_id)→dict
   ↳Calls: F008:list_debate_sessions,F008:_get_session_path
   S: Load debate session state. If session_id is None, loads most recent.
F: list_debate_sessions()→list
   ↳Called by: F008:get_current_session_info,F008:load_debate_session
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F008:get_current_session_info],[F008:load_debate_session]
   S: List all saved debate sessions.
F: get_current_session_info()→dict
   ↳Calls: F008:list_debate_sessions
   S: Get info about current/most recent session.
F: emit_belief_signal(argument_name,stance,confidence,topic)→None
F: emit_confidence_signal(argument_name,old_confidence,new_confidence,topic)→None
F: emit_contradiction_signal(contradicted_arguments,topic)→None
F: emit_topic_signal(topic,argument_count,action)→None
F: create_belief_hypothesis(argument_name,stance,confidence,topic)→str
   S: Create hypothesis from user belief stance.
F: add_belief_evidence(hypothesis_id,argument_name,supports)→None
   S: Add supporting or contradicting evidence to hypothesis.
F: validate_belief_hypothesis(hypothesis_id)→dict
   S: Validate a belief hypothesis.
F: get_hypothesis_for_argument(argument_name,topic)→str
   S: Get or create hypothesis for argument.
F: get_belief_summary(topic)→list
   S: Get summary of all belief hypotheses for topic.
F: emit_debate_event(event_type,topic,description,metadata)→None
   ↳Called by: F008:emit_session_end_event,F008:emit_argument_viewed_event,F008:emit_user_response_event
   ↳Impact: 🔴HIGH (6 dependents) | Breaks: [F008:emit_session_end_event],[F008:emit_argument_viewed_event],[F008:emit_user_response_event]
   S: Emit debate event for timeline tracking.
F: emit_session_start_event(topic,is_resume)→None
   ↳Calls: F008:emit_debate_event
   S: Emit session start or resume event.
F: emit_argument_viewed_event(topic,argument_name)→None
   ↳Calls: F008:emit_debate_event
   S: Emit event when argument is shown to user.
F: emit_user_response_event(topic,argument_name,choice,stance)→None
   ↳Calls: F008:emit_debate_event
   S: Emit event when user responds.
F: emit_belief_changed_event(topic,argument_name,old_stance,new_stance)→None
   ↳Calls: F008:emit_debate_event
   S: Emit event when belief changes.
F: emit_contradiction_event(topic,arguments)→None
   ↳Calls: F008:emit_debate_event
   S: Emit event when contradiction detected.
---

F003│loop.py│34
D: ●json,os
F: load_graph(topic)
F: get_next_argument(topic,graph,state,beliefs)
F: map_choice_to_stance(choice)
---

F006│question_builder.py│36
F: build_question(argument,counter_argument)
F: build_structured_question(argument,counter_argument)
   S: Return a structured question dict for the ask_user_question tool format.
---

F004│retriever.py│34
D: ●argu_god
F: index_arguments(graph)
F: get_counter_argument(argument,index)
F: get_best_counter(argument)
   ↳Calls: F009:search_similar
---

F007│storage.py│44
D: ●datetime,json,os
F: load_state()
F: save_state(state)
F: load_beliefs()
F: save_beliefs(data)
F: add_response(state,argument_name,choice,custom_text)
---

F009│vector_store.py│43
D: ●chromadb,sentence_transformers
F: _get_client()
   ↳Called by: F009:_get_collection
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F009:_get_collection]
F: _get_collection()
   ↳Called by: F009:index_graph,F009:search_similar | Calls: F009:_get_client
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F009:index_graph],[F009:search_similar]
F: embed(text)
   ↳Called by: F009:index_graph,F009:search_similar
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F009:index_graph],[F009:search_similar]
F: index_graph(graph)
   ↳Calls: F009:_get_collection,F009:embed
F: search_similar(argument,top_k)
   ↳Called by: F004:get_best_counter | Calls: F009:_get_collection,F009:embed
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F004:get_best_counter]
---
