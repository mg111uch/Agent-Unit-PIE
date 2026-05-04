"""
Dependency analyzer for Codebase Atlas.

Builds dependency graph, resolves imports, detects circular dependencies.
"""

from pathlib import Path
from typing import List, Set, Dict, Optional, Tuple
from collections import defaultdict, deque

from ..models import FileInfo, DependencyGraph, AtlasData
from ..config import AtlasConfig


class DependencyAnalyzer:
    """Analyzes and builds dependency relationships between files."""
    
    def __init__(self, config: AtlasConfig):
        """
        Initialize dependency analyzer.
        
        Args:
            config: Atlas configuration
        """
        self.config = config
        self.graph = DependencyGraph()
        
        # File lookup maps
        self.file_by_ref: Dict[str, FileInfo] = {}  # ref_id -> FileInfo
        self.file_by_path: Dict[str, FileInfo] = {}  # rel_path -> FileInfo
        self.file_by_stem: Dict[str, FileInfo] = {}  # stem -> FileInfo
    
    def analyze(self, files: List[FileInfo]) -> DependencyGraph:
        """
        Build dependency graph from list of files.
        
        Args:
            files: List of parsed FileInfo objects
        
        Returns:
            Complete DependencyGraph
        """
        print("🔗 Building dependency graph...")
        
        # Build lookup maps
        self._build_lookup_maps(files)
        
        # Resolve dependencies for each file
        for file_info in files:
            self._resolve_file_dependencies(file_info)
        
        # Detect circular dependencies
        if self.config.detect_circular_deps:
            self._detect_circular_dependencies()
        
        # Build reverse dependencies
        self._build_reverse_dependencies(files)
        
        print(f"  ✓ Found {len(self.graph.edges)} internal dependencies")
        print(f"  ✓ Found {len(self.graph.external_global)} external packages")
        if self.graph.circular_groups:
            print(f"  ⚠️  Detected {len(self.graph.circular_groups)} circular dependency groups")
        
        return self.graph
    
    def _build_lookup_maps(self, files: List[FileInfo]):
        """
        Build lookup maps for fast file resolution.
        
        Args:
            files: List of files
        """
        for file_info in files:
            # By reference ID
            self.file_by_ref[file_info.ref_id] = file_info
            
            # By relative path
            self.file_by_path[file_info.rel_path] = file_info
            
            # By stem (filename without extension)
            stem = file_info.path.stem
            # Handle multiple files with same stem
            if stem not in self.file_by_stem:
                self.file_by_stem[stem] = file_info
    
    def _resolve_file_dependencies(self, file_info: FileInfo):
        """
        Resolve imports to actual file dependencies.
        
        Args:
            file_info: File to resolve dependencies for
        """
        for import_name in file_info.imports:
            # Try to resolve to internal file
            target_file = self._resolve_import(file_info, import_name)
            
            if target_file:
                # Internal dependency
                self.graph.add_edge(file_info.ref_id, target_file.ref_id)
                file_info.internal_deps.add(target_file.ref_id)
            else:
                # External dependency (library)
                if not import_name.startswith('.'):  # Skip unresolved relative imports
                    file_info.external_deps.add(import_name)
                    self.graph.external_global.add(import_name)
                    
                    if file_info.ref_id not in self.graph.external_by_file:
                        self.graph.external_by_file[file_info.ref_id] = set()
                    self.graph.external_by_file[file_info.ref_id].add(import_name)
    
    def _resolve_import(self, file_info: FileInfo, import_name: str) -> Optional[FileInfo]:
        """
        Resolve an import to a FileInfo object.
        
        Args:
            file_info: File containing the import
            import_name: Import module name
        
        Returns:
            Target FileInfo or None if external/not found
        """
        # Relative import (starts with .)
        if import_name.startswith('.'):
            return self._resolve_relative_import(file_info, import_name)
        
        # Absolute import - try to find by module name
        # First, try direct stem match
        if import_name in self.file_by_stem:
            return self.file_by_stem[import_name]
        
        # Try to find in same directory or subdirectories
        current_dir = file_info.path.parent
        for potential_file in self.file_by_path.values():
            if potential_file.path.stem == import_name:
                # Prefer files in same directory or subdirectories
                if str(current_dir) in str(potential_file.path.parent):
                    return potential_file
        
        # Not found - assume external
        return None
    
    def _resolve_relative_import(self, file_info: FileInfo, rel_import: str) -> Optional[FileInfo]:
        """
        Resolve relative import (./module or ../module).
        
        Args:
            file_info: File containing the import
            rel_import: Relative import string
        
        Returns:
            Target FileInfo or None
        """
        current_dir = file_info.path.parent
        
        # Parse relative path
        # ./module or ../module or ../../module
        parts = rel_import.split('/')
        
        # Navigate up directories
        target_dir = current_dir
        module_name = None
        
        for part in parts:
            if part == '.':
                continue
            elif part == '..':
                target_dir = target_dir.parent
            else:
                # This is the module name
                module_name = part
                break
        
        if not module_name:
            return None
        
        # Try different extensions
        for ext in ['.py', '.js', '.jsx', '.ts', '.tsx']:
            potential_path = target_dir / f"{module_name}{ext}"
            
            # Convert to relative path from project root
            try:
                rel_path = str(potential_path.relative_to(file_info.path.parent.parent.parent))
                if rel_path in self.file_by_path:
                    return self.file_by_path[rel_path]
            except:
                pass
        
        # Try as directory with index file
        for index_name in ['index.js', 'index.ts', '__init__.py']:
            potential_path = target_dir / module_name / index_name
            try:
                rel_path = str(potential_path.relative_to(file_info.path.parent.parent.parent))
                if rel_path in self.file_by_path:
                    return self.file_by_path[rel_path]
            except:
                pass
        
        return None
    
    def _detect_circular_dependencies(self):
        """
        Detect circular dependencies using Tarjan's algorithm.
        
        Populates graph.circular_groups with sets of mutually dependent files.
        """
        # Build adjacency list
        adj = defaultdict(set)
        for edge in self.graph.edges:
            adj[edge.source].add(edge.target)
        
        # Tarjan's SCC algorithm
        index_counter = [0]
        stack = []
        lowlinks = {}
        index = {}
        on_stack = defaultdict(bool)
        
        def strongconnect(node):
            index[node] = index_counter[0]
            lowlinks[node] = index_counter[0]
            index_counter[0] += 1
            on_stack[node] = True
            stack.append(node)
            
            # Check successors
            for successor in adj[node]:
                if successor not in index:
                    strongconnect(successor)
                    lowlinks[node] = min(lowlinks[node], lowlinks[successor])
                elif on_stack[successor]:
                    lowlinks[node] = min(lowlinks[node], index[successor])
            
            # Found SCC
            if lowlinks[node] == index[node]:
                component = set()
                while True:
                    successor = stack.pop()
                    on_stack[successor] = False
                    component.add(successor)
                    if successor == node:
                        break
                
                # Only add if circular (more than 1 node)
                if len(component) > 1:
                    self.graph.circular_groups.append(component)
        
        # Run algorithm on all nodes
        for node in list(adj.keys()):
            if node not in index:
                strongconnect(node)
    
    def _build_reverse_dependencies(self, files: List[FileInfo]):
        """
        Build reverse dependency map and populate file circular deps.
        
        Args:
            files: List of all files
        """
        # Update FileInfo objects with reverse deps and circular deps
        for file_info in files:
            # Reverse dependencies
            file_info.reverse_deps = self.graph.get_dependents(file_info.ref_id)
            
            # Circular dependencies
            for group in self.graph.circular_groups:
                if file_info.ref_id in group:
                    # Add all other files in the circular group
                    file_info.circular_deps = group - {file_info.ref_id}
                    break