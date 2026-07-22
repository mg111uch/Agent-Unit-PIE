# 📂 generators
Generated: 2026-07-21 18:31:40
Files: 3

---

F213│__init__.py│12
S: Generator modules for Codebase Atlas.
D: ►F211,F212
---

F212│base_generator.py│166
S: Base generator for Codebase Atlas.
D: ►F003,F206 ●collections,pathlib,typing,utils
C: BaseGenerator│[__init__,generate,_add_header,_add_overview,_add_entry_points,_add_high_risk_functions,_add_circular_dependencies,_add_navigation,_get_language_distribution,_get_children_groups,+3]
   S: Generates base.md overview file.
C: BaseGenerator│[__init__,generate,_add_header,_add_overview,_add_entry_points,_add_high_risk_functions,_add_circular_dependencies,_add_navigation,_get_language_distribution,_get_children_groups,+3]
   S: Generates base.md overview file.
   F: __init__(self,config,atlas_data)
   F: generate(self,output_dir)→str
   ↳Calls: F208:estimate_tokens,F216:write_file
      S: Generate base.md file.
   F: _add_header(self)
   ↳Calls: F216:get_timestamp
   F: _add_overview(self)
   F: _add_entry_points(self)
   F: _add_high_risk_functions(self)
   F: _add_circular_dependencies(self)
   F: _add_navigation(self)
   F: _get_language_distribution(self)→str
   F: _get_children_groups(self)→Any
   F: _get_produced_json_paths(self)→Set[str]
   F: _get_orphan_config_files(self,produced_json_paths)→List[FileInfo]
   F: _apply_budget_limits(self)
---

F211│detail_generator.py│105
S: Detail generator for Codebase Atlas.
D: ►F003,F206 ●collections,pathlib,typing,utils
C: DetailGenerator│[__init__,generate,_group_files,_get_produced_json_paths,_generate_child_file,_format_file_detail]
   S: Generates detailed children/*.md files.
C: DetailGenerator│[__init__,generate,_group_files,_get_produced_json_paths,_generate_child_file,_format_file_detail]
   S: Generates detailed children/*.md files.
   F: __init__(self,config,atlas_data)
   F: generate(self,output_dir)→List[str]
   ↳Calls: F216:ensure_directory
      S: Generate all children/*.md files.
   F: _group_files(self)→Any
   F: _get_produced_json_paths(self)→Set[str]
   F: _generate_child_file(self,children_dir,group_name,files)→str
   ↳Calls: F216:get_timestamp,F216:write_file
   F: _format_file_detail(self,file_info)→List[str]
   ↳Calls: F215:format_file
---
