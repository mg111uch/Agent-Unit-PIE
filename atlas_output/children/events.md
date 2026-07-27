# 📂 events
Generated: 2026-07-27 19:23:22
Files: 3

---

F070│event_engine.py│318
D: ●__future__,collections,kernel,traceback,typing
C: EventEngine│[__init__,emit_event,create_event,create_event_from_signal,register_handler,unregister_handler,_trigger_handlers,get_recent_events,search_events_by_source,search_events_by_tag,+3]
C: EventEngine│[__init__,emit_event,create_event,create_event_from_signal,register_handler,unregister_handler,_trigger_handlers,get_recent_events,search_events_by_source,search_events_by_tag,+3]
   F: __init__(self)
   F: emit_event(self,event,persist,trigger_handlers,add_to_working_memory,create_episode)→EventSchema
   ↳Calls: F029:generate_id,F036:generate_id,F035:generate_id
   F: create_event(self,event_type,title,description,source_unit_id,category,subtype,confidence,importance,urgency,tags,metadata,signal_references,persist,trigger_handlers)→EventSchema
   F: create_event_from_signal(self,signal,event_type,title,description,importance_multiplier)→EventSchema
   F: register_handler(self,event_type,handler)
   F: unregister_handler(self,event_type,handler)
   F: _trigger_handlers(self,event)
   F: get_recent_events(self,limit,event_type)→List[EventSchema]
   F: search_events_by_source(self,source_unit_id)→List[EventSchema]
   F: search_events_by_tag(self,tag)→List[EventSchema]
   F: link_events(self,parent_event,child_event)
   F: stats(self)→Any
   F: clear_recent_events(self)
---

F068│event_extractor.py│0
---

F069│timeline_engine.py│283
D: ●__future__,collections,dataclasses,kernel,time,+2
C: TimelineEntry│[to_dict]
C: TimelineEngine│[__init__,add_entry,add_event,add_signal,create_entry,get_entry,get_recent_entries,get_entries_between,search_by_type,search_by_tag,+5]
C: TimelineEntry│[to_dict]
   F: to_dict(self)→Any
C: TimelineEngine│[__init__,add_entry,add_event,add_signal,create_entry,get_entry,get_recent_entries,get_entries_between,search_by_type,search_by_tag,+5]
   F: __init__(self)
   F: add_entry(self,entry)
   F: add_event(self,event)→TimelineEntry
   F: add_signal(self,signal)→TimelineEntry
   F: create_entry(self,entry_id,entry_type,source_id,title,description,importance,timestamp,tags,metadata)→TimelineEntry
   F: get_entry(self,entry_id)→Optional[TimelineEntry]
   F: get_recent_entries(self,limit)→List[TimelineEntry]
   F: get_entries_between(self,start_timestamp,end_timestamp)→List[TimelineEntry]
   F: search_by_type(self,entry_type)→List[TimelineEntry]
   F: search_by_tag(self,tag)→List[TimelineEntry]
   F: search_by_source(self,source_id)→List[TimelineEntry]
   F: get_important_entries(self,min_importance)→List[TimelineEntry]
   F: remove_entry(self,entry_id)→bool
   F: stats(self)→Any
   F: clear(self)
---
