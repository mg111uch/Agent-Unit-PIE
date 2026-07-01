// web/render/clusters.js

import {
    CLUSTER_STYLES,
    TYPOGRAPHY
} from "./styles.js";

import {
    computeNodeBounds,
    expandBounds
} from "../utils/geometry.js";

const SVG_NS =
    "http://www.w3.org/2000/svg";

const CLUSTER_PADDING = 30;

/**
 * ============================================================================
 * ClusterRenderer
 * ============================================================================
 */

export class ClusterRenderer {

    constructor(options = {}) {

        this.options = options;

        this.clusterElements =
            new Map();
    }

    /**
     * ========================================================================
     * Main Render
     * ========================================================================
     */

    render(layer, state, items = null) {

        this.clusterElements.clear();

        const clusters = items ?? state.graph.clusters;

        const fragment =
            document.createDocumentFragment();

        for (const cluster of clusters) {

            const element =
                this.createCluster(
                    cluster,
                    state
                );

            if (!element) {
                continue;
            }

            fragment.appendChild(element);

            this.clusterElements.set(
                cluster.id,
                element
            );
        }

        layer.appendChild(fragment);
    }

    /**
     * ========================================================================
     * Create Cluster
     * ========================================================================
     */

    createCluster(
        cluster,
        state
    ) {

        const nodes =
            this.getClusterNodes(
                cluster,
                state
            );

        if (!nodes.length) {
            return null;
        }

        const bounds =
            expandBounds(
                computeNodeBounds(
                    nodes
                ),
                CLUSTER_PADDING
            );

        const group =
            document.createElementNS(
                SVG_NS,
                "g"
            );

        group.classList.add(
            "graph-cluster"
        );

        if (
            state.selectedClusterId ===
            cluster.id
        ) {
            group.classList.add("selected");
        }

        group.dataset.clusterId =
            cluster.id;

        const background =
            this.createBackground(
                bounds,
                cluster,
                state
            );

        const label =
            this.createLabel(
                bounds,
                cluster,
                state
            );

        group.appendChild(
            background
        );

        group.appendChild(
            label
        );

        return group;
    }

    /**
     * ========================================================================
     * Background
     * ========================================================================
     */

    createBackground(
        bounds,
        cluster,
        state
    ) {

        const rect =
            document.createElementNS(
                SVG_NS,
                "rect"
            );

        rect.setAttribute(
            "x",
            bounds.minX
        );

        rect.setAttribute(
            "y",
            bounds.minY
        );

        rect.setAttribute(
            "width",
            bounds.width
        );

        rect.setAttribute(
            "height",
            bounds.height
        );

        rect.setAttribute(
            "rx",
            CLUSTER_STYLES.BORDER_RADIUS
        );

        rect.setAttribute(
            "fill",
            CLUSTER_STYLES.BACKGROUND
        );

        rect.setAttribute(
            "fill-opacity",
            "0.25"
        );

        rect.setAttribute(
            "stroke",
            this.getBorderColor(
                cluster,
                state
            )
        );

        rect.setAttribute(
            "stroke-width",
            CLUSTER_STYLES.BORDER_WIDTH
        );

        rect.setAttribute(
            "stroke-dasharray",
            state.isClusterCollapsed(
                cluster.id
            )
                ? "8 4"
                : ""
        );

        return rect;
    }

    /**
     * ========================================================================
     * Label
     * ========================================================================
     */

    createLabel(
        bounds,
        cluster,
        state
    ) {

        const text =
            document.createElementNS(
                SVG_NS,
                "text"
            );

        const prefix =
            state.isClusterCollapsed(
                cluster.id
            )
                ? "▶ "
                : "▼ ";

        text.textContent =
            prefix +
            (
                cluster.label ||
                cluster.id
            );

        text.setAttribute(
            "x",
            bounds.minX + 12
        );

        text.setAttribute(
            "y",
            bounds.minY + 20
        );

        text.setAttribute(
            "font-family",
            TYPOGRAPHY.FONT_FAMILY
        );

        text.setAttribute(
            "font-size",
            CLUSTER_STYLES.LABEL_FONT_SIZE
        );

        text.setAttribute(
            "fill",
            CLUSTER_STYLES.LABEL_COLOR
        );

        return text;
    }

    /**
     * ========================================================================
     * Cluster Nodes
     * ========================================================================
     */

    getClusterNodes(
        cluster,
        state
    ) {

        if (
            Array.isArray(
                cluster.node_ids
            )
        ) {

            return cluster.node_ids
                .map(id =>
                    state.getNode(id)
                )
                .filter(Boolean);
        }

        return state
            .graph
            .nodes
            .filter(
                node =>
                    node.cluster_id ===
                    cluster.id
            );
    }

    /**
     * ========================================================================
     * Styles
     * ========================================================================
     */

    getBorderColor(
        cluster,
        state
    ) {

        if (
            state.isClusterCollapsed(
                cluster.id
            )
        ) {

            return CLUSTER_STYLES.COLLAPSED_BORDER;
        }

        return CLUSTER_STYLES.BORDER;
    }

    /**
     * ========================================================================
     * Updates
     * ========================================================================
     */

    updateCluster(
        cluster,
        state
    ) {

        const element =
            this.clusterElements.get(
                cluster.id
            );

        if (!element) {
            return;
        }

        // Current architecture re-renders
        // entire cluster layer.
        // Placeholder for future incremental updates.
    }

    /**
     * ========================================================================
     * Accessors
     * ========================================================================
     */

    getClusterElement(
        clusterId
    ) {

        return this.clusterElements.get(
            clusterId
        );
    }

    // Generic accessor matching the renderer's
    // updateSelection() expectations.
    getElement(clusterId) {

        return this.getClusterElement(clusterId);
    }
}