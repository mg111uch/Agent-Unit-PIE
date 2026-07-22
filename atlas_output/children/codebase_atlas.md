# 📂 codebase_atlas
Generated: 2026-07-21 18:31:40
Files: 5

---

F210│__init__.py│51
S: Codebase Atlas - AI-powered codebase mapping for intelligent agent navigation.
D: ►F003,F206
---

F208│config.py│234│⚡
S: Configuration management for Codebase Atlas.
D: ●dataclasses,pathlib,typing
C: AtlasConfig│[]
   S: Main configuration class for Codebase Atlas.
F: get_default_config()→AtlasConfig
   ↳Called by: F209:generate_atlas,F209:main,F208:load_config
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F209:generate_atlas],[F209:main],[F208:load_config]
   S: Get default configuration.
F: load_config(config_path)→AtlasConfig
   ↳Calls: F208:get_default_config
   S: Load configuration from file or return default.
   S: Args:
   S: config_path: Path to config file (future: YAML support)
   S: Returns:
   S: AtlasConfig instance
F: get_file_category(file_path)→str
   ↳Called by: F207:_create_file_info
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F207:_create_file_info]
   S: Categorize a file based on its path.
   S: Args:
   S: file_path: Path to the file
   S: Returns:
   S: Category string ('core', 'api', 'utils', etc.)
F: get_priority_level(risk_level,is_entry)→str
   S: Get priority level for base.md inclusion.
   S: Args:
   S: risk_level: 'high', 'medium', 'low', or 'safe'
   S: is_entry: Whether this is an entry point
   S: Returns:
F: estimate_tokens(text)→int
   ↳Called by: F212:generate
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F212:generate]
   S: Rough token estimation (1 token ≈ 4 characters).
   S: Args:
   S: text: Text to estimate
   S: Returns:
   S: Approximate token count
F: validate_config(config)→bool
   ↳Called by: F209:generate_atlas
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F209:generate_atlas]
   S: Validate configuration settings.
   S: Args:
   S: config: Configuration to validate
   S: Returns:
   S: True if valid
C: AtlasConfig│[]
   S: Main configuration class for Codebase Atlas.
---

F209│main.py│333│⚡
S: Main entry point for Codebase Atlas.
D: ►F003,F206,F207,F300 ●argparse,generators,pathlib,traceback,typing,+6
F: generate_atlas(project_dir,output_dir,config)→Any
   ↳Called by: F209:main | Calls: F251:update_from_graph,F258:can_parse,F257:can_parse
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F209:main]
   S: Generate complete codebase atlas.
   S: Args:
   S: project_dir: Path to project directory to analyze
   S: output_dir: Path to output directory for atlas files
   S: config: Atlas configuration (uses default if None)
F: _run_app(app,args)
   ↳Called by: F209:main
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F209:main]
F: main()
   ↳Calls: F209:generate_atlas,F225:create_app,F209:_run_app
   S: CLI entry point.
---

F206│models.py│261
S: Data models for Codebase Atlas.
D: ●dataclasses,enum,pathlib,typing
C: RiskLevel←Enum│[]
   S: Risk level for code changes.
C: FileCategory←Enum│[]
   S: File category for organization.
C: FunctionInfo│[get_signature,get_dependent_count]
   S: Information about a function or method.
C: ClassInfo│[get_method_names,get_public_methods]
   S: Information about a class.
C: FileInfo│[get_all_functions,get_high_risk_functions,get_entry_functions]
   S: Complete information about a single file.
C: DependencyEdge│[]
   S: An edge in the dependency graph.
C: DependencyGraph│[add_edge,get_dependents,get_dependencies,is_circular]
   S: Complete dependency graph for the project.
C: ImpactNode│[calculate_impact,get_all_breaks]
   S: Impact analysis for a single function.
C: AtlasData│[add_file,get_file_by_ref,get_files_by_category,get_high_risk_files,get_critical_functions]
   S: Complete atlas data for the entire project.
C: RiskLevel←Enum│[]
   S: Risk level for code changes.
C: FileCategory←Enum│[]
   S: File category for organization.
C: FunctionInfo│[get_signature,get_dependent_count]
   S: Information about a function or method.
   F: get_signature(self,compact)→str
      S: Get function signature string.
   F: get_dependent_count(self)→int
      S: Get total number of dependents (callers + consumers).
C: ClassInfo│[get_method_names,get_public_methods]
   S: Information about a class.
   F: get_method_names(self)→List[str]
      S: Get list of method names.
   F: get_public_methods(self)→List[FunctionInfo]
      S: Get only public methods (not starting with _).
C: FileInfo│[get_all_functions,get_high_risk_functions,get_entry_functions]
   S: Complete information about a single file.
   F: get_all_functions(self)→List[FunctionInfo]
      S: Get all functions including methods from classes.
   F: get_high_risk_functions(self)→List[FunctionInfo]
      S: Get functions with HIGH risk level.
   F: get_entry_functions(self)→List[FunctionInfo]
      S: Get functions marked as entry points.
C: DependencyEdge│[]
   S: An edge in the dependency graph.
C: DependencyGraph│[add_edge,get_dependents,get_dependencies,is_circular]
   S: Complete dependency graph for the project.
   F: add_edge(self,source,target,import_type)
   ↳Calls: F074:add,F051:add
      S: Add a dependency edge.
   F: get_dependents(self,ref_id)→Set[str]
      S: Get all files that depend on this file.
   F: get_dependencies(self,ref_id)→Set[str]
      S: Get all files this file depends on.
   F: is_circular(self,ref_id)→bool
      S: Check if file is part of circular dependency.
C: ImpactNode│[calculate_impact,get_all_breaks]
   S: Impact analysis for a single function.
   F: calculate_impact(self)
      S: Calculate total impact count and risk level.
   F: get_all_breaks(self)→Any
      S: Get all things that break if this function changes.
      S: Returns:
      S: List of (file_ref, function_name, reason) tuples
C: AtlasData│[add_file,get_file_by_ref,get_files_by_category,get_high_risk_files,get_critical_functions]
   S: Complete atlas data for the entire project.
   F: add_file(self,file_info)
      S: Add a file to the atlas.
   F: get_file_by_ref(self,ref_id)→Optional[FileInfo]
      S: Get file by reference ID.
   F: get_files_by_category(self,category)→List[FileInfo]
      S: Get all files in a category.
   F: get_high_risk_files(self)→List[FileInfo]
      S: Get files with high-risk functions.
   F: get_critical_functions(self)→Any
      S: Get all functions with HIGH risk or entry points.
---

F207│scanner.py│168
S: File scanner for Codebase Atlas.
D: ►F003,F206 ●os,pathlib,typing
C: FileScanner│[__init__,scan,_create_file_info,get_files_by_extension,get_python_files,get_javascript_files,get_html_files,get_config_files,get_files_by_category,get_statistics,+1]
   S: Scans project directory and discovers relevant files.
F: scan_project(config)→List[FileInfo]
   S: Convenience function to scan a project.
   S: Args:
   S: config: Atlas configuration
   S: Returns:
   S: List of FileInfo objects
C: FileScanner│[__init__,scan,_create_file_info,get_files_by_extension,get_python_files,get_javascript_files,get_html_files,get_config_files,get_files_by_category,get_statistics,+1]
   S: Scans project directory and discovers relevant files.
   F: __init__(self,config)
      S: Initialize scanner.
      S: Args:
      S: config: Atlas configuration
   F: scan(self)→List[FileInfo]
      S: Scan project directory and return list of FileInfo objects.
      S: Returns:
      S: List of FileInfo objects
   F: _create_file_info(self,file_path,ext)→FileInfo
   ↳Calls: F208:get_file_category
      S: Create FileInfo object for a file.
      S: Args:
      S: file_path: Absolute path to file
      S: ext: File extension
      S: Returns:
   F: get_files_by_extension(self,extensions)→List[FileInfo]
      S: Get files matching specific extensions.
      S: Args:
      S: extensions: Set of extensions (e.g., {'.py', '.js'})
      S: Returns:
      S: List of matching FileInfo objects
   F: get_python_files(self)→List[FileInfo]
      S: Get all Python files.
   F: get_javascript_files(self)→List[FileInfo]
      S: Get all JavaScript/TypeScript files.
   F: get_html_files(self)→List[FileInfo]
      S: Get all HTML files.
   F: get_config_files(self)→List[FileInfo]
      S: Get all config files.
   F: get_files_by_category(self,category)→List[FileInfo]
      S: Get files by category.
      S: Args:
      S: category: FileCategory enum value
      S: Returns:
      S: List of matching FileInfo objects
   F: get_statistics(self)→dict
      S: Get scanning statistics.
      S: Returns:
      S: Dictionary with statistics
   F: print_statistics(self)
      S: Print scanning statistics to console.
---
