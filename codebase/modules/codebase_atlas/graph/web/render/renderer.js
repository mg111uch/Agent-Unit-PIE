// web/render/renderer.js

import { EventEmitter, GRAPH_EVENTS }
    from "../core/events.js";

/**
 * ============================================================================
 * GraphRenderer
 * ============================================================================
 *
 * Top-level SVG rendering coordinator.
 *
 * Responsibilities:
 *   - Own SVG layers
 *   - Manage render lifecycle
 *   - Manage viewport transform
 *   - Delegate rendering to specialized renderers
 *
 * Does NOT:
 *   - Create node SVG details
 *   - Create edge SVG details
 *   - Handle dragging
 *   - Handle search
 * ============================================================================
 */

export class GraphRenderer extends EventEmitter {

    constructor(options = {}) {

        super();

        this.state = options.state;

        this.svg =
            this._resolveElement(
                options.svg ?? "graph-svg"
            );

        this.viewport =
            this._resolveElement(
                options.viewport ?? "viewport"
            );

        this.clusterLayer =
            this._resolveElement(
                options.clusterLayer ?? "cluster-layer"
            );

        this.edgeLayer =
            this._resolveElement(
                options.edgeLayer ?? "edge-layer"
            );

        this.nodeLayer =
            this._resolveElement(
                options.nodeLayer ?? "node-layer"
            );

        this.overlayLayer =
            this._resolveElement(
                options.overlayLayer ?? "overlay-layer"
            );

        this.nodeRenderer = null;
        this.edgeRenderer = null;
        this.clusterRenderer = null;

        this.renderCount = 0;

        this._bindStateEvents();
    }

    // =====================================================================
    // Dependency Injection
    // =====================================================================

    setNodeRenderer(renderer) {
        this.nodeRenderer = renderer;
    }

    setEdgeRenderer(renderer) {
        this.edgeRenderer = renderer;
    }

    setClusterRenderer(renderer) {
        this.clusterRenderer = renderer;
    }

    // =====================================================================
    // State Binding
    // =====================================================================

    _bindStateEvents() {

        if (!this.state) {
            return;
        }

        this.state.on(
            GRAPH_EVENTS.VIEWPORT_CHANGED,
            () => this.updateViewport()
        );

        this.state.on(
            GRAPH_EVENTS.SELECTION_CHANGED,
            () => this.render()
        );

        this.state.on(
            GRAPH_EVENTS.VISIBILITY_CHANGED,
            () => this.render()
        );

        this.state.on(
            GRAPH_EVENTS.CLUSTER_CHANGED,
            () => this.render()
        );

        this.state.on(
            GRAPH_EVENTS.STATE_CHANGED,
            () => this.render()
        );
    }

    // =====================================================================
    // Initial Render
    // =====================================================================

    initialize() {

        this.updateViewport();

        this.render();

        return this;
    }

    // =====================================================================
    // Main Render Pipeline
    // =====================================================================

    render() {

        this.emit(
            GRAPH_EVENTS.BEFORE_RENDER,
            {
                renderer: this,
            }
        );

        this.clearLayers();

        this.renderClusters();

        this.renderEdges();

        this.renderNodes();

        this.renderOverlays();

        this.renderCount += 1;

        this.emit(
            GRAPH_EVENTS.AFTER_RENDER,
            {
                renderer: this,
                renderCount: this.renderCount,
            }
        );
    }

    // =====================================================================
    // Render Delegation
    // =====================================================================

    renderClusters() {

        if (!this.clusterRenderer) {
            return;
        }

        this.clusterRenderer.render(
            this.clusterLayer,
            this.state
        );
    }

    renderEdges() {

        if (!this.edgeRenderer) {
            return;
        }

        this.edgeRenderer.render(
            this.edgeLayer,
            this.state
        );
    }

    renderNodes() {

        if (!this.nodeRenderer) {
            return;
        }

        this.nodeRenderer.render(
            this.nodeLayer,
            this.state
        );
    }

    renderOverlays() {

        while (
            this.overlayLayer.firstChild
        ) {
            this.overlayLayer.removeChild(
                this.overlayLayer.firstChild
            );
        }
    }

    // =====================================================================
    // Layer Utilities
    // =====================================================================

    clearLayers() {

        this._clear(this.clusterLayer);
        this._clear(this.edgeLayer);
        this._clear(this.nodeLayer);
        this._clear(this.overlayLayer);
    }

    _clear(layer) {

        while (layer.firstChild) {

            layer.removeChild(
                layer.firstChild
            );
        }
    }

    // =====================================================================
    // Viewport
    // =====================================================================

    updateViewport() {

        const zoom =
            this.state?.zoom ?? 1;

        const panX =
            this.state?.panX ?? 0;

        const panY =
            this.state?.panY ?? 0;

        this.viewport.setAttribute(
            "transform",
            `translate(${panX},${panY}) scale(${zoom})`
        );
    }

    // =====================================================================
    // Bounds
    // =====================================================================

    getGraphBounds() {

        const nodes =
            this.state?.graph?.nodes ?? [];

        if (!nodes.length) {

            return {
                minX: 0,
                minY: 0,
                maxX: 0,
                maxY: 0,
                width: 0,
                height: 0,
            };
        }

        let minX = Infinity;
        let minY = Infinity;
        let maxX = -Infinity;
        let maxY = -Infinity;

        for (const node of nodes) {

            const x =
                node.position?.x ?? 0;

            const y =
                node.position?.y ?? 0;

            minX = Math.min(minX, x);
            minY = Math.min(minY, y);

            maxX = Math.max(maxX, x);
            maxY = Math.max(maxY, y);
        }

        return {

            minX,
            minY,

            maxX,
            maxY,

            width: maxX - minX,
            height: maxY - minY,
        };
    }

    // =====================================================================
    // Fit To View
    // =====================================================================

    fitToViewport(padding = 80) {

        const bounds =
            this.getGraphBounds();

        const svgRect =
            this.svg.getBoundingClientRect();

        if (
            bounds.width === 0 ||
            bounds.height === 0
        ) {
            return;
        }

        const scaleX =
            (svgRect.width - padding * 2) /
            bounds.width;

        const scaleY =
            (svgRect.height - padding * 2) /
            bounds.height;

        const scale =
            Math.min(scaleX, scaleY);

        this.state.setZoom(scale);

        const centerX =
            bounds.minX +
            bounds.width / 2;

        const centerY =
            bounds.minY +
            bounds.height / 2;

        const panX =
            svgRect.width / 2 -
            centerX * scale;

        const panY =
            svgRect.height / 2 -
            centerY * scale;

        this.state.setPan(
            panX,
            panY
        );
    }

    // =====================================================================
    // Helpers
    // =====================================================================

    _resolveElement(value) {

        if (value instanceof Element) {
            return value;
        }

        const element =
            document.getElementById(value);

        if (!element) {

            throw new Error(
                `Renderer element not found: ${value}`
            );
        }

        return element;
    }
}