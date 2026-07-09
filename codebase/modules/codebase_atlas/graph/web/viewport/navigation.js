// web/viewport/navigation.js
import {
    NAVIGATION,
    VIEWPORT,
} from "../core/constants.js";
import {
    computeNodeBounds,
    expandBounds,
    getNodeCenter,
} from "../utils/geometry.js";

/**
 * ============================================================================
 * GraphNavigation
 * ============================================================================
 *
 * High-level graph navigation built on top of ViewportController.
 *
 * ============================================================================
 */
export class GraphNavigation {
    constructor(options = {}) {
        this.state = options.state;
        this.viewport = options.viewport;
        this.renderer = options.renderer;
    }
    /* Graph */
    fitGraph() {
        const nodes =
            this.state?.graph?.nodes ?? [];
        if (!nodes.length) {
            return;
        }
        const bounds =
            expandBounds(
                computeNodeBounds(nodes),
                VIEWPORT.FIT_PADDING
            );
        this.viewport.fitBounds(
            bounds
        );
    }
    /* Nodes */
    centerOnNode(
        nodeId
    ) {
        const node =
            this.state.getNode(
                nodeId
            );
        if (!node) {
            return false;
        }
        const center =
            getNodeCenter(node);
        this.viewport.centerOn(
            center.x,
            center.y
        );
        return true;
    }
    zoomToNode(
        nodeId,
        zoom =
            NAVIGATION.ZOOM_TO_NODE_SCALE
    ) {
        const node =
            this.state.getNode(
                nodeId
            );
        if (!node) {
            return false;
        }
        const center =
            getNodeCenter(node);
        this.viewport.setZoom(
            zoom
        );
        this.viewport.centerOn(
            center.x,
            center.y
        );
        return true;
    }
    /* Clusters */
    centerOnCluster(
        clusterId
    ) {
        const bounds =
            this.getClusterBounds(
                clusterId
            );
        if (!bounds) {
            return false;
        }
        const centerX =
            bounds.minX +
            bounds.width / 2;
        const centerY =
            bounds.minY +
            bounds.height / 2;
        this.viewport.centerOn(
            centerX,
            centerY
        );
        return true;
    }
    zoomToCluster(
        clusterId,
        zoom =
            NAVIGATION.ZOOM_TO_CLUSTER_SCALE
    ) {
        const bounds =
            this.getClusterBounds(
                clusterId
            );
        if (!bounds) {
            return false;
        }
        const centerX =
            bounds.minX +
            bounds.width / 2;
        const centerY =
            bounds.minY +
            bounds.height / 2;
        this.viewport.setZoom(
            zoom
        );
        this.viewport.centerOn(
            centerX,
            centerY
        );
        return true;
    }
    fitCluster(
        clusterId
    ) {
        const bounds =
            this.getClusterBounds(
                clusterId
            );
        if (!bounds) {
            return false;
        }
        this.viewport.fitBounds(
            expandBounds(
                bounds,
                VIEWPORT.FIT_PADDING
            )
        );
        return true;
    }
    /* Generic Bounds */
    zoomToBounds(
        bounds
    ) {
        if (!bounds) {
            return false;
        }
        this.viewport.fitBounds(
            bounds
        );
        return true;
    }
    /* Cluster Helpers */
    getClusterBounds(
        clusterId
    ) {
        const cluster =
            this.state.graph.clusters
                ?.find(
                    c =>
                        c.id ===
                        clusterId
                );
        if (!cluster) {
            return null;
        }
        let nodes = [];
        if (
            Array.isArray(
                cluster.node_ids
            )
        ) {
            nodes =
                cluster.node_ids
                    .map(id =>
                        this.state.getNode(
                            id
                        )
                    )
                    .filter(Boolean);
        } else {
            nodes =
                this.state.graph.nodes
                    .filter(
                        node =>
                            node.cluster_id ===
                            clusterId
                    );
        }
        if (!nodes.length) {
            return null;
        }
        return computeNodeBounds(
            nodes
        );
    }
    /* Convenience */
    resetView() {
        this.viewport.reset();
    }
    getCurrentView() {
        return {
            zoom:
                this.viewport.zoom,
            panX:
                this.viewport.panX,
            panY:
                this.viewport.panY,
        };
    }
}