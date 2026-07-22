# 📂 utils
Generated: 2026-07-21 18:31:40
Files: 8

---

F214│__init__.py│29
S: Utility modules for Codebase Atlas.
D: ►F215,F216
---

F215│formatting.py│175
S: Formatting utilities for Codebase Atlas output.
D: ►F003,F206 ●typing
F: format_file(file_info,config,impact_nodes)→List[str]
   ↳Called by: F211:_format_file_detail | Calls: F215:_format_impact_lines
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F211:_format_file_detail]
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
   ↳Called by: F215:format_file
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F215:format_file]
   S: Format impact analysis lines for a function.
   S: Format:
   S: ↳Called by: F012,F045 | Calls: F024,F025
   S: ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F012,F045,F050]
   S: Args:
F: truncate_text(text,max_length,suffix)→str
   S: Truncate text to maximum length.
---

F232│geometry.js│252
F: distance(x1,y1,x2,y2)
   ↳Calls: F232:clamp,F232:rectsIntersect,F232:rectCenter
F: midpoint(x1,y1,x2,y2)
   ↳Called by: F232:distance | Calls: F232:clamp,F232:rectsIntersect,F232:rectCenter
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F232:distance]
F: lerp(a,b,t)
   ↳Called by: F232:midpoint,F232:distance | Calls: F232:clamp,F232:rectsIntersect,F232:rectCenter
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F232:midpoint],[F232:distance]
F: clamp(value,min,max)
   ↳Called by: F232:midpoint,F232:distance,F232:lerp | Calls: F232:rectsIntersect,F232:rectCenter,F232:lineRectIntersection
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F232:midpoint],[F232:distance],[F232:lerp]
F: rectCenter(rect)
   ↳Called by: F232:clamp,F232:rectsIntersect,F232:rectCenter | Calls: F232:rectsIntersect,F232:rectCenter,F232:lineRectIntersection
   ↳Impact: 🔴HIGH (11 dependents) | Breaks: [F232:clamp],[F232:rectsIntersect],[F232:rectCenter]
F: pointInRect(x,y,rect)
   ↳Called by: F232:clamp,F232:rectCenter,F232:lerp | Calls: F232:rectsIntersect,F249:if,F248:if
   ↳Impact: 🔴HIGH (5 dependents) | Breaks: [F232:clamp],[F232:rectCenter],[F232:lerp]
F: rectsIntersect(a,b)
   ↳Called by: F232:clamp,F232:rectCenter,F232:lerp | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (6 dependents) | Breaks: [F232:clamp],[F232:rectCenter],[F232:lerp]
F: getNodeRect(node)
   ↳Called by: F232:clamp,F232:rectsIntersect,F232:rectCenter | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (13 dependents) | Breaks: [F232:clamp],[F232:rectsIntersect],[F232:rectCenter]
F: getNodeCenter(node)
   ↳Called by: F232:clamp,F233:zoomToNode,F232:rectsIntersect | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (10 dependents) | Breaks: [F232:clamp],[F233:zoomToNode],[F232:rectsIntersect]
F: lineRectIntersection(rect,targetX,targetY)
   ↳Called by: F232:clamp,F232:rectsIntersect,F232:rectCenter | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (7 dependents) | Breaks: [F232:clamp],[F232:rectsIntersect],[F232:rectCenter]
F: nodeConnectionPoints(sourceNode,targetNode)
   ↳Called by: F241:shouldRenderLabel,F241:createLine,F232:lineRectIntersection | Calls: F232:rectCenter,F232:lineRectIntersection,F232:expandBounds
   ↳Impact: 🔴HIGH (4 dependents) | Breaks: [F241:shouldRenderLabel],[F241:createLine],[F232:lineRectIntersection]
F: expandBounds(bounds,padding)
   ↳Called by: F243:for,F232:nodeConnectionPoints,F233:zoomToCluster | Calls: F249:if,F236:for,F248:if
   ↳Impact: 🔴HIGH (9 dependents) | Breaks: [F243:for],[F232:nodeConnectionPoints],[F233:zoomToCluster]
F: computeNodeBounds(nodes)
   ↳Called by: F243:for,F232:expandBounds,F233:if | Calls: F249:if,F236:for,F232:angleBetween
   ↳Impact: 🔴HIGH (8 dependents) | Breaks: [F243:for],[F232:expandBounds],[F233:if]
F: angleBetween(x1,y1,x2,y2)
   ↳Called by: F232:computeNodeBounds | Calls: F232:radiansToDegrees
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F232:computeNodeBounds]
F: radiansToDegrees(radians)
   ↳Called by: F232:angleBetween
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F232:angleBetween]
---

F068│ids.py│122
D: ●__future__,hashlib,typing,uuid
F: generate_id(prefix,length)→str
   ↳Called by: F109:emit_event,F068:generate_hypothesis_id,F068:generate_signal_id
   ↳Impact: 🔴HIGH (20 dependents) | Breaks: [F109:emit_event],[F068:generate_hypothesis_id],[F068:generate_signal_id]
   S: Generate short random ID.
   S: Example:
   S: unit_a1b2c3d4e5f6
F: generate_hash_id(content,prefix,length)→str
   S: Generate deterministic ID from content.
   S: Same input -> same ID.
F: generate_time_id(timestamp,prefix,length)→str
   S: Generate ID using timestamp hash.
F: generate_unit_id(unit_type,length)→str
   ↳Calls: F073:generate_id,F074:generate_id,F076:generate_id
F: generate_signal_id(signal_type,length)→str
   ↳Calls: F073:generate_id,F074:generate_id,F076:generate_id
F: generate_event_id(event_type,length)→str
   ↳Calls: F073:generate_id,F074:generate_id,F076:generate_id
F: generate_pattern_id(pattern_type,length)→str
   ↳Calls: F073:generate_id,F074:generate_id,F076:generate_id
F: generate_relation_id(relation_type,length)→str
   ↳Calls: F073:generate_id,F074:generate_id,F076:generate_id
F: generate_hypothesis_id(hypothesis_type,length)→str
   ↳Calls: F073:generate_id,F074:generate_id,F076:generate_id
F: generate_session_id(agent_name)→str
   ↳Calls: F073:generate_id,F074:generate_id,F076:generate_id
F: is_valid_id(value)→bool
   ↳Called by: F068:extract_suffix,F068:extract_prefix
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F068:extract_suffix],[F068:extract_prefix]
   S: Minimal validation check.
F: extract_prefix(entity_id)→Optional[str]
   ↳Calls: F068:is_valid_id
F: extract_suffix(entity_id)→Optional[str]
   ↳Calls: F068:is_valid_id
---

F216│io_helpers.py│139
S: I/O helper utilities for Codebase Atlas.
D: ●os,pathlib,pickle,shutil,typing,+1
F: ensure_directory(dir_path)→Path
   ↳Called by: F211:generate,F209:generate_atlas,F216:append_to_file
   ↳Impact: 🔴HIGH (4 dependents) | Breaks: [F211:generate],[F209:generate_atlas],[F216:append_to_file]
   S: Ensure a directory exists, create if it doesn't.
   S: Args:
   S: dir_path: Path to directory
   S: Returns:
   S: Path object for the directory
F: write_file(file_path,content,encoding)→bool
   ↳Called by: F212:generate,F211:_generate_child_file | Calls: F216:ensure_directory
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F212:generate],[F211:_generate_child_file]
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
   ↳Called by: F212:_add_header,F211:_generate_child_file
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F212:_add_header],[F211:_generate_child_file]
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
   ↳Called by: F209:generate_atlas
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F209:generate_atlas]
   S: Remove all files and subdirectories in directory except specified ones.
   S: Args:
   S: dir_path: Directory to clean
   S: keep_files: List of filenames to keep
F: append_to_file(file_path,content,encoding)
   ↳Calls: F216:ensure_directory
   S: Append content to file.
   S: Args:
   S: file_path: Path to file
   S: content: Content to append
   S: encoding: File encoding
---

F065│logger.py│144
D: ●__future__,kernel,logging,pathlib,typing
C: SqliteLogHandler←logging.Handler│[__init__,db,emit]
F: get_logger(name,level,log_to_console,log_to_sqlite)→logging.Logger
   ↳Called by: F065:get_child_logger
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F065:get_child_logger]
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
   ↳Calls: F065:get_logger
   S: Example:
   S: kernel.memory
   S: kernel.simulation
C: SqliteLogHandler←logging.Handler│[__init__,db,emit]
   F: __init__(self)
   F: db(self)
   F: emit(self,record)
   ↳Called by: F236:once,F240:subscribe,F236:if
   ↳Impact: 🔴HIGH (6 dependents) | Breaks: [F236:once],[F240:subscribe],[F236:if]
---

F067│paths.py│118
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

F066│timestamps.py│165
D: ●__future__,datetime,typing
F: utc_now()→str
   ↳Called by: F072:update_timestamp,F073:update_timestamp,F076:mark_interaction
   ↳Impact: 🔴HIGH (9 dependents) | Breaks: [F072:update_timestamp],[F073:update_timestamp],[F076:mark_interaction]
   S: Returns ISO UTC timestamp.
F: local_now()→str
   S: Returns local timezone timestamp.
F: unix_timestamp()→int
   S: Returns unix timestamp in seconds.
F: parse_timestamp(timestamp)→datetime
   ↳Called by: F066:add_days,F066:human_readable_delta,F066:is_before
   ↳Impact: 🔴HIGH (7 dependents) | Breaks: [F066:add_days],[F066:human_readable_delta],[F066:is_before]
   S: Parse ISO timestamp string.
F: format_timestamp(dt)→str
   ↳Called by: F066:add_days,F066:add_seconds
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F066:add_days],[F066:add_seconds]
   S: Convert datetime to ISO string.
F: seconds_between(start,end)→float
   ↳Called by: F066:hours_between,F066:minutes_between,F066:days_between | Calls: F066:parse_timestamp
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F066:hours_between],[F066:minutes_between],[F066:days_between]
   S: Difference in seconds.
F: minutes_between(start,end)→float
   ↳Calls: F066:seconds_between
F: hours_between(start,end)→float
   ↳Calls: F066:seconds_between
F: days_between(start,end)→float
   ↳Calls: F066:seconds_between
F: add_seconds(timestamp,seconds)→str
   ↳Called by: F066:add_hours,F066:add_minutes | Calls: F066:format_timestamp,F066:parse_timestamp
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F066:add_hours],[F066:add_minutes]
F: add_minutes(timestamp,minutes)→str
   ↳Calls: F066:add_seconds
F: add_hours(timestamp,hours)→str
   ↳Calls: F066:add_seconds
F: add_days(timestamp,days)→str
   ↳Calls: F066:format_timestamp,F066:parse_timestamp
F: is_before(timestamp_a,timestamp_b)→bool
   ↳Calls: F066:parse_timestamp
F: is_after(timestamp_a,timestamp_b)→bool
   ↳Calls: F066:parse_timestamp
F: is_between(timestamp,start,end)→bool
   ↳Calls: F066:parse_timestamp
F: human_readable_delta(past_timestamp)→str
   ↳Calls: F066:parse_timestamp
   S: Example:
   S: 5 minutes ago
   S: 2 hours ago
---
