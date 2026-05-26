"""
Impact analyzer for Codebase Atlas.

Builds "what breaks if X changes" analysis by tracking:
- Function call chains
- Variable dependencies
- Risk assessment
"""

from typing import List, Dict, Set, Tuple
from collections import defaultdict

from ..models import (
    FileInfo, FunctionInfo, ImpactNode, RiskLevel, AtlasData
)
from ..config import AtlasConfig


class ImpactAnalyzer:
    """Analyzes impact of code changes across the codebase."""
    
    def __init__(self, config: AtlasConfig):
        """
        Initialize impact analyzer.
        
        Args:
            config: Atlas configuration
        """
        self.config = config
        
        # Impact tracking maps
        self.impact_nodes: Dict[str, ImpactNode] = {}  # "ref_id:func_name" -> ImpactNode
        
        # Function lookup maps
        self.func_by_name: Dict[str, List[Tuple[str, FunctionInfo]]] = defaultdict(list)  # func_name -> [(ref_id, FunctionInfo)]
        self.func_by_file: Dict[str, List[FunctionInfo]] = defaultdict(list)  # ref_id -> [FunctionInfo]
        
        # Variable tracking
        self.var_writers: Dict[str, Set[Tuple[str, str]]] = defaultdict(set)  # var_name -> {(ref_id, func_name)}
        self.var_readers: Dict[str, Set[Tuple[str, str]]] = defaultdict(set)  # var_name -> {(ref_id, func_name)}
    
    def analyze(self, files: List[FileInfo]) -> Dict[str, ImpactNode]:
        """
        Build impact analysis for all functions.
        
        Args:
            files: List of parsed FileInfo objects
        
        Returns:
            Dictionary of impact nodes
        """
        print("💥 Analyzing impact chains...")
        
        # Build function lookup maps
        self._build_function_maps(files)
        
        # Build variable dependency maps
        self._build_variable_maps(files)
        
        # Build impact nodes for each function
        self._build_impact_nodes(files)
        
        # Resolve call relationships
        self._resolve_call_relationships()
        
        # Track variable dependencies
        self._track_variable_dependencies()
        
        # Calculate risk levels
        self._calculate_risk_levels()
        
        # Update FileInfo objects with risk levels
        self._update_file_risk_levels(files)
        
        print(f"  ✓ Analyzed {len(self.impact_nodes)} functions")
        high_risk = sum(1 for n in self.impact_nodes.values() if n.risk_level == RiskLevel.HIGH)
        print(f"  ✓ Identified {high_risk} high-risk functions")
        
        return self.impact_nodes
    
    def _build_function_maps(self, files: List[FileInfo]):
        """
        Build function lookup maps.
        
        Args:
            files: List of files
        """
        for file_info in files:
            all_funcs = file_info.get_all_functions()
            
            for func in all_funcs:
                # By name (for call resolution)
                self.func_by_name[func.name].append((file_info.ref_id, func))
                
                # By file
                self.func_by_file[file_info.ref_id].append(func)
    
    def _build_variable_maps(self, files: List[FileInfo]):
        """
        Build variable read/write tracking maps.
        
        Args:
            files: List of files
        """
        for file_info in files:
            for func in file_info.get_all_functions():
                func_key = (file_info.ref_id, func.name)
                
                # Track variable writes
                for var in func.writes_vars:
                    self.var_writers[var].add(func_key)
                
                # Track variable reads
                for var in func.reads_vars:
                    self.var_readers[var].add(func_key)
    
    def _build_impact_nodes(self, files: List[FileInfo]):
        """
        Create ImpactNode for each function.
        
        Args:
            files: List of files
        """
        for file_info in files:
            for func in file_info.get_all_functions():
                node_key = f"{file_info.ref_id}:{func.name}"
                
                impact_node = ImpactNode(
                    function_name=func.name,
                    file_ref=file_info.ref_id,
                    reads_vars=func.reads_vars.copy(),
                    writes_vars=func.writes_vars.copy(),
                    external_calls=func.external_calls.copy(),
                )
                
                self.impact_nodes[node_key] = impact_node
    
    def _resolve_call_relationships(self):
        """
        Resolve function calls to actual function references.
        
        Populates direct_callers and direct_calls in ImpactNodes.
        """
        for node_key, impact_node in self.impact_nodes.items():
            file_ref, func_name = node_key.split(':', 1)
            
            # Get the FunctionInfo
            func_info = self._get_function(file_ref, func_name)
            if not func_info:
                continue
            
            # Resolve calls
            for call_name in func_info.calls:
                # Find functions with this name
                targets = self.func_by_name.get(call_name, [])
                
                for target_ref, target_func in targets:
                    # Add to direct_calls
                    impact_node.direct_calls.add((target_ref, target_func.name))
                    
                    # Add reverse relationship (callers)
                    target_key = f"{target_ref}:{target_func.name}"
                    if target_key in self.impact_nodes:
                        self.impact_nodes[target_key].direct_callers.add((file_ref, func_name))
    
    def _track_variable_dependencies(self):
        """
        Track indirect dependencies through variables.
        
        If function A writes var X, and function B reads var X,
        then B depends on A's output.
        """
        for var_name, writers in self.var_writers.items():
            readers = self.var_readers.get(var_name, set())
            
            # Each reader depends on each writer's output
            for reader_ref, reader_func in readers:
                reader_key = f"{reader_ref}:{reader_func}"
                
                if reader_key in self.impact_nodes:
                    for writer_ref, writer_func in writers:
                        # Skip if same function
                        if (writer_ref, writer_func) != (reader_ref, reader_func):
                            self.impact_nodes[reader_key].reads_output.add((writer_ref, writer_func))
    
    def _calculate_risk_levels(self):
        """
        Calculate risk level for each function based on dependents.
        
        Uses thresholds from config:
        - HIGH: 3+ dependents
        - MEDIUM: 2 dependents
        - LOW: 1 dependent
        - SAFE: 0 dependents
        """
        for impact_node in self.impact_nodes.values():
            impact_node.calculate_impact()
            
            # Apply configured thresholds
            count = impact_node.total_impact_count
            
            if count >= self.config.risk_threshold_high:
                impact_node.risk_level = RiskLevel.HIGH
            elif count >= self.config.risk_threshold_medium:
                impact_node.risk_level = RiskLevel.MEDIUM
            elif count >= 1:
                impact_node.risk_level = RiskLevel.LOW
            else:
                impact_node.risk_level = RiskLevel.SAFE
    
    def _update_file_risk_levels(self, files: List[FileInfo]):
        """
        Update FunctionInfo objects with calculated risk levels.
        
        Args:
            files: List of files
        """
        for file_info in files:
            for func in file_info.get_all_functions():
                node_key = f"{file_info.ref_id}:{func.name}"
                
                if node_key in self.impact_nodes:
                    impact_node = self.impact_nodes[node_key]
                    func.risk_level = impact_node.risk_level
                    
                    # Update called_by
                    func.called_by = {f"{ref}:{name}" for ref, name in impact_node.direct_callers}
    
    def _get_function(self, file_ref: str, func_name: str) -> FunctionInfo:
        """
        Get FunctionInfo by file reference and function name.
        
        Args:
            file_ref: File reference ID
            func_name: Function name
        
        Returns:
            FunctionInfo or None
        """
        funcs = self.func_by_file.get(file_ref, [])
        for func in funcs:
            if func.name == func_name:
                return func
        return None
    
    def get_impact_chain(
        self,
        file_ref: str,
        func_name: str,
        depth: int = None
    ) -> List[Tuple[str, str, int]]:
        """
        Get impact chain for a function (who breaks if this changes).
        
        Args:
            file_ref: File reference ID
            func_name: Function name
            depth: Maximum depth (from config if None)
        
        Returns:
            List of (file_ref, func_name, depth_level) tuples
        """
        if depth is None:
            depth = self.config.impact_depth
        
        node_key = f"{file_ref}:{func_name}"
        if node_key not in self.impact_nodes:
            return []
        
        visited = set()
        impact_chain = []
        
        def traverse(current_key, current_depth):
            if current_depth > depth or current_key in visited:
                return
            
            visited.add(current_key)
            
            if current_key not in self.impact_nodes:
                return
            
            node = self.impact_nodes[current_key]
            
            # Add direct callers
            for ref, name in node.direct_callers:
                caller_key = f"{ref}:{name}"
                impact_chain.append((ref, name, current_depth))
                traverse(caller_key, current_depth + 1)
            
            # Add output consumers
            for ref, name in node.reads_output:
                consumer_key = f"{ref}:{name}"
                impact_chain.append((ref, name, current_depth))
                traverse(consumer_key, current_depth + 1)
        
        # Start traversal
        traverse(node_key, 1)
        
        return impact_chain
    
    def get_critical_functions(self) -> List[Tuple[str, str, ImpactNode]]:
        """
        Get all critical functions (HIGH risk or entry points).
        
        Returns:
            List of (file_ref, func_name, ImpactNode) tuples
        """
        critical = []
        
        for node_key, impact_node in self.impact_nodes.items():
            file_ref, func_name = node_key.split(':', 1)
            
            # Get function info to check if entry point
            func = self._get_function(file_ref, func_name)
            
            if impact_node.risk_level == RiskLevel.HIGH or (func and func.is_entry):
                critical.append((file_ref, func_name, impact_node))
        
        return critical