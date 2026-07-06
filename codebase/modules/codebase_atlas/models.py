"""
Data models for Codebase Atlas.

This module defines all data structures used throughout the analysis pipeline.
"""

from pathlib import Path
from typing import List, Set, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


# =============================================================================
# ENUMS
# =============================================================================

class RiskLevel(Enum):
    """Risk level for code changes."""
    SAFE = "safe"      # 0 dependents
    LOW = "low"        # 1 dependent
    MEDIUM = "medium"  # 2 dependents
    HIGH = "high"      # 3+ dependents


class FileCategory(Enum):
    """File category for organization."""
    CORE = "core"
    API = "api"
    DATA = "data"
    UTILS = "utils"
    TESTS = "tests"
    CONFIG = "config"
    OTHER = "other"


# =============================================================================
# FUNCTION & CLASS INFO
# =============================================================================

@dataclass
class FunctionInfo:
    """Information about a function or method."""
    name: str
    args: List[Tuple[str, Optional[str]]] = field(default_factory=list)  # (name, type)
    returns: Optional[str] = None
    docstring: Optional[str] = None
    is_entry: bool = False
    is_method: bool = False
    is_async: bool = False
    decorators: List[str] = field(default_factory=list)
    line_number: int = 0
    
    # Impact analysis
    calls: Set[str] = field(default_factory=set)  # Function names called
    called_by: Set[str] = field(default_factory=set)  # Function names that call this
    reads_vars: Set[str] = field(default_factory=set)  # Variables read
    writes_vars: Set[str] = field(default_factory=set)  # Variables written
    external_calls: Set[str] = field(default_factory=set)  # External lib calls
    
    risk_level: RiskLevel = RiskLevel.SAFE
    produces_json: List[str] = field(default_factory=list)
    
    def get_signature(self, compact: bool = False) -> str:
        """Get function signature string."""
        if compact:
            args_str = ','.join([name for name, _ in self.args])
            ret_str = f"→{self.returns}" if self.returns else ""
            return f"{self.name}({args_str}){ret_str}"
        else:
            args_str = ', '.join([
                f"{name}: {typ}" if typ else name 
                for name, typ in self.args
            ])
            ret_str = f" -> {self.returns}" if self.returns else ""
            return f"{self.name}({args_str}){ret_str}"
    
    def get_dependent_count(self) -> int:
        """Get total number of dependents (callers + consumers)."""
        return len(self.called_by) + sum(1 for _ in self.reads_vars)


@dataclass
class ClassInfo:
    """Information about a class."""
    name: str
    bases: List[str] = field(default_factory=list)
    methods: List[FunctionInfo] = field(default_factory=list)
    docstring: Optional[str] = None
    line_number: int = 0
    
    # Composition
    uses_components: Set[str] = field(default_factory=set)  # Component names
    
    def get_method_names(self) -> List[str]:
        """Get list of method names."""
        return [m.name for m in self.methods]
    
    def get_public_methods(self) -> List[FunctionInfo]:
        """Get only public methods (not starting with _)."""
        return [m for m in self.methods if not m.name.startswith('_')]


# =============================================================================
# FILE INFO
# =============================================================================

@dataclass
class FileInfo:
    """Complete information about a single file."""
    
    # Basic metadata
    path: Path
    rel_path: str  # Relative to project root
    ref_id: str  # Reference ID (F001, F002, etc.)
    ext: str  # File extension
    category: FileCategory = FileCategory.OTHER
    
    # Content metrics
    loc: int = 0  # Lines of code
    docstring: Optional[str] = None
    error: Optional[str] = None
    
    # Code structure
    imports: Set[str] = field(default_factory=set)  # Module names imported
    exports: Set[str] = field(default_factory=set)  # Names exported (JS/TS)
    classes: List[ClassInfo] = field(default_factory=list)
    functions: List[FunctionInfo] = field(default_factory=list)
    config_keys: List[str] = field(default_factory=list)  # For config files
    
    # Special markers
    entry_point: bool = False
    is_react_component: bool = False
    react_components: List[str] = field(default_factory=list)
    template_engine: Optional[str] = None  # For HTML files
    html_analyzed: bool = False
    
    # Dependencies (filled by DependencyAnalyzer)
    internal_deps: Set[str] = field(default_factory=set)  # File ref IDs
    external_deps: Set[str] = field(default_factory=set)  # Package names
    reverse_deps: Set[str] = field(default_factory=set)  # Files that depend on this
    circular_deps: Set[str] = field(default_factory=set)  # Circular refs
    
    def get_all_functions(self) -> List[FunctionInfo]:
        """Get all functions including methods from classes."""
        funcs = list(self.functions)
        for cls in self.classes:
            funcs.extend(cls.methods)
        return funcs
    
    def get_high_risk_functions(self) -> List[FunctionInfo]:
        """Get functions with HIGH risk level."""
        return [f for f in self.get_all_functions() if f.risk_level == RiskLevel.HIGH]
    
    def get_entry_functions(self) -> List[FunctionInfo]:
        """Get functions marked as entry points."""
        return [f for f in self.get_all_functions() if f.is_entry]


# =============================================================================
# DEPENDENCY GRAPH
# =============================================================================

@dataclass
class DependencyEdge:
    """An edge in the dependency graph."""
    source: str  # Source file ref ID
    target: str  # Target file ref ID
    import_type: str  # 'import', 'from', 'require', etc.
    line_number: int = 0


@dataclass
class DependencyGraph:
    """Complete dependency graph for the project."""
    
    # File-level dependencies
    edges: List[DependencyEdge] = field(default_factory=list)
    
    # Quick lookups
    forward_deps: Dict[str, Set[str]] = field(default_factory=dict)  # file -> files it depends on
    reverse_deps: Dict[str, Set[str]] = field(default_factory=dict)  # file -> files that depend on it
    circular_groups: List[Set[str]] = field(default_factory=list)  # Groups of files in circular deps
    
    # External dependencies
    external_by_file: Dict[str, Set[str]] = field(default_factory=dict)  # file -> external packages
    external_global: Set[str] = field(default_factory=set)  # All external packages
    
    def add_edge(self, source: str, target: str, import_type: str = "import"):
        """Add a dependency edge."""
        edge = DependencyEdge(source, target, import_type)
        self.edges.append(edge)
        
        # Update forward deps
        if source not in self.forward_deps:
            self.forward_deps[source] = set()
        self.forward_deps[source].add(target)
        
        # Update reverse deps
        if target not in self.reverse_deps:
            self.reverse_deps[target] = set()
        self.reverse_deps[target].add(source)
    
    def get_dependents(self, ref_id: str) -> Set[str]:
        """Get all files that depend on this file."""
        return self.reverse_deps.get(ref_id, set())
    
    def get_dependencies(self, ref_id: str) -> Set[str]:
        """Get all files this file depends on."""
        return self.forward_deps.get(ref_id, set())
    
    def is_circular(self, ref_id: str) -> bool:
        """Check if file is part of circular dependency."""
        return any(ref_id in group for group in self.circular_groups)


# =============================================================================
# IMPACT ANALYSIS
# =============================================================================

@dataclass
class ImpactNode:
    """Impact analysis for a single function."""
    
    function_name: str
    file_ref: str
    
    # Direct impacts
    direct_callers: Set[Tuple[str, str]] = field(default_factory=set)  # (file_ref, func_name)
    direct_calls: Set[Tuple[str, str]] = field(default_factory=set)  # (file_ref, func_name)
    
    # Indirect impacts (consumers of outputs)
    reads_output: Set[Tuple[str, str]] = field(default_factory=set)  # (file_ref, func_name)
    
    # Variables
    reads_vars: Set[str] = field(default_factory=set)
    writes_vars: Set[str] = field(default_factory=set)
    
    # External calls
    external_calls: Set[str] = field(default_factory=set)
    
    # Risk assessment
    risk_level: RiskLevel = RiskLevel.SAFE
    total_impact_count: int = 0
    
    def calculate_impact(self):
        """Calculate total impact count and risk level."""
        self.total_impact_count = (
            len(self.direct_callers) + 
            len(self.reads_output)
        )
        
        # Set risk level
        if self.total_impact_count >= 3:
            self.risk_level = RiskLevel.HIGH
        elif self.total_impact_count == 2:
            self.risk_level = RiskLevel.MEDIUM
        elif self.total_impact_count == 1:
            self.risk_level = RiskLevel.LOW
        else:
            self.risk_level = RiskLevel.SAFE
    
    def get_all_breaks(self) -> List[Tuple[str, str, str]]:
        """
        Get all things that break if this function changes.
        
        Returns:
            List of (file_ref, function_name, reason) tuples
        """
        breaks = []
        
        for file_ref, func_name in self.direct_callers:
            breaks.append((file_ref, func_name, "direct call"))
        
        for file_ref, func_name in self.reads_output:
            breaks.append((file_ref, func_name, "consumes output"))
        
        return breaks


# =============================================================================
# ATLAS DATA CONTAINER
# =============================================================================

@dataclass
class AtlasData:
    """Complete atlas data for the entire project."""
    
    # All files
    files: List[FileInfo] = field(default_factory=list)
    file_map: Dict[str, FileInfo] = field(default_factory=dict)  # ref_id -> FileInfo
    
    # Dependencies
    dependency_graph: DependencyGraph = field(default_factory=DependencyGraph)
    
    # Impact analysis
    impact_nodes: Dict[str, ImpactNode] = field(default_factory=dict)  # "file_ref:func_name" -> ImpactNode
    
    # Entry points
    entry_points: List[Tuple[str, str]] = field(default_factory=list)  # (file_ref, function_name)
    
    # Statistics
    total_loc: int = 0
    total_files: int = 0
    language_distribution: Dict[str, int] = field(default_factory=dict)
    
    def add_file(self, file_info: FileInfo):
        """Add a file to the atlas."""
        self.files.append(file_info)
        self.file_map[file_info.ref_id] = file_info
        self.total_files += 1
        self.total_loc += file_info.loc
    
    def get_file_by_ref(self, ref_id: str) -> Optional[FileInfo]:
        """Get file by reference ID."""
        return self.file_map.get(ref_id)
    
    def get_files_by_category(self, category: FileCategory) -> List[FileInfo]:
        """Get all files in a category."""
        return [f for f in self.files if f.category == category]
    
    def get_high_risk_files(self) -> List[FileInfo]:
        """Get files with high-risk functions."""
        return [f for f in self.files if f.get_high_risk_functions()]
    
    def get_critical_functions(self) -> List[Tuple[FileInfo, FunctionInfo]]:
        """Get all functions with HIGH risk or entry points."""
        critical = []
        for file_info in self.files:
            for func in file_info.get_all_functions():
                if func.risk_level == RiskLevel.HIGH or func.is_entry:
                    critical.append((file_info, func))
        return critical