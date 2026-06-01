"""
graph_models.py

Canonical graph model used by all graph renderers and algorithms.

AtlasData
    ↓
GraphBuilder
    ↓
GraphData
    ├── MermaidRenderer
    ├── InteractiveRenderer
    ├── GraphAlgorithms
    └── Future AI tooling
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set


# ============================================================================
# ENUMS
# ============================================================================


class NodeType(str, Enum):
    FILE = "file"
    FUNCTION = "function"
    CLASS = "class"
    MODULE = "module"
    PACKAGE = "package"
    EXTERNAL = "external"


class EdgeType(str, Enum):
    DEPENDS_ON = "depends_on"
    IMPORTS = "imports"
    CALLS = "calls"
    INHERITS = "inherits"
    REFERENCES = "references"


class RiskLevel(str, Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class GraphType(str, Enum):
    DEPENDENCY = "dependency"
    CALL = "call"

# ============================================================================
# CORE GRAPH OBJECTS
# ============================================================================


@dataclass(slots=True)
class GraphNode:
    """
    Canonical graph node.

    Examples:
        file node
        function node
        class node
        external dependency node
    """

    id: str
    label: str
    node_type: NodeType

    color: str | None = None
    size: float | None = None

    risk_level: RiskLevel = RiskLevel.NONE
    entry_point: bool = False

    cluster_id: Optional[str] = None

    metadata: Dict[str, Any] = field(default_factory=dict)

    x: Optional[float] = None
    y: Optional[float] = None

    pinned: bool = False
    hidden: bool = False


@dataclass(slots=True)
class GraphEdge:
    """
    Canonical graph edge.
    """

    id: str

    source: str
    target: str

    label: str | None = None

    edge_type: EdgeType

    weight: float = 1.0
    strength: float = 1.0

    metadata: Dict[str, Any] = field(default_factory=dict)

    hidden: bool = False


@dataclass(slots=True)
class GraphCluster:
    """
    Logical grouping.

    Examples:
        file containing functions
        package containing modules
        directory grouping files
    """

    id: str
    label: str

    node_ids: Set[str] = field(default_factory=set)

    parent_cluster_id: Optional[str] = None

    metadata: Dict[str, Any] = field(default_factory=dict)

    collapsed: bool = False


# ============================================================================
# GRAPH ROOT OBJECT
# ============================================================================


@dataclass(slots=True)
class GraphData:
    """
    Canonical graph representation.

    All renderers and algorithms consume this object.
    """

    graph_type: GraphType

    nodes: Dict[str, GraphNode] = field(default_factory=dict)
    edges: Dict[str, GraphEdge] = field(default_factory=dict)
    clusters: Dict[str, GraphCluster] = field(default_factory=dict)

    metadata: Dict[str, Any] = field(default_factory=dict)

    # ---------------------------------------------------------------------
    # Node operations
    # ---------------------------------------------------------------------

    def add_node(self, node: GraphNode) -> None:
        self.nodes[node.id] = node

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        return self.nodes.get(node_id)

    def has_node(self, node_id: str) -> bool:
        return node_id in self.nodes

    # ---------------------------------------------------------------------
    # Edge operations
    # ---------------------------------------------------------------------

    def add_edge(self, edge: GraphEdge) -> None:
        self.edges[edge.id] = edge

    def get_edge(self, edge_id: str) -> Optional[GraphEdge]:
        return self.edges.get(edge_id)

    # ---------------------------------------------------------------------
    # Cluster operations
    # ---------------------------------------------------------------------

    def add_cluster(self, cluster: GraphCluster) -> None:
        self.clusters[cluster.id] = cluster

    def get_cluster(self, cluster_id: str) -> Optional[GraphCluster]:
        return self.clusters.get(cluster_id)

    # ---------------------------------------------------------------------
    # Query helpers
    # ---------------------------------------------------------------------

    def outgoing_edges(self, node_id: str) -> List[GraphEdge]:
        return [
            edge
            for edge in self.edges.values()
            if edge.source == node_id
        ]

    def incoming_edges(self, node_id: str) -> List[GraphEdge]:
        return [
            edge
            for edge in self.edges.values()
            if edge.target == node_id
        ]

    def neighbors(self, node_id: str) -> Set[str]:
        result = set()

        for edge in self.edges.values():
            if edge.source == node_id:
                result.add(edge.target)
            elif edge.target == node_id:
                result.add(edge.source)

        return result

    # ---------------------------------------------------------------------
    # Statistics
    # ---------------------------------------------------------------------

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        return len(self.edges)

    @property
    def cluster_count(self) -> int:
        return len(self.clusters)