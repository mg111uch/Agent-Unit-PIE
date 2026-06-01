# 📂 signals
Generated: 2026-06-01 13:39:55
Files: 5

---

F059│belief_signal_handler.py│152
D: ●kernel
F: handle_belief_shift_signal(signal)
   S: Handler for belief_shift signals - tracks belief changes.
F: handle_contradiction_signal(signal)
   S: Handler for contradiction_detected signals.
F: handle_confidence_change_signal(signal)
   S: Handler for confidence_change signals.
F: register_handlers()
   S: Register all belief signal handlers.
F: unregister_handlers()
   S: Unregister all belief signal handlers.
---

F058│signal_engine.py│343
D: ●__future__,collections,kernel,traceback,typing
C: SignalEngine│[__init__,emit_signal,create_signal,register_handler,unregister_handler,_trigger_handlers,get_recent_signals,search_signals_by_source,search_signals_by_tag,aggregate_signal_values,+3]
---

F057│signal_extractor.py│0
---

F060│signal_router.py│0
---

F061│signal_validator.py│274
D: ●__future__,kernel,typing
C: SignalValidationResult│[__init__,add_error,add_warning,to_dict]
C: SignalValidator│[validate,_validate_basic_fields,_validate_signal_type,_validate_metrics,_validate_value,_validate_metadata,is_valid,assert_valid,log_validation_result]
---
