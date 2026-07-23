# 📂 retrieval
Generated: 2026-07-23 14:15:38
Files: 7

---

F058│hierarchy_retriever.py│394
D: ●__future__,collections,dataclasses,kernel,time,+1
C: HierarchyNode│[to_dict]
C: HierarchyRetriever│[__init__,add_node,create_node,build_from_semantic_memory,retrieve_hierarchy_context,_recursive_collect,get_node_path,get_subtree_nodes,_collect_subtree,retrieve_topic_context,+5]
C: HierarchyNode│[to_dict]
   F: to_dict(self)→Any
C: HierarchyRetriever│[__init__,add_node,create_node,build_from_semantic_memory,retrieve_hierarchy_context,_recursive_collect,get_node_path,get_subtree_nodes,_collect_subtree,retrieve_topic_context,+5]
   F: __init__(self)
   F: add_node(self,node)
   F: create_node(self,node_id,title,node_type,level,parent_id,metadata)→HierarchyNode
   F: build_from_semantic_memory(self)
   F: retrieve_hierarchy_context(self,node_id,depth)→Any
   F: _recursive_collect(self,node_id,depth,visited)→Any
   F: get_node_path(self,node_id)→List[HierarchyNode]
   F: get_subtree_nodes(self,node_id,depth)→List[HierarchyNode]
   F: _collect_subtree(self,node_id,depth,visited,results)
   F: retrieve_topic_context(self,topic,depth,limit)→Any
   F: retrieve_semantic_cluster(self,concept,limit)→Any
   F: get_root_nodes(self)→List[HierarchyNode]
   F: search_hierarchy(self,query)→List[HierarchyNode]
   F: stats(self)→Any
   F: clear(self)
---

F056│pattern_retriever.py│539
S: kernel/retrieval/pattern_retriever.py
D: ●__future__,logging,typing
C: PatternRetriever│[__init__,get_pattern,get_patterns_by_type,get_patterns_by_category,get_unit_patterns,get_high_confidence_patterns,get_anomaly_patterns,get_opportunity_patterns,get_risk_patterns,get_temporal_patterns,+8]
   S: Unified pattern retrieval engine.
C: PatternRetriever│[__init__,get_pattern,get_patterns_by_type,get_patterns_by_category,get_unit_patterns,get_high_confidence_patterns,get_anomaly_patterns,get_opportunity_patterns,get_risk_patterns,get_temporal_patterns,+8]
   S: Unified pattern retrieval engine.
   F: __init__(self,pattern_storage,pattern_engine,timeline_retriever,relation_engine,embedding_engine,config)
   F: get_pattern(self,pattern_id)→Any
      S: Retrieve single pattern.
   F: get_patterns_by_type(self,pattern_type,limit)→Any
      S: Retrieve patterns by type.
   F: get_patterns_by_category(self,category,limit)→Any
      S: Retrieve patterns by ontology category.
   F: get_unit_patterns(self,unit_id,limit)→Any
      S: Retrieve patterns linked to unit.
   F: get_high_confidence_patterns(self,threshold,limit)→Any
      S: Retrieve high-confidence patterns.
   F: get_anomaly_patterns(self,limit)→Any
      S: Retrieve anomaly patterns.
   F: get_opportunity_patterns(self,limit)→Any
      S: Retrieve opportunity patterns.
   F: get_risk_patterns(self,limit)→Any
      S: Retrieve risk patterns.
   F: get_temporal_patterns(self,start_time,end_time,limit)→Any
      S: Retrieve timeline-bound patterns.
   F: get_recurring_patterns(self,limit)→Any
      S: Retrieve recurring patterns.
   F: get_cross_unit_patterns(self,min_units,limit)→Any
      S: Retrieve patterns spanning multiple units.
   F: get_causal_patterns(self,limit)→Any
      S: Retrieve causal relation patterns.
   F: semantic_search(self,query,limit)→Any
      S: Semantic pattern retrieval.
   F: get_all_patterns(self)→Any
      S: Retrieve all patterns.
   F: summarize_patterns(self)→Any
      S: Generate pattern statistics.
   F: retrieve_for_context(self,query,unit_id,limit)→Any
      S: Retrieve optimized cognition packet.
   F: health_check(self)→Any
---

F059│relation_retriever.py│7
C: RelationEngine│[link,get_relations,detect_cross_unit_correlations]
C: RelationEngine│[link,get_relations,detect_cross_unit_correlations]
   F: link(self,source_unit,target_unit,relation_type,confidence)
      S: Create directed edge: user_001 → project_x (works_on, 0.9)
   F: get_relations(self,unit_id)→list[Relation]
      S: Return all outbound and inbound relations for a unit
   F: detect_cross_unit_correlations(self,unit_ids)→list[Pattern]
      S: Find patterns that span multiple units
---

F057│retrieval_engine.py│386
D: ●__future__,collections,kernel,math,time,+1
C: RetrievalResult│[__init__,to_dict]
C: RetrievalEngine│[__init__,search,search_semantic_memory,search_episodic_memory,search_working_memory,retrieve_patterns,retrieve_recent_timeline,build_context,_calculate_text_score,memory_summary,+1]
C: RetrievalResult│[__init__,to_dict]
   F: __init__(self,item_id,item_type,score,content,metadata)
   F: to_dict(self)→Any
C: RetrievalEngine│[__init__,search,search_semantic_memory,search_episodic_memory,search_working_memory,retrieve_patterns,retrieve_recent_timeline,build_context,_calculate_text_score,memory_summary,+1]
   F: __init__(self)
   F: search(self,query,limit)→List[RetrievalResult]
   F: search_semantic_memory(self,query,limit)→List[RetrievalResult]
   F: search_episodic_memory(self,query,limit)→List[RetrievalResult]
   F: search_working_memory(self,query,limit)→List[RetrievalResult]
   F: retrieve_patterns(self,pattern_type,limit)→List[RetrievalResult]
   F: retrieve_recent_timeline(self,limit)→List[RetrievalResult]
   F: build_context(self,query,max_items)→Any
   F: _calculate_text_score(self,query,text)→float
   F: memory_summary(self)→Any
   F: clear_all_retrieval_cache(self)
---

F054│semantic_retriever.py│518
D: ●__future__,kernel,math,sentence_transformers,time,+4
C: SemanticSearchResult│[to_dict]
C: EmbeddingBackend│[search_similar,index_text]
C: ChromaBackend←EmbeddingBackend│[__init__,_get_collection,_get_model,_embed,search_similar,index_text]
C: SemanticRetriever│[__init__,set_embedding_backend,search_by_embedding,search_by_concept,semantic_traversal,_traverse_recursive,multi_concept_search,build_semantic_context,retrieve_related_knowledge,detect_semantic_clusters,+2]
C: SemanticSearchResult│[to_dict]
   F: to_dict(self)→Any
C: EmbeddingBackend│[search_similar,index_text]
   F: search_similar(self,text,top_k)→Any
   ↳Called by: F141:get_best_counter
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F141:get_best_counter]
   F: index_text(self,node_id,text)→None
C: ChromaBackend←EmbeddingBackend│[__init__,_get_collection,_get_model,_embed,search_similar,index_text]
   F: __init__(self,collection_name,persist_dir)
   F: _get_collection(self)
   ↳Called by: F146:index_graph,F146:search_similar,F145:_store_user_knowledge
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F146:index_graph],[F146:search_similar],[F145:_store_user_knowledge]
   F: _get_model(self)
   ↳Called by: F146:embed
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F146:embed]
   F: _embed(self,text)→List[float]
   F: search_similar(self,text,top_k)→Any
   ↳Called by: F141:get_best_counter
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F141:get_best_counter]
   F: index_text(self,node_id,text,metadata)
C: SemanticRetriever│[__init__,set_embedding_backend,search_by_embedding,search_by_concept,semantic_traversal,_traverse_recursive,multi_concept_search,build_semantic_context,retrieve_related_knowledge,detect_semantic_clusters,+2]
   F: __init__(self)
   F: set_embedding_backend(self,backend)
   F: search_by_embedding(self,query,limit)→List[SemanticSearchResult]
   F: search_by_concept(self,concept,limit)→List[SemanticSearchResult]
   F: semantic_traversal(self,start_node_id,max_depth)→List[SemanticSearchResult]
   F: _traverse_recursive(self,node_id,current_depth,max_depth,visited,results,current_score)
   F: multi_concept_search(self,concepts,limit)→List[SemanticSearchResult]
   F: build_semantic_context(self,query,limit)→Any
   F: retrieve_related_knowledge(self,node_id,limit)→Any
   F: detect_semantic_clusters(self,min_connections)→Any
   F: _cluster_dfs(self,node_id,visited,cluster_nodes)
   F: summary(self)→Any
---

F053│timeline_retriever.py│514
S: kernel/retrieval/timeline_retriever.py
D: ●__future__,datetime,logging,typing
C: TimelineRetriever│[__init__,retrieve_events,retrieve_memories,retrieve_patterns,retrieve_window,build_chronology_chain,detect_temporal_clusters,retrieve_historical_snapshot,retrieve_future_projection,summarize_timeline,+2]
   S: Timeline-aware retrieval engine.
C: TimelineRetriever│[__init__,retrieve_events,retrieve_memories,retrieve_patterns,retrieve_window,build_chronology_chain,detect_temporal_clusters,retrieve_historical_snapshot,retrieve_future_projection,summarize_timeline,+2]
   S: Timeline-aware retrieval engine.
   F: __init__(self,timeline_engine,event_engine,memory_engine,pattern_engine,simulation_engine,config)
   F: retrieve_events(self,start_time,end_time,event_types,unit_id,limit)→Any
      S: Retrieve timeline events.
   F: retrieve_memories(self,start_time,end_time,unit_id,limit)→Any
      S: Retrieve memories within timeline.
   F: retrieve_patterns(self,start_time,end_time,pattern_types,unit_id,limit)→Any
      S: Retrieve temporal patterns.
   F: retrieve_window(self,center_time,before_seconds,after_seconds,unit_id)→Any
      S: Retrieve timeline context window.
   F: build_chronology_chain(self,unit_id,limit)→Any
      S: Build chronological cognition chain.
   F: detect_temporal_clusters(self,events,cluster_gap_seconds)→Any
      S: Detect temporally close clusters.
   F: retrieve_historical_snapshot(self,unit_id,timestamp)→Any
      S: Retrieve historical cognition snapshot.
   F: retrieve_future_projection(self,unit_id)→Any
      S: Retrieve future simulation state.
   F: summarize_timeline(self,unit_id)→Any
      S: Generate timeline summary.
   F: health_check(self)→Any
   F: parse_time(timestamp)→Optional[datetime]
---

F055│unit_retriever.py│395
S: kernel/retrieval/unit_retriever.py
D: ●__future__,logging,typing
C: UnitRetriever│[__init__,get_unit,get_units_by_type,query_units,get_related_units,get_units_by_pattern,get_units_by_behavior,semantic_search,retrieve_near_timeline,get_all_units,+3]
   S: Unified unit retrieval layer.
C: UnitRetriever│[__init__,get_unit,get_units_by_type,query_units,get_related_units,get_units_by_pattern,get_units_by_behavior,semantic_search,retrieve_near_timeline,get_all_units,+3]
   S: Unified unit retrieval layer.
   F: __init__(self,unit_registry,unit_storage,pattern_storage,relation_engine,embedding_engine,config)
   F: get_unit(self,unit_id)→Any
      S: Retrieve single unit.
   F: get_units_by_type(self,unit_type,limit)→Any
      S: Retrieve units by type.
   F: query_units(self,filters,limit)→Any
      S: Query units using filters.
   F: get_related_units(self,unit_id,relation_type)→Any
      S: Retrieve related units.
   F: get_units_by_pattern(self,pattern_type,limit)→Any
      S: Retrieve units linked to pattern.
   F: get_units_by_behavior(self,behavior_name)→Any
      S: Retrieve units using behavior.
   F: semantic_search(self,query,limit)→Any
      S: Semantic similarity retrieval.
   F: retrieve_near_timeline(self,timestamp,window_size)→Any
      S: Retrieve units near timeline.
   F: get_all_units(self)→Any
      S: Retrieve all active units.
   F: get_digital_twin(self,unit_id)→Any
      S: Retrieve digital twin state.
   F: retrieve_for_context(self,query,unit_id,limit)→Any
      S: Retrieve optimized cognition packet.
   F: health_check(self)→Any
---
