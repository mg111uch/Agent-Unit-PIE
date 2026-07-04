// web/graph_viewer.js

import { GraphState }
    from "./core/state.js";

import { GraphStorage }
    from "./core/storage.js";

import { GraphRenderer }
    from "./render/renderer.js";

import { NodeRenderer }
    from "./render/nodes.js";

import { EdgeRenderer }
    from "./render/edges.js";

import { ClusterRenderer }
    from "./render/clusters.js";

import { ViewportController }
    from "./viewport/viewport.js";

import { GraphNavigation }
    from "./viewport/navigation.js";

import {
    SelectionManager
} from "./interaction/selection.js";

import {
    GraphEventController
} from "./interaction/events.js";

import {
    DragController
} from "./interaction/drag.js";

import {
    GraphInteractionManager
} from "./interaction/interaction.js";

import { GraphLayoutEngine }
    from "./layout/layout.js";

const LARGE_GRAPH_THRESHOLD = 200;

/**
 * ============================================================================
 * GraphViewer
 * ============================================================================
 *
 * Top-level application controller.
 *
 * Responsibilities:
 *   - Create graph state
 *   - Restore persisted state
 *   - Create renderers
 *   - Coordinate lifecycle
 *
 * Does NOT:
 *   - Render nodes directly
 *   - Handle dragging
 *   - Handle search
 *   - Handle viewport controls
 *
 * ============================================================================
 */

export class GraphViewer {

    constructor(options = {}) {

        this.options = options;

        this.graphData =
            options.graphData;

        this._hadViewportSnapshot = false;

        if (!this.graphData) {

            throw new Error(
                "graphData is required"
            );
        }

        // -------------------------------------------------------------
        // Core
        // -------------------------------------------------------------

        this.state =
            new GraphState(
                this.graphData
            );
        
        this.state._buildCallNodeParent();
        
        this.layout =
            GraphLayoutEngine;

        this.applyInitialLayout();

        const graphType =
            this.graphData?.graph_type ??
            "unknown";

        this.storage =
            new GraphStorage(
                options.storageNamespace ??
                `interactive-graph:${graphType}`
            );

        this.childData =
            options.childData ??
            {};

        // -------------------------------------------------------------
        // Renderers
        // -------------------------------------------------------------

        this.nodeRenderer =
            new NodeRenderer();

        this.edgeRenderer =
            new EdgeRenderer();

        this.clusterRenderer =
            new ClusterRenderer();

        const nodeCount =
            this.graphData?.nodes?.length ?? 0;

        this.useViewportCulling =
            nodeCount >= LARGE_GRAPH_THRESHOLD;

        this.renderer =
            new GraphRenderer({

                state:
                    this.state,

                svg:
                    options.svg ??
                    "graph-svg",

                viewport:
                    options.viewport ??
                    "viewport",

                clusterLayer:
                    options.clusterLayer ??
                    "cluster-layer",

                edgeLayer:
                    options.edgeLayer ??
                    "edge-layer",

                nodeLayer:
                    options.nodeLayer ??
                    "node-layer",

                overlayLayer:
                    options.overlayLayer ??
                    "overlay-layer",

                cullOnRender:
                    this.useViewportCulling,
            });

        this.renderer
            .setNodeRenderer(
                this.nodeRenderer
            );

        this.renderer
            .setEdgeRenderer(
                this.edgeRenderer
            );

        this.renderer
            .setClusterRenderer(
                this.clusterRenderer
            );

        this._unsubscribeStorage =
            null;

        this.viewport =
            new ViewportController({
                state: this.state,
                renderer: this.renderer,
            });

        this.navigation =
            new GraphNavigation({

                state:
                    this.state,

                viewport:
                    this.viewport,

                renderer:
                    this.renderer,
            });

        this.selection =
            new SelectionManager({
                state: this.state,
            });

        this.events =
            new GraphEventController({
                svg: "graph-svg",
                state: this.state,
                viewport: this.viewport,
            });

        this.drag =
            new DragController({
                state: this.state,
                renderer: this.renderer,
                selection: this.selection,
                events: this.events,
                viewport: this.viewport,
            });

        this.interaction =
            new GraphInteractionManager({

                state: this.state,

                renderer: this.renderer,

                viewport: this.viewport,

                navigation: this.navigation,

                selection: this.selection,

                events: this.events,

                drag: this.drag,

                viewer: this,
            });

        this.events.initialize();
    }

    /**
     * ========================================================================
     * Startup
     * ========================================================================
     */

    async initialize() {

        this._hadViewportSnapshot =
            this.restoreState();

        if (
            this._hadViewportSnapshot &&
            this.viewport
        ) {

            this.viewport.zoom =
                this.state.zoom;

            this.viewport.panX =
                this.state.panX;

            this.viewport.panY =
                this.state.panY;

            this.viewport.updateTransform();
        }

        await this._loadChildPositions();

        this.attachStorage();

        this.renderer.initialize();

        this.renderer.whenMeasured(
            () => this._initialRender()
        );

        return this;
    }

    _initialRender() {

        const nodeCount =
            this.state.graph?.nodes?.length ?? 0;

        if (nodeCount >= LARGE_GRAPH_THRESHOLD) {

            return this.renderer
                .renderChunked()
                .then(() => {

                    if (this._hadViewportSnapshot) {

                        this.viewport.zoom =
                            this.state.zoom;

                        this.viewport.panX =
                            this.state.panX;

                        this.viewport.panY =
                            this.state.panY;

                        this.viewport.updateTransform();

                    } else {

                        this.navigation.fitGraph();
                    }

                    this._replayExpandedNodes();

                    return this;
                });
        }

        if (this._hadViewportSnapshot) {

            this.viewport.zoom =
                this.state.zoom;

            this.viewport.panX =
                this.state.panX;

            this.viewport.panY =
                this.state.panY;

            this.viewport.updateTransform();

            this.renderer.render();

            this._replayExpandedNodes();

            return this;
        }

        this.renderer.render();

        this.navigation.fitGraph();

        this._replayExpandedNodes();

        return this;
    }

    _replayExpandedNodes() {

        const ids =
            Array.from(
                this.state.expandedNodes
            );

        this.state.expandedNodes.clear();

        for (const nodeId of ids) {

            this.expandNode(nodeId);
        }
    }

    /**
     * ========================================================================
     * Graph Swap
     * ========================================================================
     */

    setGraphData(graphData) {

        if (!graphData) {

            throw new Error(
                "graphData is required"
            );
        }

        this.graphData = graphData;

        const graphType =
            graphData?.graph_type ??
            "unknown";

        const newNamespace =
            `interactive-graph:${graphType}`;

        if (
            this.storage.namespace !==
            newNamespace
        ) {

            this.storage.namespace =
                newNamespace;
        }

        this.storage.suspend();

        try {

            this.state.setGraph(graphData);

            this.selection.clear();

            this.applyInitialLayout();

        } finally {

            this.storage.resume();
        }

        this.restoreState();

        const nodeCount =
            graphData?.nodes?.length ?? 0;

        if (nodeCount >= LARGE_GRAPH_THRESHOLD) {

            return this.renderer
                .renderChunked()
                .then(() => {

                    this.navigation.fitGraph();
                    return this;
                });
        }

        this.renderer.render();

        this.navigation.fitGraph();

        return this;
    }

    /**
     * ========================================================================
     * Persistence
     * ========================================================================
     */

    restoreState() {

        try {

            this.storage.restore(
                this.state
            );

        } catch (error) {

            console.warn(
                "Failed to restore graph state",
                error
            );
        }
    }

    applyInitialLayout() {

        const nodes =
            this.state.graph?.nodes ?? [];

        const missing =
            nodes.some(
                node =>
                    !node.position ||
                    node.position.x == null ||
                    node.position.y == null
            );

        if (!missing) {
            return;
        }

        const hasClusters =
            (this.state.graph?.clusters?.length || 0) >
            0;

        const graphType =
            this.graphData?.graph_type ??
            "unknown";

        if (graphType === "call" && hasClusters) {
            this.layout.clusterGrid(
                this.state.graph,
                {
                    microSpacing: 140,
                    macroSpacing: 400,
                    clusterMargin: 60,
                }
            );

            return;
        }

        if (
            nodes.length >= LARGE_GRAPH_THRESHOLD
        ) {

            this.layout.grid(
                this.state.graph,
                { spacing: 180 }
            );

            return;
        }

        this.layout.hierarchical(
            this.state.graph
        );
    }

    attachStorage() {

        this._unsubscribeStorage =
            this.storage.attach(
                this.state
            );

        this._unsubscribeServerSave =
            this.state.subscribe(
                "nodes:moved",
                () => this._savePositionsToServer()
            );
    }

    _savePositionsToServer() {

        if (!this.state?.graph?.nodes) {
            return;
        }

        const graphType =
            this.graphData?.graph_type ??
            "unknown";

        const expandedChildIds = new Set();

        for (const group
             of this.state.getExpandGroups().values()) {
            for (const childId of group.childNodeIds) {
                expandedChildIds.add(childId);
            }
        }

        const positions = {};

        for (const node of this.state.graph.nodes) {

            if (
                node.position &&
                Number.isFinite(
                    node.position.x
                ) &&
                Number.isFinite(
                    node.position.y
                ) &&
                !expandedChildIds.has(node.id)
            ) {

                positions[node.id] = {
                    x: Math.round(node.position.x),
                    y: Math.round(node.position.y),
                };
            }
        }

        const child_offsets = {};

        for (const [
            parentId,
            offsets
        ] of this.state.childPositions) {
            child_offsets[parentId] = { ...offsets };
        }

        for (const [
            parentId,
            group
        ] of this.state.getExpandGroups()) {

            const parent =
                this.state.getNode(parentId);

            if (!parent || !parent.position) {
                continue;
            }

            const offsets = {};

            for (const childId
                 of group.childNodeIds) {

                const child =
                    this.state.getNode(childId);

                if (!child || !child.position) {
                    continue;
                }

                const dx =
                    child.position.x -
                    parent.position.x;

                const dy =
                    child.position.y -
                    parent.position.y;

                if (
                    Number.isFinite(dx) &&
                    Number.isFinite(dy)
                ) {

                    offsets[childId] = {
                        dx: Math.round(dx),
                        dy: Math.round(dy),
                    };
                }
            }

            if (Object.keys(offsets).length > 0) {
                child_offsets[parentId] = offsets;
                this.state.childPositions.set(
                    parentId,
                    offsets
                );
            }
        }

        fetch("/api/save-positions", {
            method: "POST",
            headers: {
                "Content-Type":
                    "application/json",
            },
            body: JSON.stringify({
                graph_type: graphType,
                positions,
                child_offsets,
            }),
        }).catch(() => {});
    }

    async _loadChildPositions() {

        try {

            const response =
                await fetch(
                    "/api/child-offsets"
                );

            if (!response.ok) {
                return;
            }

            const data =
                await response.json();

            if (
                data &&
                typeof data === "object"
            ) {

                this.state.childPositions =
                    new Map(
                        Object.entries(data)
                    );
            }

        } catch {
            // silently ignore
        }
    }

    save() {

        this.storage.save(
            this.state
        );
    }

    clearSavedState() {

        this.storage.clear();
    }

    /**
     * ========================================================================
     * Rendering
     * ========================================================================
     */

    render() {

        this.renderer.render();
    }

    fitToView() {

        this.navigation.fitGraph();
    }

    // =====================================================================
    // Expand / Collapse
    // =====================================================================

    async expandNode(nodeId) {

        const node = this.state.getNode(nodeId);

        if (!node || node.scope !== "file") {
            return;
        }

        if (this.state.isExpanded(nodeId)) {
            return;
        }

        let children =
            this.state.getCachedChildren(nodeId);

        if (!children) {

            children =
                await this._fetchChildren(nodeId);

            if (
                !children ||
                !children.nodes.length
            ) {
                return;
            }
        }

        this.state.addChildren(nodeId, children);

        const savedPositions =
            this.state.getChildPositions(
                nodeId
            );

        if (savedPositions) {

            for (const child of children.nodes) {

                const offset =
                    savedPositions[child.id];

                if (offset) {
                    child.position = {
                        x: node.position.x +
                            offset.dx,
                        y: node.position.y +
                            offset.dy,
                    };
                }
            }

        } else {

            GraphLayoutEngine.layoutChildren(
                node,
                children.nodes
            );
        }

        const childIds =
            children.nodes.map(
                n => n.id
            );

        this.state.trackExpandGroup(
            nodeId,
            childIds
        );

        this.state.expandNode(nodeId);
    }

    collapseNode(nodeId) {

        const node = this.state.getNode(nodeId);

        if (!node || node.scope !== "file") {
            return;
        }

        if (!this.state.isExpanded(nodeId)) {
            return;
        }

        this.state.collapseNode(nodeId);
    }

    async _fetchChildren(nodeId) {

        if (this.childData[nodeId]) {
            return this.childData[nodeId];
        }

        try {

            const response =
                await fetch(
                    `/api/graph/children/${encodeURIComponent(nodeId)}`
                );

            if (!response.ok) {
                return {
                    nodes: [],
                    edges: []
                };
            }

            const data =
                await response.json();

            this.childData[nodeId] = data;

            return data;

        } catch {

            return {
                nodes: [],
                edges: []
            };
        }
    }

    /**
     * ========================================================================
     * Accessors
     * ========================================================================
     */

    getState() {
        return this.state;
    }

    getRenderer() {
        return this.renderer;
    }

    getNodeRenderer() {
        return this.nodeRenderer;
    }

    getEdgeRenderer() {
        return this.edgeRenderer;
    }

    getClusterRenderer() {
        return this.clusterRenderer;
    }

    getViewport() {
        return this.viewport;
    }

    getNavigation() {
        return this.navigation;
    }

    /**
     * ========================================================================
     * Cleanup
     * ========================================================================
     */

    destroy() {

        if (
            this._unsubscribeStorage
        ) {

            this._unsubscribeStorage();
        }

        if (
            this._unsubscribeServerSave
        ) {

            this._unsubscribeServerSave();
        }
    }
}

/**
 * ============================================================================
 * Factory Helper
 * ============================================================================
 */

export function createGraphViewer(
    graphData,
    options = {}
) {

    return new GraphViewer({

        graphData,

        ...options,
    }).initialize();
}