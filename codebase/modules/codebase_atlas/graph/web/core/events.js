// web/core/events.js

/**
 * ============================================================================
 * EventEmitter
 * ============================================================================
 *
 * Lightweight publish/subscribe system used throughout the graph engine.
 *
 * Features:
 *   - on()
 *   - once()
 *   - off()
 *   - emit()
 *   - clear()
 *   - listenerCount()
 *
 * No DOM dependencies.
 * ============================================================================
 */

export class EventEmitter {

    constructor() {
        this._listeners = new Map();
    }

    /**
     * Subscribe to an event.
     *
     * @param {string} eventName
     * @param {Function} callback
     * @returns {Function} unsubscribe function
     */
    on(eventName, callback) {

        if (typeof callback !== "function") {
            throw new TypeError(
                `Event listener for "${eventName}" must be a function`
            );
        }

        if (!this._listeners.has(eventName)) {
            this._listeners.set(eventName, new Set());
        }

        this._listeners.get(eventName).add(callback);

        return () => {
            this.off(eventName, callback);
        };
    }

    /**
     * Subscribe once.
     *
     * Listener automatically removed after first emit.
     */
    once(eventName, callback) {

        const wrapper = (payload) => {

            this.off(eventName, wrapper);

            callback(payload);
        };

        return this.on(eventName, wrapper);
    }

    /**
     * Remove listener.
     */
    off(eventName, callback) {

        const listeners = this._listeners.get(eventName);

        if (!listeners) {
            return;
        }

        listeners.delete(callback);

        if (listeners.size === 0) {
            this._listeners.delete(eventName);
        }
    }

    /**
     * Emit event.
     */
    emit(eventName, payload = {}) {

        const listeners = this._listeners.get(eventName);

        if (!listeners || listeners.size === 0) {
            return;
        }

        // Clone to prevent modification during iteration.
        const snapshot = [...listeners];

        for (const listener of snapshot) {

            try {
                listener(payload);
            }
            catch (error) {

                console.error(
                    `[EventEmitter] Error in "${eventName}" listener`,
                    error
                );
            }
        }
    }

    /**
     * Remove all listeners for one event.
     */
    clear(eventName) {

        if (eventName) {
            this._listeners.delete(eventName);
            return;
        }

        this._listeners.clear();
    }

    /**
     * Check if event has listeners.
     */
    hasListeners(eventName) {

        return this.listenerCount(eventName) > 0;
    }

    /**
     * Number of listeners for event.
     */
    listenerCount(eventName) {

        return this._listeners.get(eventName)?.size || 0;
    }

    /**
     * Get registered event names.
     */
    eventNames() {

        return [...this._listeners.keys()];
    }
}


/**
 * ============================================================================
 * Graph Event Constants
 * ============================================================================
 *
 * Optional shared event names.
 * Import where needed to avoid typos.
 * ============================================================================
 */

export const GRAPH_EVENTS = Object.freeze({

    // ------------------------------------------------------------------------
    // State
    // ------------------------------------------------------------------------

    STATE_CHANGED: "stateChanged",

    // ------------------------------------------------------------------------
    // Selection
    // ------------------------------------------------------------------------

    SELECTION_CHANGED: "selectionChanged",
    MULTI_SELECTION_CHANGED: "multiSelectionChanged",

    // ------------------------------------------------------------------------
    // Viewport
    // ------------------------------------------------------------------------

    VIEWPORT_CHANGED: "viewportChanged",

    // ------------------------------------------------------------------------
    // Visibility
    // ------------------------------------------------------------------------

    VISIBILITY_CHANGED: "visibilityChanged",

    // ------------------------------------------------------------------------
    // Clusters
    // ------------------------------------------------------------------------

    CLUSTER_CHANGED: "clusterChanged",

    // ------------------------------------------------------------------------
    // Pinning
    // ------------------------------------------------------------------------

    PIN_CHANGED: "pinChanged",

    // ------------------------------------------------------------------------
    // Rendering
    // ------------------------------------------------------------------------

    BEFORE_RENDER: "beforeRender",
    AFTER_RENDER: "afterRender",

    // ------------------------------------------------------------------------
    // Search
    // ------------------------------------------------------------------------

    SEARCH_STARTED: "searchStarted",
    SEARCH_COMPLETED: "searchCompleted",

    // ------------------------------------------------------------------------
    // Graph Lifecycle
    // ------------------------------------------------------------------------

    GRAPH_LOADED: "graphLoaded",
    GRAPH_RESET: "graphReset",
});