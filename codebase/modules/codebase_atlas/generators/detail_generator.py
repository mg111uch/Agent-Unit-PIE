"""
Detail generator for Codebase Atlas.

Generates children/*.md files (Layer 2) - detailed breakdown of file groups.
Includes inline impact matrices and docstrings for every function.
"""

from pathlib import Path
from typing import List, Dict
from collections import defaultdict

from ..models import AtlasData, FileInfo
from ..config import AtlasConfig
from ..utils import (
    write_file, get_timestamp, ensure_directory,
    format_file,
)


class DetailGenerator:
    """Generates detailed children/*.md files."""

    def __init__(self, config: AtlasConfig, atlas_data: AtlasData):
        self.config = config
        self.atlas_data = atlas_data

    def generate(self, output_dir: str) -> List[str]:
        """Generate all children/*.md files."""
        print("📂 Generating children files...")

        children_dir = Path(output_dir) / self.config.children_dir
        ensure_directory(str(children_dir))

        file_groups = self._group_files()

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
        lines = []

        lines.extend([
            f"# 📂 {group_name}",
            f"Generated: {get_timestamp()}",
            f"Files: {len(files)}",
            "",
            "---",
            "",
        ])

        for file_info in sorted(files, key=lambda f: f.path.name):
            lines.extend(self._format_file_detail(file_info))
            lines.append("")

        file_path = children_dir / f"{group_name}.md"
        content = '\n'.join(lines)
        write_file(str(file_path), content)

        loc = len(lines)
        if loc > self.config.child_max_loc:
            print(f"  ⚠️  {group_name}.md exceeds target LOC ({loc} > {self.config.child_max_loc})")

        return str(file_path)

    def _format_file_detail(self, file_info: FileInfo) -> List[str]:
        lines = []

        lines.extend(format_file(
            file_info,
            self.config,
            impact_nodes=self.atlas_data.impact_nodes,
        ))

        lines.append("---")

        return lines
