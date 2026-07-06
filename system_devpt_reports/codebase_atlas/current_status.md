# Current Development status

# Graph engine contains

```text
Backend
    ↓
Graph JSON
    ↓
GraphState
    ↓
GraphLayoutEngine
    ↓
GraphStorage
    ↓
NodeRenderer
EdgeRenderer
ClusterRenderer
    ↓
GraphRenderer
    ↓
ViewportController
    ↓
GraphNavigation
    ↓
SelectionManager
    ↓
GraphEventController
    ↓
DragController
    ↓
GraphInteractionManager
```

---

## Phase 1 — Backend (✅ Completed)

* `graph_models.py`
Single source of truth for graph structure.
Contains: GraphData,Node,Edge,Cluster,NodeType,EdgeType

* `graph_builder.py`
AtlasData -> GraphBuilder -> GraphData
Moves graph extraction logic out of renderers.

* `graph_serializer.py`
GraphData ↔ JSON
Needed for browser interactive view.
Example:
```json
{
  "nodes": [],
  "edges": [],
  "clusters": []
}
```

* `interactive_renderer.py`
GraphData ─> InteractiveRenderer ─> JSON ─> graph_viewer.html (server-injected)
Produces browser-consumable graph data.

* `serve.py`
AtlasData -> GraphBuilder-> GraphData -> InteractiveRenderer

New flow is:

```text
Build Graph
   ↓
interactive_renderer.py
   ↓
Graph JSON
   ↓
serve.py (/api/graph)
   ↓
graph_viewer.html
   ↓
graph_viewer.js
    ↓
GraphState
    ↓
GraphRenderer
    ↓
viewport/
    ↓
interaction/
    ↓
SVG Renderers
```

---

## Phase 2 — Graph Web Frontend (✅ Completed)

The frontend is no longer merely rendering SVG.

```text
  Backend Graph Model
          ↓
      graph JSON
          ↓
     GraphState
          ↓
    GraphRenderer
       /  |  \
 Cluster Edge Node
          ↓
         SVG
```

* `web/interaction/drag.js`
Currently performs `renderer.render();` on every pointer move.That is acceptable for 100–300 nodes but becomes expensive later.

Instead of full rerender, a better future direction is:

```text
DragController
      ↓
state update
      ↓
renderer.updateNode(...)
renderer.updateEdge(...)
renderer.updateCluster(...)
```

* `web/interaction/interaction.js`
Responsibility:

```text
ViewportController
      +
GraphNavigation
      +
SelectionManager
      +
GraphEventController
      +
DragController
      ↓
GraphInteractionManager
```

This becomes the single object created by `graph_viewer.js` to wire the entire graph engine together.

* `web/render/virtual_renderer.js`
Provides: lazy rendering

* `web/render/viewport_culler.js`

* `web/render/lod.js`
Level of detail:
far zoom: hide labels
mid zoom: show labels
close zoom: full metadata

---

# Last Session Summary 

## Problem statement

Suppose I have this project codebase structure:

```
project_dir/
├── subdir1/                         
│   ├── subsubdir1/
│   │   ├── file2.py         
│   │   └── file3.py          
│   └── file4.py  
├── subdir2/                         
│   ├── subsubdir2/
│   │   ├── file5.py         
│   │   └── file6.py          
│   └── file7.py
└── file1.py  
```

I want to render node graph of this project, but as there are so many files in node, rendering whole graph simultaneously and relocating nodes is not possible. What else i could do is render graph of subdirectories one by one, rearrange node as i want and save it. Finally rendering whole codebase becomes easy as it just load saved state of already arranged subdirectories nodes. How could this be achieved with respect to current graph served using `python/Agentic_Unit_PIE/codebase/modules/codebase_atlas/graph/backend/serve.py`. Also can we group files nodes in boxes as per the subdirectories are organised in the codebase.

## Plan

### 1. Group files into directory clusters (boxes)
The backend already supports `GraphCluster` and the frontend `ClusterRenderer` already draws SVG boxes. The only missing piece is populating clusters from directory structure:
- In `GraphBuilder.build_dependency_graph()`, derive one `GraphCluster` per directory from `FileInfo.path`.
- Set `node.cluster_id = directory_cluster.id` for each file node.
- Build parent/child cluster hierarchy for nested dirs (`parent_cluster_id`).
Result: `ClusterRenderer` draws rounded rects around each subdirectory’s files.

### 2. Per-cluster subgraph rendering
Add a cluster-scoped endpoint:
- `GET /api/graph/cluster/<cluster_id>` returns nodes, cluster-internal edges, and boundary edges to other clusters.
- Frontend opens a cluster, fetches its nodes/edges, runs `GraphLayoutEngine.clusterGrid` (already implemented) or grid, lets user drag, and saves.

### 3. Frontend cluster navigation
- Add a cluster browser panel in `graph_viewer.html` / `graph_viewer.js` listing clusters.
- On selection, call `GraphViewer.setGraphData({...subgraph...})`, which already handles layout, render, and viewport fit.
- When leaving a cluster, POST positions to `/api/save-positions` with a per-cluster graph type key.

### 4. Persist and reload positions per cluster
Current `serve.py` already has position save/load plus `child_offsets` for relative positioning. Extend it:
- Add keys like `directory:<cluster_id>` to `_POS_FILE`.
- `_merge_positions` reads all `directory:*` keys in addition to `unified` so full-graph restore reuses per-cluster layouts.
- POST body uses `graph_type: "directory:<cluster_id>"`.

### 5. Assemble full codebase with saved state
- Build full graph with directory clusters.
- `GraphLayoutEngine.clusterGrid` handles macro (cluster) and micro (file) layout.
- `_merge_positions` overlays saved per-cluster positions, so the final full view uses user-arranged subdirectories.
- Existing viewport culling and chunked rendering in `graph_viewer.js` keep performance large.
