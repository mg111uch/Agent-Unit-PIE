"""
Base generator for Codebase Atlas.

Generates base.md (Layer 1) - the entry point file that agents read first.
Compact format (<100 LOC, <1000 tokens) with links to detailed children files.
"""

from pathlib import Path
from typing import List, Dict
from collections import defaultdict

from ..models import AtlasData, FileInfo
from ..config import AtlasConfig, estimate_tokens
from ..utils import write_file, get_timestamp


class BaseGenerator:
    """Generates base.md overview file."""

    def __init__(self, config: AtlasConfig, atlas_data: AtlasData):
        self.config = config
        self.atlas_data = atlas_data
        self.lines: List[str] = []

    def generate(self, output_dir: str) -> str:
        """Generate base.md file."""
        print("📝 Generating base.md...")

        self.lines = []

        self._add_header()
        self._add_overview()
        self._add_entry_points()
        self._add_high_risk_functions()
        self._add_circular_dependencies()
        self._add_navigation()

        self._apply_budget_limits()

        output_path = Path(output_dir) / self.config.base_filename
        content = '\n'.join(self.lines)
        write_file(str(output_path), content)

        loc = len(self.lines)
        tokens = estimate_tokens(content)
        print(f"  ✓ Generated base.md ({loc} lines, ~{tokens} tokens)")

        if loc > self.config.base_max_loc:
            print(f"  ⚠️  Exceeded target LOC ({loc} > {self.config.base_max_loc})")

        return str(output_path)

    def _add_header(self):
        self.lines.extend([
            "# 🗺️ CODEBASE ATLAS",
            f"Generated: {get_timestamp()}",
            "",
            "---",
            "",
        ])

    def _add_overview(self):
        lang_dist = self._get_language_distribution()
        self.lines.append(
            f"Overview: {self.atlas_data.total_files}files "
            f"{self.atlas_data.total_loc}LOC "
            f"{lang_dist} "
            f"{len(self.atlas_data.entry_points)}entries"
        )
        self.lines.append("")

    def _add_entry_points(self):
        if not self.atlas_data.entry_points:
            return

        entries = self.atlas_data.entry_points[:10]
        entry_refs = [
            f"{ref}:{func}" if func != 'file' else ref
            for ref, func, _cat in entries
        ]
        self.lines.append(f"Entries: {','.join(entry_refs)}")
        self.lines.append("")

    def _add_high_risk_functions(self):
        high_risk = self.atlas_data.get_critical_functions()

        if not high_risk:
            return

        high_risk_sorted = sorted(
            high_risk,
            key=lambda x: x[1].risk_level.value,
            reverse=True
        )[:15]

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
        if not self.atlas_data.dependency_graph.circular_groups:
            return

        count = len(self.atlas_data.dependency_graph.circular_groups)
        self.lines.append(f"⚠️ Circular: {count} groups")
        self.lines.append("")

    def _add_navigation(self):
        children_groups = self._get_children_groups()
        child_names = [f"{name}.md" for name in children_groups.keys()]
        self.lines.append(f"Children: {','.join(child_names)}")
        self.lines.append("")

    def _get_language_distribution(self) -> str:
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
        by_directory = defaultdict(list)

        for file_info in self.atlas_data.files:
            dir_path = file_info.path.parent
            dir_name = dir_path.name if dir_path.name else 'root'
            by_directory[dir_name].append(file_info)

        final_groups = {}

        for dir_name, files in by_directory.items():
            if len(files) <= self.config.max_files_per_child:
                final_groups[dir_name] = files
            else:
                for i in range(0, len(files), self.config.max_files_per_child):
                    chunk = files[i:i + self.config.max_files_per_child]
                    group_name = f"{dir_name}_{i // self.config.max_files_per_child + 1}"
                    final_groups[group_name] = chunk

        return final_groups

    def _apply_budget_limits(self):
        current_loc = len(self.lines)

        if current_loc <= self.config.base_max_loc:
            return

        truncated_lines = self.lines[:self.config.base_max_loc - 3]
        truncated_lines.extend([
            "",
            "---",
            "*[Truncated - see children/ for complete details]*",
        ])

        self.lines = truncated_lines
