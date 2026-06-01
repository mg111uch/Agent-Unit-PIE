// web/render/styles.js

/**
 * ============================================================================
 * Graph Visual Theme
 * ============================================================================
 *
 * Centralized visual configuration for the graph engine.
 *
 * Responsibilities:
 *   - Colors
 *   - Dimensions
 *   - Typography
 *   - Edge styles
 *   - Cluster styles
 *
 * No rendering logic.
 * No DOM access.
 * ============================================================================
 */

/* ============================================================================
 * Node Dimensions
 * ============================================================================
 */

export const NODE_DIMENSIONS = Object.freeze({

    DEFAULT_WIDTH: 180,
    DEFAULT_HEIGHT: 48,

    MIN_WIDTH: 120,
    MIN_HEIGHT: 36,

    CORNER_RADIUS: 8,
});

/* ============================================================================
 * Node Colors
 * ============================================================================
 */

export const NODE_COLORS = Object.freeze({

    module: "#5B8FF9",
    package: "#61DDAA",

    class: "#F6BD16",
    function: "#7262FD",

    file: "#78D3F8",

    service: "#F6903D",
    database: "#9661BC",

    external: "#F08BB4",

    unknown: "#808080",
});

/* ============================================================================
 * Risk Colors
 * ============================================================================
 */

export const RISK_COLORS = Object.freeze({

    critical: "#ff4d4f",
    high: "#ff7a45",
    medium: "#faad14",
    low: "#52c41a",

    unknown: "#999999",
});

/* ============================================================================
 * Node Border Styles
 * ============================================================================
 */

export const NODE_BORDERS = Object.freeze({

    NORMAL: {
        color: "#202020",
        width: 1,
    },

    SELECTED: {
        color: "#ffffff",
        width: 3,
    },

    PINNED: {
        color: "#ffd666",
        width: 2,
    },

    HOVERED: {
        color: "#ffffff",
        width: 2,
    },
});

/* ============================================================================
 * Typography
 * ============================================================================
 */

export const TYPOGRAPHY = Object.freeze({

    FONT_FAMILY:
        "Inter, system-ui, sans-serif",

    NODE_FONT_SIZE: 13,

    CLUSTER_FONT_SIZE: 14,

    SIDEBAR_FONT_SIZE: 13,
});

/* ============================================================================
 * Edge Styles
 * ============================================================================
 */

export const EDGE_STYLES = Object.freeze({

    DEFAULT: {
        color: "#7d8590",
        width: 1.5,
    },

    SELECTED: {
        color: "#ffffff",
        width: 3,
    },

    HIGHLIGHTED: {
        color: "#4f8cff",
        width: 3,
    },

    DEPENDS_ON: {
        color: "#8b949e",
        dasharray: "",
    },

    IMPORTS: {
        color: "#58a6ff",
        dasharray: "",
    },

    CALLS: {
        color: "#3fb950",
        dasharray: "",
    },

    REFERENCES: {
        color: "#d29922",
        dasharray: "5 5",
    },

    INHERITS: {
        color: "#bc8cff",
        dasharray: "",
    },

    UNKNOWN: {
        color: "#7d8590",
        dasharray: "",
    },
});

/* ============================================================================
 * Cluster Styles
 * ============================================================================
 */

export const CLUSTER_STYLES = Object.freeze({

    BACKGROUND: "#161b22",

    BORDER: "#30363d",

    COLLAPSED_BORDER: "#58a6ff",

    BORDER_WIDTH: 1.5,

    BORDER_RADIUS: 10,

    LABEL_COLOR: "#e6edf3",

    LABEL_FONT_SIZE: 14,
});

/* ============================================================================
 * Viewport
 * ============================================================================
 */

export const VIEWPORT = Object.freeze({

    MIN_ZOOM: 0.1,

    MAX_ZOOM: 8.0,

    DEFAULT_ZOOM: 1.0,

    ZOOM_STEP: 1.15,
});

/* ============================================================================
 * Selection
 * ============================================================================
 */

export const SELECTION = Object.freeze({

    BOX_FILL: "rgba(79,140,255,0.15)",

    BOX_STROKE: "#4f8cff",

    BOX_STROKE_WIDTH: 1,
});

/* ============================================================================
 * Animation
 * ============================================================================
 */

export const ANIMATION = Object.freeze({

    FAST: 100,

    NORMAL: 200,

    SLOW: 350,
});

/* ============================================================================
 * Helpers
 * ============================================================================
 */

export function getNodeColor(nodeType) {

    return (
        NODE_COLORS[nodeType] ??
        NODE_COLORS.unknown
    );
}

export function getRiskColor(riskLevel) {

    return (
        RISK_COLORS[riskLevel] ??
        RISK_COLORS.unknown
    );
}

export function getEdgeStyle(edgeType) {

    return (
        EDGE_STYLES[
            edgeType?.toUpperCase?.()
        ] ??
        EDGE_STYLES.UNKNOWN
    );
}