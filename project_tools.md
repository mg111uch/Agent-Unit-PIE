## Project specific tool usage commands

- **Make Codebase_atlas:** `cd /home/manigupt/Hello/python/Agentic_Unit_PIE/codebase/modules && conda run -n myenv python -m codebase_atlas.main --project-dir /home/manigupt/Hello/python/Agentic_Unit_PIE/codebase --output-dir /home/manigupt/Hello/python/Agentic_Unit_PIE/atlas_output --ignore-dirs agent_tools cache data ingestion logs rag_pipeline ralph_loop skills sloperator temp tests units visualization topics mindmaps --serve --port 9090`

- **Load saved atlas and serve** `python -m codebase_atlas.main --output-dir /home/manigupt/Hello/python/Agentic_Unit_PIE/atlas_output --load`

- **Add markers:** `cd /home/manigupt/Hello/python/Agentic_Unit_PIE/codebase/agent_tools/atlas_tools && python add_markers.py --md_file /home/manigupt/Hello/python/Agentic_Unit_PIE/code_atlas.md --project_path "/home/manigupt/Hello/python/Agentic_Unit_PIE"`

- **Codebase size:** `cd /home/manigupt/Hello/python/Agentic_Unit_PIE/codebase/agent_tools/atlas_tools && conda run -n myenv python codebase_size.py --directory /home/manigupt/Hello/python/Agentic_Unit_PIE/codebase --extensions .py .js .html --output-file /home/manigupt/Hello/python/Agentic_Unit_PIE/code_atlas.md --start-marker "## Codebase size" --end-marker "## End Codebase size"`

- **Make directory:** 
`cd /home/manigupt/Hello/python/Agentic_Unit_PIE/codebase/agent_tools/atlas_tools && conda run -n myenv python make_directree.py --reverse --show_stats --base_path /home/manigupt/Hello/python/Agentic_Unit_PIE --md_file /home/manigupt/Hello/python/Agentic_Unit_PIE/code_atlas.md --ignore_dir chroma_data .adk encoding_cache .git .pytest_cache agent_tools rag_pipeline ralph_loop skills sloperator utils_files episodic logs simulations --ignore_files .env --start_marker '### FILE_MAP Tree' --end_marker '### End Tree'`

- **Copy Content:** `cd /home/manigupt/Hello/python/Agentic_Unit_PIE/codebase/agent_tools/atlas_tools && conda run -n myenv python copyContent.py --mode dump --md_file /home/manigupt/Hello/python/Agentic_Unit_PIE/code_atlas.md --base_path /home/manigupt/Hello/python/Agentic_Unit_PIE --output_file /home/manigupt/Hello/python/Agentic_Unit_PIE/code_dump.txt --start_marker '### FILE_MAP Tree' --end_marker '### End Tree'`

- **Count Tokens in file:** `cd /home/manigupt/Hello/python/Agentic_Unit_PIE/codebase/agent_tools/atlas_tools && conda run -n myenv python token_count.py /home/manigupt/Hello/python/Agentic_Unit_PIE/code_atlas.md`

- **Check if file exists:** `cd /home/manigupt/Hello/python/Agentic_Unit_PIE/codebase/agent_tools/atlas_tools && conda run -n myenv python path_file_exists.py /home/manigupt/Hello/python/Agentic_Unit_PIE/code_atlas.md`

- **Generate project tools:** `python gen_tools_file.py --atlas_path /home/manigupt/Hello/python/Agentic_Unit_PIE/codebase/atlas_output --conda_env myenv --project_path /path/to/project`

- **Init project harness:** `python init_harness.py --atlas_path /home/manigupt/Hello/python/Agentic_Unit_PIE/codebase/atlas_output --conda_env myenv --project_path /path/to/project`

- **Execute in order:** `cd /home/manigupt/Hello/python/Agentic_Unit_PIE/codebase/agent_tools/atlas_tools && python run_cmds.py /home/manigupt/Hello/python/Agentic_Unit_PIE/project_tools.md "Make directory" "Codebase size" "Count Tokens in file" "Make Codebase_atlas" "Add markers"`