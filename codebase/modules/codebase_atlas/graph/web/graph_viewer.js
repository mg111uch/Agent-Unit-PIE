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

        this.storage =
            new GraphStorage(
                options.storageNamespace ??
                "interactive-graph"
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

    attachStorage() {

        this._unsubscribeStorage =
            this.storage.attach(
                this.state
            );
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

        this.renderer.fitToViewport();
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