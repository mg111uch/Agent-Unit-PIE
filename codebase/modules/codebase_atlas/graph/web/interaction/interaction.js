// web/interaction/interaction.js

import {
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

        this.initialize();
    }

    /* ===================================================================== */
    /* Lifecycle                                                              */
    /* ===================================================================== */

    initialize() {

        this.bindSelection();

        this.bindNavigation();

        this.bindViewport();
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

                this.selection.clear();

                this.refresh();
            }
        );
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