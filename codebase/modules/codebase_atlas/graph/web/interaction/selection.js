// web/interaction/selection.js

import { EventEmitter }
    from "../core/events.js";
import {
    GRAPH_EVENTS
} from "../core/events.js";

/**
 * ============================================================================
 * SelectionManager
 * ============================================================================
 *
 * Owns:
 *   - selected nodes
 *   - selected edges
 *   - selected clusters
 *
 * Does NOT own:
 *   - DOM events
 *   - rendering
 *   - dragging
 *   - viewport
 *
 * ============================================================================
 */
export class SelectionManager extends EventEmitter {
    constructor(options = {}) {
        super();
        this.state =
            options.state;
        this.selectedNodes =
            new Set();
        this.selectedEdges =
            new Set();
        this.selectedClusters =
            new Set();
    }
    /* Clear */
    clear() {
        const changed =
            this.hasSelection();
        this.selectedNodes.clear();
        this.selectedEdges.clear();
        this.selectedClusters.clear();
        if (changed) {
            this._emitChange();
        }
    }
    hasSelection() {
        return (
            this.selectedNodes.size > 0 ||
            this.selectedEdges.size > 0 ||
            this.selectedClusters.size > 0
        );
    }
    /* Node Selection */
    selectNode(
        nodeId,
        additive = false
    ) {
        if (!additive) {
            this.clear();
        }
        this.selectedNodes.add(
            nodeId
        );
        this._syncLegacyState();
        this._emitChange();
    }
    deselectNode(
        nodeId
    ) {
        if (
            this.selectedNodes.delete(
                nodeId
            )
        ) {
            this._syncLegacyState();
            this._emitChange();
        }
    }
    toggleNode(
        nodeId
    ) {
        if (
            this.selectedNodes.has(
                nodeId
            )
        ) {
            this.selectedNodes.delete(
                nodeId
            );
        } else {
            this.selectedNodes.add(
                nodeId
            );
        }
        this._syncLegacyState();
        this._emitChange();
    }
    isNodeSelected(
        nodeId
    ) {
        return this.selectedNodes.has(
            nodeId
        );
    }
    getSelectedNodes() {
        return Array.from(
            this.selectedNodes
        );
    }
    /* Edge Selection */
    selectEdge(
        edgeId,
        additive = false
    ) {
        if (!additive) {
            this.clear();
        }
        this.selectedEdges.add(
            edgeId
        );
        this._emitChange();
    }
    deselectEdge(
        edgeId
    ) {
        if (
            this.selectedEdges.delete(
                edgeId
            )
        ) {
            this._emitChange();
        }
    }
    toggleEdge(
        edgeId
    ) {
        if (
            this.selectedEdges.has(
                edgeId
            )
        ) {
            this.selectedEdges.delete(
                edgeId
            );
        } else {
            this.selectedEdges.add(
                edgeId
            );
        }
        this._emitChange();
    }
    isEdgeSelected(
        edgeId
    ) {
        return this.selectedEdges.has(
            edgeId
        );
    }
    getSelectedEdges() {
        return Array.from(
            this.selectedEdges
        );
    }
    /* Cluster Selection */
    selectCluster(
        clusterId,
        additive = false
    ) {
        if (!additive) {
            this.clear();
        }
        this.selectedClusters.add(
            clusterId
        );
        this._emitChange();
    }
    deselectCluster(
        clusterId
    ) {
        if (
            this.selectedClusters.delete(
                clusterId
            )
        ) {
            this._emitChange();
        }
    }
    toggleCluster(
        clusterId
    ) {
        if (
            this.selectedClusters.has(
                clusterId
            )
        ) {
            this.selectedClusters.delete(
                clusterId
            );
        } else {
            this.selectedClusters.add(
                clusterId
            );
        }
        this._emitChange();
    }
    isClusterSelected(
        clusterId
    ) {
        return this.selectedClusters.has(
            clusterId
        );
    }
    getSelectedClusters() {
        return Array.from(
            this.selectedClusters
        );
    }
    /* Bulk Selection */
    selectNodes(
        nodeIds,
        additive = false
    ) {
        if (!additive) {
            this.clear();
        }
        for (const id of nodeIds) {
            this.selectedNodes.add(
                id
            );
        }
        this._syncLegacyState();
        this._emitChange();
    }
    selectEdges(
        edgeIds,
        additive = false
    ) {
        if (!additive) {
            this.clear();
        }
        for (const id of edgeIds) {
            this.selectedEdges.add(
                id
            );
        }
        this._emitChange();
    }
    selectClusters(
        clusterIds,
        additive = false
    ) {
        if (!additive) {
            this.clear();
        }
        for (const id of clusterIds) {
            this.selectedClusters.add(
                id
            );
        }
        this._emitChange();
    }
    /* Queries */
    getSelectionSummary() {
        return {
            nodes:
                this.getSelectedNodes(),
            edges:
                this.getSelectedEdges(),
            clusters:
                this.getSelectedClusters(),
            nodeCount:
                this.selectedNodes.size,
            edgeCount:
                this.selectedEdges.size,
            clusterCount:
                this.selectedClusters.size,
        };
    }
    /* Internal */
    _syncLegacyState() {
        if (!this.state) {
            return;
        }
        const firstNode =
            this.selectedNodes
                .values()
                .next()
                .value;
        this.state.selectedNodeId =
            firstNode ?? null;
    }
    _emitChange() {
        const payload =
            this.getSelectionSummary();
        this.emit(
            GRAPH_EVENTS.SELECTION_CHANGED,
            payload
        );
        if (this.state?.emit) {
            this.state.emit(
                GRAPH_EVENTS.SELECTION_CHANGED,
                payload
            );
        }
    }
}