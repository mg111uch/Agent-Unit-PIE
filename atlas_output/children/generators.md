# 📂 generators
Generated: 2026-06-01 13:39:55
Files: 4

---

F078│__init__.py│15
S: Generator modules for Codebase Atlas.
D: ►F076,F077,F079
---

F077│base_generator.py│143
S: Base generator for Codebase Atlas.
D: ►F070,F072 ●collections,pathlib,typing,utils
C: BaseGenerator│[__init__,generate,_add_header,_add_overview,_add_entry_points,_add_high_risk_functions,_add_circular_dependencies,_add_navigation,_get_language_distribution,_get_children_groups,+1]
   S: Generates base.md overview file.
---

F076│detail_generator.py│86
S: Detail generator for Codebase Atlas.
D: ►F070,F072 ●collections,pathlib,typing,utils
C: DetailGenerator│[__init__,generate,_group_files,_generate_child_file,_format_file_detail]
   S: Generates detailed children/*.md files.
---

F079│mermaid_generator.py│153
S: Mermaid graph generator for Codebase Atlas.
D: ►F070,F072 ●re,typing
C: MermaidGenerator│[__init__,_sanitize_id,_sanitize_label,_is_init_py,generate_dependency_graph,generate_call_graph,_find_function,_func_node_id,_file_risk_class,_func_risk_class,+1]
   S: Generates Mermaid.js flowcharts from atlas data.
---
