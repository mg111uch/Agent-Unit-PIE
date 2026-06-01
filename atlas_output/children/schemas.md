# 📂 schemas
Generated: 2026-06-01 13:39:55
Files: 8

---

F030│event_schema.py│230
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
   ↳Called by: F025:generate_signal_id,F029:add_evidence,F030:add_evidence
   ↳Impact: 🔴HIGH (20 dependents) | Breaks: [F025:generate_signal_id],[F029:add_evidence],[F030:add_evidence]
F: utc_now()→str
   ↳Called by: F033:deactivate,F032:deactivate,F029:deactivate
   ↳Impact: 🔴HIGH (9 dependents) | Breaks: [F033:deactivate],[F032:deactivate],[F029:deactivate]
---

F026│hypothesis_schema.py│0
---

F028│memory_schema.py│0
---

F029│pattern_schema.py│264
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
   ↳Called by: F025:generate_signal_id,F029:add_evidence,F030:add_evidence
   ↳Impact: 🔴HIGH (20 dependents) | Breaks: [F025:generate_signal_id],[F029:add_evidence],[F030:add_evidence]
F: utc_now()→str
   ↳Called by: F033:deactivate,F032:deactivate,F029:deactivate
   ↳Impact: 🔴HIGH (9 dependents) | Breaks: [F033:deactivate],[F032:deactivate],[F029:deactivate]
---

F033│relation_schema.py│172
D: ●__future__,dataclasses,datetime,typing,uuid
C: RelationEndpoint│[]
C: RelationMetrics│[]
C: RelationEvidence│[]
C: RelationTimeline│[]
C: RelationContext│[]
C: RelationMetadata│[]
C: RelationSchema│[to_dict,create,add_evidence,add_tag,add_related_event,add_related_signal,add_related_pattern,update_strength,update_confidence,mark_interaction,+1]
F: generate_id(prefix)→str
   ↳Called by: F025:generate_signal_id,F029:add_evidence,F030:add_evidence
   ↳Impact: 🔴HIGH (20 dependents) | Breaks: [F025:generate_signal_id],[F029:add_evidence],[F030:add_evidence]
F: utc_now()→str
   ↳Called by: F033:deactivate,F032:deactivate,F029:deactivate
   ↳Impact: 🔴HIGH (9 dependents) | Breaks: [F033:deactivate],[F032:deactivate],[F029:deactivate]
---

F032│signal_schema.py│115
D: ●__future__,dataclasses,datetime,typing,uuid
C: SignalSource│[]
C: SignalEvidence│[]
C: SignalContext│[]
C: SignalMetrics│[]
C: SignalMetadata│[]
C: SignalSchema│[to_dict,create,add_evidence,add_related_unit,add_related_event,add_tag,update_confidence,deactivate]
F: generate_id(prefix)→str
   ↳Called by: F025:generate_signal_id,F029:add_evidence,F030:add_evidence
   ↳Impact: 🔴HIGH (20 dependents) | Breaks: [F025:generate_signal_id],[F029:add_evidence],[F030:add_evidence]
F: utc_now()→str
   ↳Called by: F033:deactivate,F032:deactivate,F029:deactivate
   ↳Impact: 🔴HIGH (9 dependents) | Breaks: [F033:deactivate],[F032:deactivate],[F029:deactivate]
---

F027│simulation_schema.py│0
---

F031│unit_schema.py│144
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
   ↳Called by: F025:generate_signal_id,F029:add_evidence,F030:add_evidence
   ↳Impact: 🔴HIGH (20 dependents) | Breaks: [F025:generate_signal_id],[F029:add_evidence],[F030:add_evidence]
F: utc_now()→str
   ↳Called by: F033:deactivate,F032:deactivate,F029:deactivate
   ↳Impact: 🔴HIGH (9 dependents) | Breaks: [F033:deactivate],[F032:deactivate],[F029:deactivate]
---
