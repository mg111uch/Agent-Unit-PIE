# 📂 parsers
Generated: 2026-07-21 18:31:40
Files: 6

---

F255│__init__.py│20
S: Parser modules for Codebase Atlas.
D: ►F253,F254,F256,F257,F258
---

F257│base_parser.py│72
S: Base parser interface for Codebase Atlas.
D: ►F003,F206 ●abc,typing
C: BaseParser←ABC│[__init__,can_parse,parse,read_file_content,count_loc,extract_first_docstring_line]
   S: Abstract base class for file parsers.
C: BaseParser←ABC│[__init__,can_parse,parse,read_file_content,count_loc,extract_first_docstring_line]
   S: Abstract base class for file parsers.
   F: __init__(self,config)
      S: Initialize parser.
      S: Args:
      S: config: Atlas configuration
   F: can_parse(self,file_info)→bool
   ↳Called by: F209:generate_atlas
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F209:generate_atlas]
      S: Check if this parser can handle the given file.
      S: Args:
      S: file_info: File to check
      S: Returns:
      S: True if parser can handle this file
   F: parse(self,file_info)→FileInfo
      S: Parse file and populate FileInfo with analysis results.
      S: Args:
      S: file_info: FileInfo object with basic metadata
      S: Returns:
      S: FileInfo object with parsed content (classes, functions, etc.)
   F: read_file_content(self,file_info)→Optional[str]
      S: Read and return file content.
      S: Args:
      S: file_info: File to read
      S: Returns:
      S: File content as string, or None if error
   F: count_loc(self,content)→int
      S: Count lines of code (non-empty lines).
      S: Args:
      S: content: File content
      S: Returns:
      S: Number of non-empty lines
   F: extract_first_docstring_line(self,docstring)→Optional[str]
      S: Extract first line of docstring.
      S: Args:
      S: docstring: Full docstring
      S: Returns:
      S: First line, or None
---

F254│config_parser.py│95
S: Config file parser for Codebase Atlas.
D: ►F003,F206,F257 ●json,typing,yaml
C: ConfigParser←BaseParser│[can_parse,parse,_parse_json,_parse_yaml,_extract_keys]
   S: Parser for JSON and YAML configuration files.
C: ConfigParser←BaseParser│[can_parse,parse,_parse_json,_parse_yaml,_extract_keys]
   S: Parser for JSON and YAML configuration files.
   F: can_parse(self,file_info)→bool
   ↳Called by: F209:generate_atlas
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F209:generate_atlas]
      S: Check if this is a config file.
   F: parse(self,file_info)→FileInfo
      S: Parse configuration file.
      S: Args:
      S: file_info: File to parse
      S: Returns:
      S: FileInfo with config keys extracted
   F: _parse_json(self,content)→Any
      S: Parse JSON content.
      S: Args:
      S: content: JSON string
      S: Returns:
      S: Parsed data
   F: _parse_yaml(self,content)→Any
      S: Parse YAML content.
      S: Args:
      S: content: YAML string
      S: Returns:
      S: Parsed data
   F: _extract_keys(self,data,prefix,max_depth)→List[str]
      S: Extract keys from parsed config data.
      S: Recursively extracts keys up to max_depth levels.
      S: Args:
      S: data: Parsed data
      S: prefix: Key prefix for nested keys
---

F253│html_parser.py│84
S: HTML parser for Codebase Atlas.
D: ►F003,F206,F257 ●re
C: HTMLParser←BaseParser│[can_parse,parse,_detect_template_engine,_extract_script_imports]
   S: Parser for HTML files and templates.
C: HTMLParser←BaseParser│[can_parse,parse,_detect_template_engine,_extract_script_imports]
   S: Parser for HTML files and templates.
   F: can_parse(self,file_info)→bool
   ↳Called by: F209:generate_atlas
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F209:generate_atlas]
      S: Check if this is an HTML file.
   F: parse(self,file_info)→FileInfo
      S: Parse HTML file and detect template engine.
      S: Args:
      S: file_info: File to parse
      S: Returns:
      S: FileInfo with template engine detected
   F: _detect_template_engine(self,content)→str
      S: Detect which template engine is used.
      S: Args:
      S: content: HTML content
      S: Returns:
      S: Template engine name or "Static HTML"
   F: _extract_script_imports(self,content)→set
      S: Extract script imports from HTML.
      S: Looks for:
      S: - <script src="..."></script>
      S: - <link rel="stylesheet" href="...">
      S: Args:
---

F256│javascript_parser.py│337
S: JavaScript/TypeScript parser for Codebase Atlas.
D: ►F003,F206,F257 ●re,typing
C: JavaScriptParser←BaseParser│[can_parse,parse,_remove_comments,_extract_imports,_extract_exports,_extract_functions,_extract_classes,_extract_class_body,_extract_class_methods,_parse_parameters,+4]
   S: Parser for JavaScript/TypeScript files using regex.
C: JavaScriptParser←BaseParser│[can_parse,parse,_remove_comments,_extract_imports,_extract_exports,_extract_functions,_extract_classes,_extract_class_body,_extract_class_methods,_parse_parameters,+4]
   S: Parser for JavaScript/TypeScript files using regex.
   F: can_parse(self,file_info)→bool
   ↳Called by: F209:generate_atlas
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F209:generate_atlas]
      S: Check if this is a JavaScript/TypeScript file.
   F: parse(self,file_info)→FileInfo
      S: Parse JavaScript/TypeScript file.
      S: Args:
      S: file_info: File to parse
      S: Returns:
      S: FileInfo with parsed content
   F: _remove_comments(self,content)→str
      S: Remove comments from JavaScript code.
      S: Args:
      S: content: JavaScript code
      S: Returns:
      S: Code with comments removed
   F: _extract_imports(self,content)→Set[str]
      S: Extract import statements.
      S: Patterns:
      S: - import X from 'module'
      S: - import { X, Y } from 'module'
      S: - const X = require('module')
   F: _extract_exports(self,content)→Set[str]
      S: Extract export statements.
      S: Args:
      S: content: File content
      S: Returns:
      S: Set of exported names
   F: _extract_functions(self,content,original)→List[FunctionInfo]
      S: Extract function definitions.
      S: Patterns:
      S: - function name(...) { }
      S: - async function name(...) { }
      S: - const name = (...) => { }
   F: _extract_classes(self,content,original)→List[ClassInfo]
      S: Extract class definitions.
      S: Pattern: class Name extends Base { }
      S: Args:
      S: content: Content with comments removed
      S: original: Original content
   F: _extract_class_body(self,content,start)→str
      S: Extract class body content (between braces).
      S: Args:
      S: content: Full content
      S: start: Start position after opening brace
      S: Returns:
   F: _extract_class_methods(self,class_body)→List[FunctionInfo]
      S: Extract methods from class body.
      S: Args:
      S: class_body: Class body content
      S: Returns:
      S: List of FunctionInfo objects for methods
   F: _parse_parameters(self,params)→Any
      S: Parse function parameters.
      S: Args:
      S: params: Parameter string
      S: Returns:
      S: List of (name, type) tuples
   F: _extract_function_calls(self,content,start,func_info)
      S: Extract function calls from function body.
      S: Args:
      S: content: Full content
      S: start: Start position of function body
      S: func_info: FunctionInfo to populate
   F: _detect_react_components(self,file_info,content)
      S: Detect React components in JSX/TSX files.
      S: Args:
      S: file_info: File info to update
      S: content: File content
   F: _is_entry_point_function(self,name)→bool
      S: Check if function is an entry point.
      S: Args:
      S: name: Function name
      S: Returns:
      S: True if entry point
   F: _has_entry_point_pattern(self,content)→bool
      S: Check if content has entry point patterns.
      S: Args:
      S: content: File content
      S: Returns:
      S: True if has entry point pattern
---

F258│python_parser.py│347│⚡
S: Python parser for Codebase Atlas.
D: ►F003,F206,F257 ●ast,typing
C: PythonParser←BaseParser│[can_parse,parse,_extract_imports,_parse_class,_parse_function,_extract_arguments,_extract_calls_and_vars,_extract_component_usage,_get_annotation,_get_name,+5]
   S: Parser for Python files using AST.
C: PythonParser←BaseParser│[can_parse,parse,_extract_imports,_parse_class,_parse_function,_extract_arguments,_extract_calls_and_vars,_extract_component_usage,_get_annotation,_get_name,+5]
   S: Parser for Python files using AST.
   F: can_parse(self,file_info)→bool
   ↳Called by: F209:generate_atlas
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F209:generate_atlas]
      S: Check if this is a Python file.
   F: parse(self,file_info)→FileInfo
      S: Parse Python file using AST.
      S: Args:
      S: file_info: File to parse
      S: Returns:
      S: FileInfo with parsed content
   F: _extract_imports(self,tree)→Set[str]
      S: Extract all import statements.
      S: Args:
      S: tree: AST tree
      S: Returns:
      S: Set of imported module names (top-level only)
   F: _parse_class(self,node,content)→ClassInfo
      S: Parse a class definition.
      S: Args:
      S: node: ClassDef AST node
      S: content: File content (for line numbers)
      S: Returns:
   F: _parse_function(self,node,content,is_method)→FunctionInfo
      S: Parse a function/method definition.
      S: Args:
      S: node: FunctionDef AST node
      S: content: File content
      S: is_method: Whether this is a class method
   F: _extract_arguments(self,args)→Any
      S: Extract function arguments with type hints.
      S: Args:
      S: args: arguments AST node
      S: Returns:
      S: List of (name, type) tuples
   F: _extract_calls_and_vars(self,node,func_info)
      S: Extract function calls and variable usage.
      S: Args:
      S: node: FunctionDef node
      S: func_info: FunctionInfo to populate
   F: _extract_component_usage(self,node,class_info)
      S: Extract component usage for ECS patterns.
      S: Args:
      S: node: ClassDef node
      S: class_info: ClassInfo to populate
   F: _get_annotation(self,node)→Optional[str]
      S: Get type annotation as string.
      S: Args:
      S: node: Annotation AST node
      S: Returns:
      S: Type string or None
   F: _get_name(self,node)→Optional[str]
      S: Get name from AST node.
      S: Args:
      S: node: AST node
      S: Returns:
      S: Name string or None
   F: _is_main_guard(self,node)→bool
      S: Check if this is if __name__ == '__main__'.
      S: Args:
      S: node: If AST node
      S: Returns:
      S: True if main guard
   F: _is_entry_point_function(self,name,decorators)→bool
      S: Check if function is an entry point.
      S: Args:
      S: name: Function name
      S: decorators: List of decorator names
      S: Returns:
   F: _detect_json_outputs(self,node)→List[str]
   F: _get_open_path_from_call(self,node)→Optional[str]
   F: _has_entry_point_pattern(self,content)→bool
      S: Check if content has entry point patterns.
      S: Args:
      S: content: File content
      S: Returns:
      S: True if has entry point pattern
---
