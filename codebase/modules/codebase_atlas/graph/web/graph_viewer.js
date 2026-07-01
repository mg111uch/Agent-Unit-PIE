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
            });

        this.events.initialize();
    }

    /**
     * ========================================================================
     * Startup
     * ========================================================================
     */

    initialize() {

        this.restoreState();

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

        const positions = {};

        for (const node of this.state.graph.nodes) {

            if (
                node.position &&
                Number.isFinite(
                    node.position.x
                ) &&
                Number.isFinite(
                    node.position.y
                )
            ) {

                positions[node.id] = {
                    x: node.position.x,
                    y: node.position.y,
                };
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
            }),
        }).catch(() => {});
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