# 📂 ontology
Generated: 2026-06-01 13:39:55
Files: 8

---

F039│behavior_types.py│470
D: ●dataclasses,typing
C: BehaviorTypeDefinition│[]
F: get_behavior_type(behavior_type)→Optional[BehaviorTypeDefinition]
F: behavior_type_exists(behavior_type)→bool
F: list_behavior_types()→List[str]
F: get_behaviors_by_category(category)→List[str]
F: get_behaviors_for_unit_type(unit_type)→List[str]
---

F037│event_types.py│384
S: kernel/ontology/event_types.py
D: ●__future__
F: is_valid_event_type(event_type)→bool
F: get_event_category(event_type)→str
F: get_events_by_category(category)
F: list_event_categories()
F: list_all_event_types()
---

F043│hypothesis_types.py│0
---

F040│pattern_types.py│329
S: kernel/ontology/pattern_types.py
D: ●__future__
F: is_valid_pattern_type(pattern_type)→bool
F: get_pattern_category(pattern_type)→str
F: get_patterns_by_category(category)
F: list_pattern_categories()
F: list_all_pattern_types()
---

F041│relation_types.py│387
D: ●dataclasses,typing
C: RelationTypeDefinition│[]
F: get_relation_type(relation_type)→Optional[RelationTypeDefinition]
F: relation_type_exists(relation_type)→bool
F: list_relation_types()→List[str]
F: get_relation_types_by_category(category)→List[str]
F: get_inverse_relation(relation_type)→Optional[str]
---

F044│resource_types.py│318
D: ●dataclasses,typing
C: ResourceTypeDefinition│[]
F: get_resource_type(resource_type)→Optional[ResourceTypeDefinition]
F: resource_type_exists(resource_type)→bool
F: list_resource_types()→List[str]
F: get_resources_by_category(category)→List[str]
F: get_related_signals(resource_type)→List[str]
---

F042│signal_types.py│226
D: ●dataclasses,typing
C: SignalTypeDefinition│[]
F: get_signal_type(signal_type)→Optional[SignalTypeDefinition]
   ↳Called by: F061:_validate_signal_type
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F061:_validate_signal_type]
F: signal_type_exists(signal_type)→bool
   ↳Called by: F061:_validate_signal_type,F058:emit_signal
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F061:_validate_signal_type],[F058:emit_signal]
F: list_signal_types()→List[str]
F: get_signal_types_by_category(category)→List[str]
---

F038│unit_types.py│319
D: ●dataclasses,typing
C: UnitTypeDefinition│[]
F: get_unit_type(unit_type)→Optional[UnitTypeDefinition]
F: unit_type_exists(unit_type)→bool
F: list_unit_types()→List[str]
F: get_unit_types_by_category(category)→List[str]
---
