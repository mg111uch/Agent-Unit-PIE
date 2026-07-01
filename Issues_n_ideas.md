50 nodes is well under `LARGE_GRAPH_THRESHOLD` (200) — so none of the culling/chunking/LOD code even engages for this case. Whatever's hanging here is a different bug, and it's specific to **call graphs**, which is the clue that matters.

## Root cause: `hierarchical()` layout has no cycle protection

`applyInitialLayout()` sends anything under 200 nodes to `GraphLayoutEngine.hierarchical()`. Look at the level-assignment loop:

```js
while (queue.length) {
    const current = queue.shift();
    const currentLevel = levels.get(current);

    graph.edges.forEach(edge => {
        if (edge.source !== current) return;

        const nextLevel = currentLevel + 1;

        if (!levels.has(edge.target) || nextLevel > levels.get(edge.target)) {
            levels.set(edge.target, nextLevel);
            queue.push(edge.target);   // <-- re-enqueued every time level increases
        }
    });
}
```

This is longest-path level assignment, and it's only valid on a **DAG**. It assumes: visit a node, push its neighbors at `level+1`, done. But call graphs are exactly the kind of graph where cycles are common and expected — recursion (`f` calls `f`), mutual recursion (`f` calls `g` calls `f`), or just a callback registered back into a dispatcher. Dependency graphs are more likely to be acyclic (or you'd have a circular-import bug); call graphs routinely aren't.

The moment there's a cycle reachable from a root, this loop doesn't terminate: each trip around the cycle increases `nextLevel` by 1, which is always `> levels.get(edge.target)` from the previous trip, so the target gets re-enqueued forever. It's not proportional to node count at all — a 50-node graph with one recursive function will spin exactly as hard as a 5,000-node one. That matches your symptom precisely: the hang doesn't correlate with size, and it happens in `applyInitialLayout()`, which runs in the `GraphViewer` constructor — **before any rendering, chunking, or culling code even runs.** This explains why patches 1 and 2 didn't touch it.

## Fix

Bound the level growth so a cycle can't cause unbounded re-enqueuing — cap it at `graph.nodes.length` (the maximum possible level in a real DAG of that size), and once a node has been "settled" past that bound, stop propagating through it:

```diff
     static hierarchical(graph, options = {}) {

         const levelSpacing = options.levelSpacing ?? 220;
         const nodeSpacing = options.nodeSpacing ?? 140;
+        const maxLevel = graph.nodes.length + 1;

         const incoming = new Map();
         ...
         while (queue.length) {

             const current = queue.shift();
             const currentLevel = levels.get(current);

             graph.edges.forEach(edge => {

                 if (edge.source !== current) {
                     return;
                 }

                 const nextLevel = currentLevel + 1;

+                // A DAG can never need more levels than it has nodes.
+                // If we'd exceed that, we're going around a cycle —
+                // stop propagating through this edge instead of
+                // re-enqueuing forever.
+                if (nextLevel > maxLevel) {
+                    return;
+                }
+
                 if (
                     !levels.has(edge.target) ||
                     nextLevel > levels.get(edge.target)
                 ) {
                     levels.set(edge.target, nextLevel);
                     queue.push(edge.target);
                 }
             });
         }
```

This is a safety cap, not a real fix for layout *quality* — a graph with cycles will still get somewhat arbitrary levels for the nodes inside the cycle (whichever level they happened to settle at when the cap kicked in), but it will **terminate**, and the graph will render instead of hanging.

If you want the layout to actually look right for cyclic call graphs (not just avoid hanging), the proper fix is to detect back-edges with a DFS visiting-set and exclude them from level propagation entirely, so cycles get broken deterministically rather than capped arbitrarily:

```js
static hierarchical(graph, options = {}) {
    const levelSpacing = options.levelSpacing ?? 220;
    const nodeSpacing = options.nodeSpacing ?? 140;

    const adjacency = new Map();
    graph.nodes.forEach(n => adjacency.set(n.id, []));
    graph.edges.forEach(e => {
        if (adjacency.has(e.source)) adjacency.get(e.source).push(e.target);
    });

    const levels = new Map();
    const visiting = new Set();  // on current DFS stack -> back edge if hit again
    const visited = new Set();

    function assignLevel(nodeId, depth) {
        if (visiting.has(nodeId)) return;      // back edge — cycle, skip it
        if (visited.has(nodeId) && levels.get(nodeId) >= depth) return;

        levels.set(nodeId, Math.max(levels.get(nodeId) ?? 0, depth));
        visiting.add(nodeId);
        visited.add(nodeId);

        for (const next of adjacency.get(nodeId) ?? []) {
            assignLevel(next, depth + 1);
        }

        visiting.delete(nodeId);
    }

    const incoming = new Map();
    graph.nodes.forEach(n => incoming.set(n.id, 0));
    graph.edges.forEach(e => incoming.set(e.target, (incoming.get(e.target) || 0) + 1));
    const roots = graph.nodes.filter(n => (incoming.get(n.id) || 0) === 0);

    (roots.length ? roots : graph.nodes.slice(0, 1)).forEach(r => assignLevel(r.id, 0));
    graph.nodes.forEach(n => { if (!levels.has(n.id)) assignLevel(n.id, 0); });

    // bucket + position exactly as before, unchanged
    ...
}
```

This is more code, but it's the correct way to level a graph that isn't guaranteed to be a DAG, and it fixes the disconnected-node case for free too (any node the BFS never reached before is now guaranteed a level via the final `forEach`).

I'd start with the cheap cap (2-line diff) to confirm this is actually the bug and unblock loading, then swap in the DFS version if the resulting layout quality bothers you for recursive call graphs.