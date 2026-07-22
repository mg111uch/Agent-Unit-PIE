# 📂 atlas_tools_1
Generated: 2026-07-21 18:31:40
Files: 10

---

F042│add_markers.py│120│⚡
S: add_markers.py - Transform markdown file to final form with project path
D: ●argparse,sys
F: transform_markdown_file(md_file_path,project_path)
   ↳Called by: F042:main
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F042:main]
   S: Transform a markdown file to final form by replacing Overview and adding project path.
   S: Args:
   S: md_file_path: Path to the markdown file
   S: project_path: Path to add after '- **Project path:' marker
   S: Returns:
F: main()
   ↳Calls: F042:transform_markdown_file
   S: Main entry point for the script.
---

F048│codebase_size.py│100│⚡
S: Tool to Count total Lines of Code (LOC), Total token size and Number of files in a codebase
D: ►F040 ●argparse,os,typing
F: count_lines_of_code(file_path)→int
   S: Counts the number of non-empty lines in a file.
   S: Args:
   S: file_path (str): The path to the file.
   S: Returns:
   S: int: The number of non-empty lines.
F: scan_and_process_files(directory,extensions,process_func,ignore_dir,ignored_files)→None
   S: Iteratively scans a directory for files with specified extensions and runs a given function on each file path.
   S: Args:
   S: directory (str): The root directory to scan.
   S: extensions (List[str]): List of file extensions to look for (e.g., ['.py', '.js']).
   S: process_func (Callable[[str], None]): A function to run on each matching file path.
---

F044│copyContent.py│136│⚡
D: ●argparse,os,re
F: copy_contents(input_file,output_file,start_marker,end_marker)
F: dump_checked_files(md_file,start_marker,end_marker,base_path,output_file)
---

F043│gen_tools_file.py│71│⚡
S: <project_path>path/to/project</project_path>
D: ●argparse,re
F: extract_tag_content(docstring,tag)
   S: Extract content from XML-like tag in docstring.
F: extract_md_content(docstring)
   ↳Called by: F043:main
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F043:main]
   S: Extract content between <project_tools.md> and </project_tools.md>.
F: main()
   ↳Calls: F043:extract_md_content
---

F046│init_harness.py│227│⚡
S: Usage Instructions:
D: ●argparse,os,shutil,subprocess
F: check_conflicts(project_path)
   ↳Called by: F046:main
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F046:main]
   S: Check for existing files/directories with conflicting names.
F: should_create_item(item_name,conflict_decisions)
   ↳Called by: F046:run_project_tool_command,F046:create_main_py,F046:create_code_atlas_md
   ↳Impact: 🔴HIGH (5 dependents) | Breaks: [F046:run_project_tool_command],[F046:create_main_py],[F046:create_code_atlas_md]
   S: Check if we should create the item based on user's decision.
F: create_directory_structure(project_path,conflict_decisions)
   ↳Called by: F046:main | Calls: F046:should_create_item
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F046:main]
   S: Create the required directory structure.
F: create_main_py(project_path,conflict_decisions)
   ↳Called by: F046:main | Calls: F046:should_create_item
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F046:main]
   S: Create main.py with the specified content.
F: create_agent_harness_md(project_path,project_path_value,conda_env,conflict_decisions)
   ↳Called by: F046:main | Calls: F046:should_create_item
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F046:main]
   S: Create agent_harness.md with placeholders replaced.
F: create_code_atlas_md(project_path,conflict_decisions)
   ↳Called by: F046:main | Calls: F046:should_create_item
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F046:main]
   S: Create code_atlas.md with the specified content.
F: run_project_tool_command(atlas_path,conda_env,project_path,conflict_decisions)
   ↳Called by: F046:main | Calls: F046:should_create_item
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F046:main]
   S: Run the command to generate project_tools.md.
F: main()
   ↳Calls: F046:run_project_tool_command,F046:create_main_py,F046:create_code_atlas_md
---

F039│make_directree.py│204│⚡
S: This script can operate in two modes:
D: ►F040 ●argparse,os
F: parse_args()
F: read_structure(md_file,start_marker,end_marker)
F: parse_tree(lines)
F: create_structure(base_path,tree)
   ↳Called by: F039:create_structure | Calls: F039:create_structure
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F039:create_structure]
F: generate_tree(directory,ignored_dirs,ignored_files,show_stats)
   ↳Calls: F040:count_tokens
F: prune_tree(tree,ignored_dirs)
   ↳Called by: F039:prune_tree | Calls: F039:prune_tree
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F039:prune_tree]
F: write_tree_to_md(md_file,start_marker,end_marker,tree,directory,show_stats)
---

F047│mini_code_map.py│82│⚡
D: ●ast,json,os,pathlib,yaml
C: AtlasGenerator│[__init__,parse_python_file,parse_config_file,generate]
C: AtlasGenerator│[__init__,parse_python_file,parse_config_file,generate]
   F: __init__(self,root_dir)
   F: parse_python_file(self,file_path)
      S: Extracts classes, functions, and methods using AST.
   F: parse_config_file(self,file_path,file_type)
      S: Summarizes keys in JSON/YAML files.
   F: generate(self)
---

F045│path_file_exists.py│34│⚡
D: ●argparse,os
F: check_path_exists_os(path_string)
   S: Checks if a file or directory exists using os.path.
   S: Args:
   S: path_string (str): The path to check.
   S: Returns:
   S: bool: True if the path exists, False otherwise.
---

F041│run_cmds.py│219│⚡
S: run_cmds.py - Execute commands from a markdown file in user-defined order
D: ●argparse,pathlib,re,subprocess,sys
F: parse_commands_from_md(md_file_path)
   ↳Called by: F041:main
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F041:main]
   S: Parse commands from a markdown file.
   S: Expected format:
   S: - **Command Name:** `command to execute`
   S: Also handles:
   S: - **Command Name:**
F: list_available_commands(commands)
   ↳Called by: F041:main
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F041:main]
   S: Print all available commands found in the markdown file.
F: run_command(command_name,command_text)
   ↳Called by: F041:main
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F041:main]
   S: Execute a single command.
   S: Args:
   S: command_name: Name of the command (for display)
   S: command_text: The actual command to execute
   S: Returns:
F: main()
   ↳Calls: F041:parse_commands_from_md,F041:list_available_commands,F041:run_command
   S: Main entry point for the script.
---

F040│token_count.py│134│⚡
S: Token Count Tool
D: ●argparse,json,os,tiktoken
F: download_encoding(encoding_name)
   S: Download and save encoding files locally to tiktoken's cache.
   S: Args:
   S: encoding_name (str): Name of the tokenizer encoding.
   S: Returns:
   S: tuple: Paths to the vocab.json and merges.txt files, or None on failure.
F: load_encoding_locally(encoding_name)
   ↳Called by: F040:count_tokens_string,F040:count_tokens
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F040:count_tokens_string],[F040:count_tokens]
   S: Load encoding from local cache or download if not available.
   S: Uses tiktoken's built-in caching mechanism.
   S: Args:
   S: encoding_name (str): Name of the tokenizer encoding.
   S: Returns:
F: count_tokens(file_path,encoding_name)
   ↳Called by: F039:generate_tree | Calls: F040:load_encoding_locally
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F039:generate_tree]
   S: Count the number of tokens in a text file using a specified tokenizer encoding.
   S: Args:
   S: file_path (str): Path to the text file to analyze.
   S: encoding_name (str): Name of the tokenizer encoding (e.g., 'cl100k_base' for GPT-4).
   S: Returns:
F: count_tokens_string(text,encoding_name)
   ↳Called by: F251:insert_function,F251:insert_file_as_symbol,F251:insert_class | Calls: F040:load_encoding_locally
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F251:insert_function],[F251:insert_file_as_symbol],[F251:insert_class]
   S: Count the number of tokens in a string using a specified tokenizer encoding.
   S: Args:
   S: text (str): The text string to tokenize.
   S: encoding_name (str): Name of the tokenizer encoding (e.g., 'cl100k_base' for GPT-4).
   S: Returns:
---
