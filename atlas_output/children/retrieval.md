# 📂 retrieval
Generated: 2026-06-01 13:39:55
Files: 7

---

F055│hierarchy_retriever.py│428
D: ●collections,dataclasses,kernel,time,typing,+1
C: HierarchyNode│[to_dict]
C: HierarchyRetriever│[__init__,add_node,create_node,build_from_semantic_memory,retrieve_hierarchy_context,_recursive_collect,get_node_path,get_subtree_nodes,_collect_subtree,retrieve_topic_context,+5]
---

F053│pattern_retriever.py│581
S: kernel/retrieval/pattern_retriever.py
D: ●__future__,logging,typing
C: PatternRetriever│[__init__,get_pattern,get_patterns_by_type,get_patterns_by_category,get_unit_patterns,get_high_confidence_patterns,get_anomaly_patterns,get_opportunity_patterns,get_risk_patterns,get_temporal_patterns,+8]
   S: Unified pattern retrieval engine.
---

F056│relation_retriever.py│7
C: RelationEngine│[link,get_relations,detect_cross_unit_correlations]
---

F054│retrieval_engine.py│422
D: ●collections,kernel,math,time,typing,+1
C: RetrievalResult│[__init__,to_dict]
C: RetrievalEngine│[__init__,search,search_semantic_memory,search_episodic_memory,search_working_memory,retrieve_patterns,retrieve_recent_timeline,build_context,_calculate_text_score,memory_summary,+1]
---

F051│semantic_retriever.py│460
D: ●collections,kernel,math,time,typing,+2
C: SemanticSearchResult│[to_dict]
C: SemanticRetriever│[__init__,search_by_concept,semantic_traversal,_traverse_recursive,multi_concept_search,build_semantic_context,retrieve_related_knowledge,detect_semantic_clusters,_cluster_dfs,summary]
---

F050│timeline_retriever.py│546
S: kernel/retrieval/timeline_retriever.py
D: ●__future__,datetime,logging,typing
C: TimelineRetriever│[__init__,retrieve_events,retrieve_memories,retrieve_patterns,retrieve_window,build_chronology_chain,detect_temporal_clusters,retrieve_historical_snapshot,retrieve_future_projection,summarize_timeline,+2]
   S: Timeline-aware retrieval engine.
---

F052│unit_retriever.py│447
S: kernel/retrieval/unit_retriever.py
D: ●__future__,logging,typing
C: UnitRetriever│[__init__,get_unit,get_units_by_type,query_units,get_related_units,get_units_by_pattern,get_units_by_behavior,semantic_search,retrieve_near_timeline,get_all_units,+3]
   S: Unified unit retrieval layer.
---
