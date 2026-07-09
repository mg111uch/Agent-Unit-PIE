// web/render/renderer.js

import { EventEmitter, GRAPH_EVENTS }
    from "../core/events.js";

import { ViewportCuller }
    from "./viewport_culler.js";
import {
    computeNodeBounds,
    expandBounds
} from "../utils/geometry.js";
function yieldToBrowser() {
    return new Promise(resolve => {
        if (
            typeof requestAnimationFrame ===
            "function"
        ) {
            requestAnimationFrame(
                () => resolve()
            );
        } else {
            setTimeout(
                () => resolve(),
                16
            );
        }
    });
}

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
        this.culler = new ViewportCuller({
            svg: this.svg,
            state: this.state,
        });
        this.cullOnRender =
            options.cullOnRender ?? true;
        this.nodeRenderer = null;
        this.edgeRenderer = null;
        this.clusterRenderer = null;
        this.renderCount = 0;
        // Tracks the previous selection so we can
        // toggle classes on both the old and the new
        // selected element on a SELECTION_CHANGED event.
        // The state event payload only carries the new
        // id; we have to remember the old one ourselves.
        this._lastSelection = {
            nodeId: null,
            edgeId: null,
            clusterId: null,
        };
        this._bindStateEvents();
    }
    // Dependency Injection
    setNodeRenderer(renderer) {
        this.nodeRenderer = renderer;
    }
    setEdgeRenderer(renderer) {
        this.edgeRenderer = renderer;
    }
    setClusterRenderer(renderer) {
        this.clusterRenderer = renderer;
    }
    // State Binding
    _bindStateEvents() {
        if (!this.state) {
            return;
        }
        this.state.on(
            GRAPH_EVENTS.VIEWPORT_CHANGED,
            () => this.applyViewport()
        );
        this.state.on(
            GRAPH_EVENTS.SELECTION_CHANGED,
            () => this.updateSelection()
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
            GRAPH_EVENTS.NODE_EXPANDED,
            () => this.render()
        );
        this.state.on(
            GRAPH_EVENTS.NODE_COLLAPSED,
            () => this.render()
        );
        this.state.on(
            GRAPH_EVENTS.STATE_CHANGED,
            () => this.render()
        );
    }
    // Initial Render
    initialize() {
        this.updateViewport();
        return this;
    }
    /**
     * Run `callback` once the SVG has a non-zero
     * on-screen size.  The first call to `render()`
     * happens before the browser has measured the
     * SVG, which makes `ViewportCuller` fall back to
     * the full graph and defeats culling for the
     * very paint that matters most.  Defer until the
     * SVG has real width/height.
     *
     * Yields to the browser between polls so we do
     * not spin.  Caps the number of polls to avoid
     * hanging if the SVG never gets a size.
     */
    whenMeasured(callback) {
        const MAX_POLLS = 30;
        let polls = 0;
        const check = () => {
            if (!this.svg) {
                callback();
                return;
            }
            const rect =
                this.svg.getBoundingClientRect();
            if (
                rect.width > 0 &&
                rect.height > 0
            ) {
                callback();
                return;
            }
            polls += 1;
            if (polls >= MAX_POLLS) {
                callback();
                return;
            }
            if (
                typeof requestAnimationFrame ===
                "function"
            ) {
                requestAnimationFrame(check);
            } else {
                setTimeout(check, 16);
            }
        };
        check();
    }
    // Main Render Pipeline
    render() {
        this.emit(
            GRAPH_EVENTS.BEFORE_RENDER,
            {
                renderer: this,
            }
        );
        this.clearLayers();
        const culled = this._cullForRender();
        this.renderClusters(culled.clusters);
        this.renderExpandGroups();
        this.renderEdges(culled.edges);
        this.renderNodes(culled.nodes);
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
    // Targeted Selection Update
    //
    // Replaces a full re-render on SELECTION_CHANGED.
    // Toggles a CSS class on the previously selected
    // element (if any) and on the newly selected element
    // (if any). The actual visual change is driven by
    // CSS rules in graph_viewer.html that override the
    // presentation attributes set during initial render.
    //
    // Cost: O(1) DOM mutations, no SVG element creation,
    // no layout, no attribute writes for the rest of the
    // graph.
    updateSelection() {
        if (!this.state) {
            return;
        }
        const current = {
            nodeId: this.state.selectedNodeId,
            edgeId: this.state.selectedEdgeId,
            clusterId: this.state.selectedClusterId,
        };
        const previous = this._lastSelection;
        this._toggleSelectedClass(
            this.nodeRenderer,
            previous.nodeId,
            current.nodeId
        );
        this._toggleSelectedClass(
            this.edgeRenderer,
            previous.edgeId,
            current.edgeId
        );
        this._toggleSelectedClass(
            this.clusterRenderer,
            previous.clusterId,
            current.clusterId
        );
        this._lastSelection = current;
    }
    _toggleSelectedClass(
        renderer,
        previousId,
        currentId
    ) {
        if (!renderer || typeof renderer.getElement !== "function") {
            return;
        }
        if (previousId && previousId !== currentId) {
            const oldElement =
                renderer.getElement(previousId);
            if (oldElement) {
                oldElement.classList.remove(
                    "selected"
                );
            }
        }
        if (currentId) {
            const newElement =
                renderer.getElement(currentId);
            if (newElement) {
                newElement.classList.add(
                    "selected"
                );
            }
        }
    }
    // Viewport Culling
    /**
     * Returns the subset of nodes, edges, and
     * clusters that intersect the visible graph
     * region.  Falls back to the full graph when
     * the SVG has no measured size yet (e.g. before
     * first layout).
     */
    _cullForRender() {
        if (!this.state?.graph) {
            return {
                nodes: [],
                edges: [],
                clusters: [],
                culled: false,
            };
        }
        if (
            !this.cullOnRender ||
            !this.culler
        ) {
            return {
                nodes:
                    this.state.graph.nodes ?? [],
                edges:
                    this.state.graph.edges ?? [],
                clusters:
                    this.state.graph.clusters ?? [],
                culled: false,
            };
        }
        return this.culler.cull(
            this.state.graph
        );
    }
    /**
     * Updates the SVG viewport transform and re-renders
     * the visible subset.  Bound to VIEWPORT_CHANGED,
     * which fires on pan and zoom.
     *
     * Work per call is O(visible), not O(total graph),
     * so panning stays responsive even for graphs that
     * have tens of thousands of nodes/edges.
     */
    applyViewport() {
        this.updateViewport();
        if (!this.state?.graph) {
            return;
        }
        this.render();
    }
    // Chunked Render (yields to the browser between batches)
    async renderChunked(chunkSize = 200) {
        this.emit(
            GRAPH_EVENTS.BEFORE_RENDER,
            {
                renderer: this,
            }
        );
        this.clearLayers();
        const culled = this._cullForRender();
        this.renderClusters(culled.clusters);
        const edges = culled.edges;
        for (
            let i = 0;
            i < edges.length;
            i += chunkSize
        ) {
            this.renderEdgesSubset(
                edges.slice(i, i + chunkSize)
            );
            await yieldToBrowser();
        }
        const nodes = culled.nodes;
        for (
            let i = 0;
            i < nodes.length;
            i += chunkSize
        ) {
            this.renderNodesSubset(
                nodes.slice(i, i + chunkSize)
            );
            await yieldToBrowser();
        }
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
    renderEdgesSubset(edges) {
        if (!this.edgeRenderer) {
            return;
        }
        this.edgeRenderer.render(
            this.edgeLayer,
            this.state,
            edges
        );
    }
    renderNodesSubset(nodes) {
        if (!this.nodeRenderer) {
            return;
        }
        this.nodeRenderer.render(
            this.nodeLayer,
            this.state,
            nodes
        );
    }
    // Render Delegation
    renderClusters(items) {
        if (!this.clusterRenderer) {
            return;
        }
        this.clusterRenderer.render(
            this.clusterLayer,
            this.state,
            items
        );
    }
    renderEdges(items) {
        if (!this.edgeRenderer) {
            return;
        }
        this.edgeRenderer.render(
            this.edgeLayer,
            this.state,
            items
        );
    }
    renderNodes(items) {
        if (!this.nodeRenderer) {
            return;
        }
        this.nodeRenderer.render(
            this.nodeLayer,
            this.state,
            items
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
    renderExpandGroups() {
        if (
            !this.state?.getExpandGroups
        ) {
            return;
        }
        const groups =
            this.state.getExpandGroups();
        if (!groups.size) {
            return;
        }
        const SVG_NS =
            "http://www.w3.org/2000/svg";
        const PADDING = 20;
        const fragment =
            document.createDocumentFragment();
        for (const [
            parentId,
            group,
        ] of groups) {
            const parent =
                this.state.getNode(
                    parentId
                );
            if (!parent) {
                continue;
            }
            const childNodes =
                group.childNodeIds
                    .map(
                        id =>
                            this.state
                                .getNode(id)
                    )
                    .filter(Boolean);
            const allNodes = [
                parent,
                ...childNodes,
            ];
            const bounds =
                expandBounds(
                    computeNodeBounds(
                        allNodes
                    ),
                    PADDING
                );
            const rect =
                document.createElementNS(
                    SVG_NS,
                    "rect"
                );
            rect.classList.add(
                "expand-group-bg"
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
                10
            );
            fragment.appendChild(
                rect
            );
        }
        this.clusterLayer.appendChild(
            fragment
        );
    }
    // Layer Utilities
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
    // Viewport
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
    // Bounds
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
    // Fit To View
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
    // Helpers
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