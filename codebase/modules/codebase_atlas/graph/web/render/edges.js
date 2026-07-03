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

    render(layer, state, items = null) {

        this.edgeElements.clear();

        const edges = items ?? state.graph.edges;

        // -----------------------------------------------------------
        // Deduplicate by (source, target) pair.
        //
        // Call graphs in particular repeat the same
        // (caller, callee) edge many times because each
        // call site is a separate edge.  Drawing N lines
        // for N identical pairs is wasted DOM, wasted
        // compositing, and a confusing visual.
        //
        // The first edge in each group is the
        // representative: it owns the rendered id and
        // selection state.  The count is shown as a
        // small badge when > 1.
        // -----------------------------------------------------------

        const groups = new Map();

        for (const edge of edges) {

            if (state.hiddenEdges?.has(edge.id)) {
                continue;
            }

            const key =
                edge.source + "\u0000" +
                edge.target;

            if (groups.has(key)) {
                groups.get(key).count += 1;
                continue;
            }

            groups.set(key, {
                representative: edge,
                count: 1,
            });
        }

        const fragment =
            document.createDocumentFragment();

        for (const group of groups.values()) {

            const edge = group.representative;

            const source =
                state.getNodeOrParent(
                    edge.source
                );

            const target =
                state.getNodeOrParent(
                    edge.target
                );

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
                    state,
                    group.count
                );

            fragment.appendChild(element);

            this.edgeElements.set(
                edge.id,
                element
            );
        }

        layer.appendChild(fragment);
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
        state,
        count = 1
    ) {

        const group =
            document.createElementNS(
                SVG_NS,
                "g"
            );

        group.classList.add("graph-edge");

        if (state.selectedEdgeId === edge.id) {
            group.classList.add("selected");
        }

        group.dataset.edgeId = edge.id;

        if (count > 1) {
            group.classList.add("merged");
            group.dataset.edgeCount = count;
        }

        const line =
            this.createLine(
                edge,
                source,
                target,
                state
            );

        // Thicker stroke for merged edges so the
        // visual weight matches the duplicate count.
        if (count > 1) {

            line.setAttribute(
                "stroke-width",
                Math.min(
                    1 + Math.log2(count),
                    6
                ).toString()
            );
        }

        group.appendChild(line);

        if (count > 1) {

            const badge =
                this.createCountBadge(
                    source,
                    target,
                    count
                );

            if (badge) {
                group.appendChild(badge);
            }
        }

        if (
            edge.label &&
            this.shouldRenderLabel(state)
        ) {

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
     * Edge labels are extremely expensive in SVG
     * (text layout dominates cost above a few
     * thousand nodes).
     *
     * Call graphs are the worst case: edges are
     * almost always the same opaque "calls"
     * relation, and labels add no information.
     *
     * Dependency graphs keep their labels because
     * the edge type (imports, inherits, references)
     * is actually useful when read.
     */
    shouldRenderLabel(state) {

        const graphType =
            state?.graph?.metadata?.graph_type;

        if (graphType === "call") {
            return false;
        }

        return true;
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

        const resolvedSource =
            this.resolveEdgeEndpoint(
                source,
                state
            );

        const resolvedTarget =
            this.resolveEdgeEndpoint(
                target,
                state
            );

        const line =
            document.createElementNS(
                SVG_NS,
                "line"
            );

        const {
            source: sourcePos,
            target: targetPos
        } = nodeConnectionPoints(
            resolvedSource,
            resolvedTarget
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

    resolveEdgeEndpoint(
        node,
        state
    ) {

        if (
            node.scope !== "call" ||
            !node.parent_id
        ) {
            return node;
        }

        if (
            state.isExpanded(node.parent_id)
        ) {
            return node;
        }

        const parent =
            state.getNode(node.parent_id);

        return parent || node;
    }

    /**
     * ========================================================================
     * Label
     * ========================================================================
     */

    createCountBadge(
        source,
        target,
        count
    ) {

        const sourcePos =
            this.getNodeCenter(source);

        const targetPos =
            this.getNodeCenter(target);

        const cx =
            (sourcePos.x + targetPos.x) / 2;

        const cy =
            (sourcePos.y + targetPos.y) / 2 - 4;

        const text =
            document.createElementNS(
                SVG_NS,
                "text"
            );

        text.textContent = `x${count}`;

        text.setAttribute("x", cx);
        text.setAttribute("y", cy);

        text.setAttribute(
            "text-anchor",
            "middle"
        );

        text.setAttribute(
            "font-family",
            "ui-monospace, SFMono-Regular, Menlo, monospace"
        );

        text.setAttribute(
            "font-size",
            "9"
        );

        text.setAttribute(
            "font-weight",
            "600"
        );

        text.setAttribute(
            "fill",
            "#ffffff"
        );

        text.setAttribute(
            "stroke",
            "#0f1117"
        );

        text.setAttribute(
            "stroke-width",
            "3"
        );

        text.setAttribute(
            "paint-order",
            "stroke"
        );

        text.classList.add("graph-edge-badge");

        return text;
    }

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
            state.getNodeOrParent(
                edge.source
            );

        const target =
            state.getNodeOrParent(
                edge.target
            );

        if (!source || !target) {
            return;
        }

        const resolvedSource =
            this.resolveEdgeEndpoint(
                source,
                state
            );

        const resolvedTarget =
            this.resolveEdgeEndpoint(
                target,
                state
            );

        const line =
            group.querySelector("line");

        if (!line) {
            return;
        }

        const sourcePos =
            this.getNodeCenter(
                resolvedSource
            );

        const targetPos =
            this.getNodeCenter(
                resolvedTarget
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

        const midX =
            (sourcePos.x + targetPos.x) / 2;

        const midY =
            (sourcePos.y + targetPos.y) / 2 - 4;

        const badge =
            group.querySelector(
                ".graph-edge-badge"
            );

        if (badge) {

            badge.setAttribute("x", midX);
            badge.setAttribute("y", midY);
        }

        const textNodes =
            group.querySelectorAll("text");

        for (const node of textNodes) {

            if (
                node.classList &&
                node.classList.contains(
                    "graph-edge-badge"
                )
            ) {
                continue;
            }

            node.setAttribute("x", midX);
            node.setAttribute("y", midY);
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

    // Generic accessor matching the renderer's
    // updateSelection() expectations.
    getElement(edgeId) {

        return this.getEdgeElement(edgeId);
    }
}