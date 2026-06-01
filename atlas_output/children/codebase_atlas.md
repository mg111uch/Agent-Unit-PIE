# 📂 codebase_atlas
Generated: 2026-06-01 13:39:55
Files: 6

---

F074│__init__.py│51
S: Codebase Atlas - AI-powered codebase mapping for intelligent agent navigation.
D: ►F070,F072
---

F072│config.py│234│⚡
S: Configuration management for Codebase Atlas.
D: ●dataclasses,pathlib,typing
C: AtlasConfig│[]
   S: Main configuration class for Codebase Atlas.
F: get_default_config()→AtlasConfig
   ↳Called by: F073:main,F072:load_config,F073:generate_atlas
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F073:main],[F072:load_config],[F073:generate_atlas]
   S: Get default configuration.
F: load_config(config_path)→AtlasConfig
   ↳Calls: F072:get_default_config
   S: Load configuration from file or return default.
   S: Args:
   S: config_path: Path to config file (future: YAML support)
   S: Returns:
   S: AtlasConfig instance
F: get_file_category(file_path)→str
   ↳Called by: F071:_create_file_info
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F071:_create_file_info]
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
   ↳Called by: F077:generate
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F077:generate]
   S: Rough token estimation (1 token ≈ 4 characters).
   S: Args:
   S: text: Text to estimate
   S: Returns:
   S: Approximate token count
F: validate_config(config)→bool
   ↳Called by: F073:generate_atlas
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F073:generate_atlas]
   S: Validate configuration settings.
   S: Args:
   S: config: Configuration to validate
   S: Returns:
   S: True if valid
---

F073│main.py│263│⚡
S: Main entry point for Codebase Atlas.
D: ►F070,F071,F072,F075 ●analyzers,argparse,generators,sys,utils,+4
F: generate_atlas(project_dir,output_dir,config)→AtlasData
   ↳Called by: F073:main | Calls: F090:can_parse,F091:can_parse,F072:validate_config
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F073:main]
   S: Generate complete codebase atlas.
   S: Args:
   S: project_dir: Path to project directory to analyze
   S: output_dir: Path to output directory for atlas files
   S: config: Atlas configuration (uses default if None)
F: main()
   ↳Calls: F075:serve_atlas,F082:save_atlas_data,F082:load_atlas_data
   S: CLI entry point.
---

F070│models.py│258
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
---

F071│scanner.py│168
S: File scanner for Codebase Atlas.
D: ►F070,F072 ●os,pathlib,typing
C: FileScanner│[__init__,scan,_create_file_info,get_files_by_extension,get_python_files,get_javascript_files,get_html_files,get_config_files,get_files_by_category,get_statistics,+1]
   S: Scans project directory and discovers relevant files.
F: scan_project(config)→List[FileInfo]
   S: Convenience function to scan a project.
   S: Args:
   S: config: Atlas configuration
   S: Returns:
   S: List of FileInfo objects
---

F075│serve.py│496
S: Local HTTP server for interactive graph exploration.
D: ►F070,F072 ●generators,http,json,webbrowser
C: _GraphHandler←BaseHTTPRequestHandler│[do_GET,log_message]
   S: HTTP handler serving the graph explorer HTML.
F: build_graph_html(atlas_data,config)→str
   ↳Called by: F075:serve_atlas
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F075:serve_atlas]
   S: Build HTML page with embedded Mermaid graphs.
F: serve_atlas(atlas_data,config,host,port,open_browser)
   ↳Called by: F073:main | Calls: F075:build_graph_html
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F073:main]
   S: Start local HTTP server to explore dependency and call graphs.
   S: Args:
   S: atlas_data: Complete atlas analysis data
   S: config: Atlas configuration
   S: host: Host to bind the HTTP server to
---
