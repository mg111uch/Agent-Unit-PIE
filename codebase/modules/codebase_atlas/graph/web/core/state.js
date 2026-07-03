// web/core/state.js

/**
 * ============================================================================
 * GraphState
 * ============================================================================
 *
 * Central application state.
 *
 * Responsibilities:
 *   - Hold graph data
 *   - Hold selection state
 *   - Hold viewport state
 *   - Hold visibility state
 *   - Notify listeners
 *
 * Non-responsibilities:
 *   - Rendering
 *   - DOM manipulation
 *   - SVG generation
 *   - Event handling
 * ============================================================================
 */

import { EventEmitter } from "./events.js";

export class GraphState extends EventEmitter {

    constructor(graphData) {

        super();

        this.graph = graphData;

        // ---------------------------------------------------------------------
        // Lookup Maps
        // ---------------------------------------------------------------------

        this.nodeMap = new Map();
        this.edgeMap = new Map();
        this.clusterMap = new Map();

        this._buildIndexes();

        // ---------------------------------------------------------------------
        // Selection State
        // ---------------------------------------------------------------------

        this.selectedNodeId = null;
        this.selectedEdgeId = null;
        this.selectedClusterId = null;

        // Multi-select support
        this.selectedNodes = new Set();

        // Live preview of nodes under the box-select rectangle
        this.previewSelectedNodes = new Set();

        // ---------------------------------------------------------------------
        // Viewport State
        // ---------------------------------------------------------------------

        this.zoom = 1.0;

        this.panX = 0;
        this.panY = 0;

        // ---------------------------------------------------------------------
        // Visibility State
        // ---------------------------------------------------------------------

        this.hiddenNodes = new Set();
        this.hiddenEdges = new Set();

        this.collapsedClusters = new Set();
        this.expandedNodes = new Set();

        this.childCache = new Map();

        this.expandGroups = new Map();

        this.childPositions = new Map();

        this.pinnedNodes = new Set();

        // ---------------------------------------------------------------------
        // Derived Graph Relationships
        // ---------------------------------------------------------------------

        this.incomingEdges = new Map();
        this.outgoingEdges = new Map();

        this.clusterNodes = new Map();

        this._buildRelationships();

        this.callNodeParent = new Map();

        this._buildCallNodeParent();

        // ---------------------------------------------------------------------
        // Event Subscribers
        // ---------------------------------------------------------------------

        this.listeners = new Map();
    }

    // =========================================================================
    // Graph Construction
    // =========================================================================

    _buildIndexes() {

        for (const node of this.graph.nodes) {
            this.nodeMap.set(node.id, node);
        }

        for (const edge of this.graph.edges) {
            this.edgeMap.set(edge.id, edge);
        }

        for (const cluster of this.graph.clusters) {
            this.clusterMap.set(cluster.id, cluster);
        }
    }

    _buildRelationships() {

        for (const node of this.graph.nodes) {

            this.incomingEdges.set(node.id, []);
            this.outgoingEdges.set(node.id, []);
        }

        for (const edge of this.graph.edges) {

            if (this.outgoingEdges.has(edge.source)) {
                this.outgoingEdges.get(edge.source).push(edge);
            }

            if (this.incomingEdges.has(edge.target)) {
                this.incomingEdges.get(edge.target).push(edge);
            }
        }

        this._buildClusterNodes();
    }

    _buildCallNodeParent() {

        this.callNodeParent.clear();

        for (const edge of this.graph.edges) {

            const source =
                this.graph.nodes[edge.source];

            const target =
                this.graph.nodes[edge.target];

            const sourceParent =
                source?.parent_id;

            const targetParent =
                target?.parent_id;

            if (sourceParent && targetParent) {

                if (sourceParent !== targetParent) {

                    if (
                        !this.callNodeParent.has(
                            source.id
                        )
                    ) {
                        this.callNodeParent.set(
                            source.id,
                            sourceParent
                        );
                    }

                    if (
                        !this.callNodeParent.has(
                            target.id
                        )
                    ) {
                        this.callNodeParent.set(
                            target.id,
                            targetParent
                        );
                    }
                }

                continue;
            }

            if (sourceParent) {

                if (
                    !this.callNodeParent.has(
                        source.id
                    )
                ) {
                    this.callNodeParent.set(
                        source.id,
                        sourceParent
                    );
                }
            }

            if (targetParent) {

                if (
                    !this.callNodeParent.has(
                        target.id
                    )
                ) {
                    this.callNodeParent.set(
                        target.id,
                        targetParent
                    );
                }
            }
        }
    }

    // =========================================================================
    // Event System
    // =========================================================================

    subscribe(eventName, callback) {

        if (!this.listeners.has(eventName)) {
            this.listeners.set(eventName, new Set());
        }

        this.listeners.get(eventName).add(callback);

        return () => {
            this.listeners.get(eventName)?.delete(callback);
        };
    }

    emit(eventName, payload = {}) {

        const listeners = this.listeners.get(eventName);

        if (listeners) {

            for (const callback of listeners) {
                callback(payload);
            }
        }

        super.emit(eventName, payload);
    }

    // =========================================================================
    // Selection
    // =========================================================================

    selectNode(nodeId) {

        if (!this.nodeMap.has(nodeId)) {
            return;
        }

        this.selectedNodeId = nodeId;

        this.emit("selectionChanged", {
            type: "node",
            id: nodeId,
        });
    }

    clearNodeSelection() {

        this.selectedNodeId = null;

        this.emit("selectionChanged", {
            type: "node",
            id: null,
        });
    }

    selectEdge(edgeId) {

        if (!this.edgeMap.has(edgeId)) {
            return;
        }

        this.selectedEdgeId = edgeId;

        this.emit("selectionChanged", {
            type: "edge",
            id: edgeId,
        });
    }

    selectCluster(clusterId) {

        if (!this.clusterMap.has(clusterId)) {
            return;
        }

        this.selectedClusterId = clusterId;

        this.emit("selectionChanged", {
            type: "cluster",
            id: clusterId,
        });
    }

    // =========================================================================
    // Multi Selection
    // =========================================================================

    addSelectedNode(nodeId) {

        this.selectedNodes.add(nodeId);

        this.emit("multiSelectionChanged", {
            selectedNodes: [...this.selectedNodes],
        });
    }

    removeSelectedNode(nodeId) {

        this.selectedNodes.delete(nodeId);

        this.emit("multiSelectionChanged", {
            selectedNodes: [...this.selectedNodes],
        });
    }

    clearSelectedNodes() {

        this.selectedNodes.clear();

        this.emit("multiSelectionChanged", {
            selectedNodes: [...this.selectedNodes],
        });
    }

    /* =======================================================================
       Graph Swap
       ======================================================================= */

    setGraph(graphData) {

        if (!graphData) {
            return;
        }

        this.graph = graphData;

        this.selectedNodeId = null;
        this.selectedNodes = new Set();
        this.previewSelectedNodes = new Set();
        this.hiddenNodes = new Set();
        this.hiddenEdges = new Set();
        this.collapsedClusters = new Set();
        this.expandedNodes = new Set();
        this.childCache = new Map();
        this.expandGroups = new Map();
        this.childPositions = new Map();
        this.pinnedNodes = new Set();

        this.zoom = 1.0;
        this.panX = 0;
        this.panY = 0;

        this.nodeMap = new Map();
        this.edgeMap = new Map();
        this.clusterMap = new Map();
        this._buildIndexes();

        this.incomingEdges = new Map();
        this.outgoingEdges = new Map();
        this.clusterNodes = new Map();
        this._buildRelationships();

        this.callNodeParent = new Map();
        this._buildCallNodeParent();

        this.emit("graphChanged", {});
    }

    /* =======================================================================
       Box-Select Preview
       ======================================================================= */

    setPreviewSelectedNodes(nodeIds) {

        this.previewSelectedNodes =
            new Set(nodeIds || []);

        this.emit("previewChanged", {
            ids: Array.from(
                this.previewSelectedNodes
            ),
        });
    }

    clearPreviewSelectedNodes() {

        if (
            this.previewSelectedNodes.size === 0
        ) {
            return;
        }

        this.previewSelectedNodes.clear();

        this.emit("previewChanged", {
            ids: [],
        });
    }

    // =========================================================================
    // Viewport
    // =========================================================================

    setZoom(zoom) {

        this.zoom = zoom;

        this.emit("viewportChanged", {
            zoom: this.zoom,
            panX: this.panX,
            panY: this.panY,
        });
    }

    setPan(x, y) {

        this.panX = x;
        this.panY = y;

        this.emit("viewportChanged", {
            zoom: this.zoom,
            panX: this.panX,
            panY: this.panY,
        });
    }

    // =========================================================================
    // Node Visibility
    // =========================================================================

    hideNode(nodeId) {

        this.hiddenNodes.add(nodeId);

        this.emit("visibilityChanged");
    }

    showNode(nodeId) {

        this.hiddenNodes.delete(nodeId);

        this.emit("visibilityChanged");
    }

    isNodeHidden(nodeId) {

        return this.hiddenNodes.has(nodeId);
    }

    // =========================================================================
    // Cluster Collapse
    // =========================================================================

    collapseCluster(clusterId) {

        this.collapsedClusters.add(clusterId);

        this.emit("clusterChanged", {
            clusterId,
            collapsed: true,
        });
    }

    expandCluster(clusterId) {

        this.collapsedClusters.delete(clusterId);

        this.emit("clusterChanged", {
            clusterId,
            collapsed: false,
        });
    }

    isClusterCollapsed(clusterId) {

        return this.collapsedClusters.has(clusterId);
    }

    // =========================================================================
    // Node Expand / Collapse
    // =========================================================================

    expandNode(nodeId) {

        if (!this.nodeMap.has(nodeId)) {
            return;
        }

        this.expandedNodes.add(nodeId);

        this.emit("nodeExpanded", {
            nodeId,
        });
    }

    collapseNode(nodeId) {

        this.expandedNodes.delete(nodeId);

        this.removeChildren(nodeId);

        this.untrackExpandGroup(nodeId);

        this.emit("nodeCollapsed", {
            nodeId,
        });
    }

    isExpanded(nodeId) {

        return this.expandedNodes.has(nodeId);
    }

    cacheChildren(nodeId, children) {

        this.childCache.set(
            nodeId,
            children
        );
    }

    getCachedChildren(nodeId) {

        return this.childCache.get(nodeId) || null;
    }

    addChildren(nodeId, children) {

        this.cacheChildren(nodeId, children);

        for (const node of children.nodes) {

            this.graph.nodes.push(node);
            this.nodeMap.set(node.id, node);

            this.incomingEdges.set(node.id, []);
            this.outgoingEdges.set(node.id, []);

            if (node.parent_id) {
                this.callNodeParent.set(
                    node.id,
                    node.parent_id
                );
            }
        }

        for (const edge of children.edges) {

            this.graph.edges.push(edge);
            this.edgeMap.set(edge.id, edge);

            if (this.outgoingEdges.has(edge.source)) {
                this.outgoingEdges.get(edge.source).push(edge);
            }

            if (this.incomingEdges.has(edge.target)) {
                this.incomingEdges.get(edge.target).push(edge);
            }
        }

        this._buildClusterNodes();
    }

    removeChildren(nodeId) {

        const cached =
            this.childCache.get(nodeId);

        if (!cached) {
            return;
        }

        const parent =
            this.getNode(nodeId);

        if (parent?.position) {

            const offsets = {};

            for (const child of cached.nodes) {

                if (
                    child.position?.x != null
                ) {

                    offsets[child.id] = {
                        dx:
                            child.position.x -
                            parent.position.x,
                        dy:
                            child.position.y -
                            parent.position.y,
                    };
                }
            }

            this.childPositions.set(
                nodeId,
                offsets
            );
        }

        const nodeIds = new Set(
            cached.nodes.map(n => n.id)
        );

        const edgeIds = new Set(
            cached.edges.map(e => e.id)
        );

        this.graph.nodes =
            this.graph.nodes.filter(
                n => !nodeIds.has(n.id)
            );

        this.graph.edges =
            this.graph.edges.filter(
                e => !edgeIds.has(e.id)
            );

        for (const child of cached.nodes) {

            this.nodeMap.delete(child.id);
            this.incomingEdges.delete(child.id);
            this.outgoingEdges.delete(child.id);
            this.callNodeParent.delete(child.id);
        }

        for (const edge of cached.edges) {

            this.edgeMap.delete(edge.id);
        }

        this.childCache.delete(nodeId);

        this._buildClusterNodes();
    }

    _buildClusterNodes() {

        this.clusterNodes.clear();

        for (const cluster of this.graph.clusters) {
            this.clusterNodes.set(cluster.id, []);
        }

        for (const node of this.graph.nodes) {

            const clusterId = node.cluster_id;

            if (!clusterId) {
                continue;
            }

            if (!this.clusterNodes.has(clusterId)) {
                this.clusterNodes.set(clusterId, []);
            }

            this.clusterNodes.get(clusterId).push(node);
        }
    }

    // =========================================================================
    // Expand Groups
    // =========================================================================

    trackExpandGroup(parentNodeId, childNodeIds) {

        this.expandGroups.set(
            parentNodeId,
            { childNodeIds }
        );
    }

    untrackExpandGroup(parentNodeId) {

        this.expandGroups.delete(parentNodeId);
    }

    getExpandGroups() {

        return this.expandGroups;
    }

    getChildPositions(nodeId) {

        return this.childPositions.get(
            nodeId
        ) || null;
    }

    // =========================================================================
    // Pinning
    // =========================================================================

    pinNode(nodeId) {

        this.pinnedNodes.add(nodeId);

        this.emit("pinChanged", {
            nodeId,
            pinned: true,
        });
    }

    unpinNode(nodeId) {

        this.pinnedNodes.delete(nodeId);

        this.emit("pinChanged", {
            nodeId,
            pinned: false,
        });
    }

    isPinned(nodeId) {

        return this.pinnedNodes.has(nodeId);
    }

    // =========================================================================
    // Accessors
    // =========================================================================

    getNode(nodeId) {
        return this.nodeMap.get(nodeId);
    }

    getEdge(edgeId) {
        return this.edgeMap.get(edgeId);
    }

    getCluster(clusterId) {
        return this.clusterMap.get(clusterId);
    }

    getIncomingEdges(nodeId) {
        return this.incomingEdges.get(nodeId) || [];
    }

    getOutgoingEdges(nodeId) {
        return this.outgoingEdges.get(nodeId) || [];
    }

    getClusterNodes(clusterId) {
        return this.clusterNodes.get(clusterId) || [];
    }

    getNodeOrParent(nodeId) {

        const node = this.nodeMap.get(nodeId);

        if (node) {
            return node;
        }

        const parentId =
            this.callNodeParent.get(nodeId);

        if (parentId) {
            return this.nodeMap.get(parentId);
        }

        return null;
    }

    // =========================================================================
    // Statistics
    // =========================================================================

    getStats() {

        return {
            nodes: this.graph.nodes.length,
            edges: this.graph.edges.length,
            clusters: this.graph.clusters.length,

            hiddenNodes: this.hiddenNodes.size,
            collapsedClusters: this.collapsedClusters.size,
            pinnedNodes: this.pinnedNodes.size,
        };
    }
}