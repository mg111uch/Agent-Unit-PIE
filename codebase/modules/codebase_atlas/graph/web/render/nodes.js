// web/render/nodes.js

import {
    NODE_COLORS,
    RISK_COLORS,
    NODE_DIMENSIONS,
    NODE_BORDERS,
    TYPOGRAPHY
} from "./styles.js";

const SVG_NS = "http://www.w3.org/2000/svg";

/**
 * ============================================================================
 * NodeRenderer
 * ============================================================================
 */

export class NodeRenderer {

    constructor(options = {}) {

        this.options = {
            width: NODE_DIMENSIONS.DEFAULT_WIDTH,
            height: NODE_DIMENSIONS.DEFAULT_HEIGHT,
            ...options,
        };

        this.nodeElements = new Map();
    }

    /**
     * ------------------------------------------------------------------------
     * Main Render Entry
     * ------------------------------------------------------------------------
     */

    render(layer, state) {

        this.nodeElements.clear();

        const nodes = state.graph.nodes;

        for (const node of nodes) {

            if (state.isNodeHidden(node.id)) {
                continue;
            }

            if (
                node.cluster_id &&
                state.isClusterCollapsed(node.cluster_id)
            ) {
                continue;
            }

            const element =
                this.createNode(node, state);

            layer.appendChild(element);

            this.nodeElements.set(
                node.id,
                element
            );
        }
    }

    /**
     * ------------------------------------------------------------------------
     * Node Creation
     * ------------------------------------------------------------------------
     */

    createNode(node, state) {

        const group =
            document.createElementNS(
                SVG_NS,
                "g"
            );

        group.classList.add("graph-node");

        group.dataset.nodeId = node.id;

        const x =
            node.position?.x ?? 0;

        const y =
            node.position?.y ?? 0;

        group.setAttribute(
            "transform",
            `translate(${x},${y})`
        );

        const width =
            node.width ??
            this.options.width;

        const height =
            node.height ??
            this.options.height;

        const rect =
            this.createBackgroundRect(
                node,
                width,
                height,
                state
            );

        const label =
            this.createLabel(
                node,
                width,
                height
            );

        group.appendChild(rect);
        group.appendChild(label);

        if (node.entry_point) {

            const badge =
                this.createEntryPointBadge(
                    width
                );

            group.appendChild(badge);
        }

        if (node.risk_level) {

            const risk =
                this.createRiskIndicator(
                    node.risk_level,
                    width,
                    height
                );

            group.appendChild(risk);
        }

        return group;
    }

    /**
     * ------------------------------------------------------------------------
     * Background
     * ------------------------------------------------------------------------
     */

    createBackgroundRect(
        node,
        width,
        height,
        state
    ) {

        const rect =
            document.createElementNS(
                SVG_NS,
                "rect"
            );

        rect.setAttribute("x", 0);
        rect.setAttribute("y", 0);

        rect.setAttribute(
            "width",
            width
        );

        rect.setAttribute(
            "height",
            height
        );

        rect.setAttribute("rx", 8);

        const fill =
            node.visual?.color ??
            TYPOGRAPHY[node.type] ??
            TYPOGRAPHY.unknown;

        rect.setAttribute(
            "fill",
            fill
        );

        rect.setAttribute(
            "stroke",
            this.getBorderColor(
                node,
                state
            )
        );

        rect.setAttribute(
            "stroke-width",
            this.getBorderWidth(
                node,
                state
            )
        );

        return rect;
    }

    /**
     * ------------------------------------------------------------------------
     * Label
     * ------------------------------------------------------------------------
     */

    createLabel(
        node,
        width,
        height
    ) {

        const text =
            document.createElementNS(
                SVG_NS,
                "text"
            );

        text.textContent =
            node.label;

        text.setAttribute(
            "x",
            width / 2
        );

        text.setAttribute(
            "y",
            height / 2 + 5
        );

        text.setAttribute(
            "text-anchor",
            "middle"
        );

        text.setAttribute(
            "font-size",
            "13"
        );

        text.setAttribute(
            "font-family",
            "sans-serif"
        );

        text.setAttribute(
            "fill",
            "#ffffff"
        );

        return text;
    }

    /**
     * ------------------------------------------------------------------------
     * Entry Point Marker
     * ------------------------------------------------------------------------
     */

    createEntryPointBadge(
        width
    ) {

        const circle =
            document.createElementNS(
                SVG_NS,
                "circle"
            );

        circle.setAttribute(
            "cx",
            width - 12
        );

        circle.setAttribute(
            "cy",
            12
        );

        circle.setAttribute(
            "r",
            5
        );

        circle.setAttribute(
            "fill",
            "#00e676"
        );

        return circle;
    }

    /**
     * ------------------------------------------------------------------------
     * Risk Marker
     * ------------------------------------------------------------------------
     */

    createRiskIndicator(
        riskLevel,
        width,
        height
    ) {

        const rect =
            document.createElementNS(
                SVG_NS,
                "rect"
            );

        rect.setAttribute(
            "x",
            width - 6
        );

        rect.setAttribute(
            "y",
            0
        );

        rect.setAttribute(
            "width",
            6
        );

        rect.setAttribute(
            "height",
            height
        );

        rect.setAttribute(
            "fill",
            RISK_COLORS[
                riskLevel
            ] ?? "#999999"
        );

        return rect;
    }

    /**
     * ------------------------------------------------------------------------
     * Visual State
     * ------------------------------------------------------------------------
     */

    getBorderColor(
        node,
        state
    ) {

        if (
            state.selectedNodeId ===
            node.id
        ) {
            return "#ffffff";
        }

        if (
            state.isPinned(node.id)
        ) {
            return "#ffd666";
        }

        return "#202020";
    }

    getBorderWidth(
        node,
        state
    ) {

        if (
            state.selectedNodeId ===
            node.id
        ) {
            return 3;
        }

        if (
            state.isPinned(node.id)
        ) {
            return 2;
        }

        return 1;
    }

    /**
     * ------------------------------------------------------------------------
     * Updates
     * ------------------------------------------------------------------------
     */

    updateNode(
        node,
        state
    ) {

        const element =
            this.nodeElements.get(
                node.id
            );

        if (!element) {
            return;
        }

        const x =
            node.position?.x ?? 0;

        const y =
            node.position?.y ?? 0;

        element.setAttribute(
            "transform",
            `translate(${x},${y})`
        );
    }

    /**
     * ------------------------------------------------------------------------
     * Accessors
     * ------------------------------------------------------------------------
     */

    getNodeElement(
        nodeId
    ) {

        return this.nodeElements.get(
            nodeId
        );
    }
}