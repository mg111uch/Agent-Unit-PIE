// web/interaction/drag.js

import { DRAG } from "../core/constants.js";

import {
    INTERACTION_EVENTS,
} from "./events.js";

/**
 * ============================================================================
 * DragController
 * ============================================================================
 */

export class DragController {

    constructor(options = {}) {

        this.state =
            options.state;

        this.renderer =
            options.renderer;

        this.selection =
            options.selection;

        this.events =
            options.events;

        this.viewport =
            options.viewport;

        this.dragging = false;

        this.dragTarget = null;

        this.startPointer = null;

        this.lastPointer = null;

        this.draggedNodes =
            new Set();

        this._bindEvents();
    }

    /* ===================================================================== */
    /* Event Wiring                                                           */
    /* ===================================================================== */

    _bindEvents() {

        if (!this.events) {
            return;
        }

        this.events.on(
            INTERACTION_EVENTS.POINTER_DOWN,
            this.onPointerDown.bind(this)
        );

        this.events.on(
            INTERACTION_EVENTS.POINTER_MOVE,
            this.onPointerMove.bind(this)
        );

        this.events.on(
            INTERACTION_EVENTS.POINTER_UP,
            this.onPointerUp.bind(this)
        );
    }

    /* ===================================================================== */
    /* Pointer Down                                                           */
    /* ===================================================================== */

    onPointerDown(event) {

        if (
            event.button !== 0
        ) {
            return;
        }

        if (
            event.target?.type !==
            "node"
        ) {
            return;
        }

        const nodeId =
            event.target.id;

        this.dragTarget =
            nodeId;

        this.startPointer = {

            x: event.graphX,
            y: event.graphY,
        };

        this.lastPointer = {

            x: event.graphX,
            y: event.graphY,
        };

        this.dragging = false;

        this.draggedNodes.clear();

        if (
            this.selection?.isNodeSelected(
                nodeId
            )
        ) {

            const selected =
                this.selection
                    .getSelectedNodes();

            for (const id of selected) {

                this.draggedNodes.add(
                    id
                );
            }

        } else {

            this.draggedNodes.add(
                nodeId
            );
        }
    }

    /* ===================================================================== */
    /* Pointer Move                                                           */
    /* ===================================================================== */

    onPointerMove(event) {

        if (!this.dragTarget) {
            return;
        }

        const dx =
            event.graphX -
            this.startPointer.x;

        const dy =
            event.graphY -
            this.startPointer.y;

        if (!this.dragging) {

            const distance =
                Math.sqrt(
                    dx * dx +
                    dy * dy
                );

            if (
                distance <
                DRAG.START_THRESHOLD_PX
            ) {
                return;
            }

            this.dragging = true;
        }

        const moveX =
            event.graphX -
            this.lastPointer.x;

        const moveY =
            event.graphY -
            this.lastPointer.y;

        this.moveNodes(
            moveX,
            moveY
        );

        this.lastPointer = {

            x: event.graphX,
            y: event.graphY,
        };
    }

    /* ===================================================================== */
    /* Pointer Up                                                             */
    /* ===================================================================== */

    onPointerUp() {

        if (
            this.dragging
        ) {

            this.commitDrag();
        }

        this.reset();
    }

    /* ===================================================================== */
    /* Movement                                                               */
    /* ===================================================================== */

    moveNodes(
        deltaX,
        deltaY
    ) {

        for (
            const nodeId
            of this.draggedNodes
        ) {

            const node =
                this.state.getNode(
                    nodeId
                );

            if (!node) {
                continue;
            }

            if (
                !node.position
            ) {

                node.position = {
                    x: 0,
                    y: 0,
                };
            }

            node.position.x +=
                deltaX;

            node.position.y +=
                deltaY;

            if (
                DRAG.ENABLE_GRID_SNAP
            ) {

                node.position.x =
                    this.snap(
                        node.position.x
                    );

                node.position.y =
                    this.snap(
                        node.position.y
                    );
            }
        }

        this.requestRender();
    }

    snap(value) {

        const size =
            DRAG.GRID_SNAP_SIZE;

        if (!size) {
            return value;
        }

        return (
            Math.round(
                value / size
            ) * size
        );
    }

    /* ===================================================================== */
    /* Rendering                                                              */
    /* ===================================================================== */

    requestRender() {

        if (
            this.renderer?.render
        ) {

            this.renderer.render();
        }
    }

    commitDrag() {

        if (
            this.state?.emit
        ) {

            this.state.emit(
                "nodes:moved",
                {
                    nodeIds:
                        Array.from(
                            this.draggedNodes
                        ),
                }
            );
        }
    }

    /* ===================================================================== */
    /* State                                                                  */
    /* ===================================================================== */

    reset() {

        this.dragging = false;

        this.dragTarget = null;

        this.startPointer = null;

        this.lastPointer = null;

        this.draggedNodes.clear();
    }

    isDragging() {

        return this.dragging;
    }

    getDraggedNodes() {

        return Array.from(
            this.draggedNodes
        );
    }
}