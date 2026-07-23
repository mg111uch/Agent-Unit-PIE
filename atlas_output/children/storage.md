# 📂 storage
Generated: 2026-07-23 14:15:38
Files: 5

---

F009│hypothesis_storage.py│0
---

F008│pattern_storage.py│365
S: storage/pattern_storage.py
D: ●__future__,datetime,json,logging,pathlib,+1
C: PatternStorage│[__init__,save_pattern,load_pattern,list_patterns,search_patterns,update_indexes,save_pattern_summary,delete_pattern,pattern_exists,write_json,+3]
   S: Global persistent pattern storage manager.
C: PatternStorage│[__init__,save_pattern,load_pattern,list_patterns,search_patterns,update_indexes,save_pattern_summary,delete_pattern,pattern_exists,write_json,+3]
   S: Global persistent pattern storage manager.
   F: __init__(self,base_path)
   F: save_pattern(self,pattern)→str
      S: Persist pattern to storage.
   F: load_pattern(self,pattern_type,pattern_id)→Any
      S: Load pattern by type + ID.
   F: list_patterns(self,pattern_type)→List[str]
      S: List stored patterns.
   F: search_patterns(self,pattern_type,tags,min_confidence)→Any
      S: Basic metadata search over patterns.
   F: update_indexes(self,pattern)→None
      S: Update lightweight metadata indexes.
   F: save_pattern_summary(self,summary_name,summary_data)→None
      S: Store higher-order pattern summaries.
   F: delete_pattern(self,pattern_type,pattern_id)→bool
      S: Delete pattern file.
   F: pattern_exists(self,pattern_type,pattern_id)→bool
   F: write_json(self,path,data)→None
   F: read_json(self,path)→Any
   F: utc_now()→str
   ↳Called by: F034:update_timestamp,F036:deactivate,F035:deactivate
   ↳Impact: 🔴HIGH (9 dependents) | Breaks: [F034:update_timestamp],[F036:deactivate],[F035:deactivate]
   F: generate_pattern_id()→str
---

F005│raw_observation_storage.py│0
---

F007│timeline_storage.py│0
---

F006│unit_storage.py│413
S: storage/unit_storage.py
D: ●__future__,datetime,json,pathlib,shutil,+2
C: UnitStorage│[__init__,create_unit,load_unit,save_observation,save_event,save_signal,save_pattern,save_relation,save_summary,save_working_memory,+6]
   S: Universal persistent unit storage manager.
F: write_json(path,data)→None
F: read_json(path)→Any
C: UnitStorage│[__init__,create_unit,load_unit,save_observation,save_event,save_signal,save_pattern,save_relation,save_summary,save_working_memory,+6]
   S: Universal persistent unit storage manager.
   F: __init__(self,base_path)
   F: create_unit(self,unit_id,unit_type,metadata)→Any
      S: Create new unit directory structure.
   F: load_unit(self,unit_type,unit_id)→Any
      S: Load unit identity.
   F: save_observation(self,unit_type,unit_id,observation)→str
      S: Store observation.
   F: save_event(self,unit_type,unit_id,event)→str
      S: Store event.
   F: save_signal(self,unit_type,unit_id,signal)→str
      S: Store signal.
   F: save_pattern(self,unit_type,unit_id,pattern)→str
      S: Store pattern.
   F: save_relation(self,unit_type,unit_id,relation)→str
      S: Store relation.
   F: save_summary(self,unit_type,unit_id,summary_name,summary_data)→None
      S: Store compressed summaries.
   F: save_working_memory(self,unit_type,unit_id,memory_name,memory_data)→None
      S: Store generated working memory packets.
   F: list_units(self,unit_type)→List[str]
      S: List stored units.
   F: unit_exists(self,unit_type,unit_id)→bool
   F: delete_unit(self,unit_type,unit_id)→bool
      S: Delete unit recursively.
   F: get_unit_path(self,unit_type,unit_id)→Path
   F: write_json(self,path,data)→None
   F: read_json(self,path)→Any
---
