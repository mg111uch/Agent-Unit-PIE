"""
Base parser interface for Codebase Atlas.

This module defines the abstract interface that all parsers must implement.
"""

from abc import ABC, abstractmethod
from typing import Optional
from ..models import FileInfo
from ..config import AtlasConfig


class BaseParser(ABC):
    """Abstract base class for file parsers."""
    
    def __init__(self, config: AtlasConfig):
        """
        Initialize parser.
        
        Args:
            config: Atlas configuration
        """
        self.config = config
    
    @abstractmethod
    def can_parse(self, file_info: FileInfo) -> bool:
        """
        Check if this parser can handle the given file.
        
        Args:
            file_info: File to check
        
        Returns:
            True if parser can handle this file
        """
        pass
    
    @abstractmethod
    def parse(self, file_info: FileInfo) -> FileInfo:
        """
        Parse file and populate FileInfo with analysis results.
        
        Args:
            file_info: FileInfo object with basic metadata
        
        Returns:
            FileInfo object with parsed content (classes, functions, etc.)
        """
        pass
    
    def read_file_content(self, file_info: FileInfo) -> Optional[str]:
        """
        Read and return file content.
        
        Args:
            file_info: File to read
        
        Returns:
            File content as string, or None if error
        """
        try:
            with open(file_info.path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            file_info.error = f"Read error: {str(e)}"
            return None
    
    def count_loc(self, content: str) -> int:
        """
        Count lines of code (non-empty lines).
        
        Args:
            content: File content
        
        Returns:
            Number of non-empty lines
        """
        return len([line for line in content.split('\n') if line.strip()])
    
    def extract_first_docstring_line(self, docstring: Optional[str]) -> Optional[str]:
        """
        Extract first line of docstring.
        
        Args:
            docstring: Full docstring
        
        Returns:
            First line, or None
        """
        if not docstring:
            return None
        
        first_line = docstring.split('\n')[0].strip()
        return first_line if first_line else None