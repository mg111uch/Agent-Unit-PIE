# 📂 memory
Generated: 2026-07-26 16:20:18
Files: 5

---

F051│episodic_memory.py│297
D: ●__future__,collections,dataclasses,kernel,time,+1
C: Episode│[to_dict]
C: EpisodicMemory│[__init__,add_episode,create_episode,get_episode,get_recent_episodes,search_by_tag,search_by_entity,search_by_event,search_by_importance,get_timeline,+4]
C: Episode│[to_dict]
   F: to_dict(self)→Any
C: EpisodicMemory│[__init__,add_episode,create_episode,get_episode,get_recent_episodes,search_by_tag,search_by_entity,search_by_event,search_by_importance,get_timeline,+4]
   F: __init__(self)
   F: add_episode(self,episode,persist)
   F: create_episode(self,episode_id,episode_type,summary,entities,events,signals,patterns,relations,tags,importance,emotional_weight,confidence,metadata,persist)→Episode
   F: get_episode(self,episode_id)→Optional[Episode]
   F: get_recent_episodes(self,limit)→List[Episode]
   F: search_by_tag(self,tag)→List[Episode]
   F: search_by_entity(self,entity_id)→List[Episode]
   F: search_by_event(self,event_id)→List[Episode]
   F: search_by_importance(self,min_importance)→List[Episode]
   F: get_timeline(self)→List[Episode]
   F: remove_episode(self,episode_id)→bool
   F: load_episode_from_disk(self,episode_id)→Optional[Episode]
   F: stats(self)→Any
   F: clear(self)
---

F050│memory_engine.py│197
D: ●__future__,kernel,typing
C: MemoryEngine│[__init__,db,_persist_structured,save_object,load_object,delete_object,list_objects,search_by_prefix,object_exists,save_unit,+9]
C: MemoryEngine│[__init__,db,_persist_structured,save_object,load_object,delete_object,list_objects,search_by_prefix,object_exists,save_unit,+9]
   F: __init__(self)
   F: db(self)
   F: _persist_structured(self,memory_type,object_id,data)
   F: save_object(self,memory_type,object_id,data)→str
   F: load_object(self,memory_type,object_id)→Any
   F: delete_object(self,memory_type,object_id)→bool
   F: list_objects(self,memory_type)→List[str]
   F: search_by_prefix(self,memory_type,prefix)→List[str]
   F: object_exists(self,memory_type,object_id)→bool
   F: save_unit(self,unit,memory_type)→str
   F: load_unit(self,unit_id,memory_type)→Any
   F: save_signal(self,signal,memory_type)→str
   F: load_signal(self,signal_id,memory_type)→Any
   F: save_event(self,event,memory_type)→str
   F: load_event(self,event_id,memory_type)→Any
   F: save_pattern(self,pattern,memory_type)→str
   F: load_pattern(self,pattern_id,memory_type)→Any
   F: save_relation(self,relation,memory_type)→str
   F: load_relation(self,relation_id,memory_type)→Any
---

F053│pattern_memory.py│0
---

F052│semantic_memory.py│423
D: ●__future__,collections,dataclasses,kernel,time,+1
C: SemanticNode│[to_dict]
C: SemanticEdge│[to_dict]
C: SemanticMemory│[__init__,add_node,create_node,add_edge,create_edge,get_node,get_edge,search_by_tag,search_by_topic,search_by_concept,+9]
C: SemanticNode│[to_dict]
   F: to_dict(self)→Any
C: SemanticEdge│[to_dict]
   F: to_dict(self)→Any
C: SemanticMemory│[__init__,add_node,create_node,add_edge,create_edge,get_node,get_edge,search_by_tag,search_by_topic,search_by_concept,+9]
   F: __init__(self)
   F: add_node(self,node,persist)
   ↳Calls: F035:add
   F: create_node(self,node_id,node_type,title,content,concepts,tags,metadata,confidence,importance,source_refs,topic_id,persist)→SemanticNode
   F: add_edge(self,edge,persist)
   ↳Calls: F035:add
   F: create_edge(self,edge_id,source_node_id,target_node_id,relation_type,weight,confidence,metadata,topic_id,persist)→SemanticEdge
   F: get_node(self,node_id)→Optional[SemanticNode]
   F: get_edge(self,edge_id)→Optional[SemanticEdge]
   F: search_by_tag(self,tag)→List[SemanticNode]
   F: search_by_topic(self,topic_id)→List[SemanticNode]
   F: search_by_concept(self,concept)→List[SemanticNode]
   F: search_by_type(self,node_type)→List[SemanticNode]
   F: search_content(self,query)→List[SemanticNode]
   F: get_neighbors(self,node_id)→List[SemanticNode]
   F: get_connected_nodes(self,node_id,depth)→List[SemanticNode]
   F: remove_node(self,node_id)→bool
   F: remove_edge(self,edge_id)→bool
   F: load_node_from_disk(self,node_id)→Optional[SemanticNode]
   F: stats(self)→Any
   F: clear(self)
---

F049│working_memory.py│233
D: ●__future__,collections,dataclasses,kernel,time,+1
C: WorkingMemoryItem│[touch,is_expired,to_dict]
C: WorkingMemory│[__init__,add_memory,get_memory,update_memory,remove_memory,search_by_tag,search_by_type,search_by_importance,cleanup_expired,get_top_memories,+3]
C: WorkingMemoryItem│[touch,is_expired,to_dict]
   F: touch(self)
   F: is_expired(self)→bool
   F: to_dict(self)→Any
C: WorkingMemory│[__init__,add_memory,get_memory,update_memory,remove_memory,search_by_tag,search_by_type,search_by_importance,cleanup_expired,get_top_memories,+3]
   F: __init__(self,max_items)
   F: add_memory(self,memory_id,memory_type,content,importance,confidence,tags,metadata,ttl_seconds)→WorkingMemoryItem
   F: get_memory(self,memory_id)→Optional[WorkingMemoryItem]
   F: update_memory(self,memory_id,content,importance,confidence,metadata)→bool
   F: remove_memory(self,memory_id)→bool
   F: search_by_tag(self,tag)→List[WorkingMemoryItem]
   F: search_by_type(self,memory_type)→List[WorkingMemoryItem]
   F: search_by_importance(self,min_importance)→List[WorkingMemoryItem]
   F: cleanup_expired(self)
   F: get_top_memories(self,limit)→List[WorkingMemoryItem]
   F: stats(self)→Any
   F: clear(self)
   F: _evict_oldest(self)
---
