"""
Parser modules for Codebase Atlas.

This package contains parsers for different file types:
- Python (AST-based)
- JavaScript/TypeScript/JSX/TSX (regex-based)
- HTML (template detection)
- JSON/YAML (config parsing)
"""

from .base_parser import BaseParser
from .python_parser import PythonParser
from .javascript_parser import JavaScriptParser
from .config_parser import ConfigParser
from .html_parser import HTMLParser

__all__ = [
    'BaseParser',
    'PythonParser',
    'JavaScriptParser',
    'ConfigParser',
    'HTMLParser',
]