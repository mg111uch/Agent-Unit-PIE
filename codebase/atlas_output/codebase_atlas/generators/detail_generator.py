"""
Detail generator for Codebase Atlas.

Generates children/*.md files (Layer 2) - detailed breakdown of file groups.
Includes inline impact matrices for functions.
"""

from pathlib import Path
from typing import List, Dict
from collections import defaultdict

from ..models import AtlasData, FileInfo, FunctionInfo, ImpactNode
from ..config import AtlasConfig
from ..utils import (
    write_file, get_timestamp, ensure_directory,
    format_compact, format_verbose, format_impact_analysis
)


class DetailGenerator:
    """Generates detailed children/*.md files."""
    
    def __init__(self, config: AtlasConfig, atlas_data: AtlasData):
        """
        Initialize detail generator.
        
        Args:
            config: Atlas configuration
            atlas_data: Complete atlas data
        """
        self.config = config
        self.atlas_data = atlas_data
    
    def generate(self, output_dir: str) -> List[str]:
        """
        Generate all children/*.md files.
        
        Args:
            output_dir: Output directory path
        
        Returns:
            List of generated file paths
        """
        print("📂 Generating children files...")
        
        # Create children directory
        children_dir = Path(output_dir) / self.config.children_dir
        ensure_directory(str(children_dir))
        
        # Group files
        file_groups = self._group_files()
        
        # Generate a child file for each group
        generated_paths = []
        
        for group_name, files in file_groups.items():
            file_path = self._generate_child_file(
                children_dir,
                group_name,
                files
            )
            generated_paths.append(file_path)
        
        print(f"  ✓ Generated {len(generated_paths)} children files")
        
        return generated_paths
    
    def _group_files(self) -> Dict[str, List[FileInfo]]:
        """
        Group files for children file generation.
        
        Returns:
            Dict mapping group name to list of files
        """
        # Group by directory first
        by_directory = defaultdict(list)
        
        for file_info in self.atlas_data.files:
            # Get directory name
            dir_path = file_info.path.parent
            dir_name = dir_path.name if dir_path.name else 'root'
            by_directory[dir_name].append(file_info)
        
        # Split large groups
        final_groups = {}
        
        for dir_name, files in by_directory.items():
            if len(files) <= self.config.max_files_per_child:
                final_groups[dir_name] = files
            else:
                # Split into chunks
                for i in range(0, len(files), self.config.max_files_per_child):
                    chunk = files[i:i + self.config.max_files_per_child]
                    chunk_num = i // self.config.max_files_per_child + 1
                    group_name = f"{dir_name}_{chunk_num}"
                    final_groups[group_name] = chunk
        
        return final_groups
    
    def _generate_child_file(
        self,
        children_dir: Path,
        group_name: str,
        files: List[FileInfo]
    ) -> str:
        """
        Generate a single child file.
        
        Args:
            children_dir: Children directory path
            group_name: Name for this group
            files: List of files to include
        
        Returns:
            Path to generated file
        """
        lines = []
        
        # Header
        lines.extend([
            f"# 📂 {group_name}",
            f"**Generated:** {get_timestamp()}",
            f"**Files:** {len(files)}",
            "",
            "---",
            "",
        ])
        
        # Add each file
        for file_info in sorted(files, key=lambda f: f.path.name):
            lines.extend(self._format_file_detail(file_info))
            lines.append("")
        
        # Write file
        file_path = children_dir / f"{group_name}.md"
        content = '\n'.join(lines)
        write_file(str(file_path), content)
        
        # Check LOC
        loc = len(lines)
        if loc > self.config.child_max_loc:
            print(f"  ⚠️  {group_name}.md exceeds target LOC ({loc} > {self.config.child_max_loc})")
        
        return str(file_path)
    
    def _format_file_detail(self, file_info: FileInfo) -> List[str]:
        """
        Format complete file details.
        
        Args:
            file_info: File to format
        
        Returns:
            List of formatted lines
        """
        lines = []
        
        if self.config.verbose_mode:
            # Use verbose formatting from utils
            lines.extend(format_verbose(file_info, self.config))
            
            # Add impact analysis for functions
            lines.extend(self._format_functions_with_impact(file_info, verbose=True))
        else:
            # Use compact formatting from utils
            lines.extend(format_compact(file_info, self.config))
            
            # Add compact impact analysis
            lines.extend(self._format_functions_with_impact(file_info, verbose=False))
        
        lines.append("---")
        
        return lines
    
    def _format_functions_with_impact(
        self,
        file_info: FileInfo,
        verbose: bool
    ) -> List[str]:
        """
        Format functions with inline impact analysis.
        
        Args:
            file_info: File containing functions
            verbose: Use verbose formatting
        
        Returns:
            List of formatted lines
        """
        lines = []
        
        # Get all functions (including class methods)
        all_funcs = file_info.get_all_functions()
        
        if not all_funcs:
            return lines
        
        # Only show impact for functions with dependencies or risks
        funcs_with_impact = [
            f for f in all_funcs
            if f.called_by or f.calls or f.risk_level.value != 'safe'
        ]
        
        if not funcs_with_impact:
            return lines
        
        if verbose:
            lines.append("### Impact Analysis")
            lines.append("")
        
        for func in funcs_with_impact:
            # Get impact node
            node_key = f"{file_info.ref_id}:{func.name}"
            impact_node = self.atlas_data.impact_nodes.get(node_key)
            
            if not impact_node:
                continue
            
            # Format function with impact
            if verbose:
                lines.append(f"#### `{func.get_signature(compact=False)}`")
                lines.append("")
            else:
                lines.append(f"F: {func.get_signature(compact=True)}")
            
            # Add impact analysis
            impact_lines = format_impact_analysis(
                func,
                impact_node,
                self.config,
                compact=not verbose
            )
            lines.extend(impact_lines)
            
            if verbose:
                lines.append("")
        
        return lines
    
    def _format_class_detail(
        self,
        file_info: FileInfo,
        verbose: bool
    ) -> List[str]:
        """
        Format class details with method impact.
        
        Args:
            file_info: File containing classes
            verbose: Use verbose formatting
        
        Returns:
            List of formatted lines
        """
        lines = []
        
        if not file_info.classes:
            return lines
        
        for cls in file_info.classes:
            if verbose:
                # Class header
                base_str = f" extends {', '.join(cls.bases)}" if cls.bases else ""
                lines.append(f"### Class: `{cls.name}`{base_str}")
                lines.append("")
                
                if cls.docstring:
                    lines.append(f"*{cls.docstring.split(chr(10))[0][:100]}*")
                    lines.append("")
                
                # Methods with impact
                if cls.methods:
                    lines.append("**Methods:**")
                    lines.append("")
                    
                    for method in cls.methods:
                        # Get impact
                        node_key = f"{file_info.ref_id}:{method.name}"
                        impact_node = self.atlas_data.impact_nodes.get(node_key)
                        
                        if impact_node and impact_node.total_impact_count > 0:
                            risk_symbol = self.config.risk_symbols.get(
                                impact_node.risk_level.value, ''
                            )
                            lines.append(
                                f"- `{method.get_signature(compact=False)}` "
                                f"{risk_symbol}"
                            )
                            
                            # Add brief impact
                            if impact_node.direct_callers:
                                callers = [f"[{r}]:{n}" for r, n in list(impact_node.direct_callers)[:3]]
                                lines.append(f"  - Called by: {', '.join(callers)}")
                        else:
                            lines.append(f"- `{method.get_signature(compact=False)}`")
                    
                    lines.append("")
            else:
                # Compact class format already handled in format_compact
                pass
        
        return lines