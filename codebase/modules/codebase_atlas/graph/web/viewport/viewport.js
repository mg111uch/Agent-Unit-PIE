// web/viewport/viewport.js

import {
    VIEWPORT,
    clampZoom,
} from "../core/constants.js";

/**
 * ============================================================================
 * ViewportController
 * ============================================================================
 *
 * Owns:
 *   - zoom
 *   - pan
 *   - coordinate transforms
 *
 * Does NOT own:
 *   - selection
 *   - dragging
 *   - navigation
 * ============================================================================
 */

export class ViewportController {

    constructor(options = {}) {

        this.state = options.state;
        this.renderer = options.renderer;

        this.svg =
            this._resolveElement(
                options.svg ?? "graph-svg"
            );

        this.viewport =
            this._resolveElement(
                options.viewport ?? "viewport"
            );

        this.zoom =
            this.state?.zoom ??
            VIEWPORT.DEFAULT_ZOOM;

        this.panX =
            this.state?.panX ?? 0;

        this.panY =
            this.state?.panY ?? 0;

        this.updateTransform();
    }

    /* ===================================================================== */
    /* Zoom                                                                   */
    /* ===================================================================== */

    setZoom(
        zoom,
        anchorX = null,
        anchorY = null
    ) {

        const newZoom =
            clampZoom(zoom);

        if (
            anchorX === null ||
            anchorY === null
        ) {

            this.zoom = newZoom;

            this._syncState();

            return;
        }

        const before =
            this.screenToGraph(
                anchorX,
                anchorY
            );

        this.zoom = newZoom;

        const after =
            this.screenToGraph(
                anchorX,
                anchorY
            );

        this.panX +=
            (after.x - before.x) *
            this.zoom;

        this.panY +=
            (after.y - before.y) *
            this.zoom;

        this._syncState();
    }

    zoomIn(
        factor = VIEWPORT.ZOOM_STEP
    ) {

        this.setZoom(
            this.zoom * factor
        );
    }

    zoomOut(
        factor = VIEWPORT.ZOOM_STEP
    ) {

        this.setZoom(
            this.zoom / factor
        );
    }

    /* ===================================================================== */
    /* Pan                                                                    */
    /* ===================================================================== */

    setPan(x, y) {

        this.panX = x;
        this.panY = y;

        this._syncState();
    }

    panBy(dx, dy) {

        this.panX += dx;
        this.panY += dy;

        this._syncState();
    }

    /* ===================================================================== */
    /* Coordinate Conversion                                                  */
    /* ===================================================================== */

    screenToGraph(
        screenX,
        screenY
    ) {

        const rect =
            this.svg.getBoundingClientRect();

        return {

            x:
                (screenX -
                    rect.left -
                    this.panX) /
                this.zoom,

            y:
                (screenY -
                    rect.top -
                    this.panY) /
                this.zoom,
        };
    }

    graphToScreen(
        graphX,
        graphY
    ) {

        const rect =
            this.svg.getBoundingClientRect();

        return {

            x:
                rect.left +
                this.panX +
                graphX * this.zoom,

            y:
                rect.top +
                this.panY +
                graphY * this.zoom,
        };
    }

    /* ===================================================================== */
    /* Centering                                                              */
    /* ===================================================================== */

    centerOn(
        graphX,
        graphY
    ) {

        const rect =
            this.svg.getBoundingClientRect();

        this.panX =
            rect.width / 2 -
            graphX * this.zoom;

        this.panY =
            rect.height / 2 -
            graphY * this.zoom;

        this._syncState();
    }

    /* ===================================================================== */
    /* Bounds                                                                 */
    /* ===================================================================== */

    fitBounds(
        bounds,
        padding =
            VIEWPORT.FIT_PADDING
    ) {

        if (
            !bounds ||
            bounds.width <= 0 ||
            bounds.height <= 0
        ) {
            return;
        }

        const rect =
            this.svg.getBoundingClientRect();

        const scaleX =
            (rect.width - padding * 2) /
            bounds.width;

        const scaleY =
            (rect.height - padding * 2) /
            bounds.height;

        const zoom =
            clampZoom(
                Math.min(
                    scaleX,
                    scaleY
                )
            );

        this.zoom = zoom;

        const centerX =
            bounds.minX +
            bounds.width / 2;

        const centerY =
            bounds.minY +
            bounds.height / 2;

        this.panX =
            rect.width / 2 -
            centerX * zoom;

        this.panY =
            rect.height / 2 -
            centerY * zoom;

        this._syncState();
    }

    reset() {

        this.zoom =
            VIEWPORT.DEFAULT_ZOOM;

        this.panX = 0;
        this.panY = 0;

        this._syncState();
    }

    /* ===================================================================== */
    /* Transform                                                              */
    /* ===================================================================== */

    updateTransform() {

        this.viewport.setAttribute(
            "transform",
            `translate(${this.panX},${this.panY}) scale(${this.zoom})`
        );
    }

    /* ===================================================================== */
    /* State Sync                                                             */
    /* ===================================================================== */

    _syncState() {

        if (this.state) {

            this.state.zoom =
                this.zoom;

            this.state.panX =
                this.panX;

            this.state.panY =
                this.panY;

            this.state.emit(
                "viewportChanged",
                {
                    zoom: this.zoom,
                    panX: this.panX,
                    panY: this.panY,
                }
            );
        }

        this.updateTransform();
    }

    /* ===================================================================== */
    /* Helpers                                                                */
    /* ===================================================================== */

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
                `Viewport element not found: ${value}`
            );
        }

        return element;
    }
}