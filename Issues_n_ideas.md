## Problem statement
While generating initial layout in `python/Agentic_Unit_PIE/codebase/modules/codebase_atlas/graph/web/layout/layout.js` , most of the call graph file boxes containing group of file nodes are overlapped over each other. How could they be rendered at positions so that initial layout when call graph is loaded gives a clear sparse view.I am going to rearrange the positions manually later anyway.

## Solution
The overlap isn't really a bug in the level/position math — it's that `hierarchical()` (and `grid()`) position **nodes**, completely ignorant of `cluster_id`. Cluster boxes are drawn afterward as a bounding rect around whichever member nodes ended up there, so when two files' functions get interleaved across the same BFS levels, their bounding rects necessarily overlap. Fixing node spacing won't fix this — the layout needs to treat clusters as first-class units.

**Plan:**

1. **Two-pass layout: cluster-level first, node-level second.**
   - Pass 1: build a coarse graph where each cluster (file) is a single node, and edges are cluster-to-cluster (derived by mapping each node edge to its `cluster_id` pair, deduped). Run `hierarchical()` (or even just `grid()`) on *that* to get one macro-position per cluster.
   - Pass 2: within each cluster, lay out its member nodes locally (small grid is enough) around the cluster's macro-position as an offset/origin.
   - This guarantees clusters are spatially coherent by construction, instead of by luck.

2. **Size clusters before placing them, not after.** Compute each cluster's footprint (roughly `sqrt(memberCount) * nodeSpacing` per side) up front, and use that to decide macro-spacing in pass 1 — a cluster with 40 functions needs more room than one with 2. Otherwise a uniform macro-grid will still clip large clusters into their neighbors.

3. **Add a cluster margin, not just node margin.** Nodes need spacing from each other; clusters need a separate, larger buffer between *box edges*, not box centers, since the box grows with member count.

4. **Ungrouped/no-cluster nodes** should get their own synthetic "cluster" (or be placed on a separate outer ring/row) rather than being interleaved with real clusters in the same pass — otherwise they'll keep landing inside other clusters' bounding boxes.

5. **Cheap safety net (optional, do this regardless of the above):** after layout, compute all cluster bounding boxes and run a simple pairwise rectangle-overlap resolution pass — if two cluster boxes intersect, push them apart along the axis of least overlap. This catches any residual overlap from imperfect macro-layout without needing a perfect algorithm, and since you're rearranging manually afterward anyway, it just needs to be "good enough to see structure," not optimal.

Practically: implement step 1+2 as the primary fix (that's what actually produces a sparse, readable initial view), and add step 5 as a cheap finishing pass since it's a few lines and eliminates whatever residual overlap the macro-layout leaves.