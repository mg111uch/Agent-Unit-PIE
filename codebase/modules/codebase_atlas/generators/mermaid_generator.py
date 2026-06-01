"""Mermaid graph generator for Codebase Atlas.

Converts dependency and call graph data into Mermaid.js flowchart syntax
for browser-based visualization.
"""

import re
from typing import List, Optional
from ..config import AtlasConfig
from ..models import AtlasData, FileInfo, FunctionInfo, RiskLevel


class MermaidGenerator:
    """Generates Mermaid.js flowcharts from atlas data."""

    def __init__(self, config: AtlasConfig, atlas_data: AtlasData):
        self.config = config
        self.atlas_data = atlas_data

    @staticmethod
    def _sanitize_id(text: str) -> str:
        return re.sub(r'[^a-zA-Z0-9_]', '_', text)

    @staticmethod
    def _sanitize_label(text: str) -> str:
        return text.replace('"', '&quot;').replace('[', '(').replace(']', ')')

    @staticmethod
    def _is_init_py(file_info) -> bool:
        return file_info.path.name == '__init__.py'

    def generate_dependency_graph(self) -> str:
        """Generate Mermaid flowchart of file-level dependencies."""
        lines = ["flowchart TD"]

        dep_graph = self.atlas_data.dependency_graph
        used_refs = set()
        for edge in dep_graph.edges:
            if not self._is_init_py(self.atlas_data.file_map.get(edge.source)) and \
               not self._is_init_py(self.atlas_data.file_map.get(edge.target)):
                used_refs.add(edge.source)
                used_refs.add(edge.target)

        for file_info in self.atlas_data.files:
            if self._is_init_py(file_info):
                continue
            if file_info.ref_id not in used_refs and not file_info.entry_point:
                continue
            ref = file_info.ref_id
            label = self._sanitize_label(file_info.path.name)
            node = f'{ref}["{label}"]'
            style = self._file_risk_class(file_info)
            if style:
                lines.append(f"    {node}:::{style}")
            else:
                lines.append(f"    {node}")

        for edge in dep_graph.edges:
            if self._is_init_py(self.atlas_data.file_map.get(edge.source)) or \
               self._is_init_py(self.atlas_data.file_map.get(edge.target)):
                continue
            lines.append(f"    {edge.source} --> {edge.target}")

        lines.extend(self._get_class_defs())
        return "\n".join(lines)

    def generate_call_graph(self) -> str:
        """Generate Mermaid flowchart of function call relationships."""
        funcs_in_edges: set = set()
        for node_key, impact_node in self.atlas_data.impact_nodes.items():
            file_ref, func_name = node_key.split(':', 1)
            if not impact_node.direct_calls:
                continue
            file_info = self.atlas_data.file_map.get(file_ref)
            if not file_info or self._is_init_py(file_info):
                continue
            funcs_in_edges.add((file_ref, func_name))
            for target_ref, target_func in impact_node.direct_calls:
                target_info = self.atlas_data.file_map.get(target_ref)
                if target_info and not self._is_init_py(target_info):
                    funcs_in_edges.add((target_ref, target_func))

        if not funcs_in_edges:
            lines = ["graph TD"]
            lines.append('    empty["No function call relationships"]')
            lines.extend(self._get_class_defs())
            return "\n".join(lines)

        grouped: dict = {}
        for file_ref, func_name in funcs_in_edges:
            grouped.setdefault(file_ref, []).append(func_name)

        lines = ["graph TD"]

        for file_info in self.atlas_data.files:
            if self._is_init_py(file_info):
                continue
            ref = file_info.ref_id
            func_names = grouped.get(ref)
            if not func_names:
                continue
            filename = self._sanitize_label(file_info.path.name)
            lines.append(f"    subgraph {ref}[{filename}]")
            for func_name in func_names:
                node_id = self._func_node_id(ref, func_name)
                func = self._find_function(file_info, func_name)
                label = self._sanitize_label(f"{func_name}()")
                if func:
                    style = self._func_risk_class(func)
                else:
                    style = None
                if style:
                    lines.append(f'    {node_id}["{label}"]:::{style}')
                else:
                    lines.append(f'    {node_id}["{label}"]')
            lines.append("    end")

        for node_key, impact_node in self.atlas_data.impact_nodes.items():
            file_ref, func_name = node_key.split(':', 1)
            if not impact_node.direct_calls:
                continue
            src_info = self.atlas_data.file_map.get(file_ref)
            if not src_info or self._is_init_py(src_info):
                continue
            source_id = self._func_node_id(file_ref, func_name)
            for target_ref, target_func in impact_node.direct_calls:
                tgt_info = self.atlas_data.file_map.get(target_ref)
                if tgt_info and self._is_init_py(tgt_info):
                    continue
                target_id = self._func_node_id(target_ref, target_func)
                lines.append(f"    {source_id} --> {target_id}")

        lines.extend(self._get_class_defs())
        return "\n".join(lines)

    @staticmethod
    def _find_function(file_info, func_name: str):
        for func in file_info.functions:
            if func.name == func_name:
                return func
        for cls in file_info.classes:
            for method in cls.methods:
                if method.name == func_name:
                    return method
        return None

    def _func_node_id(self, file_ref: str, func_name: str) -> str:
        return f"{file_ref}_{self._sanitize_id(func_name)}"

    def _file_risk_class(self, file_info: FileInfo) -> Optional[str]:
        if file_info.entry_point:
            return "entry"
        if file_info.get_high_risk_functions():
            return "high"
        if file_info.circular_deps:
            return "circular"
        return None

    def _func_risk_class(self, func: FunctionInfo) -> Optional[str]:
        if func.is_entry:
            return "entry"
        if func.risk_level == RiskLevel.HIGH:
            return "high"
        if func.risk_level == RiskLevel.MEDIUM:
            return "medium"
        if func.risk_level == RiskLevel.LOW:
            return "low"
        return None

    @staticmethod
    def _get_class_defs() -> List[str]:
        return [
            "    classDef entry fill:none,stroke:#4CAF50,stroke-width:3px,stroke-dasharray: 5 3;",
            "    classDef high fill:none,stroke:#f44336,stroke-width:3px;",
            "    classDef medium fill:none,stroke:#FF9800,stroke-width:3px;",
            "    classDef low fill:none,stroke:#FFEB3B,stroke-width:3px;",
            "    classDef circular fill:none,stroke:#9C27B0,stroke-width:3px,stroke-dasharray: 5 5;",
        ]
