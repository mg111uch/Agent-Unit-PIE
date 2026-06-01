# 📂 parsers
Generated: 2026-06-01 13:39:55
Files: 6

---

F089│__init__.py│20
S: Parser modules for Codebase Atlas.
D: ►F087,F088,F090,F091,F092
---

F091│base_parser.py│72
S: Base parser interface for Codebase Atlas.
D: ►F070,F072 ●abc,typing
C: BaseParser←ABC│[__init__,can_parse,parse,read_file_content,count_loc,extract_first_docstring_line]
   S: Abstract base class for file parsers.
---

F088│config_parser.py│95
S: Config file parser for Codebase Atlas.
D: ►F070,F072,F091 ●json,typing,yaml
C: ConfigParser←BaseParser│[can_parse,parse,_parse_json,_parse_yaml,_extract_keys]
   S: Parser for JSON and YAML configuration files.
---

F087│html_parser.py│84
S: HTML parser for Codebase Atlas.
D: ►F070,F072,F091 ●re
C: HTMLParser←BaseParser│[can_parse,parse,_detect_template_engine,_extract_script_imports]
   S: Parser for HTML files and templates.
---

F090│javascript_parser.py│337
S: JavaScript/TypeScript parser for Codebase Atlas.
D: ►F070,F072,F091 ●re,typing
C: JavaScriptParser←BaseParser│[can_parse,parse,_remove_comments,_extract_imports,_extract_exports,_extract_functions,_extract_classes,_extract_class_body,_extract_class_methods,_parse_parameters,+4]
   S: Parser for JavaScript/TypeScript files using regex.
---

F092│python_parser.py│298│⚡
S: Python parser for Codebase Atlas.
D: ►F070,F072,F091 ●ast,typing
C: PythonParser←BaseParser│[can_parse,parse,_extract_imports,_parse_class,_parse_function,_extract_arguments,_extract_calls_and_vars,_extract_component_usage,_get_annotation,_get_name,+3]
   S: Parser for Python files using AST.
---
