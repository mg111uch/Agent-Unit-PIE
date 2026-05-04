Using your available tools (especially the code_execution tool for file I/O in the Python REPL environment), directly process the files in directory '/python/Popula' (supported file types [.py, .js, .jsx, .ts, .tsx, .html]). For each file, read its content, generate the required YAML-formatted metadata header using your internal reasoning and prompting techniques, prepend the header to the original content, and write the modified content back to the same file in place. Ensure the original file content follows the header unchanged.Prepend metadata as DocString. Generate the metadata as follows:

- **summary**: A concise 1-2 sentence abstractive summary of the file's purpose/content. Specifically apply Chain of Density (CoD) prompting adapted for code: Internally perform 3 iterative rounds of densification by adding salient code entities (e.g., functions, classes, variables, imports) without increasing length. Use this internal prompt template for each round: "Revise this code summary to add one missing salient entity (e.g., [list from AST: func1, class2]) while keeping under 100 words. Previous: [last summary]."

- **dependencies**: A list of strings representing dependent files (parse imports/requires from the file content using regex in your code_execution tool for common patterns like `import .* from 'path'` or `require('path')`; make paths relative; if none, empty list).

- **tags**: A list of 3-5 inferred keywords (e.g., extract from summary or common terms like 'auth', 'utils' via internal TF-IDF simulation on identifiers/comments).

- **hierarchy_mapping**: A nested YAML dict of the file's structure (generate via your internal LLM reasoning post-simulated AST parse): e.g., { "classes": { "UserModel": { "inherits": "BaseModel", "methods": ["create()", "update()"] } }, "functions": ["main()", "helper()"] }. Use this internal prompt: "From this code's AST, generate a YAML hierarchy of classes and functions."

- **graph_methods**: A simplified JSON graph representation (nodes/edges) for dependencies and call flows (infer via your internal LLM reasoning from code): e.g., { "nodes": [{"id": "login_user", "type": "function"}], "edges": [{"from": "main", "to": "login_user", "type": "calls"}] }. Include control flow graph (CFG) outline as a subfield: "if auth_fail → log_error; else → proceed." Use this internal prompt: "Extract a lightweight dep graph and CFG from this code as JSON."

Structure the YAML header like this (exact format), ensuring it's valid YAML:
```
metadata:
  summary: "Advanced CoD-generated summary here."
  dependencies: ["rel/path/to/dep1.py", "rel/path/to/dep2.js"]
  tags: ["auth", "login", "security"]
  hierarchy_mapping:
    classes: {...}
    functions: [...]
  graph_methods:
    dependency_graph: {...}
    cfg_outline: "Simplified flow description."
```
