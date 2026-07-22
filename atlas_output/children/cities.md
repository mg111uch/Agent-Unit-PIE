# 📂 cities
Generated: 2026-07-21 18:31:40
Files: 4

---

F127│city_initializer.py│328
S: units/cities/city_initializer.py
D: ●__future__,datetime,logging,typing
C: CityInitializer│[__init__,initialize_city,build_economy_model,build_governance_model,build_infrastructure_model,build_social_model,build_financial_model,build_digital_twin_model,build_simulation_model,build_knowledge_base,+4]
   S: Create and initialize city units.
C: CityInitializer│[__init__,initialize_city,build_economy_model,build_governance_model,build_infrastructure_model,build_social_model,build_financial_model,build_digital_twin_model,build_simulation_model,build_knowledge_base,+4]
   S: Create and initialize city units.
   F: __init__(self,unit_storage,ontology_registry,config)
   F: initialize_city(self,city_id,city_name,country,state,population,metadata)→Any
      S: Create fully initialized city unit.
   F: build_economy_model(self)→Any
      S: Initialize economy structure.
   F: build_governance_model(self)→Any
      S: Governance + policy structure.
   F: build_infrastructure_model(self)→Any
      S: Physical infrastructure structure.
   F: build_social_model(self)→Any
      S: Population + social structure.
   F: build_financial_model(self)→Any
      S: Financial flow model.
   F: build_digital_twin_model(self)→Any
      S: Spatial + simulation twin.
   F: build_simulation_model(self)→Any
      S: Simulation state.
   F: build_knowledge_base(self)→Any
      S: City cognition KB.
   F: build_pattern_tracking(self)→Any
      S: Pattern cognition tracking.
   F: generate_city_snapshot(self,city_unit)→Any
      S: Generate lightweight city summary.
   F: health_check(self)→Any
   F: utc_now()→str
   ↳Called by: F072:update_timestamp,F073:update_timestamp,F076:mark_interaction
   ↳Impact: 🔴HIGH (9 dependents) | Breaks: [F072:update_timestamp],[F073:update_timestamp],[F076:mark_interaction]
---

F126│city_pattern_detector.py│0
---

F125│city_signal_mapper.py│0
---

F124│city_summary_generator.py│0
---
