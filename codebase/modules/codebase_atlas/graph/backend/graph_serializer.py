"""
graph_serializer.py

Serialization layer for GraphData.

Supports:

    GraphData -> dict
    GraphData -> JSON

    dict -> GraphData
    JSON -> GraphData

Used by:

    Interactive graph viewer
    Layout persistence
    Graph caching
    Future API endpoints
    AI tooling
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict

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

class GraphSerializer:
    # Public Serialization API
    @classmethod
    def to_dict(
        cls,
        graph: GraphData,
    ) -> Dict[str, Any]:
        result = {}
        if "project_id" in graph.metadata:
            result["project_id"] = graph.metadata["project_id"]
        result["graph_type"] = graph.graph_type.value
        result["metadata"] = {
            k: v for k, v in graph.metadata.items()
            if k != "project_id"
        }
        result["nodes"] = [
            cls._node_to_dict(node)
            for node in graph.nodes.values()
        ]
        result["edges"] = [
            cls._edge_to_dict(edge)
            for edge in graph.edges.values()
        ]
        result["clusters"] = [
            cls._cluster_to_dict(cluster)
            for cluster in graph.clusters.values()
        ]
        return result
    @classmethod
    def to_nested_dict(
        cls,
        graph: GraphData,
    ) -> Dict[str, Any]:
        file_nodes = []
        children_by_parent = {}
        for node in graph.nodes.values():
            if node.scope == "file":
                file_nodes.append(
                    cls._node_to_dict(node)
                )
            elif node.parent_id:
                parent_id = node.parent_id
                if parent_id not in children_by_parent:
                    children_by_parent[parent_id] = {
                        "nodes": [],
                        "edges": [],
                    }
                children_by_parent[parent_id]["nodes"].append(
                    cls._node_to_dict(node)
                )
        top_level_edges = []
        for edge in graph.edges.values():
            source = graph.nodes.get(edge.source)
            target = graph.nodes.get(edge.target)
            source_is_call = (
                source and
                source.parent_id
            )
            target_is_call = (
                target and
                target.parent_id
            )
            if (
                source_is_call and
                target_is_call
            ):
                if (
                    source.parent_id ==
                    target.parent_id
                ):
                    children_by_parent[
                        source.parent_id
                    ]["edges"].append(
                        cls._edge_to_dict(edge)
                    )
                else:
                    top_level_edges.append(
                        cls._edge_to_dict(edge)
                    )
            elif (
                source_is_call and
                not target_is_call
            ) or (
                not source_is_call and
                target_is_call
            ):
                top_level_edges.append(
                    cls._edge_to_dict(edge)
                )
            elif (
                not source_is_call and
                not target_is_call
            ):
                top_level_edges.append(
                    cls._edge_to_dict(edge)
                )
        return {
            "graph_type": graph.graph_type.value,
            "metadata": graph.metadata,
            "nodes": file_nodes,
            "edges": top_level_edges,
            "clusters": [
                cls._cluster_to_dict(cluster)
                for cluster in graph.clusters.values()
            ],
            "children_by_parent": children_by_parent,
        }
    @classmethod
    def to_json(
        cls,
        graph: GraphData,
        *,
        indent: int = 2,
    ) -> str:
        return json.dumps(
            cls.to_dict(graph),
            indent=indent,
            sort_keys=False,
        )
    @classmethod
    def save_json(
        cls,
        graph: GraphData,
        output_path: str | Path,
        *,
        indent: int = 2,
    ) -> None:
        output_path = Path(output_path)
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        output_path.write_text(
            cls.to_json(
                graph,
                indent=indent,
            ),
            encoding="utf-8",
        )
    # Public Deserialization API
    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
    ) -> GraphData:
        metadata = data.get("metadata", {}).copy()
        if "project_id" in data:
            metadata.setdefault("project_id", data["project_id"])
        graph = GraphData(
            graph_type=GraphType(
                data["graph_type"]
            ),
            metadata=metadata,
        )
        #
        # Clusters first
        #
        for cluster_data in data.get(
            "clusters",
            [],
        ):
            cluster = cls._cluster_from_dict(
                cluster_data
            )
            graph.add_cluster(cluster)
        #
        # Nodes
        #
        for node_data in data.get(
            "nodes",
            [],
        ):
            node = cls._node_from_dict(
                node_data
            )
            graph.add_node(node)
        #
        # Edges
        #
        for edge_data in data.get(
            "edges",
            [],
        ):
            edge = cls._edge_from_dict(
                edge_data
            )
            graph.add_edge(edge)
        return graph
    @classmethod
    def from_json(
        cls,
        json_text: str,
    ) -> GraphData:
        return cls.from_dict(
            json.loads(json_text)
        )
    @classmethod
    def load_json(
        cls,
        input_path: str | Path,
    ) -> GraphData:
        input_path = Path(input_path)
        return cls.from_json(
            input_path.read_text(
                encoding="utf-8"
            )
        )
    # Node Serialization
    @staticmethod
    def _node_to_dict(
        node: GraphNode,
    ) -> Dict[str, Any]:
        data = {
            "id": node.id,
            "label": node.label,
            "type": node.node_type.value,
            "risk_level": node.risk_level.value,
            "entry_point": node.entry_point,
            "cluster_id": node.cluster_id,
            "parent_id": node.parent_id,
            "scope": node.scope,
            "metadata": node.metadata,
        }
        if node.x is not None and node.y is not None:
            data["position"] = {
                "x": node.x,
                "y": node.y,
            }
        if node.pinned or node.hidden or node.color:
            data["visual"] = {
                "pinned": node.pinned,
                "hidden": node.hidden,
                "color": node.color,
            }
        return data
    @staticmethod
    def _node_from_dict(
        data: Dict[str, Any],
    ) -> GraphNode:
        return GraphNode(
            id=data["id"],
            label=data["label"],
            node_type=NodeType(
                data["type"]
            ),
            risk_level=RiskLevel(
                data["risk_level"]
            ),
            entry_point=data.get(
                "entry_point",
                False,
            ),
            cluster_id=data.get(
                "cluster_id"
            ),
            parent_id=data.get(
                "parent_id"
            ),
            scope=data.get(
                "scope",
                "file"
            ),
            metadata=data.get(
                "metadata",
                {},
            ),
            x=data.get("x"),
            y=data.get("y"),
            pinned=data.get(
                "pinned",
                False,
            ),
            hidden=data.get(
                "hidden",
                False,
            ),
            color=data.get(
                "color"
            ),
        )
    # Edge Serialization
    @staticmethod
    def _edge_to_dict(
        edge: GraphEdge,
    ) -> Dict[str, Any]:
        data = asdict(edge)
        data["type"] = (
            edge.edge_type.value
        )
        return data
    @staticmethod
    def _edge_from_dict(
        data: Dict[str, Any],
    ) -> GraphEdge:
        return GraphEdge(
            id=data["id"],
            source=data["source"],
            target=data["target"],
            edge_type=EdgeType(
                data["type"]
            ),
            label=data.get(
                "label"
            ),
            weight=data.get(
                "weight",
                1.0,
            ),
            metadata=data.get(
                "metadata",
                {},
            ),
            hidden=data.get(
                "hidden",
                False,
            ),
        )
    # Cluster Serialization
    @staticmethod
    def _cluster_to_dict(
        cluster: GraphCluster,
    ) -> Dict[str, Any]:
        return {
            "id": cluster.id,
            "label": cluster.label,
            "node_ids": sorted(
                cluster.node_ids
            ),
            "parent_cluster_id": (
                cluster.parent_cluster_id
            ),
            "metadata": cluster.metadata,
            "collapsed": cluster.collapsed,
        }
    @staticmethod
    def _cluster_from_dict(
        data: Dict[str, Any],
    ) -> GraphCluster:
        return GraphCluster(
            id=data["id"],
            label=data["label"],
            node_ids=set(
                data.get(
                    "node_ids",
                    [],
                )
            ),
            parent_cluster_id=data.get(
                "parent_cluster_id"
            ),
            metadata=data.get(
                "metadata",
                {},
            ),
            collapsed=data.get(
                "collapsed",
                False,
            ),
        )