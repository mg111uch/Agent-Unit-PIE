# 📂 schemas
Generated: 2026-07-27 19:23:22
Files: 8

---

F034│event_schema.py│196
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
   ↳Called by: F029:generate_relation_id,F034:add_evidence,F034:create
   ↳Impact: 🔴HIGH (20 dependents) | Breaks: [F029:generate_relation_id],[F034:add_evidence],[F034:create]
F: utc_now()→str
   ↳Called by: F036:deactivate,F036:update_confidence,F033:update_timestamp
   ↳Impact: 🔴HIGH (9 dependents) | Breaks: [F036:deactivate],[F036:update_confidence],[F033:update_timestamp]
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
   ↳Calls: F029:generate_id,F036:generate_id,F035:generate_id
   F: add_participant(self,unit_id,unit_type,role,impact_score)
   F: add_evidence(self,evidence_type,content,source_ref,confidence,metadata)
   ↳Calls: F029:generate_id,F036:generate_id,F035:generate_id
   F: add_relation(self,related_event_id,relation_type,strength)
   F: add_generated_signal(self,signal_id)
   F: add_tag(self,tag)
   F: set_location(self,name,location_id,latitude,longitude,region,country)
   F: deactivate(self)
   ↳Calls: F152:utc_now,F033:utc_now,F122:utc_now
   F: update_timestamp(self)
   ↳Calls: F152:utc_now,F033:utc_now,F122:utc_now
---

F030│hypothesis_schema.py│43
D: ●__future__,dataclasses,time,typing
C: HypothesisSchema│[to_dict]
C: HypothesisSchema│[to_dict]
   F: to_dict(self)→Any
---

F032│memory_schema.py│0
---

F033│pattern_schema.py│224
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
   ↳Called by: F029:generate_relation_id,F034:add_evidence,F034:create
   ↳Impact: 🔴HIGH (20 dependents) | Breaks: [F029:generate_relation_id],[F034:add_evidence],[F034:create]
F: utc_now()→str
   ↳Called by: F036:deactivate,F036:update_confidence,F033:update_timestamp
   ↳Impact: 🔴HIGH (9 dependents) | Breaks: [F036:deactivate],[F036:update_confidence],[F033:update_timestamp]
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
   ↳Calls: F029:generate_id,F036:generate_id,F035:generate_id
   F: add_unit(self,unit_id,unit_type,role,influence_score)
   F: add_signal(self,signal_id,signal_type,weight,confidence)
   F: add_event(self,event_id,event_type,weight)
   F: add_causal_link(self,target_pattern_id,relation_type,strength,confidence)
   F: add_evidence(self,evidence_type,content,source_ref,confidence,metadata)
   ↳Calls: F029:generate_id,F036:generate_id,F035:generate_id
   F: add_tag(self,tag)
   F: update_confidence(self,confidence)
   F: update_strength(self,strength)
   F: deactivate(self)
   ↳Calls: F152:utc_now,F033:utc_now,F122:utc_now
   F: update_timestamp(self)
   ↳Calls: F152:utc_now,F033:utc_now,F122:utc_now
---

F037│relation_schema.py│144
D: ●__future__,dataclasses,datetime,typing,uuid
C: RelationEndpoint│[]
C: RelationMetrics│[]
C: RelationEvidence│[]
C: RelationTimeline│[]
C: RelationContext│[]
C: RelationMetadata│[]
C: RelationSchema│[to_dict,create,add_evidence,add_tag,add_related_event,add_related_signal,add_related_pattern,update_strength,update_confidence,mark_interaction,+1]
F: generate_id(prefix)→str
   ↳Called by: F029:generate_relation_id,F034:add_evidence,F034:create
   ↳Impact: 🔴HIGH (20 dependents) | Breaks: [F029:generate_relation_id],[F034:add_evidence],[F034:create]
F: utc_now()→str
   ↳Called by: F036:deactivate,F036:update_confidence,F033:update_timestamp
   ↳Impact: 🔴HIGH (9 dependents) | Breaks: [F036:deactivate],[F036:update_confidence],[F033:update_timestamp]
C: RelationEndpoint│[]
C: RelationMetrics│[]
C: RelationEvidence│[]
C: RelationTimeline│[]
C: RelationContext│[]
C: RelationMetadata│[]
C: RelationSchema│[to_dict,create,add_evidence,add_tag,add_related_event,add_related_signal,add_related_pattern,update_strength,update_confidence,mark_interaction,+1]
   F: to_dict(self)→Any
   F: create(cls,relation_type,source_unit_id,source_unit_type,target_unit_id,target_unit_type,direction,description)→'RelationSchema'
   ↳Calls: F029:generate_id,F036:generate_id,F035:generate_id
   F: add_evidence(self,evidence_type,content,source_ref,confidence,metadata)
   ↳Calls: F029:generate_id,F036:generate_id,F035:generate_id
   F: add_tag(self,tag)
   F: add_related_event(self,event_id)
   F: add_related_signal(self,signal_id)
   F: add_related_pattern(self,pattern_id)
   F: update_strength(self,strength)
   F: update_confidence(self,confidence)
   F: mark_interaction(self)
   ↳Calls: F152:utc_now,F033:utc_now,F122:utc_now
   F: deactivate(self)
   ↳Calls: F152:utc_now,F033:utc_now,F122:utc_now
---

F036│signal_schema.py│115
D: ●__future__,dataclasses,datetime,typing,uuid
C: SignalSource│[]
C: SignalEvidence│[]
C: SignalContext│[]
C: SignalMetrics│[]
C: SignalMetadata│[]
C: SignalSchema│[to_dict,create,add_evidence,add_related_unit,add_related_event,add_tag,update_confidence,deactivate]
F: generate_id(prefix)→str
   ↳Called by: F029:generate_relation_id,F034:add_evidence,F034:create
   ↳Impact: 🔴HIGH (20 dependents) | Breaks: [F029:generate_relation_id],[F034:add_evidence],[F034:create]
F: utc_now()→str
   ↳Called by: F036:deactivate,F036:update_confidence,F033:update_timestamp
   ↳Impact: 🔴HIGH (9 dependents) | Breaks: [F036:deactivate],[F036:update_confidence],[F033:update_timestamp]
C: SignalSource│[]
C: SignalEvidence│[]
C: SignalContext│[]
C: SignalMetrics│[]
C: SignalMetadata│[]
C: SignalSchema│[to_dict,create,add_evidence,add_related_unit,add_related_event,add_tag,update_confidence,deactivate]
   F: to_dict(self)→Any
   F: create(cls,signal_type,value,category,subtype,source_type,source_id,source_name)→'SignalSchema'
   ↳Calls: F029:generate_id,F036:generate_id,F035:generate_id
   F: add_evidence(self,evidence_type,content,confidence,metadata)
   ↳Calls: F029:generate_id,F036:generate_id,F035:generate_id
   F: add_related_unit(self,unit_id)
   F: add_related_event(self,event_id)
   F: add_tag(self,tag)
   F: update_confidence(self,confidence)
   ↳Calls: F152:utc_now,F033:utc_now,F122:utc_now
   F: deactivate(self)
   ↳Calls: F152:utc_now,F033:utc_now,F122:utc_now
---

F031│simulation_schema.py│0
---

F035│unit_schema.py│144
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
   ↳Called by: F029:generate_relation_id,F034:add_evidence,F034:create
   ↳Impact: 🔴HIGH (20 dependents) | Breaks: [F029:generate_relation_id],[F034:add_evidence],[F034:create]
F: utc_now()→str
   ↳Called by: F036:deactivate,F036:update_confidence,F033:update_timestamp
   ↳Impact: 🔴HIGH (9 dependents) | Breaks: [F036:deactivate],[F036:update_confidence],[F033:update_timestamp]
C: UnitIdentity│[]
C: UnitState│[]
C: UnitResources│[add,consume]
   F: add(self,key,value)
   ↳Called by: F090:_build_variable_maps,F052:add_node,F052:add_edge
   ↳Impact: 🔴HIGH (7 dependents) | Breaks: [F090:_build_variable_maps],[F052:add_node],[F052:add_edge]
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
   ↳Calls: F029:generate_id,F036:generate_id,F035:generate_id
   F: add_behavior(self,behavior_type,priority,metadata)
   ↳Calls: F029:generate_id,F036:generate_id,F035:generate_id
   F: add_signal(self,signal_id,signal_type,confidence)
   F: add_relation(self,relation_type,target_unit_id,strength,metadata)
   ↳Calls: F029:generate_id,F036:generate_id,F035:generate_id
   F: update_timestamp(self)
   ↳Calls: F152:utc_now,F033:utc_now,F122:utc_now
---
