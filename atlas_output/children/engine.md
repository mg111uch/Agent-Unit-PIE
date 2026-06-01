# 📂 engine
Generated: 2026-06-01 13:39:55
Files: 8

---

F128│analyzer.py│14
F: detect_contradictions(beliefs,graph)
   ↳Called by: F126:run_explore_loop
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F126:run_explore_loop]
---

F131│cli.py│9
D: ●argu_god,json,os
F: argu_cli(mode,topic)
   ↳Calls: F126:run_explore_loop
---

F132│kernel_bridge.py│418
D: ●datetime,kernel,os,sys,uuid,+1
F: _get_session_path(session_id)
   ↳Called by: F132:save_debate_session,F132:load_debate_session
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F132:save_debate_session],[F132:load_debate_session]
F: save_debate_session(topic,state,beliefs,session_id)→str
   ↳Called by: F126:run_explore_loop | Calls: F132:_get_session_path
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F126:run_explore_loop]
   S: Save debate session state.
F: load_debate_session(session_id)→dict
   ↳Called by: F126:run_explore_loop | Calls: F132:_get_session_path,F132:list_debate_sessions
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F126:run_explore_loop]
   S: Load debate session state. If session_id is None, loads most recent.
F: list_debate_sessions()→list
   ↳Called by: F132:get_current_session_info,F132:load_debate_session
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F132:get_current_session_info],[F132:load_debate_session]
   S: List all saved debate sessions.
F: get_current_session_info()→dict
   ↳Called by: F126:run_explore_loop | Calls: F132:list_debate_sessions
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F126:run_explore_loop]
   S: Get info about current/most recent session.
F: emit_belief_signal(argument_name,stance,confidence,topic)→None
   ↳Called by: F126:run_explore_loop
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F126:run_explore_loop]
F: emit_confidence_signal(argument_name,old_confidence,new_confidence,topic)→None
   ↳Called by: F126:run_explore_loop
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F126:run_explore_loop]
F: emit_contradiction_signal(contradicted_arguments,topic)→None
   ↳Called by: F126:run_explore_loop
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F126:run_explore_loop]
F: emit_topic_signal(topic,argument_count,action)→None
   ↳Called by: F126:run_explore_loop
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F126:run_explore_loop]
F: create_belief_hypothesis(argument_name,stance,confidence,topic)→str
   ↳Called by: F126:run_explore_loop
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F126:run_explore_loop]
   S: Create hypothesis from user belief stance.
F: add_belief_evidence(hypothesis_id,argument_name,supports)→None
   ↳Called by: F126:run_explore_loop
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F126:run_explore_loop]
   S: Add supporting or contradicting evidence to hypothesis.
F: validate_belief_hypothesis(hypothesis_id)→dict
   ↳Called by: F126:run_explore_loop
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F126:run_explore_loop]
   S: Validate a belief hypothesis.
F: get_hypothesis_for_argument(argument_name,topic)→str
   ↳Called by: F126:run_explore_loop
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F126:run_explore_loop]
   S: Get or create hypothesis for argument.
F: get_belief_summary(topic)→list
   S: Get summary of all belief hypotheses for topic.
F: emit_debate_event(event_type,topic,description,metadata)→None
   ↳Called by: F132:emit_contradiction_event,F132:emit_user_response_event,F132:emit_session_start_event
   ↳Impact: 🔴HIGH (6 dependents) | Breaks: [F132:emit_contradiction_event],[F132:emit_user_response_event],[F132:emit_session_start_event]
   S: Emit debate event for timeline tracking.
F: emit_session_start_event(topic,is_resume)→None
   ↳Called by: F126:run_explore_loop | Calls: F132:emit_debate_event
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F126:run_explore_loop]
   S: Emit session start or resume event.
F: emit_argument_viewed_event(topic,argument_name)→None
   ↳Called by: F126:run_explore_loop | Calls: F132:emit_debate_event
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F126:run_explore_loop]
   S: Emit event when argument is shown to user.
F: emit_user_response_event(topic,argument_name,choice,stance)→None
   ↳Called by: F126:run_explore_loop | Calls: F132:emit_debate_event
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F126:run_explore_loop]
   S: Emit event when user responds.
F: emit_belief_changed_event(topic,argument_name,old_stance,new_stance)→None
   ↳Called by: F126:run_explore_loop | Calls: F132:emit_debate_event
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F126:run_explore_loop]
   S: Emit event when belief changes.
F: emit_contradiction_event(topic,arguments)→None
   ↳Called by: F126:run_explore_loop | Calls: F132:emit_debate_event
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F126:run_explore_loop]
   S: Emit event when contradiction detected.
---

F126│loop.py│194
D: ●argu_god,datetime,json,os
F: load_graph(topic)
   ↳Called by: F126:run_explore_loop
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F126:run_explore_loop]
F: get_next_argument(topic,graph,state,beliefs)
   ↳Called by: F126:run_explore_loop
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F126:run_explore_loop]
F: get_user_choice()
   ↳Called by: F126:run_explore_loop
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F126:run_explore_loop]
F: map_choice_to_stance(choice)
   ↳Called by: F126:run_explore_loop
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F126:run_explore_loop]
F: run_explore_loop(topic)
   ↳Called by: F131:argu_cli | Calls: F129:build_question,F127:get_best_counter,F132:save_debate_session
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F131:argu_cli]
---

F129│question_builder.py│18
F: build_question(argument,counter_argument)
   ↳Called by: F126:run_explore_loop
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F126:run_explore_loop]
---

F127│retriever.py│34
D: ●argu_god
F: index_arguments(graph)
   ↳Called by: F126:run_explore_loop
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F126:run_explore_loop]
F: get_counter_argument(argument,index)
   ↳Called by: F126:run_explore_loop
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F126:run_explore_loop]
F: get_best_counter(argument)
   ↳Called by: F126:run_explore_loop | Calls: F133:search_similar
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F126:run_explore_loop]
---

F130│storage.py│44
D: ●datetime,json,os
F: load_state()
   ↳Called by: F126:run_explore_loop
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F126:run_explore_loop]
F: save_state(state)
   ↳Called by: F126:run_explore_loop
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F126:run_explore_loop]
F: load_beliefs()
   ↳Called by: F126:run_explore_loop
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F126:run_explore_loop]
F: save_beliefs(data)
   ↳Called by: F126:run_explore_loop
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F126:run_explore_loop]
F: add_response(state,argument_name,choice,custom_text)
   ↳Called by: F126:run_explore_loop
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F126:run_explore_loop]
---

F133│vector_store.py│32
D: ●chromadb,sentence_transformers
F: embed(text)
   ↳Called by: F133:index_graph,F133:search_similar
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F133:index_graph],[F133:search_similar]
F: index_graph(graph)
   ↳Called by: F126:run_explore_loop | Calls: F133:embed
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F126:run_explore_loop]
F: search_similar(argument,top_k)
   ↳Called by: F127:get_best_counter | Calls: F133:embed
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F127:get_best_counter]
---
