"""
interactive_renderer.py

GraphData -> Interactive Graph JSON

This renderer produces a stable frontend contract.

The frontend should never need AtlasData,
Mermaid syntax, or internal Python objects.

Future consumers:
    - graph_viewer.js
    - graph_search.js
    - graph_layout.js
    - AI architecture explorer
    - API endpoints
"""
from __future__ import annotations

from typing import Any

from backend.graph_models import (
    GraphData,
    GraphNode,
    GraphEdge,
    GraphCluster,
)


INTERACTIVE_GRAPH_VERSION = 1


class InteractiveRenderer:

    @classmethod
    def render(
        cls,
        graph: GraphData,
    ) -> dict[str, Any]:

        return {
            "version": INTERACTIVE_GRAPH_VERSION,
            "graph_type": graph.graph_type.value,
            "metadata": graph.metadata,

            "stats": {
                "nodes": graph.node_count,
                "edges": graph.edge_count,
                "clusters": graph.cluster_count,
            },

            "nodes": [
                cls._node_to_dict(node)
                for node in graph.nodes.values()
            ],

            "edges": [
                cls._edge_to_dict(edge)
                for edge in graph.edges.values()
            ],

            "clusters": [
                cls._cluster_to_dict(cluster)
                for cluster in graph.clusters.values()
            ],
        }

    # =====================================================================
    # Node
    # =====================================================================

    @staticmethod
    def _node_to_dict(
        node: GraphNode,
    ) -> dict[str, Any]:

        return {
            "id": node.id,
            "label": node.label,

            "type": node.node_type.value,
            "risk_level": node.risk_level.value,

            "entry_point": node.entry_point,

            "cluster_id": node.cluster_id,

            "position": {
                "x": node.x,
                "y": node.y,
            },

            "visual": {
                "pinned": node.pinned,
                "hidden": node.hidden,
                "color": node.color,
            },

            "metadata": node.metadata,
        }

    # =====================================================================
    # Edge
    # =====================================================================

    @staticmethod
    def _edge_to_dict(
        edge: GraphEdge,
    ) -> dict[str, Any]:

        return {
            "id": edge.id,

            "source": edge.source,
            "target": edge.target,

            "type": edge.edge_type.value,
            "label": edge.label,

            "weight": edge.weight,

            "hidden": edge.hidden,

            "metadata": edge.metadata,
        }

    # =====================================================================
    # Cluster
    # =====================================================================

    @staticmethod
    def _cluster_to_dict(
        cluster: GraphCluster,
    ) -> dict[str, Any]:

        return {
            "id": cluster.id,
            "label": cluster.label,

            "collapsed": cluster.collapsed,

            "parent_cluster_id":
                cluster.parent_cluster_id,

            "node_ids":
                sorted(cluster.node_ids),

            "metadata":
                cluster.metadata,
        }