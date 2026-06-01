# 📂 analyzers
Generated: 2026-06-01 13:39:55
Files: 4

---

F084│__init__.py│15
S: Analyzer modules for Codebase Atlas.
D: ►F083,F085,F086
---

F085│dependency_analyzer.py│216
S: Dependency analyzer for Codebase Atlas.
D: ►F070,F072 ●collections,pathlib,typing
C: DependencyAnalyzer│[__init__,analyze,_build_lookup_maps,_resolve_file_dependencies,_resolve_import,_resolve_relative_import,_detect_circular_dependencies,_build_reverse_dependencies]
   S: Analyzes and builds dependency relationships between files.
---

F083│entry_point_detector.py│168
S: Entry point detector for Codebase Atlas.
D: ►F070,F072 ●collections,typing
C: EntryPointDetector│[__init__,detect,_add_entry_point,_categorize_entry_point,get_critical_entry_points,get_entry_points_by_category,get_entry_points_for_file,format_entry_point]
   S: Detects and categorizes entry points across the codebase.
---

F086│impact_analyzer.py│245
S: Impact analyzer for Codebase Atlas.
D: ►F070,F072 ●collections,typing
C: ImpactAnalyzer│[__init__,analyze,_build_function_maps,_build_variable_maps,_build_impact_nodes,_resolve_call_relationships,_track_variable_dependencies,_calculate_risk_levels,_update_file_risk_levels,_get_function,+2]
   S: Analyzes impact of code changes across the codebase.
---
