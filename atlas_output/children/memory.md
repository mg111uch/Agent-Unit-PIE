# 📂 memory
Generated: 2026-06-01 13:39:55
Files: 5

---

F047│episodic_memory.py│323
D: ●collections,dataclasses,kernel,time,typing,+1
C: Episode│[to_dict]
C: EpisodicMemory│[__init__,add_episode,create_episode,get_episode,get_recent_episodes,search_by_tag,search_by_entity,search_by_event,search_by_importance,get_timeline,+4]
---

F046│memory_engine.py│248
D: ●__future__,json,kernel,pathlib,typing
C: MemoryEngine│[__init__,save_object,load_object,delete_object,save_unit,load_unit,save_signal,load_signal,save_event,load_event,+9]
---

F049│pattern_memory.py│0
---

F048│semantic_memory.py│437
D: ●collections,dataclasses,kernel,time,typing,+1
C: SemanticNode│[to_dict]
C: SemanticEdge│[to_dict]
C: SemanticMemory│[__init__,add_node,create_node,add_edge,create_edge,get_node,get_edge,search_by_tag,search_by_concept,search_by_type,+8]
---

F045│working_memory.py│265
D: ●collections,dataclasses,kernel,time,typing,+1
C: WorkingMemoryItem│[touch,is_expired,to_dict]
C: WorkingMemory│[__init__,add_memory,get_memory,update_memory,remove_memory,search_by_tag,search_by_type,search_by_importance,cleanup_expired,get_top_memories,+3]
---
