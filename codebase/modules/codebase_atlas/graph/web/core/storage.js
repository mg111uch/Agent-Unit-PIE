// web/core/storage.js

/**
 * ============================================================================
 * GraphStorage
 * ============================================================================
 *
 * Persists user state between sessions.
 *
 * Stores:
 *   - zoom
 *   - pan
 *   - hidden nodes
 *   - pinned nodes
 *   - collapsed clusters
 *   - custom node positions
 *
 * Does NOT store:
 *   - graph JSON
 *   - nodes/edges/clusters
 *   - SVG state
 *   - renderer state
 *
 * ============================================================================
 */

const STORAGE_VERSION = 1;

const DEFAULT_NAMESPACE = "interactive-graph";

export class GraphStorage {

    constructor(namespace = DEFAULT_NAMESPACE) {

        this.namespace = namespace;
        this.version = STORAGE_VERSION;
        this._suspendCount = 0;
    }

    // =========================================================================
    // Keys
    // =========================================================================

    get storageKey() {

        return `${this.namespace}:state:v${this.version}`;
    }

    // =========================================================================
    // Serialization
    // =========================================================================

    createSnapshot(state) {

        const nodePositions = {};

        for (const node of state.graph.nodes) {

            if (
                node.position &&
                Number.isFinite(node.position.x) &&
                Number.isFinite(node.position.y)
            ) {

                nodePositions[node.id] = {
                    x: node.position.x,
                    y: node.position.y,
                };
            }
        }

        return {

            version: this.version,

            viewport: {
                zoom: state.zoom,
                panX: state.panX,
                panY: state.panY,
            },

            hiddenNodes: [...state.hiddenNodes],

            hiddenEdges: [...state.hiddenEdges],

            pinnedNodes: [...state.pinnedNodes],

            collapsedClusters: [...state.collapsedClusters],

            selectedNodeId: state.selectedNodeId,

            nodePositions,
        };
    }

    // =========================================================================
    // Save
    // =========================================================================

    save(state) {

        try {

            const snapshot =
                this.createSnapshot(state);

            localStorage.setItem(
                this.storageKey,
                JSON.stringify(snapshot)
            );

            return true;

        } catch (error) {

            console.error(
                "[GraphStorage] Save failed",
                error
            );

            return false;
        }
    }

    // =========================================================================
    // Load
    // =========================================================================

    load() {

        try {

            const raw =
                localStorage.getItem(
                    this.storageKey
                );

            if (!raw) {
                return null;
            }

            return JSON.parse(raw);

        } catch (error) {

            console.error(
                "[GraphStorage] Load failed",
                error
            );

            return null;
        }
    }

    // =========================================================================
    // Restore
    // =========================================================================

    restore(state) {

        const snapshot = this.load();

        if (!snapshot) {
            return false;
        }

        try {

            // -------------------------------------------------------------
            // Viewport
            // -------------------------------------------------------------

            if (snapshot.viewport) {

                state.zoom =
                    snapshot.viewport.zoom ?? 1;

                state.panX =
                    snapshot.viewport.panX ?? 0;

                state.panY =
                    snapshot.viewport.panY ?? 0;
            }

            // -------------------------------------------------------------
            // Visibility
            // -------------------------------------------------------------

            state.hiddenNodes = new Set(
                snapshot.hiddenNodes || []
            );

            state.hiddenEdges = new Set(
                snapshot.hiddenEdges || []
            );

            // -------------------------------------------------------------
            // Pinning
            // -------------------------------------------------------------

            state.pinnedNodes = new Set(
                snapshot.pinnedNodes || []
            );

            // -------------------------------------------------------------
            // Clusters
            // -------------------------------------------------------------

            state.collapsedClusters =
                new Set(
                    snapshot.collapsedClusters || []
                );

            // -------------------------------------------------------------
            // Selection
            // -------------------------------------------------------------

            state.selectedNodeId =
                snapshot.selectedNodeId || null;

            // -------------------------------------------------------------
            // Node Positions
            // -------------------------------------------------------------

            const positions =
                snapshot.nodePositions || {};

            for (const node of state.graph.nodes) {

                const pos =
                    positions[node.id];

                if (!pos) {
                    continue;
                }

                if (!node.position) {
                    node.position = {};
                }

                node.position.x = pos.x;
                node.position.y = pos.y;
            }

            return true;

        } catch (error) {

            console.error(
                "[GraphStorage] Restore failed",
                error
            );

            return false;
        }
    }

    // =========================================================================
    // Delete
    // =========================================================================

    clear() {

        try {

            localStorage.removeItem(
                this.storageKey
            );

            return true;

        } catch (error) {

            console.error(
                "[GraphStorage] Clear failed",
                error
            );

            return false;
        }
    }

    // =========================================================================
    // Auto Save
    // =========================================================================

    attach(state) {

        const save = () => {

            if (this._suspendCount > 0) {
                return;
            }

            this.save(state);
        };

        const unsubscribers = [

            state.subscribe(
                "viewportChanged",
                save
            ),

            state.subscribe(
                "visibilityChanged",
                save
            ),

            state.subscribe(
                "clusterChanged",
                save
            ),

            state.subscribe(
                "pinChanged",
                save
            ),

            state.subscribe(
                "selectionChanged",
                save
            ),

            state.subscribe(
                "nodes:moved",
                save
            ),
        ];

        return () => {

            for (const unsubscribe of unsubscribers) {

                unsubscribe();
            }
        };
    }

    // =====================================================================
    // Suspend / Resume
    // =====================================================================

    suspend() {

        this._suspendCount += 1;
    }

    resume() {

        if (this._suspendCount > 0) {
            this._suspendCount -= 1;
        }
    }
}

/**
 * ============================================================================
 * Helpers
 * ============================================================================
 */

export function createStorage(namespace) {

    return new GraphStorage(namespace);
}