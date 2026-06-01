// web/utils/geometry.js

/**
 * ============================================================================
 * Geometry Utilities
 * ============================================================================
 *
 * Shared geometry helpers used by:
 *   - Edge rendering
 *   - Node rendering
 *   - Cluster rendering
 *   - Dragging
 *   - Selection
 *   - Viewport fitting
 *
 * No DOM access.
 * Pure functions only.
 * ============================================================================
 */

/* ============================================================================
 * Basic Helpers
 * ============================================================================
 */

export function distance(x1, y1, x2, y2) {

    const dx = x2 - x1;
    const dy = y2 - y1;

    return Math.sqrt(dx * dx + dy * dy);
}

export function midpoint(x1, y1, x2, y2) {

    return {
        x: (x1 + x2) / 2,
        y: (y1 + y2) / 2,
    };
}

export function lerp(a, b, t) {

    return a + (b - a) * t;
}

export function clamp(value, min, max) {

    return Math.max(
        min,
        Math.min(max, value)
    );
}

/* ============================================================================
 * Rectangle Helpers
 * ============================================================================
 */

export function rectCenter(rect) {

    return {

        x: rect.x + rect.width / 2,

        y: rect.y + rect.height / 2,
    };
}

export function pointInRect(x, y, rect) {

    return (
        x >= rect.x &&
        x <= rect.x + rect.width &&
        y >= rect.y &&
        y <= rect.y + rect.height
    );
}

export function rectsIntersect(a, b) {

    return !(
        a.x + a.width < b.x ||
        b.x + b.width < a.x ||
        a.y + a.height < b.y ||
        b.y + b.height < a.y
    );
}

/* ============================================================================
 * Node Helpers
 * ============================================================================
 */

export function getNodeRect(node) {

    const width =
        node.width ?? 180;

    const height =
        node.height ?? 48;

    return {

        x: node.position?.x ?? 0,

        y: node.position?.y ?? 0,

        width,
        height,
    };
}

export function getNodeCenter(node) {

    const rect =
        getNodeRect(node);

    return rectCenter(rect);
}

/* ============================================================================
 * Line / Rectangle Intersection
 * ============================================================================
 *
 * Returns point where line from center exits rectangle.
 *
 * Used for:
 *   Node border attachment
 *   Arrow positioning
 * ============================================================================
 */

export function lineRectIntersection(
    rect,
    targetX,
    targetY
) {

    const center =
        rectCenter(rect);

    const dx =
        targetX - center.x;

    const dy =
        targetY - center.y;

    if (dx === 0 && dy === 0) {

        return {
            x: center.x,
            y: center.y,
        };
    }

    const halfWidth =
        rect.width / 2;

    const halfHeight =
        rect.height / 2;

    let scaleX = Infinity;
    let scaleY = Infinity;

    if (dx !== 0) {
        scaleX =
            halfWidth / Math.abs(dx);
    }

    if (dy !== 0) {
        scaleY =
            halfHeight / Math.abs(dy);
    }

    const scale =
        Math.min(scaleX, scaleY);

    return {

        x: center.x + dx * scale,

        y: center.y + dy * scale,
    };
}

/* ============================================================================
 * Node Connection Points
 * ============================================================================
 *
 * Returns edge attachment points on node borders.
 *
 * Instead of:
 *
 *   center ---- center
 *
 * Produces:
 *
 *   border ---- border
 * ============================================================================
 */

export function nodeConnectionPoints(
    sourceNode,
    targetNode
) {

    const sourceRect =
        getNodeRect(sourceNode);

    const targetRect =
        getNodeRect(targetNode);

    const sourceCenter =
        rectCenter(sourceRect);

    const targetCenter =
        rectCenter(targetRect);

    const sourcePoint =
        lineRectIntersection(
            sourceRect,
            targetCenter.x,
            targetCenter.y
        );

    const targetPoint =
        lineRectIntersection(
            targetRect,
            sourceCenter.x,
            sourceCenter.y
        );

    return {

        source: sourcePoint,

        target: targetPoint,
    };
}

/* ============================================================================
 * Bounds Helpers
 * ============================================================================
 */

export function expandBounds(
    bounds,
    padding = 0
) {

    return {

        minX: bounds.minX - padding,
        minY: bounds.minY - padding,

        maxX: bounds.maxX + padding,
        maxY: bounds.maxY + padding,

        width:
            bounds.maxX -
            bounds.minX +
            padding * 2,

        height:
            bounds.maxY -
            bounds.minY +
            padding * 2,
    };
}

export function computeNodeBounds(nodes) {

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

        const rect =
            getNodeRect(node);

        minX =
            Math.min(minX, rect.x);

        minY =
            Math.min(minY, rect.y);

        maxX =
            Math.max(
                maxX,
                rect.x + rect.width
            );

        maxY =
            Math.max(
                maxY,
                rect.y + rect.height
            );
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

/* ============================================================================
 * Angles
 * ============================================================================
 */

export function angleBetween(
    x1,
    y1,
    x2,
    y2
) {

    return Math.atan2(
        y2 - y1,
        x2 - x1
    );
}

export function radiansToDegrees(
    radians
) {

    return radians * 180 / Math.PI;
}