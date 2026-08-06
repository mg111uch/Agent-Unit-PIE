## EFFICIENCY RULES

1. **Step budget:** Aim to answer in at most 3-4 tool calls. If searching or grepping more than twice, stop and re-plan — you are wasting steps.
2. **Deadline:** Produce a final answer promptly. Do not analyze the same file more than twice — read once, follow up once, then answer.
3. **Allowed shell commands:** Only these command prefixes may be passed to `execute_command`: `{ALLOWED_COMMANDS}`. Do not attempt others (e.g. `rm`, `sed`, `grep`, `git`) — they are rejected. Use the dedicated tools (`edit_file`, `grep_search`, `glob_search`, `check_path_exists`) instead.
