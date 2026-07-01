/**
 * graph_layout.js
 *
 * Layout engine for Interactive Graph Viewer.
 *
 * Responsibilities:
 *   - Calculate node positions
 *   - Fit graph into viewport
 *   - Re-layout graph
 *
 * Does NOT:
 *   - Render SVG
 *   - Handle events
 *   - Perform search
 *   - Manage graph state
 */

export class GraphLayoutEngine {

    static hierarchical(graph, options = {}) {

        const levelSpacing = options.levelSpacing ?? 220;
        const nodeSpacing = options.nodeSpacing ?? 140;

        const adjacency = new Map();
        graph.nodes.forEach(n =>
            adjacency.set(n.id, [])
        );
        graph.edges.forEach(e => {
            if (adjacency.has(e.source)) {
                adjacency.get(e.source).push(e.target);
            }
        });

        const levels = new Map();
        const visiting = new Set();
        const visited = new Set();

        const assignLevel = (nodeId, depth) => {
            if (visiting.has(nodeId)) return;
            if (visited.has(nodeId) &&
                (levels.get(nodeId) ?? 0) >= depth) return;

            levels.set(
                nodeId,
                Math.max(levels.get(nodeId) ?? 0, depth)
            );

            visiting.add(nodeId);
            visited.add(nodeId);

            for (const next of adjacency.get(nodeId) ?? []) {
                assignLevel(next, depth + 1);
            }

            visiting.delete(nodeId);
        };

        const incoming = new Map();
        graph.nodes.forEach(n =>
            incoming.set(n.id, 0)
        );
        graph.edges.forEach(e =>
            incoming.set(
                e.target,
                (incoming.get(e.target) || 0) + 1
            )
        );

        const roots = graph.nodes.filter(
            n => (incoming.get(n.id) || 0) === 0
        );

        (roots.length
            ? roots
            : graph.nodes.slice(0, 1)
        ).forEach(r => assignLevel(r.id, 0));

        graph.nodes.forEach(n => {
            if (!levels.has(n.id)) {
                assignLevel(n.id, 0);
            }
        });

        const buckets = new Map();

        graph.nodes.forEach(node => {

            const level = levels.get(node.id) ?? 0;

            if (!buckets.has(level)) {
                buckets.set(level, []);
            }

            buckets.get(level).push(node);
        });

        buckets.forEach((nodes, level) => {

            const totalHeight =
                (nodes.length - 1) * nodeSpacing;

            nodes.forEach((node, index) => {

                node.position = {
                    x: level * levelSpacing,
                    y: index * nodeSpacing - totalHeight / 2
                };
            });
        });

        return graph;
    }

    static circular(graph, options = {}) {

        const radius = options.radius ?? 500;

        const count = graph.nodes.length;

        if (count === 0) {
            return graph;
        }

        graph.nodes.forEach((node, index) => {

            const angle =
                (Math.PI * 2 * index) / count;

            node.position = {
                x: Math.cos(angle) * radius,
                y: Math.sin(angle) * radius
            };
        });

        return graph;
    }

    static grid(graph, options = {}) {

        const spacing = options.spacing ?? 180;

        const cols =
            options.columns ??
            Math.ceil(Math.sqrt(graph.nodes.length));

        graph.nodes.forEach((node, index) => {

            const row = Math.floor(index / cols);
            const col = index % cols;

            node.position = {
                x: col * spacing,
                y: row * spacing
            };
        });

        return graph;
    }

    static forceDirected(graph, options = {}) {

        const MAX_FD_NODES = 200;

        if (graph.nodes.length > MAX_FD_NODES) {

            console.warn(
                `forceDirected: graph has ${graph.nodes.length} nodes ` +
                `(max ${MAX_FD_NODES}), falling back to grid layout`
            );

            return GraphLayoutEngine.grid(graph, options);
        }

        const iterations = options.iterations ?? 200;
        const repulsion = options.repulsion ?? 12000;
        const attraction = options.attraction ?? 0.04;
        const idealLength = options.idealLength ?? 220;

        graph.nodes.forEach((node, index) => {

            if (!node.position) {
                node.position = {
                    x: Math.cos(index) * 100,
                    y: Math.sin(index) * 100
                };
            }
        });

        for (let step = 0; step < iterations; step++) {

            const forces = new Map();

            graph.nodes.forEach(node => {
                forces.set(node.id, { x: 0, y: 0 });
            });

            //
            // Repulsion
            //

            for (let i = 0; i < graph.nodes.length; i++) {

                for (let j = i + 1; j < graph.nodes.length; j++) {

                    const a = graph.nodes[i];
                    const b = graph.nodes[j];

                    let dx =
                        b.position.x - a.position.x;

                    let dy =
                        b.position.y - a.position.y;

                    let dist =
                        Math.sqrt(dx * dx + dy * dy);

                    dist = Math.max(dist, 1);

                    const force =
                        repulsion / (dist * dist);

                    dx /= dist;
                    dy /= dist;

                    forces.get(a.id).x -= dx * force;
                    forces.get(a.id).y -= dy * force;

                    forces.get(b.id).x += dx * force;
                    forces.get(b.id).y += dy * force;
                }
            }

            //
            // Attraction
            //

            graph.edges.forEach(edge => {

                const source =
                    graph.nodeMap.get(edge.source);

                const target =
                    graph.nodeMap.get(edge.target);

                if (!source || !target) {
                    return;
                }

                let dx =
                    target.position.x -
                    source.position.x;

                let dy =
                    target.position.y -
                    source.position.y;

                let dist =
                    Math.sqrt(dx * dx + dy * dy);

                dist = Math.max(dist, 1);

                const force =
                    (dist - idealLength) *
                    attraction;

                dx /= dist;
                dy /= dist;

                forces.get(source.id).x += dx * force;
                forces.get(source.id).y += dy * force;

                forces.get(target.id).x -= dx * force;
                forces.get(target.id).y -= dy * force;
            });

            //
            // Apply
            //

            graph.nodes.forEach(node => {

                if (node.visual?.pinned) {
                    return;
                }

                const f = forces.get(node.id);

                node.position.x += f.x;
                node.position.y += f.y;
            });
        }

        return graph;
    }

    static fitToViewport(
        graph,
        width,
        height,
        padding = 100
    ) {

        if (!graph.nodes.length) {
            return graph;
        }

        const xs =
            graph.nodes.map(
                n => n.position?.x ?? 0
            );

        const ys =
            graph.nodes.map(
                n => n.position?.y ?? 0
            );

        const minX = Math.min(...xs);
        const maxX = Math.max(...xs);

        const minY = Math.min(...ys);
        const maxY = Math.max(...ys);

        const graphWidth =
            Math.max(maxX - minX, 1);

        const graphHeight =
            Math.max(maxY - minY, 1);

        const scaleX =
            (width - padding * 2) /
            graphWidth;

        const scaleY =
            (height - padding * 2) /
            graphHeight;

        const scale =
            Math.min(scaleX, scaleY);

        graph.nodes.forEach(node => {

            node.position.x =
                (node.position.x - minX) *
                scale + padding;

            node.position.y =
                (node.position.y - minY) *
                scale + padding;
        });

        return graph;
    }
}