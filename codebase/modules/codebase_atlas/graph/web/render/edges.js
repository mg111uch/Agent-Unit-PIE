// web/render/edges.js

import {
    EDGE_STYLES,
    TYPOGRAPHY
} from "./styles.js";

import {
    nodeConnectionPoints
} from "../utils/geometry.js";

const SVG_NS = "http://www.w3.org/2000/svg";

/**
 * ============================================================================
 * EdgeRenderer
 * ============================================================================
 */

export class EdgeRenderer {

    constructor(options = {}) {

        this.options = options;

        this.edgeElements = new Map();
    }

    /**
     * ========================================================================
     * Main Render Entry
     * ========================================================================
     */

    render(layer, state) {

        this.edgeElements.clear();

        for (const edge of state.graph.edges) {

            if (state.hiddenEdges?.has(edge.id)) {
                continue;
            }

            const source =
                state.getNode(edge.source);

            const target =
                state.getNode(edge.target);

            if (!source || !target) {
                continue;
            }

            if (
                state.isNodeHidden(source.id) ||
                state.isNodeHidden(target.id)
            ) {
                continue;
            }

            const element =
                this.createEdge(
                    edge,
                    source,
                    target,
                    state
                );

            layer.appendChild(element);

            this.edgeElements.set(
                edge.id,
                element
            );
        }
    }

    /**
     * ========================================================================
     * Edge Creation
     * ========================================================================
     */

    createEdge(
        edge,
        source,
        target,
        state
    ) {

        const group =
            document.createElementNS(
                SVG_NS,
                "g"
            );

        group.classList.add("graph-edge");

        group.dataset.edgeId = edge.id;

        const line =
            this.createLine(
                edge,
                source,
                target,
                state
            );

        group.appendChild(line);

        if (edge.label) {

            const label =
                this.createLabel(
                    edge,
                    source,
                    target
                );

            group.appendChild(label);
        }

        return group;
    }

    /**
     * ========================================================================
     * Edge Line
     * ========================================================================
     */

    createLine(
        edge,
        source,
        target,
        state
    ) {

        const line =
            document.createElementNS(
                SVG_NS,
                "line"
            );

        const {
            source: sourcePos,
            target: targetPos
        } = nodeConnectionPoints(
            source,
            target
        );

        line.setAttribute(
            "x1",
            sourcePos.x
        );

        line.setAttribute(
            "y1",
            sourcePos.y
        );

        line.setAttribute(
            "x2",
            targetPos.x
        );

        line.setAttribute(
            "y2",
            targetPos.y
        );

        const style =
            this.getEdgeStyle(
                edge,
                state
            );

        line.setAttribute(
            "stroke",
            style.color
        );

        line.setAttribute(
            "stroke-width",
            style.width
        );

        if (style.dasharray) {

            line.setAttribute(
                "stroke-dasharray",
                style.dasharray
            );
        }

        line.setAttribute(
            "fill",
            "none"
        );

        return line;
    }

    /**
     * ========================================================================
     * Label
     * ========================================================================
     */

    createLabel(
        edge,
        source,
        target
    ) {

        const sourcePos =
            this.getNodeCenter(source);

        const targetPos =
            this.getNodeCenter(target);

        const text =
            document.createElementNS(
                SVG_NS,
                "text"
            );

        text.textContent =
            edge.label;

        text.setAttribute(
            "x",
            (sourcePos.x + targetPos.x) / 2
        );

        text.setAttribute(
            "y",
            (sourcePos.y + targetPos.y) / 2 - 4
        );

        text.setAttribute(
            "text-anchor",
            "middle"
        );

        text.setAttribute(
            "font-family",
            TYPOGRAPHY.FONT_FAMILY
        );

        text.setAttribute(
            "font-size",
            "11"
        );

        text.setAttribute(
            "fill",
            "#c9d1d9"
        );

        return text;
    }

    /**
     * ========================================================================
     * Styling
     * ========================================================================
     */

    getEdgeStyle(
        edge,
        state
    ) {

        if (
            state.selectedEdgeId === edge.id
        ) {
            return EDGE_STYLES.SELECTED;
        }

        const type =
            edge.type?.toUpperCase();

        return (
            EDGE_STYLES[type] ??
            EDGE_STYLES.DEFAULT
        );
    }

    /**
     * ========================================================================
     * Geometry
     * ========================================================================
     */

    getNodeCenter(node) {

        const width =
            node.width ?? 180;

        const height =
            node.height ?? 48;

        return {

            x:
                (node.position?.x ?? 0) +
                width / 2,

            y:
                (node.position?.y ?? 0) +
                height / 2,
        };
    }

    /**
     * ========================================================================
     * Updates
     * ========================================================================
     */

    updateEdge(
        edge,
        state
    ) {

        const group =
            this.edgeElements.get(
                edge.id
            );

        if (!group) {
            return;
        }

        const source =
            state.getNode(edge.source);

        const target =
            state.getNode(edge.target);

        if (!source || !target) {
            return;
        }

        const line =
            group.querySelector("line");

        if (!line) {
            return;
        }

        const sourcePos =
            this.getNodeCenter(source);

        const targetPos =
            this.getNodeCenter(target);

        line.setAttribute(
            "x1",
            sourcePos.x
        );

        line.setAttribute(
            "y1",
            sourcePos.y
        );

        line.setAttribute(
            "x2",
            targetPos.x
        );

        line.setAttribute(
            "y2",
            targetPos.y
        );

        const label =
            group.querySelector("text");

        if (label) {

            label.setAttribute(
                "x",
                (sourcePos.x + targetPos.x) / 2
            );

            label.setAttribute(
                "y",
                (sourcePos.y + targetPos.y) / 2 - 4
            );
        }
    }

    /**
     * ========================================================================
     * Accessors
     * ========================================================================
     */

    getEdgeElement(edgeId) {

        return this.edgeElements.get(
            edgeId
        );
    }
}