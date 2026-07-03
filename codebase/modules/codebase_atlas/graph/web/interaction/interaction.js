// web/interaction/interaction.js

import {
    SELECTION,
    isMultiSelectKey,
} from "../core/constants.js";

import {
    INTERACTION_EVENTS,
} from "./events.js";

/**
 * ============================================================================
 * GraphInteractionManager
 * ============================================================================
 *
 * Composes:
 *
 *   SelectionManager
 *   GraphEventController
 *   DragController
 *   ViewportController
 *   GraphNavigation
 *
 * Owns:
 *   - interaction wiring
 *   - default interaction behavior
 *
 * Does NOT own:
 *   - rendering
 *   - graph data
 *   - viewport implementation
 *   - selection implementation
 *
 * ============================================================================
 */

export class GraphInteractionManager {

    constructor(options = {}) {

        this.state =
            options.state;

        this.renderer =
            options.renderer;

        this.viewport =
            options.viewport;

        this.navigation =
            options.navigation;

        this.selection =
            options.selection;

        this.events =
            options.events;

        this.drag =
            options.drag;

        this.viewer =
            options.viewer;

        this.initialize();
    }

    /* ===================================================================== */
    /* Lifecycle                                                              */
    /* ===================================================================== */

    initialize() {

        this.bindSelection();

        this.bindNavigation();

        this.bindViewport();

        this.bindBoxSelect();
    }

    destroy() {

        if (
            this.events?.destroy
        ) {

            this.events.destroy();
        }
    }

    /* ===================================================================== */
    /* Selection                                                              */
    /* ===================================================================== */

    bindSelection() {

        if (
            !this.events ||
            !this.selection
        ) {
            return;
        }

        this.events.on(
            INTERACTION_EVENTS.NODE_CLICK,
            event => {

                const nodeId =
                    event.target.id;

                const additive =
                    isMultiSelectKey(
                        event.originalEvent
                    );

                if (additive) {

                    this.selection
                        .toggleNode(
                            nodeId
                        );

                } else {

                    this.selection
                        .selectNode(
                            nodeId
                        );
                }

                this.refresh();
            }
        );

        this.events.on(
            INTERACTION_EVENTS.NODE_EXPAND_CLICK,
            event => {

                const nodeId =
                    event.target.id;

                const node =
                    this.state?.getNode?.(
                        nodeId
                    );

                if (!node) {
                    return;
                }

                if (node.scope !== "file") {
                    return;
                }

                if (this.state.isExpanded(nodeId)) {

                    this.state.collapseNode(nodeId);
                    this.viewer?.collapseNode?.(nodeId);

                } else {

                    this.viewer?.expandNode?.(nodeId);
                }

                this.refresh();
            }
        );

        this.events.on(
            INTERACTION_EVENTS.EDGE_CLICK,
            event => {

                const edgeId =
                    event.target.id;

                const additive =
                    isMultiSelectKey(
                        event.originalEvent
                    );

                if (additive) {

                    this.selection
                        .toggleEdge(
                            edgeId
                        );

                } else {

                    this.selection
                        .selectEdge(
                            edgeId
                        );
                }

                this.refresh();
            }
        );

        this.events.on(
            INTERACTION_EVENTS.CLUSTER_CLICK,
            event => {

                const clusterId =
                    event.target.id;

                const additive =
                    isMultiSelectKey(
                        event.originalEvent
                    );

                if (additive) {

                    this.selection
                        .toggleCluster(
                            clusterId
                        );

                } else {

                    this.selection
                        .selectCluster(
                            clusterId
                        );
                }

                this.refresh();
            }
        );

        this.events.on(
            INTERACTION_EVENTS.BACKGROUND_CLICK,
            () => {

                if (
                    this._suppressNextClick
                ) {

                    this._suppressNextClick =
                        false;

                    return;
                }

                this.selection.clear();

                this.refresh();
            }
        );

        if (this.state?.subscribe) {

            this.state.subscribe(
                "nodes:moved",
                () => {

                    this.selection.clear();

                    this.refresh();
                }
            );
        }
    }

    /* ===================================================================== */
    /* Navigation                                                             */
    /* ===================================================================== */

    bindNavigation() {

        if (
            !this.events ||
            !this.navigation
        ) {
            return;
        }

        this.events.on(
            INTERACTION_EVENTS.DOUBLE_CLICK,
            event => {

                if (
                    event.target.type ===
                    "node"
                ) {

                    this.navigation
                        .zoomToNode(
                            event.target.id
                        );

                    return;
                }

                if (
                    event.target.type ===
                    "cluster"
                ) {

                    this.navigation
                        .zoomToCluster(
                            event.target.id
                        );
                }
            }
        );
    }

    /* ===================================================================== */
    /* Viewport                                                               */
    /* ===================================================================== */

    bindViewport() {

        if (
            !this.events ||
            !this.viewport
        ) {
            return;
        }

        this.events.on(
            INTERACTION_EVENTS.WHEEL,
            event => {

                const wheelEvent =
                    event.originalEvent;

                wheelEvent.preventDefault();

                const factor =
                    wheelEvent.deltaY < 0
                        ? 1.1
                        : 1 / 1.1;

                this.viewport.setZoom(
                    this.viewport.zoom *
                        factor,
                    wheelEvent.clientX,
                    wheelEvent.clientY
                );
            }
        );

        this._panning = false;
        this._panLastX = 0;
        this._panLastY = 0;
        this._suppressNextClick = false;
        this._spaceDown = false;

        const isPanTrigger = event => {

            if (
                event.target?.type !==
                "background"
            ) {
                return false;
            }

            if (event.shiftKey) {
                return false;
            }

            if (event.button === 1) {
                return true;
            }

            if (
                event.button === 0 &&
                this._spaceDown
            ) {
                return true;
            }

            if (
                event.button === 0 &&
                !event.target?.id
            ) {
                return true;
            }

            return false;
        };

        this.events.on(
            INTERACTION_EVENTS.POINTER_DOWN,
            event => {

                if (!isPanTrigger(event)) {
                    return;
                }

                event.originalEvent
                    .preventDefault?.();

                this._panning = true;
                this._panLastX =
                    event.clientX;
                this._panLastY =
                    event.clientY;
                this._suppressNextClick =
                    true;
            }
        );

        this.events.on(
            INTERACTION_EVENTS.POINTER_MOVE,
            event => {

                if (!this._panning) {
                    return;
                }

                const dx =
                    event.clientX -
                    this._panLastX;

                const dy =
                    event.clientY -
                    this._panLastY;

                this._panLastX =
                    event.clientX;

                this._panLastY =
                    event.clientY;

                this.viewport.panBy(
                    dx,
                    dy
                );
            }
        );

        this.events.on(
            INTERACTION_EVENTS.POINTER_UP,
            () => {

                this._panning = false;
            }
        );

        this.events.on(
            INTERACTION_EVENTS.KEY_DOWN,
            event => {

                if (
                    event.code ===
                        "Space" ||
                    event.key === " "
                ) {
                    this._spaceDown = true;
                }
            }
        );

        this.events.on(
            INTERACTION_EVENTS.KEY_UP,
            event => {

                if (
                    event.code ===
                        "Space" ||
                    event.key === " "
                ) {
                    this._spaceDown = false;
                }
            }
        );
    }

    /* ===================================================================== */
    /* Box Select                                                             */
    /* ===================================================================== */

    bindBoxSelect() {

        if (
            !this.events ||
            !this.viewport ||
            !this.selection
        ) {
            return;
        }

        this._boxSelecting = false;
        this._boxStartX = 0;
        this._boxStartY = 0;
        this._boxRect = null;
        this._boxEngaged = false;

        const SVG_NS =
            "http://www.w3.org/2000/svg";

        const overlayLayer =
            document.getElementById(
                "overlay-layer"
            );

        const minSize =
            SELECTION.BOX_SELECT_THRESHOLD_PX /
            Math.max(
                this.viewport.zoom,
                0.01
            );

        const getBoxRect = (clientX, clientY) => {

            const start =
                this.viewport.screenToGraph(
                    this._boxStartClientX,
                    this._boxStartClientY
                );

            const current =
                this.viewport.screenToGraph(
                    clientX,
                    clientY
                );

            const x =
                Math.min(start.x, current.x);

            const y =
                Math.min(start.y, current.y);

            const w =
                Math.abs(
                    current.x - start.x
                );

            const h =
                Math.abs(
                    current.y - start.y
                );

            return { x, y, w, h };
        };

        const updateBoxRect = (
            clientX,
            clientY
        ) => {

            if (!this._boxRect) {
                return;
            }

            const { x, y, w, h } =
                getBoxRect(clientX, clientY);

            this._boxRect.setAttribute(
                "x",
                x
            );

            this._boxRect.setAttribute(
                "y",
                y
            );

            this._boxRect.setAttribute(
                "width",
                w
            );

            this._boxRect.setAttribute(
                "height",
                h
            );

            if (
                !this._boxEngaged &&
                (w > minSize || h > minSize)
            ) {

                this._boxEngaged = true;
            }
        };

        const isBoxTrigger = event => {

            if (
                event.target?.type !==
                "background"
            ) {
                return false;
            }

            if (event.button !== 0) {
                return false;
            }

            if (!event.shiftKey) {
                return false;
            }

            return true;
        };

        this.events.on(
            INTERACTION_EVENTS.POINTER_DOWN,
            event => {

                if (
                    !isBoxTrigger(event)
                ) {
                    return;
                }

                event.originalEvent
                    .preventDefault?.();

                this._boxSelecting = true;
                this._boxEngaged = false;
                this._boxStartClientX =
                    event.clientX;
                this._boxStartClientY =
                    event.clientY;

                this._suppressNextClick = true;

                if (
                    overlayLayer &&
                    !this._boxRect
                ) {

                    const rect =
                        document.createElementNS(
                            SVG_NS,
                            "rect"
                        );

                    rect.setAttribute(
                        "id",
                        "selection-box"
                    );

                    rect.setAttribute(
                        "x",
                        0
                    );

                    rect.setAttribute(
                        "y",
                        0
                    );

                    rect.setAttribute(
                        "width",
                        0
                    );

                    rect.setAttribute(
                        "height",
                        0
                    );

                    overlayLayer.appendChild(
                        rect
                    );

                    this._boxRect = rect;
                }
            }
        );

        this.events.on(
            INTERACTION_EVENTS.POINTER_MOVE,
            event => {

                if (!this._boxSelecting) {
                    return;
                }

                updateBoxRect(
                    event.clientX,
                    event.clientY
                );

                if (!this._boxEngaged) {
                    return;
                }

                const { x, y, w, h } =
                    getBoxRect(
                        event.clientX,
                        event.clientY
                    );

                if (w <= 0 || h <= 0) {
                    return;
                }

                const xMax = x + w;
                const yMax = y + h;

                const matched = [];

                for (const node of this
                    .state.graph.nodes) {

                    const nx =
                        node.position?.x;

                    const ny =
                        node.position?.y;

                    if (
                        nx == null ||
                        ny == null
                    ) {
                        continue;
                    }

                    if (
                        nx >= x &&
                        nx <= xMax &&
                        ny >= y &&
                        ny <= yMax
                    ) {

                        matched.push(
                            node.id
                        );
                    }
                }

                this.state.setPreviewSelectedNodes(
                    matched
                );

                this.refresh();
            }
        );

        const finishBoxSelect = event => {

            if (!this._boxSelecting) {
                return;
            }

            this._boxSelecting = false;

            if (this._boxRect) {

                this._boxRect.remove();
                this._boxRect = null;
            }

            this.state.clearPreviewSelectedNodes();

            if (
                !this._boxEngaged ||
                !event
            ) {
                this.refresh();
                return;
            }

            const { x, y, w, h } =
                getBoxRect(
                    event.clientX,
                    event.clientY
                );

            if (
                w <= 0 ||
                h <= 0
            ) {
                this.refresh();
                return;
            }

            const xMax = x + w;
            const yMax = y + h;

            const matched = [];

            for (const node of this
                .state.graph.nodes) {

                const nx =
                    node.position?.x;

                const ny =
                    node.position?.y;

                if (
                    nx == null ||
                    ny == null
                ) {
                    continue;
                }

                if (
                    nx >= x &&
                    nx <= xMax &&
                    ny >= y &&
                    ny <= yMax
                ) {

                    matched.push(
                        node.id
                    );
                }
            }

            if (matched.length) {

                this.selection.selectNodes(
                    matched,
                    true
                );
            }

            this.refresh();
        };

        this.events.on(
            INTERACTION_EVENTS.POINTER_UP,
            event => {

                finishBoxSelect(event);
            }
        );

        const resetStaleSuppress = () => {

            if (
                !this._panning &&
                !this._boxSelecting &&
                this._suppressNextClick
            ) {
                this._suppressNextClick =
                    false;
            }
        };

        this.events.on(
            INTERACTION_EVENTS.POINTER_DOWN,
            resetStaleSuppress
        );
    }

    /* ===================================================================== */
    /* Helpers                                                                */
    /* ===================================================================== */

    refresh() {

        if (
            this.renderer?.render
        ) {

            this.renderer.render();
        }
    }

    /* ===================================================================== */
    /* Accessors                                                              */
    /* ===================================================================== */

    getSelection() {

        return this.selection;
    }

    getViewport() {

        return this.viewport;
    }

    getNavigation() {

        return this.navigation;
    }

    getDragController() {

        return this.drag;
    }

    getEventController() {

        return this.events;
    }
}