"""
Base generator for Codebase Atlas.

Generates base.md (Layer 1) - the entry point file that agents read first.
Kept compact (<100 LOC, <1000 tokens) with links to detailed children files.
"""

from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict

from ..models import AtlasData, FileInfo, RiskLevel
from ..config import AtlasConfig, get_priority_level, estimate_tokens
from ..utils import write_file, get_timestamp


class BaseGenerator:
    """Generates base.md overview file."""
    
    def __init__(self, config: AtlasConfig, atlas_data: AtlasData):
        """
        Initialize base generator.
        
        Args:
            config: Atlas configuration
            atlas_data: Complete atlas data
        """
        self.config = config
        self.atlas_data = atlas_data
        self.lines: List[str] = []
    
    def generate(self, output_dir: str) -> str:
        """
        Generate base.md file.
        
        Args:
            output_dir: Output directory path
        
        Returns:
            Path to generated file
        """
        print("📝 Generating base.md...")
        
        self.lines = []
        
        # Header
        self._add_header()
        
        # Legend
        self._add_legend()
        
        # Overview statistics
        self._add_overview()
        
        # Critical entry points
        self._add_entry_points()
        
        # High-risk functions
        self._add_high_risk_functions()
        
        # Circular dependencies warning
        self._add_circular_dependencies()
        
        # Navigation guide (children files)
        self._add_navigation()
        
        # Check token budget and truncate if needed
        self._apply_budget_limits()
        
        # Write file
        output_path = Path(output_dir) / self.config.base_filename
        content = '\n'.join(self.lines)
        write_file(str(output_path), content)
        
        # Report
        loc = len(self.lines)
        tokens = estimate_tokens(content)
        print(f"  ✓ Generated base.md ({loc} lines, ~{tokens} tokens)")
        
        if loc > self.config.base_max_loc:
            print(f"  ⚠️  Exceeded target LOC ({loc} > {self.config.base_max_loc})")
        
        return str(output_path)
    
    def _add_header(self):
        """Add file header."""
        self.lines.extend([
            "# 🗺️ CODEBASE ATLAS",
            f"**Generated:** {get_timestamp()}",
            "",
            "**Quick Navigation:** This is Layer 1 (overview). For details, see children/ folder.",
            "",
            "---",
            "",
        ])
    
    def _add_legend(self):
        """Add symbol legend."""
        if self.config.verbose_mode:
            self.lines.extend([
                "## 📖 Legend",
                "",
                "**Symbols:**",
                f"- {self.config.compact_symbols['separator']} = Separator",
                f"- {self.config.compact_symbols['internal_dep']} = Internal dependency",
                f"- {self.config.compact_symbols['external_dep']} = External library",
                f"- {self.config.compact_symbols['entry_point']} = Entry point",
                f"- {self.config.compact_symbols['circular']} = Circular dependency",
                "",
                "**Risk Levels:**",
                f"- {self.config.risk_symbols['high']} HIGH = 3+ dependents",
                f"- {self.config.risk_symbols['medium']} MEDIUM = 2 dependents",
                f"- {self.config.risk_symbols['low']} LOW = 1 dependent",
                f"- {self.config.risk_symbols['safe']} SAFE = 0 dependents",
                "",
                "---",
                "",
            ])
        else:
            # Compact legend
            sep = self.config.compact_symbols['separator']
            self.lines.extend([
                f"Legend: {sep}=sep {self.config.compact_symbols['internal_dep']}=internal "
                f"{self.config.compact_symbols['external_dep']}=external "
                f"{self.config.compact_symbols['entry_point']}=entry "
                f"{self.config.risk_symbols['high']}=HIGH {self.config.risk_symbols['medium']}=MED "
                f"{self.config.risk_symbols['low']}=LOW {self.config.risk_symbols['safe']}=SAFE",
                "",
            ])
    
    def _add_overview(self):
        """Add overview statistics."""
        lang_dist = self._get_language_distribution()
        
        if self.config.verbose_mode:
            self.lines.extend([
                "## 📊 Overview",
                "",
                f"- **Total Files:** {self.atlas_data.total_files}",
                f"- **Total LOC:** ~{self.atlas_data.total_loc:,}",
                f"- **Languages:** {lang_dist}",
                f"- **Entry Points:** {len(self.atlas_data.entry_points)}",
                "",
            ])
        else:
            # Ultra-compact
            self.lines.append(
                f"Overview: {self.atlas_data.total_files}files {self.atlas_data.total_loc}LOC "
                f"{lang_dist} {len(self.atlas_data.entry_points)}entries"
            )
            self.lines.append("")
    
    def _add_entry_points(self):
        """Add critical entry points."""
        if not self.atlas_data.entry_points:
            return
        
        # Show first 10 entry points
        entries = self.atlas_data.entry_points[:10]
        
        if self.config.verbose_mode:
            self.lines.extend([
                "## ⚡ Entry Points",
                "",
            ])
            for file_ref, func_name, category in entries:
                if func_name == 'file':
                    self.lines.append(f"- [{file_ref}] (file-level entry) [{category}]")
                else:
                    self.lines.append(f"- [{file_ref}] `{func_name}()` [{category}]")
            
            if len(self.atlas_data.entry_points) > 10:
                remaining = len(self.atlas_data.entry_points) - 10
                self.lines.append(f"- ... +{remaining} more (see children files)")
            
            self.lines.append("")
        else:
            # Compact: just list refs
            entry_refs = [f"{ref}:{func}" if func != 'file' else ref 
                         for ref, func, cat in entries]
            self.lines.append(f"Entries: {','.join(entry_refs)}")
            self.lines.append("")
    
    def _add_high_risk_functions(self):
        """Add high-risk functions that need careful modification."""
        high_risk = self.atlas_data.get_critical_functions()
        
        if not high_risk:
            return
        
        # Limit to top 15 by impact count
        high_risk_sorted = sorted(
            high_risk,
            key=lambda x: x[1].risk_level.value,
            reverse=True
        )[:15]
        
        if self.config.verbose_mode:
            self.lines.extend([
                "## 🔴 High-Risk Functions",
                "",
                "Functions with many dependents (changes require extensive testing):",
                "",
            ])
            
            for file_info, func_info in high_risk_sorted:
                impact_node = self.atlas_data.impact_nodes.get(
                    f"{file_info.ref_id}:{func_info.name}"
                )
                if impact_node:
                    risk_symbol = self.config.risk_symbols.get(
                        impact_node.risk_level.value, ''
                    )
                    self.lines.append(
                        f"- [{file_info.ref_id}] `{func_info.name}()` "
                        f"{risk_symbol} ({impact_node.total_impact_count} dependents)"
                    )
            
            self.lines.append("")
        else:
            # Compact
            risk_items = []
            for file_info, func_info in high_risk_sorted[:10]:
                impact_node = self.atlas_data.impact_nodes.get(
                    f"{file_info.ref_id}:{func_info.name}"
                )
                if impact_node:
                    risk_symbol = self.config.risk_symbols.get(
                        impact_node.risk_level.value, ''
                    )
                    risk_items.append(
                        f"{file_info.ref_id}:{func_info.name}{risk_symbol}"
                    )
            
            if risk_items:
                self.lines.append(f"HighRisk: {','.join(risk_items)}")
                self.lines.append("")
    
    def _add_circular_dependencies(self):
        """Add circular dependency warnings."""
        if not self.atlas_data.dependency_graph.circular_groups:
            return
        
        if self.config.verbose_mode:
            self.lines.extend([
                "## ⚠️ Circular Dependencies",
                "",
            ])
            
            for i, group in enumerate(self.atlas_data.dependency_graph.circular_groups[:5]):
                refs = sorted(group)
                self.lines.append(f"- Group {i+1}: {' ↔ '.join(refs)}")
            
            if len(self.atlas_data.dependency_graph.circular_groups) > 5:
                remaining = len(self.atlas_data.dependency_graph.circular_groups) - 5
                self.lines.append(f"- ... +{remaining} more groups")
            
            self.lines.append("")
        else:
            # Compact - just count
            count = len(self.atlas_data.dependency_graph.circular_groups)
            self.lines.append(f"⚠️ Circular: {count} groups")
            self.lines.append("")
    
    def _add_navigation(self):
        """Add navigation to children files."""
        # Group files by category/directory for children files
        children_groups = self._get_children_groups()
        
        if self.config.verbose_mode:
            self.lines.extend([
                "## 🗂️ Detailed Breakdown",
                "",
                "For complete details, see children/ folder:",
                "",
            ])
            
            for group_name, files in children_groups.items():
                child_file = f"{group_name}.md"
                file_count = len(files)
                self.lines.append(f"- **{child_file}** ({file_count} files)")
            
            self.lines.append("")
        else:
            # Compact
            child_names = [f"{name}.md" for name in children_groups.keys()]
            self.lines.append(f"Children: {','.join(child_names)}")
            self.lines.append("")
    
    def _get_language_distribution(self) -> str:
        """Get language distribution string."""
        lang_count = defaultdict(int)
        
        for file_info in self.atlas_data.files:
            if file_info.ext == '.py':
                lang_count['Python'] += 1
            elif file_info.ext in {'.js', '.jsx', '.ts', '.tsx'}:
                lang_count['JS/TS'] += 1
            elif file_info.ext == '.html':
                lang_count['HTML'] += 1
            elif file_info.ext in {'.json', '.yaml', '.yml'}:
                lang_count['Config'] += 1
        
        total = sum(lang_count.values())
        parts = []
        for lang, count in sorted(lang_count.items(), key=lambda x: x[1], reverse=True):
            pct = (count / total * 100) if total > 0 else 0
            parts.append(f"{lang}({pct:.0f}%)")
        
        return ','.join(parts)
    
    def _get_children_groups(self) -> Dict[str, List[FileInfo]]:
        """
        Group files for children file generation.
        
        Returns:
            Dict mapping group name to list of files
        """
        # Group by directory
        by_directory = defaultdict(list)
        
        for file_info in self.atlas_data.files:
            dir_path = file_info.path.parent
            # Get relative directory name
            dir_name = dir_path.name if dir_path.name else 'root'
            by_directory[dir_name].append(file_info)
        
        # Split large groups if they exceed max_files_per_child
        final_groups = {}
        
        for dir_name, files in by_directory.items():
            if len(files) <= self.config.max_files_per_child:
                final_groups[dir_name] = files
            else:
                # Split into multiple groups
                for i in range(0, len(files), self.config.max_files_per_child):
                    chunk = files[i:i + self.config.max_files_per_child]
                    group_name = f"{dir_name}_{i // self.config.max_files_per_child + 1}"
                    final_groups[group_name] = chunk
        
        return final_groups
    
    def _apply_budget_limits(self):
        """Apply LOC and token budget limits with smart truncation."""
        current_loc = len(self.lines)
        
        if current_loc <= self.config.base_max_loc:
            return  # Within budget
        
        # Need to truncate - remove lower priority sections
        # Priority: Header > Legend > Overview > Entries > HighRisk > Circular > Navigation
        
        # For now, just truncate and add notice
        truncated_lines = self.lines[:self.config.base_max_loc - 3]
        truncated_lines.extend([
            "",
            "---",
            "*[Truncated - see children/ for complete details]*",
        ])
        
        self.lines = truncated_lines