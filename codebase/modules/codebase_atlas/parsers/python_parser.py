"""
Python parser for Codebase Atlas.

Uses AST (Abstract Syntax Tree) for robust Python code analysis.
"""

import ast
from typing import Optional, List, Tuple, Set
from .base_parser import BaseParser
from ..models import FileInfo, FunctionInfo, ClassInfo, RiskLevel
from ..config import AtlasConfig, PYTHON_EXTENSIONS, ENTRY_POINT_PATTERNS


class PythonParser(BaseParser):
    """Parser for Python files using AST."""
    
    def can_parse(self, file_info: FileInfo) -> bool:
        """Check if this is a Python file."""
        return file_info.ext in PYTHON_EXTENSIONS
    
    def parse(self, file_info: FileInfo) -> FileInfo:
        """
        Parse Python file using AST.
        
        Args:
            file_info: File to parse
        
        Returns:
            FileInfo with parsed content
        """
        # Read file content
        content = self.read_file_content(file_info)
        if content is None:
            return file_info
        
        file_info.loc = self.count_loc(content)
        
        # Parse with AST
        try:
            tree = ast.parse(content, filename=str(file_info.path))
        except SyntaxError as e:
            file_info.error = f"Syntax error: {str(e)}"
            return file_info
        except Exception as e:
            file_info.error = f"Parse error: {str(e)}"
            return file_info
        
        # Extract module docstring
        file_info.docstring = ast.get_docstring(tree)
        
        # Extract imports
        file_info.imports = self._extract_imports(tree)
        
        # Extract classes and functions
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                class_info = self._parse_class(node, content)
                file_info.classes.append(class_info)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_info = self._parse_function(node, content)
                file_info.functions.append(func_info)
            elif isinstance(node, ast.If):
                # Check for if __name__ == "__main__"
                if self._is_main_guard(node):
                    file_info.entry_point = True
        
        # Check for entry point patterns
        if self._has_entry_point_pattern(content):
            file_info.entry_point = True
        
        return file_info
    
    def _extract_imports(self, tree: ast.AST) -> Set[str]:
        """
        Extract all import statements.
        
        Args:
            tree: AST tree
        
        Returns:
            Set of imported module names (top-level only)
        """
        imports = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # Get top-level module name
                    module_name = alias.name.split('.')[0]
                    imports.add(module_name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    # Get top-level module name
                    module_name = node.module.split('.')[0]
                    imports.add(module_name)
        
        return imports
    
    def _parse_class(self, node: ast.ClassDef, content: str) -> ClassInfo:
        """
        Parse a class definition.
        
        Args:
            node: ClassDef AST node
            content: File content (for line numbers)
        
        Returns:
            ClassInfo object
        """
        # Extract base classes
        bases = []
        for base in node.bases:
            base_name = self._get_name(base)
            if base_name and base_name != 'object':
                bases.append(base_name)
        
        # Extract methods
        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_info = self._parse_function(item, content, is_method=True)
                methods.append(method_info)
        
        lines = content.split('\n')
        end_lineno = getattr(node, 'end_lineno', node.lineno)
        source_code = '\n'.join(lines[node.lineno - 1:end_lineno])

        class_info = ClassInfo(
            name=node.name,
            bases=bases,
            methods=methods,
            docstring=ast.get_docstring(node),
            line_number=node.lineno,
            source_code=source_code,
        )
        
        # Extract component usage (for ECS patterns)
        self._extract_component_usage(node, class_info)
        
        return class_info
    
    def _parse_function(
        self,
        node: ast.FunctionDef,
        content: str,
        is_method: bool = False
    ) -> FunctionInfo:
        """
        Parse a function/method definition.
        
        Args:
            node: FunctionDef AST node
            content: File content
            is_method: Whether this is a class method
        
        Returns:
            FunctionInfo object
        """
        # Extract arguments with type hints
        args = self._extract_arguments(node.args)
        
        # Extract return type
        returns = self._get_annotation(node.returns) if node.returns else None
        
        # Extract decorators
        decorators = [self._get_name(d) for d in node.decorator_list if self._get_name(d)]
        
        # Check if entry point
        is_entry = self._is_entry_point_function(node.name, decorators)
        
        lines = content.split('\n')
        end_lineno = getattr(node, 'end_lineno', node.lineno)
        source_code = '\n'.join(lines[node.lineno - 1:end_lineno])

        func_info = FunctionInfo(
            name=node.name,
            args=args,
            returns=returns,
            docstring=ast.get_docstring(node),
            is_entry=is_entry,
            is_method=is_method,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            decorators=decorators,
            line_number=node.lineno,
            source_code=source_code,
        )
        
        # Extract function calls and variable usage
        self._extract_calls_and_vars(node, func_info)
        func_info.produces_json = self._detect_json_outputs(node)
        
        return func_info
    
    def _extract_arguments(self, args: ast.arguments) -> List[Tuple[str, Optional[str]]]:
        """
        Extract function arguments with type hints.
        
        Args:
            args: arguments AST node
        
        Returns:
            List of (name, type) tuples
        """
        result = []
        
        for arg in args.args:
            arg_name = arg.arg
            arg_type = self._get_annotation(arg.annotation) if arg.annotation else None
            result.append((arg_name, arg_type))
        
        return result
    
    def _extract_calls_and_vars(self, node: ast.FunctionDef, func_info: FunctionInfo):
        """
        Extract function calls and variable usage.
        
        Args:
            node: FunctionDef node
            func_info: FunctionInfo to populate
        """
        for child in ast.walk(node):
            # Function calls
            if isinstance(child, ast.Call):
                call_name = self._get_name(child.func)
                if call_name:
                    # Check if external library call
                    if '.' in call_name:
                        module = call_name.split('.')[0]
                        if self.config.track_external_deps:
                            func_info.external_calls.add(call_name)
                    else:
                        func_info.calls.add(call_name)
            
            # Variable reads (Name nodes in Load context)
            elif isinstance(child, ast.Name):
                if isinstance(child.ctx, ast.Load):
                    # Variable is being read
                    func_info.reads_vars.add(child.id)
                elif isinstance(child, ast.Store):
                    # Variable is being written
                    func_info.writes_vars.add(child.id)
            
            # Attribute access (for tracking reads/writes)
            elif isinstance(child, ast.Attribute):
                attr_name = self._get_name(child)
                if attr_name and isinstance(child.ctx, ast.Load):
                    func_info.reads_vars.add(attr_name)
    
    def _extract_component_usage(self, node: ast.ClassDef, class_info: ClassInfo):
        """
        Extract component usage for ECS patterns.
        
        Args:
            node: ClassDef node
            class_info: ClassInfo to populate
        """
        for child in ast.walk(node):
            # Look for component instantiation: self.component = Component()
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Attribute):
                        attr_name = target.attr
                        # Check if looks like a component (ends with 'Component')
                        if 'component' in attr_name.lower():
                            class_info.uses_components.add(attr_name)
    
    def _get_annotation(self, node: Optional[ast.AST]) -> Optional[str]:
        """
        Get type annotation as string.
        
        Args:
            node: Annotation AST node
        
        Returns:
            Type string or None
        """
        if node is None:
            return None
        
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.Subscript):
            value_name = self._get_name(node.value)
            slice_name = self._get_name(node.slice)
            if value_name and slice_name:
                return f"{value_name}[{slice_name}]"
        elif isinstance(node, ast.Attribute):
            return self._get_name(node)
        
        return "Any"
    
    def _get_name(self, node: Optional[ast.AST]) -> Optional[str]:
        """
        Get name from AST node.
        
        Args:
            node: AST node
        
        Returns:
            Name string or None
        """
        if node is None:
            return None
        
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value_name = self._get_name(node.value)
            if value_name:
                return f"{value_name}.{node.attr}"
            return node.attr
        elif isinstance(node, ast.Constant):
            return str(node.value)
        elif isinstance(node, ast.Call):
            return self._get_name(node.func)
        
        return None
    
    def _is_main_guard(self, node: ast.If) -> bool:
        """
        Check if this is if __name__ == '__main__'.
        
        Args:
            node: If AST node
        
        Returns:
            True if main guard
        """
        if not isinstance(node.test, ast.Compare):
            return False
        
        left = node.test.left
        if isinstance(left, ast.Name) and left.id == '__name__':
            # Check if comparing to '__main__'
            for comp in node.test.comparators:
                if isinstance(comp, ast.Constant) and comp.value == '__main__':
                    return True
        
        return False
    
    def _is_entry_point_function(self, name: str, decorators: List[str]) -> bool:
        """
        Check if function is an entry point.
        
        Args:
            name: Function name
            decorators: List of decorator names
        
        Returns:
            True if entry point
        """
        # Common entry point function names
        entry_names = {'main', 'run', 'start', 'app', 'execute', 'cli'}
        if name in entry_names:
            return True
        
        # Check for entry point decorators
        entry_decorators = {'route', 'app.route', 'command', 'click.command'}
        if any(dec in entry_decorators for dec in decorators):
            return True
        
        return False
    
    def _detect_json_outputs(self, node: ast.FunctionDef) -> List[str]:
        json_paths: List[str] = []
        json_opens: List[str] = []

        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                func_full_name = self._get_name(child.func)
                if func_full_name == 'open' and child.args:
                    first = child.args[0]
                    if (
                        isinstance(first, ast.Constant)
                        and isinstance(first.value, str)
                        and first.value.endswith('.json')
                    ):
                        json_opens.append(first.value)
                    elif isinstance(first, ast.BinOp) and isinstance(first.op, ast.Add):
                        if (
                            isinstance(first.left, ast.Constant)
                            and isinstance(first.left.value, str)
                            and first.left.value.endswith('.json')
                        ):
                            json_paths.append(first.left.value)

                if func_full_name in ('json.dump', 'json.dumps') and child.args:
                    second = child.args[1] if len(child.args) >= 2 else None
                    if isinstance(second, ast.Call):
                        open_path = self._get_open_path_from_call(second)
                        if open_path:
                            json_paths.append(open_path)

        if json_opens:
            json_paths.extend(json_opens)

        return sorted(set(json_paths))

    def _get_open_path_from_call(self, node: ast.Call) -> Optional[str]:
        func_name = self._get_name(node.func)
        if func_name != 'open' or not node.args:
            return None
        path_arg = node.args[0]
        if (
            isinstance(path_arg, ast.Constant)
            and isinstance(path_arg.value, str)
            and path_arg.value.endswith('.json')
        ):
            return path_arg.value
        return None

    def _has_entry_point_pattern(self, content: str) -> bool:
        """
        Check if content has entry point patterns.
        
        Args:
            content: File content
        
        Returns:
            True if has entry point pattern
        """
        patterns = ENTRY_POINT_PATTERNS.get('python', [])
        return any(pattern in content for pattern in patterns)