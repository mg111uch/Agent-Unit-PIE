"""
Entry point detector for Codebase Atlas.

Aggregates and categorizes all entry points in the codebase.
"""

from typing import List, Dict, Set, Tuple
from collections import defaultdict

from ..models import FileInfo, FunctionInfo
from ..config import AtlasConfig


class EntryPointDetector:
    """Detects and categorizes entry points across the codebase."""
    
    # Entry point categories
    CATEGORIES = {
        'web': ['route', 'app.route', 'endpoint', 'handler', 'listen', 'render'],
        'cli': ['main', 'command', 'click.command', 'argparse', 'cli'],
        'service': ['run', 'start', 'execute', 'serve', 'daemon'],
        'test': ['test_', 'test', 'spec', 'describe'],
        'other': [],
    }
    
    def __init__(self, config: AtlasConfig):
        """
        Initialize entry point detector.
        
        Args:
            config: Atlas configuration
        """
        self.config = config
        self.entry_points: List[Tuple[str, str, str]] = []  # (file_ref, func_name, category)
        self.by_category: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
        self.by_file: Dict[str, List[str]] = defaultdict(list)
    
    def detect(self, files: List[FileInfo]) -> List[Tuple[str, str, str]]:
        """
        Detect all entry points in the codebase.
        
        Args:
            files: List of parsed FileInfo objects
        
        Returns:
            List of (file_ref, func_name, category) tuples
        """
        print("⚡ Detecting entry points...")
        
        for file_info in files:
            # File-level entry points
            if file_info.entry_point:
                self._add_entry_point(file_info.ref_id, None, file_info)
            
            # Function-level entry points
            for func in file_info.get_entry_functions():
                self._add_entry_point(file_info.ref_id, func.name, file_info, func)
        
        print(f"  ✓ Found {len(self.entry_points)} entry points")
        for category, entries in self.by_category.items():
            if entries:
                print(f"    - {category}: {len(entries)}")
        
        return self.entry_points
    
    def _add_entry_point(
        self,
        file_ref: str,
        func_name: str,
        file_info: FileInfo,
        func_info: FunctionInfo = None
    ):
        """
        Add an entry point with category detection.
        
        Args:
            file_ref: File reference ID
            func_name: Function name (None for file-level)
            file_info: FileInfo object
            func_info: FunctionInfo object (optional)
        """
        # Determine category
        category = self._categorize_entry_point(file_info, func_info)
        
        # Add to main list
        self.entry_points.append((file_ref, func_name or 'file', category))
        
        # Add to category map
        self.by_category[category].append((file_ref, func_name or 'file'))
        
        # Add to file map
        self.by_file[file_ref].append(func_name or 'file')
    
    def _categorize_entry_point(
        self,
        file_info: FileInfo,
        func_info: FunctionInfo = None
    ) -> str:
        """
        Categorize an entry point.
        
        Args:
            file_info: FileInfo object
            func_info: FunctionInfo object (optional)
        
        Returns:
            Category string
        """
        # Check function decorators and name
        if func_info:
            name_lower = func_info.name.lower()
            
            # Check decorators
            for decorator in func_info.decorators:
                for category, keywords in self.CATEGORIES.items():
                    if any(kw in decorator.lower() for kw in keywords):
                        return category
            
            # Check function name
            for category, keywords in self.CATEGORIES.items():
                if any(kw in name_lower for kw in keywords):
                    return category
        
        # Check file path
        file_path = str(file_info.path).lower()
        
        # Test files
        if 'test' in file_path or 'spec' in file_path:
            return 'test'
        
        # Web/API files
        if any(kw in file_path for kw in ['route', 'api', 'server', 'app']):
            return 'web'
        
        # CLI files
        if any(kw in file_path for kw in ['cli', 'command', 'main']):
            return 'cli'
        
        # Service files
        if any(kw in file_path for kw in ['service', 'daemon', 'worker']):
            return 'service'
        
        return 'other'
    
    def get_critical_entry_points(self) -> List[Tuple[str, str, str]]:
        """
        Get critical entry points (non-test).
        
        Returns:
            List of (file_ref, func_name, category) tuples
        """
        return [
            (ref, func, cat)
            for ref, func, cat in self.entry_points
            if cat != 'test'
        ]
    
    def get_entry_points_by_category(self, category: str) -> List[Tuple[str, str]]:
        """
        Get entry points for a specific category.
        
        Args:
            category: Category name
        
        Returns:
            List of (file_ref, func_name) tuples
        """
        return self.by_category.get(category, [])
    
    def get_entry_points_for_file(self, file_ref: str) -> List[str]:
        """
        Get entry point function names for a file.
        
        Args:
            file_ref: File reference ID
        
        Returns:
            List of function names
        """
        return self.by_file.get(file_ref, [])
    
    def format_entry_point(
        self,
        file_ref: str,
        func_name: str,
        category: str,
        compact: bool = False
    ) -> str:
        """
        Format entry point for display.
        
        Args:
            file_ref: File reference ID
            func_name: Function name
            category: Category
            compact: Use compact notation
        
        Returns:
            Formatted string
        """
        if compact:
            if func_name == 'file':
                return f"{file_ref}⚡"
            else:
                return f"{file_ref}:{func_name}⚡"
        else:
            if func_name == 'file':
                return f"[{file_ref}] ⚡ ENTRY POINT ({category})"
            else:
                return f"[{file_ref}] {func_name}() ⚡ ENTRY POINT ({category})"