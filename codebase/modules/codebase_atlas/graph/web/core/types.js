// core/types.js

/**
 * ============================================================================
 * Graph Types
 * ============================================================================
 *
 * Canonical frontend representation of graph data produced by
 * InteractiveRenderer / GraphSerializer.
 *
 * No DOM.
 * No rendering.
 * No state management.
 * Only schemas, validation and normalization.
 * ============================================================================
 */

export const NODE_TYPES = Object.freeze({
    FILE: "file",
    FUNCTION: "function",
    CLASS: "class",
    MODULE: "module",
    PACKAGE: "package",
    SERVICE: "service",
    DATABASE: "database",
    EXTERNAL: "external",
    UNKNOWN: "unknown",
});

export const EDGE_TYPES = Object.freeze({
    CALLS: "calls",
    IMPORTS: "imports",
    INHERITS: "inherits",
    REFERENCES: "references",
    DEPENDS_ON: "depends_on",
    CONTAINS: "contains",
    USES: "uses",
    UNKNOWN: "unknown",
});

export const CLUSTER_TYPES = Object.freeze({
    PACKAGE: "package",
    DIRECTORY: "directory",
    MODULE: "module",
    SERVICE: "service",
    GROUP: "group",
    UNKNOWN: "unknown",
});


/**
 * ============================================================================
 * Validation Helpers
 * ============================================================================
 */

function isObject(value) {
    return value !== null && typeof value === "object";
}

function ensureArray(value) {
    return Array.isArray(value) ? value : [];
}

function ensureString(value, fallback = "") {
    return typeof value === "string"
        ? value
        : fallback;
}

function ensureNumber(value, fallback = 0) {
    return Number.isFinite(value)
        ? value
        : fallback;
}


/**
 * ============================================================================
 * Node
 * ============================================================================
 */

export class GraphNode {

    constructor(data = {}) {

        this.id = ensureString(data.id);

        this.label = ensureString(
            data.label,
            this.id
        );

        this.type = ensureString(
            data.type,
            NODE_TYPES.UNKNOWN
        );

        this.cluster = ensureString(data.cluster);

        this.x = ensureNumber(data.x);
        this.y = ensureNumber(data.y);

        this.width = ensureNumber(data.width, 140);
        this.height = ensureNumber(data.height, 40);

        this.hidden = Boolean(data.hidden);
        this.collapsed = Boolean(data.collapsed);
        this.pinned = Boolean(data.pinned);

        this.metadata = isObject(data.metadata)
            ? data.metadata
            : {};
    }

    validate() {

        if (!this.id) {
            throw new Error(
                "GraphNode requires id"
            );
        }

        return true;
    }
}


/**
 * ============================================================================
 * Edge
 * ============================================================================
 */

export class GraphEdge {

    constructor(data = {}) {

        this.id = ensureString(
            data.id,
            `${data.source}->${data.target}`
        );

        this.source = ensureString(data.source);
        this.target = ensureString(data.target);

        this.type = ensureString(
            data.type,
            EDGE_TYPES.UNKNOWN
        );

        this.weight = ensureNumber(
            data.weight,
            1
        );

        this.hidden = Boolean(data.hidden);

        this.metadata = isObject(data.metadata)
            ? data.metadata
            : {};
    }

    validate() {

        if (!this.source) {
            throw new Error(
                `Edge ${this.id}: missing source`
            );
        }

        if (!this.target) {
            throw new Error(
                `Edge ${this.id}: missing target`
            );
        }

        return true;
    }
}


/**
 * ============================================================================
 * Cluster
 * ============================================================================
 */

export class GraphCluster {

    constructor(data = {}) {

        this.id = ensureString(data.id);

        this.label = ensureString(
            data.label,
            this.id
        );

        this.type = ensureString(
            data.type,
            CLUSTER_TYPES.UNKNOWN
        );

        this.parent = ensureString(data.parent);

        this.collapsed = Boolean(data.collapsed);

        this.metadata = isObject(data.metadata)
            ? data.metadata
            : {};
    }

    validate() {

        if (!this.id) {
            throw new Error(
                "Cluster requires id"
            );
        }

        return true;
    }
}


/**
 * ============================================================================
 * GraphData
 * ============================================================================
 */

export class GraphData {

    constructor(data = {}) {

        this.nodes = ensureArray(data.nodes)
            .map(node => new GraphNode(node));

        this.edges = ensureArray(data.edges)
            .map(edge => new GraphEdge(edge));

        this.clusters = ensureArray(data.clusters)
            .map(cluster => new GraphCluster(cluster));

        this.metadata = isObject(data.metadata)
            ? data.metadata
            : {};

        this.nodeMap = new Map();
        this.edgeMap = new Map();
        this.clusterMap = new Map();

        this.buildIndexes();
    }

    buildIndexes() {

        this.nodeMap.clear();
        this.edgeMap.clear();
        this.clusterMap.clear();

        for (const node of this.nodes) {
            this.nodeMap.set(node.id, node);
        }

        for (const edge of this.edges) {
            this.edgeMap.set(edge.id, edge);
        }

        for (const cluster of this.clusters) {
            this.clusterMap.set(
                cluster.id,
                cluster
            );
        }
    }

    validate() {

        for (const node of this.nodes) {
            node.validate();
        }

        for (const edge of this.edges) {

            edge.validate();

            if (!this.nodeMap.has(edge.source)) {
                throw new Error(
                    `Unknown source node: ${edge.source}`
                );
            }

            if (!this.nodeMap.has(edge.target)) {
                throw new Error(
                    `Unknown target node: ${edge.target}`
                );
            }
        }

        for (const cluster of this.clusters) {
            cluster.validate();
        }

        return true;
    }

    getNode(id) {
        return this.nodeMap.get(id);
    }

    getEdge(id) {
        return this.edgeMap.get(id);
    }

    getCluster(id) {
        return this.clusterMap.get(id);
    }
}


/**
 * ============================================================================
 * Factory
 * ============================================================================
 */

export function createGraphData(rawData) {

    const graph = new GraphData(rawData);

    graph.validate();

    return graph;
}