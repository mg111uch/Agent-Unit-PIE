# 📂 schemas
Generated: 2026-07-21 18:31:40
Files: 8

---

F073│event_schema.py│196
D: ●__future__,dataclasses,datetime,typing,uuid
C: EventSource│[]
C: EventParticipant│[]
C: EventLocation│[]
C: EventMetrics│[]
C: EventEvidence│[]
C: EventRelation│[]
C: EventMetadata│[]
C: EventSchema│[to_dict,create,add_participant,add_evidence,add_relation,add_generated_signal,add_tag,set_location,deactivate,update_timestamp]
F: generate_id(prefix)→str
   ↳Called by: F109:emit_event,F068:generate_hypothesis_id,F068:generate_signal_id
   ↳Impact: 🔴HIGH (20 dependents) | Breaks: [F109:emit_event],[F068:generate_hypothesis_id],[F068:generate_signal_id]
F: utc_now()→str
   ↳Called by: F072:update_timestamp,F073:update_timestamp,F076:mark_interaction
   ↳Impact: 🔴HIGH (9 dependents) | Breaks: [F072:update_timestamp],[F073:update_timestamp],[F076:mark_interaction]
C: EventSource│[]
C: EventParticipant│[]
C: EventLocation│[]
C: EventMetrics│[]
C: EventEvidence│[]
C: EventRelation│[]
C: EventMetadata│[]
C: EventSchema│[to_dict,create,add_participant,add_evidence,add_relation,add_generated_signal,add_tag,set_location,deactivate,update_timestamp]
   F: to_dict(self)→Any
   F: create(cls,event_type,title,description,category,subtype,source_type,source_id,source_name)→'EventSchema'
   ↳Calls: F073:generate_id,F074:generate_id,F076:generate_id
   F: add_participant(self,unit_id,unit_type,role,impact_score)
   F: add_evidence(self,evidence_type,content,source_ref,confidence,metadata)
   ↳Calls: F073:generate_id,F074:generate_id,F076:generate_id
   F: add_relation(self,related_event_id,relation_type,strength)
   F: add_generated_signal(self,signal_id)
   F: add_tag(self,tag)
   F: set_location(self,name,location_id,latitude,longitude,region,country)
   F: deactivate(self)
   ↳Calls: F066:utc_now,F309:utc_now,F271:utc_now
   F: update_timestamp(self)
   ↳Calls: F066:utc_now,F309:utc_now,F271:utc_now
---

F069│hypothesis_schema.py│43
D: ●__future__,dataclasses,time,typing
C: HypothesisSchema│[to_dict]
C: HypothesisSchema│[to_dict]
   F: to_dict(self)→Any
---

F071│memory_schema.py│0
---

F072│pattern_schema.py│224
D: ●__future__,dataclasses,datetime,typing,uuid
C: PatternSource│[]
C: PatternSignalRef│[]
C: PatternEventRef│[]
C: PatternUnitRef│[]
C: PatternMetrics│[]
C: PatternTimeline│[]
C: PatternCausalLink│[]
C: PatternEvidence│[]
C: PatternMetadata│[]
C: PatternSchema│[to_dict,create,add_unit,add_signal,add_event,add_causal_link,add_evidence,add_tag,update_confidence,update_strength,+2]
F: generate_id(prefix)→str
   ↳Called by: F109:emit_event,F068:generate_hypothesis_id,F068:generate_signal_id
   ↳Impact: 🔴HIGH (20 dependents) | Breaks: [F109:emit_event],[F068:generate_hypothesis_id],[F068:generate_signal_id]
F: utc_now()→str
   ↳Called by: F072:update_timestamp,F073:update_timestamp,F076:mark_interaction
   ↳Impact: 🔴HIGH (9 dependents) | Breaks: [F072:update_timestamp],[F073:update_timestamp],[F076:mark_interaction]
C: PatternSource│[]
C: PatternSignalRef│[]
C: PatternEventRef│[]
C: PatternUnitRef│[]
C: PatternMetrics│[]
C: PatternTimeline│[]
C: PatternCausalLink│[]
C: PatternEvidence│[]
C: PatternMetadata│[]
C: PatternSchema│[to_dict,create,add_unit,add_signal,add_event,add_causal_link,add_evidence,add_tag,update_confidence,update_strength,+2]
   F: to_dict(self)→Any
   F: create(cls,pattern_type,title,description,category,subtype,source_type,source_id,source_name)→'PatternSchema'
   ↳Calls: F073:generate_id,F074:generate_id,F076:generate_id
   F: add_unit(self,unit_id,unit_type,role,influence_score)
   F: add_signal(self,signal_id,signal_type,weight,confidence)
   F: add_event(self,event_id,event_type,weight)
   F: add_causal_link(self,target_pattern_id,relation_type,strength,confidence)
   F: add_evidence(self,evidence_type,content,source_ref,confidence,metadata)
   ↳Calls: F073:generate_id,F074:generate_id,F076:generate_id
   F: add_tag(self,tag)
   F: update_confidence(self,confidence)
   F: update_strength(self,strength)
   F: deactivate(self)
   ↳Calls: F066:utc_now,F309:utc_now,F271:utc_now
   F: update_timestamp(self)
   ↳Calls: F066:utc_now,F309:utc_now,F271:utc_now
---

F076│relation_schema.py│144
D: ●__future__,dataclasses,datetime,typing,uuid
C: RelationEndpoint│[]
C: RelationMetrics│[]
C: RelationEvidence│[]
C: RelationTimeline│[]
C: RelationContext│[]
C: RelationMetadata│[]
C: RelationSchema│[to_dict,create,add_evidence,add_tag,add_related_event,add_related_signal,add_related_pattern,update_strength,update_confidence,mark_interaction,+1]
F: generate_id(prefix)→str
   ↳Called by: F109:emit_event,F068:generate_hypothesis_id,F068:generate_signal_id
   ↳Impact: 🔴HIGH (20 dependents) | Breaks: [F109:emit_event],[F068:generate_hypothesis_id],[F068:generate_signal_id]
F: utc_now()→str
   ↳Called by: F072:update_timestamp,F073:update_timestamp,F076:mark_interaction
   ↳Impact: 🔴HIGH (9 dependents) | Breaks: [F072:update_timestamp],[F073:update_timestamp],[F076:mark_interaction]
C: RelationEndpoint│[]
C: RelationMetrics│[]
C: RelationEvidence│[]
C: RelationTimeline│[]
C: RelationContext│[]
C: RelationMetadata│[]
C: RelationSchema│[to_dict,create,add_evidence,add_tag,add_related_event,add_related_signal,add_related_pattern,update_strength,update_confidence,mark_interaction,+1]
   F: to_dict(self)→Any
   F: create(cls,relation_type,source_unit_id,source_unit_type,target_unit_id,target_unit_type,direction,description)→'RelationSchema'
   ↳Calls: F073:generate_id,F074:generate_id,F076:generate_id
   F: add_evidence(self,evidence_type,content,source_ref,confidence,metadata)
   ↳Calls: F073:generate_id,F074:generate_id,F076:generate_id
   F: add_tag(self,tag)
   F: add_related_event(self,event_id)
   F: add_related_signal(self,signal_id)
   F: add_related_pattern(self,pattern_id)
   F: update_strength(self,strength)
   F: update_confidence(self,confidence)
   F: mark_interaction(self)
   ↳Calls: F066:utc_now,F309:utc_now,F271:utc_now
   F: deactivate(self)
   ↳Calls: F066:utc_now,F309:utc_now,F271:utc_now
---

F075│signal_schema.py│115
D: ●__future__,dataclasses,datetime,typing,uuid
C: SignalSource│[]
C: SignalEvidence│[]
C: SignalContext│[]
C: SignalMetrics│[]
C: SignalMetadata│[]
C: SignalSchema│[to_dict,create,add_evidence,add_related_unit,add_related_event,add_tag,update_confidence,deactivate]
F: generate_id(prefix)→str
   ↳Called by: F109:emit_event,F068:generate_hypothesis_id,F068:generate_signal_id
   ↳Impact: 🔴HIGH (20 dependents) | Breaks: [F109:emit_event],[F068:generate_hypothesis_id],[F068:generate_signal_id]
F: utc_now()→str
   ↳Called by: F072:update_timestamp,F073:update_timestamp,F076:mark_interaction
   ↳Impact: 🔴HIGH (9 dependents) | Breaks: [F072:update_timestamp],[F073:update_timestamp],[F076:mark_interaction]
C: SignalSource│[]
C: SignalEvidence│[]
C: SignalContext│[]
C: SignalMetrics│[]
C: SignalMetadata│[]
C: SignalSchema│[to_dict,create,add_evidence,add_related_unit,add_related_event,add_tag,update_confidence,deactivate]
   F: to_dict(self)→Any
   F: create(cls,signal_type,value,category,subtype,source_type,source_id,source_name)→'SignalSchema'
   ↳Calls: F073:generate_id,F074:generate_id,F076:generate_id
   F: add_evidence(self,evidence_type,content,confidence,metadata)
   ↳Calls: F073:generate_id,F074:generate_id,F076:generate_id
   F: add_related_unit(self,unit_id)
   F: add_related_event(self,event_id)
   F: add_tag(self,tag)
   F: update_confidence(self,confidence)
   ↳Calls: F066:utc_now,F309:utc_now,F271:utc_now
   F: deactivate(self)
   ↳Calls: F066:utc_now,F309:utc_now,F271:utc_now
---

F070│simulation_schema.py│0
---

F074│unit_schema.py│144
D: ●__future__,dataclasses,datetime,typing,uuid
C: UnitIdentity│[]
C: UnitState│[]
C: UnitResources│[add,consume]
C: UnitTraits│[]
C: UnitBehavior│[]
C: UnitSignalRef│[]
C: UnitRelation│[]
C: UnitMemory│[]
C: UnitMetadata│[]
C: UnitSchema│[to_dict,create,add_behavior,add_signal,add_relation,update_timestamp]
F: generate_id(prefix)→str
   ↳Called by: F109:emit_event,F068:generate_hypothesis_id,F068:generate_signal_id
   ↳Impact: 🔴HIGH (20 dependents) | Breaks: [F109:emit_event],[F068:generate_hypothesis_id],[F068:generate_signal_id]
F: utc_now()→str
   ↳Called by: F072:update_timestamp,F073:update_timestamp,F076:mark_interaction
   ↳Impact: 🔴HIGH (9 dependents) | Breaks: [F072:update_timestamp],[F073:update_timestamp],[F076:mark_interaction]
C: UnitIdentity│[]
C: UnitState│[]
C: UnitResources│[add,consume]
   F: add(self,key,value)
   ↳Called by: F240:subscribe,F091:add_edge,F219:_detect_circular_dependencies
   ↳Impact: 🔴HIGH (11 dependents) | Breaks: [F240:subscribe],[F091:add_edge],[F219:_detect_circular_dependencies]
   F: consume(self,key,value)
C: UnitTraits│[]
C: UnitBehavior│[]
C: UnitSignalRef│[]
C: UnitRelation│[]
C: UnitMemory│[]
C: UnitMetadata│[]
C: UnitSchema│[to_dict,create,add_behavior,add_signal,add_relation,update_timestamp]
   F: to_dict(self)→Any
   F: create(cls,unit_type,name,source)→'UnitSchema'
   ↳Calls: F073:generate_id,F074:generate_id,F076:generate_id
   F: add_behavior(self,behavior_type,priority,metadata)
   ↳Calls: F073:generate_id,F074:generate_id,F076:generate_id
   F: add_signal(self,signal_id,signal_type,confidence)
   F: add_relation(self,relation_type,target_unit_id,strength,metadata)
   ↳Calls: F073:generate_id,F074:generate_id,F076:generate_id
   F: update_timestamp(self)
   ↳Calls: F066:utc_now,F309:utc_now,F271:utc_now
---
