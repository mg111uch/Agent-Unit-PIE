# 📂 analyzers
Generated: 2026-07-21 18:31:40
Files: 4

---

F218│__init__.py│15
S: Analyzer modules for Codebase Atlas.
D: ►F217,F219,F220
---

F219│dependency_analyzer.py│216
S: Dependency analyzer for Codebase Atlas.
D: ►F003,F206 ●collections,pathlib,typing
C: DependencyAnalyzer│[__init__,analyze,_build_lookup_maps,_resolve_file_dependencies,_resolve_import,_resolve_relative_import,_detect_circular_dependencies,_build_reverse_dependencies]
   S: Analyzes and builds dependency relationships between files.
C: DependencyAnalyzer│[__init__,analyze,_build_lookup_maps,_resolve_file_dependencies,_resolve_import,_resolve_relative_import,_detect_circular_dependencies,_build_reverse_dependencies]
   S: Analyzes and builds dependency relationships between files.
   F: __init__(self,config)
      S: Initialize dependency analyzer.
      S: Args:
      S: config: Atlas configuration
   F: analyze(self,files)→DependencyGraph
      S: Build dependency graph from list of files.
      S: Args:
      S: files: List of parsed FileInfo objects
      S: Returns:
      S: Complete DependencyGraph
   F: _build_lookup_maps(self,files)
      S: Build lookup maps for fast file resolution.
      S: Args:
      S: files: List of files
   F: _resolve_file_dependencies(self,file_info)
   ↳Calls: F074:add,F051:add
      S: Resolve imports to actual file dependencies.
      S: Args:
      S: file_info: File to resolve dependencies for
   F: _resolve_import(self,file_info,import_name)→Optional[FileInfo]
      S: Resolve an import to a FileInfo object.
      S: Args:
      S: file_info: File containing the import
      S: import_name: Import module name
      S: Returns:
   F: _resolve_relative_import(self,file_info,rel_import)→Optional[FileInfo]
      S: Resolve relative import (./module or ../module).
      S: Args:
      S: file_info: File containing the import
      S: rel_import: Relative import string
      S: Returns:
   F: _detect_circular_dependencies(self)
   ↳Calls: F074:add,F051:add
      S: Detect circular dependencies using Tarjan's algorithm.
      S: Populates graph.circular_groups with sets of mutually dependent files.
   F: _build_reverse_dependencies(self,files)
      S: Build reverse dependency map and populate file circular deps.
      S: Args:
      S: files: List of all files
---

F217│entry_point_detector.py│168
S: Entry point detector for Codebase Atlas.
D: ►F003,F206 ●collections,typing
C: EntryPointDetector│[__init__,detect,_add_entry_point,_categorize_entry_point,get_critical_entry_points,get_entry_points_by_category,get_entry_points_for_file,format_entry_point]
   S: Detects and categorizes entry points across the codebase.
C: EntryPointDetector│[__init__,detect,_add_entry_point,_categorize_entry_point,get_critical_entry_points,get_entry_points_by_category,get_entry_points_for_file,format_entry_point]
   S: Detects and categorizes entry points across the codebase.
   F: __init__(self,config)
      S: Initialize entry point detector.
      S: Args:
      S: config: Atlas configuration
   F: detect(self,files)→Any
      S: Detect all entry points in the codebase.
      S: Args:
      S: files: List of parsed FileInfo objects
      S: Returns:
      S: List of (file_ref, func_name, category) tuples
   F: _add_entry_point(self,file_ref,func_name,file_info,func_info)
      S: Add an entry point with category detection.
      S: Args:
      S: file_ref: File reference ID
      S: func_name: Function name (None for file-level)
      S: file_info: FileInfo object
   F: _categorize_entry_point(self,file_info,func_info)→str
      S: Categorize an entry point.
      S: Args:
      S: file_info: FileInfo object
      S: func_info: FunctionInfo object (optional)
      S: Returns:
   F: get_critical_entry_points(self)→Any
      S: Get critical entry points (non-test).
      S: Returns:
      S: List of (file_ref, func_name, category) tuples
   F: get_entry_points_by_category(self,category)→Any
      S: Get entry points for a specific category.
      S: Args:
      S: category: Category name
      S: Returns:
      S: List of (file_ref, func_name) tuples
   F: get_entry_points_for_file(self,file_ref)→List[str]
      S: Get entry point function names for a file.
      S: Args:
      S: file_ref: File reference ID
      S: Returns:
      S: List of function names
   F: format_entry_point(self,file_ref,func_name,category,compact)→str
      S: Format entry point for display.
      S: Args:
      S: file_ref: File reference ID
      S: func_name: Function name
      S: category: Category
---

F220│impact_analyzer.py│245
S: Impact analyzer for Codebase Atlas.
D: ►F003,F206 ●collections,typing
C: ImpactAnalyzer│[__init__,analyze,_build_function_maps,_build_variable_maps,_build_impact_nodes,_resolve_call_relationships,_track_variable_dependencies,_calculate_risk_levels,_update_file_risk_levels,_get_function,+2]
   S: Analyzes impact of code changes across the codebase.
C: ImpactAnalyzer│[__init__,analyze,_build_function_maps,_build_variable_maps,_build_impact_nodes,_resolve_call_relationships,_track_variable_dependencies,_calculate_risk_levels,_update_file_risk_levels,_get_function,+2]
   S: Analyzes impact of code changes across the codebase.
   F: __init__(self,config)
      S: Initialize impact analyzer.
      S: Args:
      S: config: Atlas configuration
   F: analyze(self,files)→Any
      S: Build impact analysis for all functions.
      S: Args:
      S: files: List of parsed FileInfo objects
      S: Returns:
      S: Dictionary of impact nodes
   F: _build_function_maps(self,files)
      S: Build function lookup maps.
      S: Args:
      S: files: List of files
   F: _build_variable_maps(self,files)
   ↳Calls: F074:add,F051:add
      S: Build variable read/write tracking maps.
      S: Args:
      S: files: List of files
   F: _build_impact_nodes(self,files)
      S: Create ImpactNode for each function.
      S: Args:
      S: files: List of files
   F: _resolve_call_relationships(self)
      S: Resolve function calls to actual function references.
      S: Populates direct_callers and direct_calls in ImpactNodes.
   F: _track_variable_dependencies(self)
      S: Track indirect dependencies through variables.
      S: If function A writes var X, and function B reads var X,
      S: then B depends on A's output.
   F: _calculate_risk_levels(self)
      S: Calculate risk level for each function based on dependents.
      S: Uses thresholds from config:
      S: - HIGH: 3+ dependents
      S: - MEDIUM: 2 dependents
      S: - LOW: 1 dependent
   F: _update_file_risk_levels(self,files)
      S: Update FunctionInfo objects with calculated risk levels.
      S: Args:
      S: files: List of files
   F: _get_function(self,file_ref,func_name)→FunctionInfo
      S: Get FunctionInfo by file reference and function name.
      S: Args:
      S: file_ref: File reference ID
      S: func_name: Function name
      S: Returns:
   F: get_impact_chain(self,file_ref,func_name,depth)→Any
      S: Get impact chain for a function (who breaks if this changes).
      S: Args:
      S: file_ref: File reference ID
      S: func_name: Function name
      S: depth: Maximum depth (from config if None)
   F: get_critical_functions(self)→Any
      S: Get all critical functions (HIGH risk or entry points).
      S: Returns:
      S: List of (file_ref, func_name, ImpactNode) tuples
---
