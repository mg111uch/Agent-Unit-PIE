// web/core/constants.js

/**
 * ============================================================================
 * Graph Engine Constants
 * ============================================================================
 *
 * Engine-wide configuration values.
 *
 * Do NOT put:
 *   - Colors
 *   - Fonts
 *   - SVG styles
 *
 * Those belong in render/styles.js
 *
 * ============================================================================
 */

/* Viewport */
export const VIEWPORT = Object.freeze({
    DEFAULT_ZOOM: 1.0,
    MIN_ZOOM: 0.10,
    MAX_ZOOM: 8.0,
    ZOOM_STEP: 1.15,
    FIT_PADDING: 100,
    ANIMATION_DURATION_MS: 250,
});

/* Navigation */
export const NAVIGATION = Object.freeze({
    CENTER_ANIMATION_MS: 250,
    ZOOM_TO_NODE_SCALE: 1.5,
    ZOOM_TO_CLUSTER_SCALE: 1.2,
});

/* Dragging */
export const DRAG = Object.freeze({
    START_THRESHOLD_PX: 3,
    AUTO_SCROLL_MARGIN: 40,
    GRID_SNAP_SIZE: 0,
    ENABLE_GRID_SNAP: false,
});

/* Selection */
export const SELECTION = Object.freeze({
    MULTI_SELECT_KEY: "Control",
    ALTERNATE_MULTI_SELECT_KEY: "Meta",
    BOX_SELECT_THRESHOLD_PX: 5,
    CLEAR_ON_BACKGROUND_CLICK: true,
});

/* Double Click */
export const INPUT = Object.freeze({
    DOUBLE_CLICK_MS: 300,
    LONG_PRESS_MS: 500,
});

/* Storage */
export const STORAGE = Object.freeze({
    DEFAULT_NAMESPACE:
        "interactive-graph",
    VIEWPORT_KEY:
        "viewport",
    SELECTION_KEY:
        "selection",
    CLUSTER_STATE_KEY:
        "clusters",
});

/* Renderer */
export const RENDER = Object.freeze({
    FULL_RENDER: "full",
    PARTIAL_RENDER: "partial",
    NODE_RENDER: "node",
    EDGE_RENDER: "edge",
    CLUSTER_RENDER: "cluster",
});

/* Layers */
export const LAYERS = Object.freeze({
    CLUSTERS:
        "cluster-layer",
    EDGES:
        "edge-layer",
    NODES:
        "node-layer",
    OVERLAY:
        "overlay-layer",
    VIEWPORT:
        "viewport",
});

/* Node Defaults */
export const NODE = Object.freeze({
    DEFAULT_WIDTH: 180,
    DEFAULT_HEIGHT: 48,
});

/* Cluster Defaults */
export const CLUSTER = Object.freeze({
    PADDING: 30,
    LABEL_MARGIN_X: 12,
    LABEL_MARGIN_Y: 20,
});

/* Engine Version */
export const ENGINE = Object.freeze({
    NAME: "interactive-graph",
    VERSION: "1.0.0",
});

/* Helpers */
export function clampZoom(value) {
    return Math.max(
        VIEWPORT.MIN_ZOOM,
        Math.min(
            VIEWPORT.MAX_ZOOM,
            value
        )
    );
}
export function isMultiSelectKey(event) {
    return (
        event.ctrlKey ||
        event.metaKey
    );
}