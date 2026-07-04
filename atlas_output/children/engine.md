# 📂 engine
Generated: 2026-07-04 15:14:21
Files: 8

---

F005│analyzer.py│14
F: detect_contradictions(beliefs,graph)
   ↳Called by: F003:run_explore_loop
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F003:run_explore_loop]
---

F008│cli.py│9
D: ●argu_god,json,os
F: argu_cli(mode,topic)
   ↳Calls: F003:run_explore_loop
---

F009│kernel_bridge.py│418
D: ●datetime,json,os,sys,uuid,+1
F: _get_session_path(session_id)
   ↳Called by: F009:save_debate_session,F009:load_debate_session
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F009:save_debate_session],[F009:load_debate_session]
F: save_debate_session(topic,state,beliefs,session_id)→str
   ↳Called by: F003:run_explore_loop | Calls: F009:_get_session_path
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F003:run_explore_loop]
   S: Save debate session state.
F: load_debate_session(session_id)→dict
   ↳Called by: F003:run_explore_loop | Calls: F009:list_debate_sessions,F009:_get_session_path
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F003:run_explore_loop]
   S: Load debate session state. If session_id is None, loads most recent.
F: list_debate_sessions()→list
   ↳Called by: F009:load_debate_session,F009:get_current_session_info
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F009:load_debate_session],[F009:get_current_session_info]
   S: List all saved debate sessions.
F: get_current_session_info()→dict
   ↳Called by: F003:run_explore_loop | Calls: F009:list_debate_sessions
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F003:run_explore_loop]
   S: Get info about current/most recent session.
F: emit_belief_signal(argument_name,stance,confidence,topic)→None
   ↳Called by: F003:run_explore_loop
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F003:run_explore_loop]
F: emit_confidence_signal(argument_name,old_confidence,new_confidence,topic)→None
   ↳Called by: F003:run_explore_loop
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F003:run_explore_loop]
F: emit_contradiction_signal(contradicted_arguments,topic)→None
   ↳Called by: F003:run_explore_loop
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F003:run_explore_loop]
F: emit_topic_signal(topic,argument_count,action)→None
   ↳Called by: F003:run_explore_loop
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F003:run_explore_loop]
F: create_belief_hypothesis(argument_name,stance,confidence,topic)→str
   ↳Called by: F003:run_explore_loop
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F003:run_explore_loop]
   S: Create hypothesis from user belief stance.
F: add_belief_evidence(hypothesis_id,argument_name,supports)→None
   ↳Called by: F003:run_explore_loop
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F003:run_explore_loop]
   S: Add supporting or contradicting evidence to hypothesis.
F: validate_belief_hypothesis(hypothesis_id)→dict
   ↳Called by: F003:run_explore_loop
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F003:run_explore_loop]
   S: Validate a belief hypothesis.
F: get_hypothesis_for_argument(argument_name,topic)→str
   ↳Called by: F003:run_explore_loop
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F003:run_explore_loop]
   S: Get or create hypothesis for argument.
F: get_belief_summary(topic)→list
   S: Get summary of all belief hypotheses for topic.
F: emit_debate_event(event_type,topic,description,metadata)→None
   ↳Called by: F009:emit_argument_viewed_event,F009:emit_session_end_event,F009:emit_belief_changed_event
   ↳Impact: 🔴HIGH (6 dependents) | Breaks: [F009:emit_argument_viewed_event],[F009:emit_session_end_event],[F009:emit_belief_changed_event]
   S: Emit debate event for timeline tracking.
F: emit_session_start_event(topic,is_resume)→None
   ↳Called by: F003:run_explore_loop | Calls: F009:emit_debate_event
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F003:run_explore_loop]
   S: Emit session start or resume event.
F: emit_argument_viewed_event(topic,argument_name)→None
   ↳Called by: F003:run_explore_loop | Calls: F009:emit_debate_event
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F003:run_explore_loop]
   S: Emit event when argument is shown to user.
F: emit_user_response_event(topic,argument_name,choice,stance)→None
   ↳Called by: F003:run_explore_loop | Calls: F009:emit_debate_event
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F003:run_explore_loop]
   S: Emit event when user responds.
F: emit_belief_changed_event(topic,argument_name,old_stance,new_stance)→None
   ↳Called by: F003:run_explore_loop | Calls: F009:emit_debate_event
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F003:run_explore_loop]
   S: Emit event when belief changes.
F: emit_contradiction_event(topic,arguments)→None
   ↳Called by: F003:run_explore_loop | Calls: F009:emit_debate_event
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F003:run_explore_loop]
   S: Emit event when contradiction detected.
---

F003│loop.py│194
D: ●argu_god,datetime,json,os
F: load_graph(topic)
   ↳Called by: F003:run_explore_loop
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F003:run_explore_loop]
F: get_next_argument(topic,graph,state,beliefs)
   ↳Called by: F003:run_explore_loop
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F003:run_explore_loop]
F: get_user_choice()
   ↳Called by: F003:run_explore_loop
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F003:run_explore_loop]
F: map_choice_to_stance(choice)
   ↳Called by: F003:run_explore_loop
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F003:run_explore_loop]
F: run_explore_loop(topic)
   ↳Called by: F008:argu_cli | Calls: F007:save_beliefs,F003:map_choice_to_stance,F006:build_question
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F008:argu_cli]
---

F006│question_builder.py│18
F: build_question(argument,counter_argument)
   ↳Called by: F003:run_explore_loop
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F003:run_explore_loop]
---

F004│retriever.py│34
D: ●argu_god
F: index_arguments(graph)
   ↳Called by: F003:run_explore_loop
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F003:run_explore_loop]
F: get_counter_argument(argument,index)
   ↳Called by: F003:run_explore_loop
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F003:run_explore_loop]
F: get_best_counter(argument)
   ↳Called by: F003:run_explore_loop | Calls: F010:search_similar
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F003:run_explore_loop]
---

F007│storage.py│44
D: ●datetime,json,os
F: load_state()
   ↳Called by: F003:run_explore_loop
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F003:run_explore_loop]
F: save_state(state)
   ↳Called by: F003:run_explore_loop
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F003:run_explore_loop]
F: load_beliefs()
   ↳Called by: F003:run_explore_loop
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F003:run_explore_loop]
F: save_beliefs(data)
   ↳Called by: F003:run_explore_loop
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F003:run_explore_loop]
F: add_response(state,argument_name,choice,custom_text)
   ↳Called by: F003:run_explore_loop
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F003:run_explore_loop]
---

F010│vector_store.py│32
D: ●chromadb,sentence_transformers
F: embed(text)
   ↳Called by: F010:index_graph,F010:search_similar
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F010:index_graph],[F010:search_similar]
F: index_graph(graph)
   ↳Called by: F003:run_explore_loop | Calls: F010:embed
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F003:run_explore_loop]
F: search_similar(argument,top_k)
   ↳Called by: F004:get_best_counter | Calls: F010:embed
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F004:get_best_counter]
---
