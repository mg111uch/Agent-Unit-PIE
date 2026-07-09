// web/render/viewport_culler.js

/**
 * ============================================================================
 * ViewportCuller
 * ============================================================================
 *
 * Determines which nodes and edges fall inside the
 * currently visible portion of the graph, given the
 * SVG's on-screen size and the viewport transform
 * (pan + zoom).
 *
 * Coordinate spaces
 * -----------------
 * Screen space: pixel coordinates inside the SVG
 *   element.  getBoundingClientRect() returns the
 *   SVG's on-screen size.
 *
 * Graph space: the untransformed coordinate system
 *   that nodes and edges live in.  Node positions
 *   are in graph space.
 *
 * The viewport applies
 *   screen = graph * zoom + pan
 *   graph  = (screen - pan) / zoom
 *
 * Culling
 * -------
 * A node is visible if its AABB (in graph space)
 * intersects the visible graph-space rectangle.
 *
 * An edge is visible if both endpoints are visible
 * (a single off-screen endpoint would draw a long
 * line crossing the visible region, but only the
 * visible-side stub is meaningful; we accept that
 * edge case and can revisit it for L7+ graphs).
 *
 * A small padding (in screen pixels) is added so
 * that elements just outside the visible area are
 * pre-rendered and ready when the user pans them in.
 * ============================================================================
 */

const DEFAULT_PADDING_PX = 120;

const LOD_FULL_PX = 28;
const LOD_DOT_PX = 4;
export class ViewportCuller {
    constructor(options = {}) {
        this.svg = options.svg;
        this.state = options.state;
        this.padding = options.padding ??
            DEFAULT_PADDING_PX;
    }
    /**
     * Compute the visible graph-space rectangle.
     * Returns null if the SVG has no measured size yet
     * (e.g. before layout), in which case culling
     * should be skipped.
     */
    getVisibleBounds() {
        if (!this.svg) {
            return null;
        }
        const rect =
            this.svg.getBoundingClientRect();
        if (
            rect.width === 0 ||
            rect.height === 0
        ) {
            return null;
        }
        const zoom =
            this.state?.zoom ?? 1;
        const panX =
            this.state?.panX ?? 0;
        const panY =
            this.state?.panY ?? 0;
        const pad = this.padding;
        return {
            minX:
                (0 - panX - pad) / zoom,
            minY:
                (0 - panY - pad) / zoom,
            maxX:
                (rect.width - panX + pad) /
                zoom,
            maxY:
                (rect.height - panY + pad) /
                zoom,
        };
    }
    isNodeVisible(node, bounds) {
        const w =
            node.width ?? 140;
        const h =
            node.height ?? 40;
        const x =
            node.position?.x ??
            node.x ?? 0;
        const y =
            node.position?.y ??
            node.y ?? 0;
        return !(
            x + w < bounds.minX ||
            x > bounds.maxX ||
            y + h < bounds.minY ||
            y > bounds.maxY
        );
    }
    resolveEdgeEndpoint(node) {
        if (
            node.scope !== "call" ||
            !node.parent_id
        ) {
            return node;
        }
        if (
            this.state?.isExpanded?.(
                node.parent_id
            )
        ) {
            return node;
        }
        const parent =
            this.state?.getNode?.(
                node.parent_id
            );
        return parent || node;
    }
    computeLod(node, zoom) {
        const w = (node.width ?? 140) * zoom;
        if (w >= LOD_FULL_PX) return "full";
        if (w >= LOD_DOT_PX) return "simple";
        return "dot";
    }
    isClusterVisible(cluster, bounds) {
        // Cluster bounds are computed by the
        // ClusterRenderer from member node bounds.
        // For culling we accept a slightly looser
        // check based on the cluster's nominal
        // metadata bounding box if present,
        // otherwise include the cluster.
        if (
            !cluster.bounds &&
            !cluster.node_ids?.length
        ) {
            return true;
        }
        if (cluster.bounds) {
            const b = cluster.bounds;
            return !(
                b.maxX < bounds.minX ||
                b.minX > bounds.maxX ||
                b.maxY < bounds.minY ||
                b.minY > bounds.maxY
            );
        }
        return true;
    }
    /**
     * Filter graph.nodes and graph.edges to the
     * visible subset.  If the SVG has no size yet,
     * returns the full arrays (graceful fallback
     * for pre-layout renders).
     */
    cull(graph) {
        const bounds =
            this.getVisibleBounds();
        if (!bounds || !graph) {
            return {
                nodes: graph?.nodes ?? [],
                edges: graph?.edges ?? [],
                clusters: graph?.clusters ?? [],
                culled: false,
            };
        }
        const zoom =
            this.state?.zoom ?? 1;
        const visibleNodes = [];
        const visibleNodeIds = new Set();
        for (const node of graph.nodes) {
            if (this.isNodeVisible(
                node, bounds
            )) {
                node._lod =
                    this.computeLod(node, zoom);
                visibleNodes.push(node);
                visibleNodeIds.add(node.id);
            }
        }
        const visibleEdges = [];
        for (const edge of graph.edges) {
            const source =
                this.state?.getNode?.(
                    edge.source
                );
            const target =
                this.state?.getNode?.(
                    edge.target
                );
            if (!source || !target) {
                continue;
            }
            const resolvedSource =
                this.resolveEdgeEndpoint(
                    source
                );
            const resolvedTarget =
                this.resolveEdgeEndpoint(
                    target
                );
            if (
                visibleNodeIds.has(
                    resolvedSource.id
                ) &&
                visibleNodeIds.has(
                    resolvedTarget.id
                )
            ) {
                visibleEdges.push(edge);
            }
        }
        const visibleClusters = [];
        for (const cluster of graph.clusters ?? []) {
            if (this.isClusterVisible(
                cluster, bounds
            )) {
                visibleClusters.push(cluster);
            }
        }
        return {
            nodes: visibleNodes,
            edges: visibleEdges,
            clusters: visibleClusters,
            visibleNodeIds,
            culled: true,
        };
    }
}