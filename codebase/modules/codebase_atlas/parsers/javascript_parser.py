"""
JavaScript/TypeScript parser for Codebase Atlas.

Uses regex patterns for parsing (no external dependencies).
Handles: .js, .jsx, .ts, .tsx files
"""

import re
from typing import Optional, List, Tuple, Set
from .base_parser import BaseParser
from ..models import FileInfo, FunctionInfo, ClassInfo, RiskLevel
from ..config import AtlasConfig, JAVASCRIPT_EXTENSIONS, ENTRY_POINT_PATTERNS


class JavaScriptParser(BaseParser):
    """Parser for JavaScript/TypeScript files using regex."""
    
    def can_parse(self, file_info: FileInfo) -> bool:
        """Check if this is a JavaScript/TypeScript file."""
        return file_info.ext in JAVASCRIPT_EXTENSIONS
    
    def parse(self, file_info: FileInfo) -> FileInfo:
        """
        Parse JavaScript/TypeScript file.
        
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
        
        # Remove comments to avoid false positives
        content_no_comments = self._remove_comments(content)
        
        # Extract imports
        file_info.imports = self._extract_imports(content_no_comments)
        
        # Extract exports
        file_info.exports = self._extract_exports(content_no_comments)
        
        # Extract functions
        file_info.functions = self._extract_functions(content_no_comments, content)
        
        # Extract classes
        file_info.classes = self._extract_classes(content_no_comments, content)
        
        # React component detection (JSX/TSX)
        if file_info.ext in {'.jsx', '.tsx'}:
            self._detect_react_components(file_info, content_no_comments)
        
        # Entry point detection
        if self._has_entry_point_pattern(content):
            file_info.entry_point = True
        
        return file_info
    
    def _remove_comments(self, content: str) -> str:
        """
        Remove comments from JavaScript code.
        
        Args:
            content: JavaScript code
        
        Returns:
            Code with comments removed
        """
        # Remove single-line comments
        content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
        
        # Remove multi-line comments
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        
        return content
    
    def _extract_imports(self, content: str) -> Set[str]:
        """
        Extract import statements.
        
        Patterns:
        - import X from 'module'
        - import { X, Y } from 'module'
        - const X = require('module')
        
        Args:
            content: File content
        
        Returns:
            Set of imported module names
        """
        imports = set()
        
        # ES6 imports: import ... from 'module'
        import_pattern = r"import\s+(?:[\w\s{},*]+\s+from\s+)?['\"]([^'\"]+)['\"]"
        for match in re.finditer(import_pattern, content):
            module = match.group(1)
            # Get top-level module (before first /)
            if module.startswith('.'):
                # Relative import - keep as is
                imports.add(module)
            else:
                # External package - get package name
                package = module.split('/')[0]
                # Remove @scope/ prefix if present
                if package.startswith('@'):
                    package = '@' + module.split('/')[1] if '/' in module else package
                imports.add(package)
        
        # CommonJS requires: require('module')
        require_pattern = r"require\(['\"]([^'\"]+)[\"\']"
        for match in re.finditer(require_pattern, content):
            module = match.group(1)
            if module.startswith('.'):
                imports.add(module)
            else:
                package = module.split('/')[0]
                imports.add(package)
        
        return imports
    
    def _extract_exports(self, content: str) -> Set[str]:
        """
        Extract export statements.
        
        Args:
            content: File content
        
        Returns:
            Set of exported names
        """
        exports = set()
        
        # export default X
        # export function X
        # export const X
        # export class X
        export_pattern = r"export\s+(?:default\s+)?(?:function|const|let|var|class)\s+(\w+)"
        for match in re.finditer(export_pattern, content):
            exports.add(match.group(1))
        
        # export { X, Y }
        export_list_pattern = r"export\s+\{([^}]+)\}"
        for match in re.finditer(export_list_pattern, content):
            names = match.group(1).split(',')
            for name in names:
                # Handle "X as Y" syntax
                name = name.strip().split(' as ')[0].strip()
                exports.add(name)
        
        return exports
    
    def _extract_functions(self, content: str, original: str) -> List[FunctionInfo]:
        """
        Extract function definitions.
        
        Patterns:
        - function name(...) { }
        - async function name(...) { }
        - const name = (...) => { }
        - const name = async (...) => { }
        
        Args:
            content: Content with comments removed
            original: Original content (for line numbers)
        
        Returns:
            List of FunctionInfo objects
        """
        functions = []
        
        # Regular functions: function name(...) { }
        func_pattern = r"(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)"
        for match in re.finditer(func_pattern, content):
            name = match.group(1)
            params = match.group(2)
            is_async = 'async' in content[max(0, match.start()-10):match.start()]
            
            func_info = FunctionInfo(
                name=name,
                args=self._parse_parameters(params),
                is_async=is_async,
                line_number=original[:match.start()].count('\n') + 1,
            )
            
            # Extract calls from function body
            self._extract_function_calls(content, match.end(), func_info)
            
            # Check if entry point
            func_info.is_entry = self._is_entry_point_function(name)
            
            functions.append(func_info)
        
        # Arrow functions: const name = (...) => { }
        arrow_pattern = r"(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*=>"
        for match in re.finditer(arrow_pattern, content):
            name = match.group(1)
            params = match.group(2)
            is_async = 'async' in content[max(0, match.start()-10):match.end()]
            
            func_info = FunctionInfo(
                name=name,
                args=self._parse_parameters(params),
                is_async=is_async,
                line_number=original[:match.start()].count('\n') + 1,
            )
            
            # Extract calls
            self._extract_function_calls(content, match.end(), func_info)
            
            # Check if entry point
            func_info.is_entry = self._is_entry_point_function(name)
            
            functions.append(func_info)
        
        return functions
    
    def _extract_classes(self, content: str, original: str) -> List[ClassInfo]:
        """
        Extract class definitions.
        
        Pattern: class Name extends Base { }
        
        Args:
            content: Content with comments removed
            original: Original content
        
        Returns:
            List of ClassInfo objects
        """
        classes = []
        
        # class Name extends Base { }
        class_pattern = r"class\s+(\w+)(?:\s+extends\s+(\w+))?\s*\{"
        for match in re.finditer(class_pattern, content):
            name = match.group(1)
            base = match.group(2)
            
            # Find class body (rough heuristic - find matching brace)
            start = match.end()
            class_body = self._extract_class_body(content, start)
            
            # Extract methods from class body
            methods = self._extract_class_methods(class_body)
            
            class_info = ClassInfo(
                name=name,
                bases=[base] if base else [],
                methods=methods,
                line_number=original[:match.start()].count('\n') + 1,
            )
            
            classes.append(class_info)
        
        return classes
    
    def _extract_class_body(self, content: str, start: int) -> str:
        """
        Extract class body content (between braces).
        
        Args:
            content: Full content
            start: Start position after opening brace
        
        Returns:
            Class body content (limited to 5000 chars)
        """
        # Simple heuristic: take next 5000 characters or until we find
        # another class definition
        end = min(start + 5000, len(content))
        body = content[start:end]
        
        # Stop at next class definition
        next_class = body.find('class ')
        if next_class > 0:
            body = body[:next_class]
        
        return body
    
    def _extract_class_methods(self, class_body: str) -> List[FunctionInfo]:
        """
        Extract methods from class body.
        
        Args:
            class_body: Class body content
        
        Returns:
            List of FunctionInfo objects for methods
        """
        methods = []
        
        # Method pattern: methodName(...) { }
        method_pattern = r"(?:async\s+)?(\w+)\s*\(([^)]*)\)\s*\{"
        for match in re.finditer(method_pattern, class_body):
            name = match.group(1)
            params = match.group(2)
            is_async = 'async' in class_body[max(0, match.start()-10):match.start()]
            
            # Skip constructor in method list (it's implicit)
            if name == 'constructor':
                continue
            
            func_info = FunctionInfo(
                name=name,
                args=self._parse_parameters(params),
                is_async=is_async,
                is_method=True,
            )
            
            # Extract calls from method body
            self._extract_function_calls(class_body, match.end(), func_info)
            
            methods.append(func_info)
            
            # Limit methods per class to avoid explosion
            if len(methods) >= 20:
                break
        
        return methods
    
    def _parse_parameters(self, params: str) -> List[Tuple[str, Optional[str]]]:
        """
        Parse function parameters.
        
        Args:
            params: Parameter string
        
        Returns:
            List of (name, type) tuples
        """
        if not params.strip():
            return []
        
        result = []
        for param in params.split(','):
            param = param.strip()
            if not param:
                continue
            
            # Handle TypeScript type annotations: name: type
            if ':' in param:
                parts = param.split(':')
                name = parts[0].strip()
                type_hint = parts[1].strip() if len(parts) > 1 else None
            else:
                name = param
                type_hint = None
            
            # Remove default values
            if '=' in name:
                name = name.split('=')[0].strip()
            
            result.append((name, type_hint))
        
        return result
    
    def _extract_function_calls(self, content: str, start: int, func_info: FunctionInfo):
        """
        Extract function calls from function body.
        
        Args:
            content: Full content
            start: Start position of function body
            func_info: FunctionInfo to populate
        """
        # Get function body (rough heuristic - next 1000 chars)
        body = content[start:min(start + 1000, len(content))]
        
        # Function call pattern: name(...)
        call_pattern = r"(\w+(?:\.\w+)*)\s*\("
        for match in re.finditer(call_pattern, body):
            call_name = match.group(1)
            
            # Check if external library call
            if '.' in call_name:
                if self.config.track_external_deps:
                    func_info.external_calls.add(call_name)
            else:
                func_info.calls.add(call_name)
    
    def _detect_react_components(self, file_info: FileInfo, content: str):
        """
        Detect React components in JSX/TSX files.
        
        Args:
            file_info: File info to update
            content: File content
        """
        components = []
        
        # Function components: export default function ComponentName
        fc_pattern = r"export\s+default\s+function\s+([A-Z]\w+)"
        for match in re.finditer(fc_pattern, content):
            components.append(match.group(1))
        
        # Arrow function components: const Component = () => ( or {
        arrow_comp_pattern = r"(?:const|let)\s+([A-Z]\w+)\s*=\s*\([^)]*\)\s*=>"
        for match in re.finditer(arrow_comp_pattern, content):
            components.append(match.group(1))
        
        # Check if component returns JSX (contains < and >)
        if '<' in content and '>' in content:
            file_info.is_react_component = True
            file_info.react_components = components
    
    def _is_entry_point_function(self, name: str) -> bool:
        """
        Check if function is an entry point.
        
        Args:
            name: Function name
        
        Returns:
            True if entry point
        """
        entry_names = {'main', 'run', 'start', 'App', 'index'}
        return name in entry_names
    
    def _has_entry_point_pattern(self, content: str) -> bool:
        """
        Check if content has entry point patterns.
        
        Args:
            content: File content
        
        Returns:
            True if has entry point pattern
        """
        patterns = ENTRY_POINT_PATTERNS.get('javascript', [])
        return any(pattern in content for pattern in patterns)