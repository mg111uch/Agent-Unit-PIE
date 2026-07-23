# 📂 utils
Generated: 2026-07-23 14:15:38
Files: 7

---

F083│__init__.py│29
S: Utility modules for Codebase Atlas.
D: ►F084,F085
---

F084│formatting.py│175
S: Formatting utilities for Codebase Atlas output.
D: ►F003,F075 ●typing
F: format_file(file_info,config,impact_nodes)→List[str]
   ↳Called by: F080:_format_file_detail | Calls: F084:_format_impact_lines
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F080:_format_file_detail]
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
   ↳Called by: F084:format_file
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F084:format_file]
   S: Format impact analysis lines for a function.
   S: Format:
   S: ↳Called by: F012,F045 | Calls: F024,F025
   S: ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F012,F045,F050]
   S: Args:
F: truncate_text(text,max_length,suffix)→str
   S: Truncate text to maximum length.
---

F028│ids.py│122
D: ●__future__,hashlib,typing,uuid
F: generate_id(prefix,length)→str
   ↳Called by: F035:create,F028:generate_unit_id,F034:add_behavior
   ↳Impact: 🔴HIGH (20 dependents) | Breaks: [F035:create],[F028:generate_unit_id],[F034:add_behavior]
   S: Generate short random ID.
   S: Example:
   S: unit_a1b2c3d4e5f6
F: generate_hash_id(content,prefix,length)→str
   S: Generate deterministic ID from content.
   S: Same input -> same ID.
F: generate_time_id(timestamp,prefix,length)→str
   S: Generate ID using timestamp hash.
F: generate_unit_id(unit_type,length)→str
   ↳Calls: F032:generate_id,F033:generate_id,F028:generate_id
F: generate_signal_id(signal_type,length)→str
   ↳Calls: F032:generate_id,F033:generate_id,F028:generate_id
F: generate_event_id(event_type,length)→str
   ↳Calls: F032:generate_id,F033:generate_id,F028:generate_id
F: generate_pattern_id(pattern_type,length)→str
   ↳Calls: F032:generate_id,F033:generate_id,F028:generate_id
F: generate_relation_id(relation_type,length)→str
   ↳Calls: F032:generate_id,F033:generate_id,F028:generate_id
F: generate_hypothesis_id(hypothesis_type,length)→str
   ↳Calls: F032:generate_id,F033:generate_id,F028:generate_id
F: generate_session_id(agent_name)→str
   ↳Calls: F032:generate_id,F033:generate_id,F028:generate_id
F: is_valid_id(value)→bool
   ↳Called by: F028:extract_suffix,F028:extract_prefix
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F028:extract_suffix],[F028:extract_prefix]
   S: Minimal validation check.
F: extract_prefix(entity_id)→Optional[str]
   ↳Calls: F028:is_valid_id
F: extract_suffix(entity_id)→Optional[str]
   ↳Calls: F028:is_valid_id
---

F085│io_helpers.py│139
S: I/O helper utilities for Codebase Atlas.
D: ●datetime,os,pathlib,pickle,shutil,+1
F: ensure_directory(dir_path)→Path
   ↳Called by: F080:generate,F085:append_to_file,F078:generate_atlas
   ↳Impact: 🔴HIGH (4 dependents) | Breaks: [F080:generate],[F085:append_to_file],[F078:generate_atlas]
   S: Ensure a directory exists, create if it doesn't.
   S: Args:
   S: dir_path: Path to directory
   S: Returns:
   S: Path object for the directory
F: write_file(file_path,content,encoding)→bool
   ↳Called by: F081:generate,F080:_generate_child_file | Calls: F085:ensure_directory
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F081:generate],[F080:_generate_child_file]
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
   ↳Called by: F080:_generate_child_file,F081:_add_header
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F080:_generate_child_file],[F081:_add_header]
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
   ↳Called by: F078:generate_atlas
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F078:generate_atlas]
   S: Remove all files and subdirectories in directory except specified ones.
   S: Args:
   S: dir_path: Directory to clean
   S: keep_files: List of filenames to keep
F: append_to_file(file_path,content,encoding)
   ↳Calls: F085:ensure_directory
   S: Append content to file.
   S: Args:
   S: file_path: Path to file
   S: content: Content to append
   S: encoding: File encoding
---

F025│logger.py│144
D: ●__future__,kernel,logging,pathlib,typing
C: SqliteLogHandler←logging.Handler│[__init__,db,emit]
F: get_logger(name,level,log_to_console,log_to_sqlite)→logging.Logger
   ↳Called by: F025:get_child_logger
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F025:get_child_logger]
   S: Create or retrieve cached logger.
   S: Log entries go to console and SQLite (replaces per-file log handlers).
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
   ↳Calls: F025:get_logger
   S: Example:
   S: kernel.memory
   S: kernel.simulation
C: SqliteLogHandler←logging.Handler│[__init__,db,emit]
   F: __init__(self)
   F: db(self)
   F: emit(self,record)
---

F027│paths.py│118
D: ●__future__,os,pathlib,typing
F: ensure_directories_exist()
F: get_kb_path(domain,entity_name)→Path
   S: Example:
   S: data/kb/cities/lucknow/
F: get_simulation_path(simulation_type,simulation_name)→Path
   S: Example:
   S: data/simulations/cities/lucknow_sim/
F: get_log_file_path(log_name)→Path
F: get_temp_file_path(filename)→Path
F: get_cache_file_path(filename)→Path
F: ensure_parent_dir(file_path)
F: path_exists(path)→bool
F: create_dir(path)
F: get_env(key,default)→Optional[str]
---

F026│timestamps.py│165
D: ●__future__,datetime,typing
F: utc_now()→str
   ↳Called by: F034:update_timestamp,F036:deactivate,F035:deactivate
   ↳Impact: 🔴HIGH (9 dependents) | Breaks: [F034:update_timestamp],[F036:deactivate],[F035:deactivate]
   S: Returns ISO UTC timestamp.
F: local_now()→str
   S: Returns local timezone timestamp.
F: unix_timestamp()→int
   S: Returns unix timestamp in seconds.
F: parse_timestamp(timestamp)→datetime
   ↳Called by: F026:is_before,F026:add_seconds,F026:human_readable_delta
   ↳Impact: 🔴HIGH (7 dependents) | Breaks: [F026:is_before],[F026:add_seconds],[F026:human_readable_delta]
   S: Parse ISO timestamp string.
F: format_timestamp(dt)→str
   ↳Called by: F026:add_seconds,F026:add_days
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F026:add_seconds],[F026:add_days]
   S: Convert datetime to ISO string.
F: seconds_between(start,end)→float
   ↳Called by: F026:minutes_between,F026:hours_between,F026:days_between | Calls: F026:parse_timestamp
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F026:minutes_between],[F026:hours_between],[F026:days_between]
   S: Difference in seconds.
F: minutes_between(start,end)→float
   ↳Calls: F026:seconds_between
F: hours_between(start,end)→float
   ↳Calls: F026:seconds_between
F: days_between(start,end)→float
   ↳Calls: F026:seconds_between
F: add_seconds(timestamp,seconds)→str
   ↳Called by: F026:add_hours,F026:add_minutes | Calls: F026:parse_timestamp,F026:format_timestamp
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F026:add_hours],[F026:add_minutes]
F: add_minutes(timestamp,minutes)→str
   ↳Calls: F026:add_seconds
F: add_hours(timestamp,hours)→str
   ↳Calls: F026:add_seconds
F: add_days(timestamp,days)→str
   ↳Calls: F026:parse_timestamp,F026:format_timestamp
F: is_before(timestamp_a,timestamp_b)→bool
   ↳Calls: F026:parse_timestamp
F: is_after(timestamp_a,timestamp_b)→bool
   ↳Calls: F026:parse_timestamp
F: is_between(timestamp,start,end)→bool
   ↳Calls: F026:parse_timestamp
F: human_readable_delta(past_timestamp)→str
   ↳Calls: F026:parse_timestamp
   S: Example:
   S: 5 minutes ago
   S: 2 hours ago
---
