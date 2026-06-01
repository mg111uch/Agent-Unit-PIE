# 📂 utils
Generated: 2026-06-01 13:39:55
Files: 7

---

F080│__init__.py│33
S: Utility modules for Codebase Atlas.
D: ►F081,F082
---

F081│formatting.py│147
S: Formatting utilities for Codebase Atlas output.
D: ►F070,F072 ●typing
F: format_file(file_info,config,impact_nodes)→List[str]
   ↳Called by: F076:_format_file_detail | Calls: F081:_format_impact_lines
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F076:_format_file_detail]
   S: Format FileInfo in unified notation with docstrings.
   S: Each function is listed individually with its signature, impact analysis,
   S: and docstring so agents understand behavior without reading source files.
   S: Format:
   S: F001│main.py│250│⚡
F: format_function_signature(func,compact)→str
   S: Format function signature.
F: format_dependency_list(deps,dep_type,config)→str
   S: Format dependency list.
F: _format_impact_lines(func,impact,config)→List[str]
   ↳Called by: F081:format_file
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F081:format_file]
   S: Format impact analysis lines for a function.
   S: Format:
   S: ↳Called by: F012,F045 | Calls: F024,F025
   S: ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F012,F045,F050]
   S: Args:
F: truncate_text(text,max_length,suffix)→str
   S: Truncate text to maximum length.
---

F025│ids.py│136
D: ●__future__,hashlib,typing,uuid
F: generate_id(prefix,length)→str
   ↳Called by: F025:generate_signal_id,F029:add_evidence,F030:add_evidence
   ↳Impact: 🔴HIGH (20 dependents) | Breaks: [F025:generate_signal_id],[F029:add_evidence],[F030:add_evidence]
   S: Generate short random ID.
   S: Example:
   S: unit_a1b2c3d4e5f6
F: generate_hash_id(content,prefix,length)→str
   S: Generate deterministic ID from content.
   S: Same input -> same ID.
F: generate_time_id(timestamp,prefix,length)→str
   S: Generate ID using timestamp hash.
F: generate_unit_id(unit_type,length)→str
   ↳Calls: F030:generate_id,F033:generate_id,F032:generate_id
F: generate_signal_id(signal_type,length)→str
   ↳Calls: F030:generate_id,F033:generate_id,F032:generate_id
F: generate_event_id(event_type,length)→str
   ↳Calls: F030:generate_id,F033:generate_id,F032:generate_id
F: generate_pattern_id(pattern_type,length)→str
   ↳Calls: F030:generate_id,F033:generate_id,F032:generate_id
F: generate_relation_id(relation_type,length)→str
   ↳Calls: F030:generate_id,F033:generate_id,F032:generate_id
F: generate_hypothesis_id(hypothesis_type,length)→str
   ↳Calls: F030:generate_id,F033:generate_id,F032:generate_id
F: generate_session_id(agent_name)→str
   ↳Calls: F030:generate_id,F033:generate_id,F032:generate_id
F: is_valid_id(value)→bool
   ↳Called by: F025:extract_suffix,F025:extract_prefix
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F025:extract_suffix],[F025:extract_prefix]
   S: Minimal validation check.
F: extract_prefix(entity_id)→Optional[str]
   ↳Calls: F025:is_valid_id
F: extract_suffix(entity_id)→Optional[str]
   ↳Calls: F025:is_valid_id
---

F082│io_helpers.py│151
S: I/O helper utilities for Codebase Atlas.
D: ●datetime,os,pathlib,pickle,typing,+1
F: ensure_directory(dir_path)→Path
   ↳Called by: F082:append_to_file,F082:write_file,F076:generate
   ↳Impact: 🔴HIGH (4 dependents) | Breaks: [F082:append_to_file],[F082:write_file],[F076:generate]
   S: Ensure a directory exists, create if it doesn't.
   S: Args:
   S: dir_path: Path to directory
   S: Returns:
   S: Path object for the directory
F: write_file(file_path,content,encoding)→bool
   ↳Called by: F077:generate,F076:_generate_child_file | Calls: F082:ensure_directory
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F077:generate],[F076:_generate_child_file]
   S: Write content to file with error handling.
   S: Args:
   S: file_path: Path to file
   S: content: Content to write
   S: encoding: File encoding
F: read_file(file_path,encoding)→Optional[str]
   S: Read file content with error handling.
   S: Args:
   S: file_path: Path to file
   S: encoding: File encoding
   S: Returns:
F: get_timestamp()→str
   ↳Called by: F076:_generate_child_file,F077:_add_header
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F076:_generate_child_file],[F077:_add_header]
   S: Get current timestamp in readable format.
   S: Returns:
   S: Timestamp string (YYYY-MM-DD HH:MM:SS)
F: get_file_size(file_path)→int
   S: Get file size in bytes.
   S: Args:
   S: file_path: Path to file
   S: Returns:
   S: File size in bytes, or 0 if file doesn't exist
F: format_file_size(size_bytes)→str
   S: Format file size in human-readable format.
   S: Args:
   S: size_bytes: Size in bytes
   S: Returns:
   S: Formatted string (e.g., "1.5 KB", "2.3 MB")
F: list_files_in_directory(dir_path,pattern)→list
   S: List all files in directory matching pattern.
   S: Args:
   S: dir_path: Directory path
   S: pattern: Glob pattern (default: all files)
   S: Returns:
F: clean_directory(dir_path,keep_files)
   ↳Called by: F073:generate_atlas
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F073:generate_atlas]
   S: Remove all files and subdirectories in directory except specified ones.
   S: Args:
   S: dir_path: Directory to clean
   S: keep_files: List of filenames to keep
F: save_atlas_data(atlas_data,dir_path)
   ↳Called by: F073:main
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F073:main]
   S: Serialize atlas data to pickle file.
F: load_atlas_data(dir_path)
   ↳Called by: F073:main
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F073:main]
   S: Load atlas data from pickle file.
F: append_to_file(file_path,content,encoding)
   ↳Calls: F082:ensure_directory
   S: Append content to file.
   S: Args:
   S: file_path: Path to file
   S: content: Content to append
   S: encoding: File encoding
---

F022│logger.py│154
D: ●__future__,kernel,logging,pathlib,typing
F: get_logger(name,level,log_to_console,log_to_file,max_bytes,backup_count)→logging.Logger
   ↳Called by: F022:get_child_logger
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F022:get_child_logger]
   S: Create or retrieve cached logger.
F: debug(message)
F: info(message)
F: warning(message)
F: error(message)
F: critical(message)
F: log_exception(exception,context)
   S: Logs exception with traceback.
F: structured_log(level,event_type,data)
   S: Structured event logging.
F: get_child_logger(child_name)→logging.Logger
   ↳Calls: F022:get_logger
   S: Example:
   S: kernel.memory
   S: kernel.simulation
---

F024│paths.py│160
D: ●__future__,os,pathlib,typing
F: ensure_directories_exist()
F: get_kb_path(domain,entity_name)→Path
   S: Example:
   S: data/kb/cities/lucknow/
F: get_memory_path(memory_type,entity_id)→Path
   S: Example:
   S: data/memory/semantic/human_abc123/
F: get_simulation_path(simulation_type,simulation_name)→Path
   S: Example:
   S: data/simulations/cities/lucknow_sim/
F: get_log_file_path(log_name)→Path
F: get_temp_file_path(filename)→Path
F: get_cache_file_path(filename)→Path
F: ensure_parent_dir(file_path)
   ↳Called by: F046:save_object
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F046:save_object]
F: path_exists(path)→bool
F: create_dir(path)
F: get_env(key,default)→Optional[str]
---

F023│timestamps.py│185
D: ●__future__,datetime,typing
F: utc_now()→str
   ↳Called by: F033:deactivate,F032:deactivate,F029:deactivate
   ↳Impact: 🔴HIGH (9 dependents) | Breaks: [F033:deactivate],[F032:deactivate],[F029:deactivate]
   S: Returns ISO UTC timestamp.
F: local_now()→str
   S: Returns local timezone timestamp.
F: unix_timestamp()→int
   S: Returns unix timestamp in seconds.
F: parse_timestamp(timestamp)→datetime
   ↳Called by: F023:human_readable_delta,F023:add_days,F023:add_seconds
   ↳Impact: 🔴HIGH (7 dependents) | Breaks: [F023:human_readable_delta],[F023:add_days],[F023:add_seconds]
   S: Parse ISO timestamp string.
F: format_timestamp(dt)→str
   ↳Called by: F023:add_seconds,F023:add_days
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F023:add_seconds],[F023:add_days]
   S: Convert datetime to ISO string.
F: seconds_between(start,end)→float
   ↳Called by: F023:minutes_between,F023:days_between,F023:hours_between | Calls: F023:parse_timestamp
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F023:minutes_between],[F023:days_between],[F023:hours_between]
   S: Difference in seconds.
F: minutes_between(start,end)→float
   ↳Calls: F023:seconds_between
F: hours_between(start,end)→float
   ↳Calls: F023:seconds_between
F: days_between(start,end)→float
   ↳Calls: F023:seconds_between
F: add_seconds(timestamp,seconds)→str
   ↳Called by: F023:add_hours,F023:add_minutes | Calls: F023:parse_timestamp,F023:format_timestamp
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F023:add_hours],[F023:add_minutes]
F: add_minutes(timestamp,minutes)→str
   ↳Calls: F023:add_seconds
F: add_hours(timestamp,hours)→str
   ↳Calls: F023:add_seconds
F: add_days(timestamp,days)→str
   ↳Calls: F023:parse_timestamp,F023:format_timestamp
F: is_before(timestamp_a,timestamp_b)→bool
   ↳Calls: F023:parse_timestamp
F: is_after(timestamp_a,timestamp_b)→bool
   ↳Calls: F023:parse_timestamp
F: is_between(timestamp,start,end)→bool
   ↳Calls: F023:parse_timestamp
F: human_readable_delta(past_timestamp)→str
   ↳Calls: F023:parse_timestamp
   S: Example:
   S: 5 minutes ago
   S: 2 hours ago
---
