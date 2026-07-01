"""
mermaid_renderer.py

GraphData -> Mermaid flowchart renderer.

This renderer is intentionally dumb:
it only converts GraphData into Mermaid syntax.

All Atlas-specific extraction logic belongs in GraphBuilder.
"""

from __future__ import annotations

import re
from typing import List

from ..graph_models import (
    EdgeType,
    GraphData,
    GraphNode,
    NodeType,
    RiskLevel,
)


class MermaidRenderer:
    """
    Renders GraphData as Mermaid flowchart syntax.
    """

    def render(self, graph: GraphData) -> str:

        graph_type = graph.metadata.get("graph_type")

        if graph_type == "call":
            return self._render_call_graph(graph)

        return self._render_dependency_graph(graph)

    # =========================================================================
    # Dependency Graph
    # =========================================================================

    def _render_dependency_graph(
        self,
        graph: GraphData,
    ) -> str:

        lines = ["flowchart TD"]

        nodes_with_edges = self._nodes_with_edges(graph)

        for node in graph.nodes.values():

            is_orphan = node.id not in nodes_with_edges

            node_line = self._render_node(node, is_orphan)

            if node_line:
                lines.append(f"    {node_line}")

        for edge in graph.edges.values():

            if edge.hidden:
                continue

            lines.append(
                f"    {edge.source} --> {edge.target}"
            )

        lines.extend(self._class_defs())

        return "\n".join(lines)

    # =========================================================================
    # Call Graph
    # =========================================================================

    def _render_call_graph(
        self,
        graph: GraphData,
    ) -> str:

        lines = ["graph TD"]

        if not graph.nodes:
            lines.append(
                '    empty["No function call relationships"]'
            )
            lines.extend(self._class_defs())
            return "\n".join(lines)

        #
        # Render clusters
        #

        for cluster in graph.clusters.values():

            if cluster.collapsed:
                continue

            lines.append(
                f"    subgraph {cluster.id}[{self._sanitize_label(cluster.label)}]"
            )

            for node_id in sorted(cluster.node_ids):

                node = graph.nodes.get(node_id)

                if not node or node.hidden:
                    continue

                node_line = self._render_node(node)

                if node_line:
                    lines.append(f"    {node_line}")

            lines.append("    end")

        #
        # Render nodes outside clusters
        #

        clustered_nodes = {
            node_id
            for cluster in graph.clusters.values()
            for node_id in cluster.node_ids
        }

        for node in graph.nodes.values():

            if node.id in clustered_nodes:
                continue

            if node.hidden:
                continue

            node_line = self._render_node(node)

            if node_line:
                lines.append(f"    {node_line}")

        #
        # Render edges
        #

        for edge in graph.edges.values():

            if edge.hidden:
                continue

            lines.append(
                f"    {edge.source} --> {edge.target}"
            )

        lines.extend(self._class_defs())

        return "\n".join(lines)

    # =========================================================================
    # Node Rendering
    # =========================================================================

    def _render_node(
        self,
        node: GraphNode,
        is_orphan: bool = False,
    ) -> str:

        label = self._sanitize_label(node.label)

        mermaid_node = (
            f'{node.id}["{label}"]'
        )

        style_class = self._node_style(node, is_orphan)

        if style_class:
            return f"{mermaid_node}:::{style_class}"

        return mermaid_node

    def _node_style(
        self,
        node: GraphNode,
        is_orphan: bool = False,
    ) -> str | None:

        #
        # Entry point takes precedence.
        #

        if node.entry_point:
            return "entry"

        #
        # Orphan (no incoming or outgoing edges)
        #

        if is_orphan:
            return "orphan"

        #
        # Risk styles.
        #

        if node.risk_level == RiskLevel.HIGH:
            return "high"

        if node.risk_level == RiskLevel.MEDIUM:
            return "medium"

        if node.risk_level == RiskLevel.LOW:
            return "low"

        #
        # Circular dependency marker.
        #

        if node.metadata.get("circular_dependency"):
            return "circular"

        return None

    # =========================================================================
    # Helpers
    # =========================================================================

    @staticmethod
    def _nodes_with_edges(graph: GraphData) -> set:

        nodes = set()

        for edge in graph.edges.values():
            nodes.add(edge.source)
            nodes.add(edge.target)

        return nodes

    @staticmethod
    def _sanitize_id(text: str) -> str:
        return re.sub(
            r"[^a-zA-Z0-9_]",
            "_",
            text,
        )

    @staticmethod
    def _sanitize_label(text: str) -> str:

        return (
            text
            .replace('"', "&quot;")
            .replace("[", "(")
            .replace("]", ")")
        )

    # =========================================================================
    # Mermaid Styling
    # =========================================================================

    @staticmethod
    def _class_defs() -> List[str]:

        return [
            (
                "    classDef entry "
                "fill:none,"
                "stroke:#4CAF50,"
                "stroke-width:3px,"
                "stroke-dasharray: 5 3;"
            ),
            (
                "    classDef high "
                "fill:none,"
                "stroke:#f44336,"
                "stroke-width:3px;"
            ),
            (
                "    classDef medium "
                "fill:none,"
                "stroke:#FF9800,"
                "stroke-width:3px;"
            ),
            (
                "    classDef low "
                "fill:none,"
                "stroke:#FFEB3B,"
                "stroke-width:3px;"
            ),
            (
                "    classDef circular "
                "fill:none,"
                "stroke:#9C27B0,"
                "stroke-width:3px,"
                "stroke-dasharray: 5 5;"
            ),
            (
                "    classDef orphan "
                "fill:#1a1a2e,"
                "stroke:#555,"
                "stroke-width:1px,"
                "stroke-dasharray: 3 3;"
            ),
        ]