# LEGACY CODE ATLAS

Generated from: `/home/manigupt/Hello/python/Agentic_Unit_PIE/codebase/kernel`

## Root
### `__init__.py`

### `compression_engine.py`
- **Class:** `CompressionEngine`
  - __init__()
  - run_cycle()
  - compress_observations()
  - compress_events()
  - aggregate_signals()
  - generate_higher_patterns()
  - compress_timelines()
  - archive_old_memory()
  - prune_low_value_memory()
  - compute_memory_value()
  - summarize_cluster()
  - build_recursive_abstraction()
  - health_check()
  - utc_now()

### `observation_pipeline.py`
- **Class:** `ObservationPipeline`
  - __init__()
  - process()
  - normalize_observation()
  - generate_events()
  - generate_signals()
  - detect_patterns()
  - update_memory()
  - run_compression_if_needed()
  - utc_now()
  - health_check()

### `ontology_registry.py`
- **Class:** `OntologyRegistry`
  - __init__()
  - is_valid()
  - get_category()
  - get_types_by_category()
  - list_types()
  - list_categories()
  - register_ontology()
  - remove_ontology()
  - search()
  - export_registry()
  - summary()

### `unit_registry.py`
- **Class:** `UnitRegistry`
  - __init__()
  - register_unit()
  - unregister_unit()
  - load_unit()
  - get_unit()
  - unit_exists()
  - get_units_by_type()
  - query_units()
  - add_relation()
  - get_relations()
  - resolve_related_units()
  - search_units()
  - clear_cache()
  - export_registry()
  - summary()
  - utc_now()

## config
### `kernel_config.py`

### `ontology_config.py`

## working_memory
## utils
### `ids.py`
- generate_id()
- generate_hash_id()
- generate_time_id()
- generate_unit_id()
- generate_signal_id()
- generate_event_id()
- generate_pattern_id()
- generate_relation_id()
- generate_hypothesis_id()
- generate_session_id()
- is_valid_id()
- extract_prefix()
- extract_suffix()

### `logger.py`
- get_logger()
- debug()
- info()
- warning()
- error()
- critical()
- log_exception()
- structured_log()
- get_child_logger()

### `paths.py`
- ensure_directories_exist()
- get_kb_path()
- get_memory_path()
- get_simulation_path()
- get_log_file_path()
- get_temp_file_path()
- get_cache_file_path()
- ensure_parent_dir()
- path_exists()
- create_dir()
- get_env()

### `timestamps.py`
- utc_now()
- local_now()
- unix_timestamp()
- parse_timestamp()
- format_timestamp()
- seconds_between()
- minutes_between()
- hours_between()
- days_between()
- add_seconds()
- add_minutes()
- add_hours()
- add_days()
- is_before()
- is_after()
- is_between()
- human_readable_delta()

## schemas
### `event_schema.py`
- **Class:** `EventSource`
- **Class:** `EventParticipant`
- **Class:** `EventLocation`
- **Class:** `EventMetrics`
- **Class:** `EventEvidence`
- **Class:** `EventRelation`
- **Class:** `EventMetadata`
- **Class:** `EventSchema`
  - to_dict()
  - create()
  - add_participant()
  - add_evidence()
  - add_relation()
  - add_generated_signal()
  - add_tag()
  - set_location()
  - deactivate()
  - update_timestamp()
- generate_id()
- utc_now()

### `hypothesis_schema.py`

### `memory_schema.py`

### `pattern_schema.py`
- **Class:** `PatternSource`
- **Class:** `PatternSignalRef`
- **Class:** `PatternEventRef`
- **Class:** `PatternUnitRef`
- **Class:** `PatternMetrics`
- **Class:** `PatternTimeline`
- **Class:** `PatternCausalLink`
- **Class:** `PatternEvidence`
- **Class:** `PatternMetadata`
- **Class:** `PatternSchema`
  - to_dict()
  - create()
  - add_unit()
  - add_signal()
  - add_event()
  - add_causal_link()
  - add_evidence()
  - add_tag()
  - update_confidence()
  - update_strength()
  - deactivate()
  - update_timestamp()
- generate_id()
- utc_now()

### `relation_schema.py`
- **Class:** `RelationEndpoint`
- **Class:** `RelationMetrics`
- **Class:** `RelationEvidence`
- **Class:** `RelationTimeline`
- **Class:** `RelationContext`
- **Class:** `RelationMetadata`
- **Class:** `RelationSchema`
  - to_dict()
  - create()
  - add_evidence()
  - add_tag()
  - add_related_event()
  - add_related_signal()
  - add_related_pattern()
  - update_strength()
  - update_confidence()
  - mark_interaction()
  - deactivate()
- generate_id()
- utc_now()

### `signal_schema.py`
- **Class:** `SignalSource`
- **Class:** `SignalEvidence`
- **Class:** `SignalContext`
- **Class:** `SignalMetrics`
- **Class:** `SignalMetadata`
- **Class:** `SignalSchema`
  - to_dict()
  - create()
  - add_evidence()
  - add_related_unit()
  - add_related_event()
  - add_tag()
  - update_confidence()
  - deactivate()
- generate_id()
- utc_now()

### `simulation_schema.py`

### `unit_schema.py`
- **Class:** `UnitIdentity`
- **Class:** `UnitState`
- **Class:** `UnitResources`
  - add()
  - consume()
- **Class:** `UnitTraits`
- **Class:** `UnitBehavior`
- **Class:** `UnitSignalRef`
- **Class:** `UnitRelation`
- **Class:** `UnitMemory`
- **Class:** `UnitMetadata`
- **Class:** `UnitSchema`
  - to_dict()
  - create()
  - add_behavior()
  - add_signal()
  - add_relation()
  - update_timestamp()
- generate_id()
- utc_now()

## hypothesis
### `confidence_engine.py`
- **Class:** `ConfidenceResult`
  - to_dict()
- **Class:** `ConfidenceEngine`
  - __init__()
  - evaluate_signal_confidence()
  - evaluate_event_confidence()
  - evaluate_pattern_confidence()
  - evaluate_hypothesis_confidence()
  - _calculate_signal_evidence()
  - _calculate_signal_consistency()
  - _calculate_source_reliability()
  - _calculate_temporal_score()
  - _calculate_quantity_score()
  - _inverse_variance_score()
  - _clamp_confidence()
  - _empty_result()
  - summarize()

### `hypothesis_engine.py`
- **Class:** `Hypothesis`
  - to_dict()
- **Class:** `HypothesisEngine`
  - __init__()
  - create_hypothesis()
  - register_hypothesis()
  - generate_from_patterns()
  - add_supporting_evidence()
  - add_contradicting_evidence()
  - validate_hypothesis()
  - get_hypothesis()
  - get_by_type()
  - get_by_category()
  - get_by_status()
  - export_to_semantic_memory()
  - stats()
  - clear()

### `validation_engine.py`

## ontology
### `behavior_types.py`
- **Class:** `BehaviorTypeDefinition`
- get_behavior_type()
- behavior_type_exists()
- list_behavior_types()
- get_behaviors_by_category()
- get_behaviors_for_unit_type()

### `event_types.py`
- is_valid_event_type()
- get_event_category()
- get_events_by_category()
- list_event_categories()
- list_all_event_types()

### `hypothesis_types.py`

### `pattern_types.py`
- is_valid_pattern_type()
- get_pattern_category()
- get_patterns_by_category()
- list_pattern_categories()
- list_all_pattern_types()

### `relation_types.py`
- **Class:** `RelationTypeDefinition`
- get_relation_type()
- relation_type_exists()
- list_relation_types()
- get_relation_types_by_category()
- get_inverse_relation()

### `resource_types.py`
- **Class:** `ResourceTypeDefinition`
- get_resource_type()
- resource_type_exists()
- list_resource_types()
- get_resources_by_category()
- get_related_signals()

### `signal_types.py`
- **Class:** `SignalTypeDefinition`
- get_signal_type()
- signal_type_exists()
- list_signal_types()
- get_signal_types_by_category()

### `unit_types.py`
- **Class:** `UnitTypeDefinition`
- get_unit_type()
- unit_type_exists()
- list_unit_types()
- get_unit_types_by_category()

## memory
### `episodic_memory.py`
- **Class:** `Episode`
  - to_dict()
- **Class:** `EpisodicMemory`
  - __init__()
  - add_episode()
  - create_episode()
  - get_episode()
  - get_recent_episodes()
  - search_by_tag()
  - search_by_entity()
  - search_by_event()
  - search_by_importance()
  - get_timeline()
  - remove_episode()
  - load_episode_from_disk()
  - stats()
  - clear()

### `memory_engine.py`
- **Class:** `MemoryEngine`
  - __init__()
  - save_object()
  - load_object()
  - delete_object()
  - save_unit()
  - load_unit()
  - save_signal()
  - load_signal()
  - save_event()
  - load_event()
  - save_pattern()
  - load_pattern()
  - save_relation()
  - load_relation()
  - list_objects()
  - search_by_prefix()
  - object_exists()
  - get_object_path()
  - _get_memory_root()

### `pattern_memory.py`

### `semantic_memory.py`
- **Class:** `SemanticNode`
  - to_dict()
- **Class:** `SemanticEdge`
  - to_dict()
- **Class:** `SemanticMemory`
  - __init__()
  - add_node()
  - create_node()
  - add_edge()
  - create_edge()
  - get_node()
  - get_edge()
  - search_by_tag()
  - search_by_concept()
  - search_by_type()
  - search_content()
  - get_neighbors()
  - get_connected_nodes()
  - remove_node()
  - remove_edge()
  - load_node_from_disk()
  - stats()
  - clear()

### `working_memory.py`
- **Class:** `WorkingMemoryItem`
  - touch()
  - is_expired()
  - to_dict()
- **Class:** `WorkingMemory`
  - __init__()
  - add_memory()
  - get_memory()
  - update_memory()
  - remove_memory()
  - search_by_tag()
  - search_by_type()
  - search_by_importance()
  - cleanup_expired()
  - get_top_memories()
  - stats()
  - clear()
  - _evict_oldest()

## retrieval
### `hierarchy_retriever.py`
- **Class:** `HierarchyNode`
  - to_dict()
- **Class:** `HierarchyRetriever`
  - __init__()
  - add_node()
  - create_node()
  - build_from_semantic_memory()
  - retrieve_hierarchy_context()
  - _recursive_collect()
  - get_node_path()
  - get_subtree_nodes()
  - _collect_subtree()
  - retrieve_topic_context()
  - retrieve_semantic_cluster()
  - get_root_nodes()
  - search_hierarchy()
  - stats()
  - clear()

### `pattern_retriever.py`
- **Class:** `PatternRetriever`
  - __init__()
  - get_pattern()
  - get_patterns_by_type()
  - get_patterns_by_category()
  - get_unit_patterns()
  - get_high_confidence_patterns()
  - get_anomaly_patterns()
  - get_opportunity_patterns()
  - get_risk_patterns()
  - get_temporal_patterns()
  - get_recurring_patterns()
  - get_cross_unit_patterns()
  - get_causal_patterns()
  - semantic_search()
  - get_all_patterns()
  - summarize_patterns()
  - retrieve_for_context()
  - health_check()

### `relation_retriever.py`
- **Class:** `RelationEngine`
  - link()
  - get_relations()
  - detect_cross_unit_correlations()

### `retrieval_engine.py`
- **Class:** `RetrievalResult`
  - __init__()
  - to_dict()
- **Class:** `RetrievalEngine`
  - __init__()
  - search()
  - search_semantic_memory()
  - search_episodic_memory()
  - search_working_memory()
  - retrieve_patterns()
  - retrieve_recent_timeline()
  - build_context()
  - _calculate_text_score()
  - memory_summary()
  - clear_all_retrieval_cache()

### `semantic_retriever.py`
- **Class:** `SemanticSearchResult`
  - to_dict()
- **Class:** `SemanticRetriever`
  - __init__()
  - search_by_concept()
  - semantic_traversal()
  - _traverse_recursive()
  - multi_concept_search()
  - build_semantic_context()
  - retrieve_related_knowledge()
  - detect_semantic_clusters()
  - _cluster_dfs()
  - summary()

### `timeline_retriever.py`
- **Class:** `TimelineRetriever`
  - __init__()
  - retrieve_events()
  - retrieve_memories()
  - retrieve_patterns()
  - retrieve_window()
  - build_chronology_chain()
  - detect_temporal_clusters()
  - retrieve_historical_snapshot()
  - retrieve_future_projection()
  - summarize_timeline()
  - health_check()
  - parse_time()

### `unit_retriever.py`
- **Class:** `UnitRetriever`
  - __init__()
  - get_unit()
  - get_units_by_type()
  - query_units()
  - get_related_units()
  - get_units_by_pattern()
  - get_units_by_behavior()
  - semantic_search()
  - retrieve_near_timeline()
  - get_all_units()
  - get_digital_twin()
  - retrieve_for_context()
  - health_check()

## signals
### `belief_signal_handler.py`
- handle_belief_shift_signal()
- handle_contradiction_signal()
- handle_confidence_change_signal()
- register_handlers()
- unregister_handlers()

### `signal_engine.py`
- **Class:** `SignalEngine`
  - __init__()
  - emit_signal()
  - create_signal()
  - register_handler()
  - unregister_handler()
  - _trigger_handlers()
  - get_recent_signals()
  - search_signals_by_source()
  - search_signals_by_tag()
  - aggregate_signal_values()
  - signal_to_event()
  - stats()
  - clear_recent_signals()

### `signal_extractor.py`

### `signal_router.py`

### `signal_validator.py`
- **Class:** `SignalValidationResult`
  - __init__()
  - add_error()
  - add_warning()
  - to_dict()
- **Class:** `SignalValidator`
  - validate()
  - _validate_basic_fields()
  - _validate_signal_type()
  - _validate_metrics()
  - _validate_value()
  - _validate_metadata()
  - is_valid()
  - assert_valid()
  - log_validation_result()

## events
### `event_engine.py`
- **Class:** `EventEngine`
  - __init__()
  - emit_event()
  - create_event()
  - create_event_from_signal()
  - register_handler()
  - unregister_handler()
  - _trigger_handlers()
  - get_recent_events()
  - search_events_by_source()
  - search_events_by_tag()
  - link_events()
  - stats()
  - clear_recent_events()

### `event_extractor.py`

### `timeline_engine.py`
- **Class:** `TimelineEntry`
  - to_dict()
- **Class:** `TimelineEngine`
  - __init__()
  - add_entry()
  - add_event()
  - add_signal()
  - create_entry()
  - get_entry()
  - get_recent_entries()
  - get_entries_between()
  - search_by_type()
  - search_by_tag()
  - search_by_source()
  - get_important_entries()
  - remove_entry()
  - stats()
  - clear()

## patterns
### `anomaly_detector.py`
- **Class:** `AnomalyResult`
  - to_dict()
- **Class:** `AnomalyDetector`
  - __init__()
  - detect_zscore_anomalies()
  - detect_spikes()
  - detect_dropouts()
  - register_anomaly_patterns()
  - analyze_signals()
  - summarize_anomaly()

### `causal_engine.py`

### `contradiction_detector.py`

### `pattern_engine.py`
- **Class:** `PatternEngine`
  - __init__()
  - register_pattern()
  - create_pattern()
  - detect_numeric_trend()
  - detect_repeated_events()
  - detect_shared_sources()
  - get_pattern()
  - get_patterns_by_type()
  - get_patterns_by_source()
  - get_recent_patterns()
  - remove_pattern()
  - stats()
  - clear()

### `trend_detector.py`
- **Class:** `TrendResult`
  - to_dict()
- **Class:** `TrendDetector`
  - __init__()
  - detect_trend()
  - detect_and_register_pattern()
  - _calculate_slope()
  - _calculate_volatility()
  - _calculate_confidence()
  - _get_direction()
  - _classify_trend()
  - moving_average()
  - detect_anomalies()
  - detect_simple_cycles()
  - summarize_trend()
