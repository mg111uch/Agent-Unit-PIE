"""
graph_builder.py

Converts AtlasData into canonical GraphData.

This is the only module that should know Atlas internals.
Renderers, algorithms, search systems, and interactive viewers
should consume GraphData instead of AtlasData directly.
"""

from __future__ import annotations

from typing import Optional

from ...models import AtlasData, RiskLevel as AtlasRiskLevel

from .graph_models import (
    EdgeType,
    GraphCluster,
    GraphData,
    GraphEdge,
    GraphNode,
    GraphType,
    NodeType,
    RiskLevel,
)


class GraphBuilder:
    """
    Builds GraphData from AtlasData.

    Produces:

        Dependency Graph
            File Nodes
            Dependency Edges

        Call Graph
            Function Nodes
            Function Call Edges
            File Clusters
    """

    def __init__(self, atlas_data: AtlasData):
        self.atlas_data = atlas_data

    # =========================================================================
    # Public API
    # =========================================================================

    def build_dependency_graph(self) -> GraphData:
        """
        Build file-level dependency graph.
        """
        graph = GraphData(graph_type=GraphType.DEPENDENCY)

        self._add_file_nodes(graph)
        self._add_dependency_edges(graph)

        graph.metadata["graph_type"] = "dependency"

        return graph

    def build_call_graph(self) -> GraphData:
        """
        Build function-level call graph.
        """
        graph = GraphData(graph_type=GraphType.CALL)

        self._add_function_clusters(graph)
        self._add_function_nodes(graph)
        self._add_call_edges(graph)

        graph.metadata["graph_type"] = "call"

        return graph

    # =========================================================================
    # Dependency Graph
    # =========================================================================

    def _add_file_nodes(self, graph: GraphData) -> None:
        used_refs = set()

        for edge in self.atlas_data.dependency_graph.edges:
            if self._is_valid_file(edge.source) and self._is_valid_file(edge.target):
                used_refs.add(edge.source)
                used_refs.add(edge.target)

        for file_info in self.atlas_data.files:

            if self._is_init_py(file_info):
                continue

            if (
                file_info.ref_id not in used_refs
                and not file_info.entry_point
            ):
                continue

            graph.add_node(
                GraphNode(
                    id=file_info.ref_id,
                    label=file_info.path.name,
                    node_type=NodeType.FILE,
                    entry_point=file_info.entry_point,
                    risk_level=self._file_risk_level(file_info),
                    metadata={
                        "path": str(file_info.path),
                    },
                )
            )

    def _add_dependency_edges(self, graph: GraphData) -> None:

        for edge in self.atlas_data.dependency_graph.edges:

            if not self._is_valid_file(edge.source):
                continue

            if not self._is_valid_file(edge.target):
                continue

            graph.add_edge(
                GraphEdge(
                    id=f"dep:{edge.source}->{edge.target}",
                    source=edge.source,
                    target=edge.target,
                    edge_type=EdgeType.DEPENDS_ON,
                )
            )

    # =========================================================================
    # Call Graph
    # =========================================================================

    def _add_function_clusters(self, graph: GraphData) -> None:

        for file_info in self.atlas_data.files:

            if self._is_init_py(file_info):
                continue

            cluster = GraphCluster(
                id=file_info.ref_id,
                label=file_info.path.name,
            )

            graph.add_cluster(cluster)

    def _add_function_nodes(self, graph: GraphData) -> None:

        funcs_in_edges = self._collect_call_graph_functions()

        for file_ref, func_name in funcs_in_edges:

            file_info = self.atlas_data.file_map.get(file_ref)

            if not file_info:
                continue

            func = self._find_function(file_info, func_name)

            node_id = self._function_node_id(
                file_ref,
                func_name,
            )

            graph.add_node(
                GraphNode(
                    id=node_id,
                    label=f"{func_name}()",
                    node_type=NodeType.FUNCTION,
                    cluster_id=file_ref,
                    risk_level=self._function_risk_level(func),
                    entry_point=getattr(func, "is_entry", False)
                    if func
                    else False,
                    metadata={
                        "file_ref": file_ref,
                        "function_name": func_name,
                    },
                )
            )

            cluster = graph.clusters.get(file_ref)

            if cluster:
                cluster.node_ids.add(node_id)

    def _add_call_edges(self, graph: GraphData) -> None:

        for node_key, impact_node in self.atlas_data.impact_nodes.items():

            file_ref, func_name = node_key.split(":", 1)

            if not impact_node.direct_calls:
                continue

            if not self._is_valid_file(file_ref):
                continue

            source_id = self._function_node_id(
                file_ref,
                func_name,
            )

            for target_ref, target_func in impact_node.direct_calls:

                if not self._is_valid_file(target_ref):
                    continue

                target_id = self._function_node_id(
                    target_ref,
                    target_func,
                )

                graph.add_edge(
                    GraphEdge(
                        id=f"call:{source_id}->{target_id}",
                        source=source_id,
                        target=target_id,
                        edge_type=EdgeType.CALLS,
                    )
                )

    # =========================================================================
    # Discovery Helpers
    # =========================================================================

    def _collect_call_graph_functions(self):

        funcs = set()

        for node_key, impact_node in self.atlas_data.impact_nodes.items():

            file_ref, func_name = node_key.split(":", 1)

            if not impact_node.direct_calls:
                continue

            if not self._is_valid_file(file_ref):
                continue

            funcs.add((file_ref, func_name))

            for target_ref, target_func in impact_node.direct_calls:

                if not self._is_valid_file(target_ref):
                    continue

                funcs.add(
                    (
                        target_ref,
                        target_func,
                    )
                )

        return funcs

    # =========================================================================
    # Risk Mapping
    # =========================================================================

    def _file_risk_level(self, file_info) -> RiskLevel:

        if file_info.get_high_risk_functions():
            return RiskLevel.HIGH

        return RiskLevel.NONE

    def _function_risk_level(
        self,
        func,
    ) -> RiskLevel:

        if func is None:
            return RiskLevel.NONE

        atlas_risk = getattr(func, "risk_level", None)

        if atlas_risk == AtlasRiskLevel.HIGH:
            return RiskLevel.HIGH

        if atlas_risk == AtlasRiskLevel.MEDIUM:
            return RiskLevel.MEDIUM

        if atlas_risk == AtlasRiskLevel.LOW:
            return RiskLevel.LOW

        return RiskLevel.NONE

    # =========================================================================
    # Atlas Helpers
    # =========================================================================

    def _is_valid_file(
        self,
        file_ref: str,
    ) -> bool:

        file_info = self.atlas_data.file_map.get(file_ref)

        if not file_info:
            return False

        return not self._is_init_py(file_info)

    @staticmethod
    def _is_init_py(file_info) -> bool:

        if file_info is None:
            return True

        return file_info.path.name == "__init__.py"

    @staticmethod
    def _function_node_id(
        file_ref: str,
        func_name: str,
    ) -> str:

        safe_name = (
            func_name
            .replace(".", "_")
            .replace(":", "_")
            .replace("-", "_")
        )

        return f"{file_ref}_{safe_name}"

    @staticmethod
    def _find_function(
        file_info,
        func_name: str,
    ):

        for func in file_info.functions:
            if func.name == func_name:
                return func

        for cls in file_info.classes:
            for method in cls.methods:
                if method.name == func_name:
                    return method

        return None