// web/interaction/events.js

import { EventEmitter }
    from "../core/events.js";

/**
 * ============================================================================
 * GraphEventController
 * ============================================================================
 *
 * Converts browser DOM events into graph events.
 *
 * Owns:
 *   - pointer listeners
 *   - wheel listeners
 *   - keyboard listeners
 *
 * Does NOT own:
 *   - selection
 *   - dragging
 *   - viewport state
 *   - rendering
 *
 * ============================================================================
 */
export const INTERACTION_EVENTS = Object.freeze({
    POINTER_DOWN:
        "pointer:down",
    POINTER_MOVE:
        "pointer:move",
    POINTER_UP:
        "pointer:up",
    POINTER_ENTER:
        "pointer:enter",
    POINTER_LEAVE:
        "pointer:leave",
    CLICK:
        "graph:click",
    DOUBLE_CLICK:
        "graph:dblclick",
    WHEEL:
        "graph:wheel",
    KEY_DOWN:
        "keyboard:down",
    KEY_UP:
        "keyboard:up",
    BACKGROUND_CLICK:
        "background:click",
    NODE_CLICK:
        "node:click",
    NODE_EXPAND_CLICK:
        "node:expand-click",
    EDGE_CLICK:
        "edge:click",
    CLUSTER_CLICK:
        "cluster:click",
});

/**
 * ============================================================================
 * GraphEventController
 * ============================================================================
 */
export class GraphEventController extends EventEmitter {
    constructor(options = {}) {
        super();
        this.svg =
            this._resolveElement(
                options.svg ?? "graph-svg"
            );
        this.viewport =
            options.viewport;
        this.state =
            options.state;
        this.enabled = false;
        this.boundHandlers = {};
    }
    /* Lifecycle */
    initialize() {
        if (this.enabled) {
            return;
        }
        this.enabled = true;
        this._bindEvents();
    }
    destroy() {
        if (!this.enabled) {
            return;
        }
        this.enabled = false;
        this._unbindEvents();
    }
    /* Binding */
    _bindEvents() {
        this.boundHandlers.pointerDown =
            this._onPointerDown.bind(this);
        this.boundHandlers.pointerMove =
            this._onPointerMove.bind(this);
        this.boundHandlers.pointerUp =
            this._onPointerUp.bind(this);
        this.boundHandlers.click =
            this._onClick.bind(this);
        this.boundHandlers.dblClick =
            this._onDoubleClick.bind(this);
        this.boundHandlers.wheel =
            this._onWheel.bind(this);
        this.boundHandlers.keyDown =
            this._onKeyDown.bind(this);
        this.boundHandlers.keyUp =
            this._onKeyUp.bind(this);
        this.svg.addEventListener(
            "pointerdown",
            this.boundHandlers.pointerDown
        );
        window.addEventListener(
            "pointermove",
            this.boundHandlers.pointerMove
        );
        window.addEventListener(
            "pointerup",
            this.boundHandlers.pointerUp
        );
        this.svg.addEventListener(
            "click",
            this.boundHandlers.click
        );
        this.svg.addEventListener(
            "dblclick",
            this.boundHandlers.dblClick
        );
        this.svg.addEventListener(
            "wheel",
            this.boundHandlers.wheel,
            { passive: false }
        );
        window.addEventListener(
            "keydown",
            this.boundHandlers.keyDown
        );
        window.addEventListener(
            "keyup",
            this.boundHandlers.keyUp
        );
    }
    _unbindEvents() {
        this.svg.removeEventListener(
            "pointerdown",
            this.boundHandlers.pointerDown
        );
        window.removeEventListener(
            "pointermove",
            this.boundHandlers.pointerMove
        );
        window.removeEventListener(
            "pointerup",
            this.boundHandlers.pointerUp
        );
        this.svg.removeEventListener(
            "click",
            this.boundHandlers.click
        );
        this.svg.removeEventListener(
            "dblclick",
            this.boundHandlers.dblClick
        );
        this.svg.removeEventListener(
            "wheel",
            this.boundHandlers.wheel
        );
        window.removeEventListener(
            "keydown",
            this.boundHandlers.keyDown
        );
        window.removeEventListener(
            "keyup",
            this.boundHandlers.keyUp
        );
    }
    /* Event Helpers */
    createGraphEvent(event) {
        const point =
            this.viewport
                ? this.viewport.screenToGraph(
                    event.clientX,
                    event.clientY
                )
                : {
                    x: event.clientX,
                    y: event.clientY,
                };
        return {
            originalEvent:
                event,
            graphX:
                point.x,
            graphY:
                point.y,
            clientX:
                event.clientX,
            clientY:
                event.clientY,
            target:
                this.resolveTarget(
                    event.target
                ),
            ctrlKey:
                event.ctrlKey,
            metaKey:
                event.metaKey,
            shiftKey:
                event.shiftKey,
            altKey:
                event.altKey,
            button:
                event.button,
        };
    }
    resolveTarget(element) {
        if (!element) {
            return null;
        }
        const node =
            element.closest?.(
                "[data-node-id]"
            );
        if (node) {
            return {
                type: "node",
                id:
                    node.dataset.nodeId,
            };
        }
        const edge =
            element.closest?.(
                "[data-edge-id]"
            );
        if (edge) {
            return {
                type: "edge",
                id:
                    edge.dataset.edgeId,
            };
        }
        const cluster =
            element.closest?.(
                "[data-cluster-id]"
            );
        if (cluster) {
            return {
                type: "cluster",
                id:
                    cluster.dataset.clusterId,
            };
        }
        return {
            type:
                "background",
            id: null,
        };
    }
    /* Pointer Events */
    _onPointerDown(event) {
        this.emit(
            INTERACTION_EVENTS.POINTER_DOWN,
            this.createGraphEvent(
                event
            )
        );
    }
    _onPointerMove(event) {
        this.emit(
            INTERACTION_EVENTS.POINTER_MOVE,
            this.createGraphEvent(
                event
            )
        );
    }
    _onPointerUp(event) {
        this.emit(
            INTERACTION_EVENTS.POINTER_UP,
            this.createGraphEvent(
                event
            )
        );
    }
    /* Clicks */
    _onClick(event) {
        const graphEvent =
            this.createGraphEvent(
                event
            );
        const expandTarget =
            event.target.closest?.(
                ".expand-btn"
            );
        if (
            expandTarget &&
            graphEvent.target.type === "node"
        ) {
            this.emit(
                INTERACTION_EVENTS.NODE_EXPAND_CLICK,
                graphEvent
            );
            return;
        }
        this.emit(
            INTERACTION_EVENTS.CLICK,
            graphEvent
        );
        switch (
            graphEvent.target.type
        ) {
            case "node":
                this.emit(
                    INTERACTION_EVENTS.NODE_CLICK,
                    graphEvent
                );
                break;
            case "edge":
                this.emit(
                    INTERACTION_EVENTS.EDGE_CLICK,
                    graphEvent
                );
                break;
            case "cluster":
                this.emit(
                    INTERACTION_EVENTS.CLUSTER_CLICK,
                    graphEvent
                );
                break;
            default:
                this.emit(
                    INTERACTION_EVENTS.BACKGROUND_CLICK,
                    graphEvent
                );
        }
    }
    _onDoubleClick(event) {
        this.emit(
            INTERACTION_EVENTS.DOUBLE_CLICK,
            this.createGraphEvent(
                event
            )
        );
    }
    /* Wheel */
    _onWheel(event) {
        this.emit(
            INTERACTION_EVENTS.WHEEL,
            this.createGraphEvent(
                event
            )
        );
    }
    /* Keyboard */
    _onKeyDown(event) {
        this.emit(
            INTERACTION_EVENTS.KEY_DOWN,
            event
        );
    }
    _onKeyUp(event) {
        this.emit(
            INTERACTION_EVENTS.KEY_UP,
            event
        );
    }
    /* Helpers */
    _resolveElement(value) {
        if (
            value instanceof Element
        ) {
            return value;
        }
        const element =
            document.getElementById(
                value
            );
        if (!element) {
            throw new Error(
                `Element not found: ${value}`
            );
        }
        return element;
    }
}