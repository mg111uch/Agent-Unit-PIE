# 📂 kernel
Generated: 2026-06-01 13:39:55
Files: 5

---

F019│__init__.py│167
S: agent_unit_pie.kernel
D: ►F015,F016,F017,F018,F064 ●memory,patterns,retrieval,signals,timeline,+1
---

F016│compression_engine.py│344
S: kernel/compression_engine.py
D: ●__future__,datetime,logging,typing
C: CompressionEngine│[__init__,run_cycle,compress_observations,compress_events,aggregate_signals,generate_higher_patterns,compress_timelines,archive_old_memory,prune_low_value_memory,compute_memory_value,+4]
   S: Recursive memory compression engine.
---

F015│observation_pipeline.py│308
S: kernel/observation_pipeline.py
D: ●__future__,datetime,logging,typing,uuid
C: ObservationPipeline│[__init__,process,normalize_observation,generate_events,generate_signals,detect_patterns,update_memory,run_compression_if_needed,utc_now,health_check]
   S: Central cognition pipeline.
---

F018│ontology_registry.py│416
S: kernel/ontology_registry.py
D: ●__future__,kernel,logging,typing
C: OntologyRegistry│[__init__,is_valid,get_category,get_types_by_category,list_types,list_categories,register_ontology,remove_ontology,search,export_registry,+1]
   S: Unified ontology access layer.
---

F017│unit_registry.py│471
S: kernel/unit_registry.py
D: ●__future__,datetime,logging,typing
C: UnitRegistry│[__init__,register_unit,unregister_unit,load_unit,get_unit,unit_exists,get_units_by_type,query_units,add_relation,get_relations,+6]
   S: Global runtime unit registry.
---
