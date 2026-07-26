# 📂 signals
Generated: 2026-07-26 16:20:18
Files: 4

---

F065│belief_signal_handler.py│159
D: ●kernel
F: handle_belief_shift_signal(signal)
   S: Handler for belief_shift signals - tracks belief changes.
F: handle_contradiction_signal(signal)
   S: Handler for contradiction_detected signals.
F: handle_confidence_change_signal(signal)
   S: Handler for confidence_change signals.
F: register_handlers()
   ↳Called by: F185:_register_kernel_tools
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F185:_register_kernel_tools]
   S: Register all belief signal handlers.
F: unregister_handlers()
   S: Unregister all belief signal handlers.
---

F064│signal_engine.py│311
D: ●__future__,collections,kernel,traceback,typing
C: SignalEngine│[__init__,emit_signal,create_signal,register_handler,unregister_handler,_trigger_handlers,get_recent_signals,search_signals_by_source,search_signals_by_tag,aggregate_signal_values,+3]
C: SignalEngine│[__init__,emit_signal,create_signal,register_handler,unregister_handler,_trigger_handlers,get_recent_signals,search_signals_by_source,search_signals_by_tag,aggregate_signal_values,+3]
   F: __init__(self)
   F: emit_signal(self,signal,persist,trigger_handlers,add_to_working_memory)→SignalSchema
   ↳Calls: F046:signal_type_exists
   F: create_signal(self,signal_type,source_unit_id,value,category,subtype,title,description,confidence,importance,tags,metadata,persist,trigger_handlers)→SignalSchema
   F: register_handler(self,signal_type,handler)
   F: unregister_handler(self,signal_type,handler)
   F: _trigger_handlers(self,signal)
   F: get_recent_signals(self,limit,signal_type)→List[SignalSchema]
   F: search_signals_by_source(self,source_unit_id)→List[SignalSchema]
   F: search_signals_by_tag(self,tag)→List[SignalSchema]
   F: aggregate_signal_values(self,signal_type)→Any
   F: signal_to_event(self,signal,event_type,title,description)→EventSchema
   F: stats(self)→Any
   F: clear_recent_signals(self)
---

F066│signal_router.py│0
---

F067│signal_validator.py│246
D: ●__future__,kernel,typing
C: SignalValidationResult│[__init__,add_error,add_warning,to_dict]
C: SignalValidator│[validate,_validate_basic_fields,_validate_signal_type,_validate_metrics,_validate_value,_validate_metadata,is_valid,assert_valid,log_validation_result]
C: SignalValidationResult│[__init__,add_error,add_warning,to_dict]
   F: __init__(self)
   F: add_error(self,message)
   F: add_warning(self,message)
   F: to_dict(self)→Any
C: SignalValidator│[validate,_validate_basic_fields,_validate_signal_type,_validate_metrics,_validate_value,_validate_metadata,is_valid,assert_valid,log_validation_result]
   F: validate(self,signal)→SignalValidationResult
   F: _validate_basic_fields(self,signal,result)
   F: _validate_signal_type(self,signal,result)
   ↳Calls: F046:get_signal_type,F046:signal_type_exists
   F: _validate_metrics(self,signal,result)
   F: _validate_value(self,signal,result)
   F: _validate_metadata(self,signal,result)
   F: is_valid(self,signal)→bool
   F: assert_valid(self,signal)
   F: log_validation_result(self,signal,result)
---
