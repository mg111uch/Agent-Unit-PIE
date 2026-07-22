# 📂 atlas_tools_2
Generated: 2026-07-21 18:31:40
Files: 2

---

F049│codebase_dump.py│38│⚡
D: ●os,pathlib
F: dump_codebase_to_text(root_dir,output_filename,excluded_dirs)
   S: Recursively finds all files in a directory and appends their contents to a single text file.
   S: Args:
   S: root_dir (str): The root directory of the codebase to scan.
   S: output_filename (str): The name of the output text file.
   S: excluded_dirs (list): A list of directory names to exclude (e.g., ['.git', '__pycache__']).
---

F050│whitespace_clean.py│382│⚡
S: Whitespace Cleaner — removes excess blank lines from function/class bodies
D: ●argparse,os,re,sys
F: _has_triple_quotes(line)→bool
   ↳Called by: F050:clean_file_content_py
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F050:clean_file_content_py]
F: _triple_quote_odd(line)→bool
   ↳Called by: F050:clean_file_content_py
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F050:clean_file_content_py]
   S: Return True if the line has an odd number of triple-quote delimiters.
F: simplify_headers(content)→str
   ↳Called by: F050:process_file
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F050:process_file]
   S: Collapse 3-line section headers into single-line format.
   S: Before:                After:
   S: # ================     # ===== NAME =====
   S: # NAME
   S: # ================
F: clean_file_content_py(content)→str
   ↳Calls: F050:_has_triple_quotes,F050:_triple_quote_odd
   S: Remove excess blank lines inside function/class bodies.
   S: Uses a look-ahead strategy: when a blank line is encountered, it peeks at
   S: the next non-blank line's indentation to decide whether the blank is inside
   S: a function/class body (→ remove) or between definitions (→ keep one).
   S: Rules:
F: clean_file_content_js_ts(content)→str
   S: Collapse excess blank lines in JS/TS files.
   S: Uses brace-depth tracking to distinguish top-level declarations from
   S: in-body blocks:
   S: - Inside braces (depth > 0): all blank lines removed.
   S: - At brace depth 0: consecutive blanks collapsed to at most one,
F: process_file(filepath,dry_run,verbose,check,simplify_headers_flag)→dict
   ↳Called by: F050:process_dir,F050:main | Calls: F050:simplify_headers
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F050:process_dir],[F050:main]
F: process_dir(dirpath,ignore_dirs,dry_run,verbose,check,simplify_headers_flag)→int
   ↳Called by: F050:main | Calls: F050:process_file
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F050:main]
   S: Recursively clean .py, .js, .jsx, .ts, .tsx files under dirpath. Returns error count.
F: main()
   ↳Calls: F050:process_dir,F050:process_file
---
