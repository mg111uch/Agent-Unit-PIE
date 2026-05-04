"""
File scanner for Codebase Atlas.

This module discovers all relevant files in the project directory and
assigns reference IDs and basic metadata.
"""

import os
from pathlib import Path
from typing import List, Set

from .config import (
    AtlasConfig,
    ALL_EXTENSIONS,
    PYTHON_EXTENSIONS,
    JAVASCRIPT_EXTENSIONS,
    HTML_EXTENSIONS,
    CONFIG_EXTENSIONS,
    get_file_category,
)
from .models import FileInfo, FileCategory


class FileScanner:
    """Scans project directory and discovers relevant files."""
    
    def __init__(self, config: AtlasConfig):
        """
        Initialize scanner.
        
        Args:
            config: Atlas configuration
        """
        self.config = config
        self.project_root = Path(config.project_dir).resolve()
        self.file_counter = 0
        self.files: List[FileInfo] = []
        
        # Statistics
        self.total_scanned = 0
        self.total_ignored = 0
    
    def scan(self) -> List[FileInfo]:
        """
        Scan project directory and return list of FileInfo objects.
        
        Returns:
            List of FileInfo objects
        """
        print(f"🔍 Scanning {self.project_root}...")
        
        for root, dirs, files in os.walk(self.project_root):
            # Filter out ignored directories in-place
            dirs[:] = [d for d in dirs if d not in self.config.ignore_dirs]
            
            for filename in files:
                self.total_scanned += 1
                
                # Skip ignored files
                if filename in self.config.ignore_files:
                    self.total_ignored += 1
                    continue
                
                file_path = Path(root) / filename
                ext = file_path.suffix.lower()
                
                # Only process supported extensions
                if ext not in ALL_EXTENSIONS:
                    self.total_ignored += 1
                    continue
                
                # Create FileInfo
                file_info = self._create_file_info(file_path, ext)
                self.files.append(file_info)
        
        print(f"📊 Found {len(self.files)} relevant files "
              f"({self.total_ignored} ignored)")
        
        return self.files
    
    def _create_file_info(self, file_path: Path, ext: str) -> FileInfo:
        """
        Create FileInfo object for a file.
        
        Args:
            file_path: Absolute path to file
            ext: File extension
        
        Returns:
            FileInfo object with basic metadata
        """
        self.file_counter += 1
        
        # Calculate relative path
        rel_path = str(file_path.relative_to(self.project_root))
        
        # Assign reference ID
        ref_id = f"F{self.file_counter:03d}"
        
        # Determine category
        category_str = get_file_category(file_path)
        category = FileCategory[category_str.upper()]
        
        # Create FileInfo
        file_info = FileInfo(
            path=file_path,
            rel_path=rel_path,
            ref_id=ref_id,
            ext=ext,
            category=category,
        )
        
        return file_info
    
    def get_files_by_extension(self, extensions: Set[str]) -> List[FileInfo]:
        """
        Get files matching specific extensions.
        
        Args:
            extensions: Set of extensions (e.g., {'.py', '.js'})
        
        Returns:
            List of matching FileInfo objects
        """
        return [f for f in self.files if f.ext in extensions]
    
    def get_python_files(self) -> List[FileInfo]:
        """Get all Python files."""
        return self.get_files_by_extension(PYTHON_EXTENSIONS)
    
    def get_javascript_files(self) -> List[FileInfo]:
        """Get all JavaScript/TypeScript files."""
        return self.get_files_by_extension(JAVASCRIPT_EXTENSIONS)
    
    def get_html_files(self) -> List[FileInfo]:
        """Get all HTML files."""
        return self.get_files_by_extension(HTML_EXTENSIONS)
    
    def get_config_files(self) -> List[FileInfo]:
        """Get all config files."""
        return self.get_files_by_extension(CONFIG_EXTENSIONS)
    
    def get_files_by_category(self, category: FileCategory) -> List[FileInfo]:
        """
        Get files by category.
        
        Args:
            category: FileCategory enum value
        
        Returns:
            List of matching FileInfo objects
        """
        return [f for f in self.files if f.category == category]
    
    def get_statistics(self) -> dict:
        """
        Get scanning statistics.
        
        Returns:
            Dictionary with statistics
        """
        stats = {
            'total_scanned': self.total_scanned,
            'total_relevant': len(self.files),
            'total_ignored': self.total_ignored,
            'by_extension': {},
            'by_category': {},
        }
        
        # Count by extension
        for ext in ALL_EXTENSIONS:
            count = len(self.get_files_by_extension({ext}))
            if count > 0:
                stats['by_extension'][ext] = count
        
        # Count by category
        for category in FileCategory:
            count = len(self.get_files_by_category(category))
            if count > 0:
                stats['by_category'][category.value] = count
        
        return stats
    
    def print_statistics(self):
        """Print scanning statistics to console."""
        stats = self.get_statistics()
        
        print("\n📈 Scanning Statistics:")
        print(f"  Total files scanned: {stats['total_scanned']}")
        print(f"  Relevant files: {stats['total_relevant']}")
        print(f"  Ignored files: {stats['total_ignored']}")
        
        if stats['by_extension']:
            print("\n  By extension:")
            for ext, count in sorted(stats['by_extension'].items()):
                print(f"    {ext}: {count}")
        
        if stats['by_category']:
            print("\n  By category:")
            for cat, count in sorted(stats['by_category'].items()):
                print(f"    {cat}: {count}")


def scan_project(config: AtlasConfig) -> List[FileInfo]:
    """
    Convenience function to scan a project.
    
    Args:
        config: Atlas configuration
    
    Returns:
        List of FileInfo objects
    """
    scanner = FileScanner(config)
    files = scanner.scan()
    scanner.print_statistics()
    return files