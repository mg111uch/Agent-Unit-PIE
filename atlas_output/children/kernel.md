# 📂 kernel
Generated: 2026-07-26 16:20:18
Files: 6

---

F021│__init__.py│141
S: agent_unit_pie.kernel
D: ►F017,F018,F019,F020,F070 ●memory,patterns,relations,signals,timeline,+1
---

F018│compression_engine.py│302
S: kernel/compression_engine.py
D: ●__future__,datetime,logging,typing
C: CompressionEngine│[__init__,run_cycle,compress_observations,compress_events,aggregate_signals,generate_higher_patterns,compress_timelines,archive_old_memory,prune_low_value_memory,compute_memory_value,+4]
   S: Recursive memory compression engine.
C: CompressionEngine│[__init__,run_cycle,compress_observations,compress_events,aggregate_signals,generate_higher_patterns,compress_timelines,archive_old_memory,prune_low_value_memory,compute_memory_value,+4]
   S: Recursive memory compression engine.
   F: __init__(self,memory_router,pattern_engine,storage_backend,config)
   F: run_cycle(self)→Any
      S: Main recursive compression cycle.
   F: compress_observations(self)→Any
      S: Compress raw observations into summaries/signals.
   F: compress_events(self)→Any
      S: Merge repetitive or low-value events.
   F: aggregate_signals(self)→Any
      S: Aggregate signals into trends and summaries.
   F: generate_higher_patterns(self)→Any
      S: Generate high-level abstractions from existing patterns.
   F: compress_timelines(self)→Any
      S: Compress long historical timelines into abstractions.
   F: archive_old_memory(self)→Any
      S: Move stale memory into cold/archive storage.
   F: prune_low_value_memory(self)→Any
      S: Remove low-value redundant cognition artifacts.
   F: compute_memory_value(self,memory_item)→float
      S: Estimate long-term importance of memory.
   F: summarize_cluster(self,items)→Any
      S: Build compressed abstraction from related memory items.
   F: build_recursive_abstraction(self,patterns)→Any
      S: Build higher-order abstraction from lower patterns.
   F: health_check(self)→Any
   F: utc_now()→str
   ↳Called by: F035:update_timestamp,F036:deactivate,F033:update_timestamp
   ↳Impact: 🔴HIGH (9 dependents) | Breaks: [F035:update_timestamp],[F036:deactivate],[F033:update_timestamp]
---

F016│context_builder.py│385
S: llm/context_builder.py
D: ●__future__,datetime,json,logging,typing
C: ContextBuilder│[__init__,build_context,retrieve_relevant_memory,prioritize_context,compress_context,compress_section,trim_to_token_limit,build_prompt_context,health_check,utc_now]
   S: Dynamic cognition context assembler.
C: ContextBuilder│[__init__,build_context,retrieve_relevant_memory,prioritize_context,compress_context,compress_section,trim_to_token_limit,build_prompt_context,health_check,utc_now]
   S: Dynamic cognition context assembler.
   F: __init__(self,retrieval_engine,memory_engine,compression_engine,token_estimator,config)
   F: build_context(self,task,unit_id,unit_type,additional_context)→Any
      S: Main context generation pipeline.
   F: retrieve_relevant_memory(self,task,unit_id,unit_type)→Any
      S: Retrieve relevant cognition artifacts.
   F: prioritize_context(self,retrieval_result,task)→Any
      S: Rank retrieved artifacts by relevance.
   F: compress_context(self,prioritized_context)→Any
      S: Compress context intelligently.
   F: compress_section(self,section_name,section_data)→Any
      S: Compress individual context section.
   F: trim_to_token_limit(self,context)→Any
      S: Ensure context fits token budget.
   F: build_prompt_context(self,context)→str
      S: Convert context into prompt-safe text.
   F: health_check(self)→Any
   F: utc_now()→str
   ↳Called by: F035:update_timestamp,F036:deactivate,F033:update_timestamp
   ↳Impact: 🔴HIGH (9 dependents) | Breaks: [F035:update_timestamp],[F036:deactivate],[F033:update_timestamp]
---

F017│observation_pipeline.py│276
S: kernel/observation_pipeline.py
D: ●__future__,datetime,logging,typing,uuid
C: ObservationPipeline│[__init__,process,normalize_observation,generate_events,generate_signals,detect_patterns,update_memory,run_compression_if_needed,utc_now,health_check]
   S: Central cognition pipeline.
C: ObservationPipeline│[__init__,process,normalize_observation,generate_events,generate_signals,detect_patterns,update_memory,run_compression_if_needed,utc_now,health_check]
   S: Central cognition pipeline.
   F: __init__(self,event_engine,signal_engine,pattern_engine,memory_router,compression_engine)
   F: process(self,observation)→Any
      S: Main cognition pipeline entry point.
      S: Parameters
      S: ----------
      S: observation : dict
      S: Raw observation data.
   F: normalize_observation(self,observation)→Any
      S: Normalize observation into canonical schema.
   F: generate_events(self,observation)→Any
      S: Convert observation into events.
   F: generate_signals(self,observation,events)→Any
      S: Generate signals from events + observations.
   F: detect_patterns(self,observation,events,signals)→Any
      S: Detect higher-order patterns.
   F: update_memory(self,observation,events,signals,patterns)→None
      S: Route cognition artifacts into memory systems.
   F: run_compression_if_needed(self)→None
      S: Optional memory compression step.
   F: utc_now()→str
   ↳Called by: F035:update_timestamp,F036:deactivate,F033:update_timestamp
   ↳Impact: 🔴HIGH (9 dependents) | Breaks: [F035:update_timestamp],[F036:deactivate],[F033:update_timestamp]
      S: UTC ISO timestamp.
   F: health_check(self)→Any
      S: Pipeline component status.
---

F020│ontology_registry.py│388
S: kernel/ontology_registry.py
D: ●__future__,kernel,logging,typing
C: OntologyRegistry│[__init__,is_valid,get_category,get_types_by_category,list_types,list_categories,register_ontology,remove_ontology,search,export_registry,+1]
   S: Unified ontology access layer.
C: OntologyRegistry│[__init__,is_valid,get_category,get_types_by_category,list_types,list_categories,register_ontology,remove_ontology,search,export_registry,+1]
   S: Unified ontology access layer.
   F: __init__(self)
   F: is_valid(self,ontology_name,value)→bool
      S: Validate ontology value.
   F: get_category(self,ontology_name,value)→str
      S: Get category of ontology value.
   F: get_types_by_category(self,ontology_name,category)
      S: Get all types under category.
   F: list_types(self,ontology_name)→List[str]
      S: List all ontology types.
   F: list_categories(self,ontology_name)→List[str]
      S: List ontology categories.
   F: register_ontology(self,ontology_name,ontology_types)→None
      S: Dynamically register ontology.
   F: remove_ontology(self,ontology_name)→bool
      S: Remove ontology.
   F: search(self,value)→Any
      S: Search value across all ontologies.
   F: export_registry(self)→Any
      S: Export ontology metadata.
   F: summary(self)→Any
---

F019│unit_registry.py│415
S: kernel/unit_registry.py
D: ●__future__,datetime,logging,typing
C: UnitRegistry│[__init__,register_unit,unregister_unit,load_unit,get_unit,unit_exists,get_units_by_type,query_units,add_relation,get_relations,+6]
   S: Global runtime unit registry.
C: UnitRegistry│[__init__,register_unit,unregister_unit,load_unit,get_unit,unit_exists,get_units_by_type,query_units,add_relation,get_relations,+6]
   S: Global runtime unit registry.
   F: __init__(self,unit_storage,ontology_registry,config)
   F: register_unit(self,unit)→bool
   ↳Calls: F035:add
      S: Register active unit.
   F: unregister_unit(self,unit_id)→bool
      S: Remove unit from active registry.
   F: load_unit(self,unit_id)→Any
      S: Load unit from storage if absent.
   F: get_unit(self,unit_id)→Any
      S: Retrieve active unit.
   F: unit_exists(self,unit_id)→bool
   F: get_units_by_type(self,unit_type)→Any
      S: Retrieve units by type.
   F: query_units(self,filters)→Any
      S: Query units using metadata filters.
   F: add_relation(self,source_unit_id,target_unit_id,relation_type,metadata)→bool
      S: Add relation between units.
   F: get_relations(self,unit_id)→Any
      S: Get unit relations.
   F: resolve_related_units(self,unit_id)→Any
      S: Resolve connected units.
   F: search_units(self,text)→Any
      S: Lightweight text search.
   F: clear_cache(self)→None
      S: Clear active cache.
   F: export_registry(self)→Any
      S: Export lightweight registry metadata.
   F: summary(self)→Any
   F: utc_now()→str
   ↳Called by: F035:update_timestamp,F036:deactivate,F033:update_timestamp
   ↳Impact: 🔴HIGH (9 dependents) | Breaks: [F035:update_timestamp],[F036:deactivate],[F033:update_timestamp]
---
