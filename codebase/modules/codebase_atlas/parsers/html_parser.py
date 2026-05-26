"""
HTML parser for Codebase Atlas.

Detects HTML files and template engines (Jinja2, Django, ERB, etc.).
"""

from .base_parser import BaseParser
from ..models import FileInfo
from ..config import AtlasConfig, HTML_EXTENSIONS


class HTMLParser(BaseParser):
    """Parser for HTML files and templates."""
    
    # Template engine detection patterns
    TEMPLATE_PATTERNS = {
        'Jinja2/Django': ['{%', '{{', '{#'],
        'ERB': ['<%=', '<%', '%>'],
        'Handlebars': ['{{#', '{{/', '{{>'],
        'Mustache': ['{{', '}}'],
        'EJS': ['<%', '<%=', '<%-'],
        'Pug/Jade': ['extends ', 'block ', 'include '],
    }
    
    def can_parse(self, file_info: FileInfo) -> bool:
        """Check if this is an HTML file."""
        return file_info.ext in HTML_EXTENSIONS
    
    def parse(self, file_info: FileInfo) -> FileInfo:
        """
        Parse HTML file and detect template engine.
        
        Args:
            file_info: File to parse
        
        Returns:
            FileInfo with template engine detected
        """
        # Read file content
        content = self.read_file_content(file_info)
        if content is None:
            return file_info
        
        file_info.loc = self.count_loc(content)
        
        # Detect template engine
        file_info.template_engine = self._detect_template_engine(content)
        
        # Mark as analyzed
        file_info.html_analyzed = True
        
        # Extract any embedded script imports (basic)
        file_info.imports = self._extract_script_imports(content)
        
        return file_info
    
    def _detect_template_engine(self, content: str) -> str:
        """
        Detect which template engine is used.
        
        Args:
            content: HTML content
        
        Returns:
            Template engine name or "Static HTML"
        """
        for engine, patterns in self.TEMPLATE_PATTERNS.items():
            if any(pattern in content for pattern in patterns):
                return engine
        
        # Check for common template file extensions in name
        # (already handled by file extension, but double-check)
        if any(ext in content for ext in ['.jinja', '.j2', '.twig']):
            return 'Jinja2'
        
        return "Static HTML"
    
    def _extract_script_imports(self, content: str) -> set:
        """
        Extract script imports from HTML.
        
        Looks for:
        - <script src="..."></script>
        - <link rel="stylesheet" href="...">
        
        Args:
            content: HTML content
        
        Returns:
            Set of imported resources
        """
        imports = set()
        
        # Script tags: <script src="path/to/file.js">
        import re
        script_pattern = r'<script[^>]+src=["\']([^"\']+)["\']'
        for match in re.finditer(script_pattern, content):
            src = match.group(1)
            # Only keep relative paths or package names
            if not src.startswith('http'):
                imports.add(src)
        
        # Link tags: <link rel="stylesheet" href="...">
        link_pattern = r'<link[^>]+href=["\']([^"\']+)["\']'
        for match in re.finditer(link_pattern, content):
            href = match.group(1)
            if not href.startswith('http'):
                imports.add(href)
        
        return imports