# Current Development status

## Phase 1 — Backend (✅ Completed)

* `graph_models.py`
Single source of truth for graph structure.
Contains: GraphData,Node,Edge,Cluster,NodeType,EdgeType

* `graph_builder.py`
AtlasData -> GraphBuilder -> GraphData
Moves graph extraction logic out of renderers.

* `mermaid_renderer.py`
GraphData -> Mermaid text

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
GraphData -> InteractiveGraphJSON
Produces browser-consumable graph data.

* `serve.py`
AtlasData -> GraphBuilder-> GraphData -> MermaidRenderer or InteractiveRenderer

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

### Performance

* `web/render/virtual_renderer.js`
Provides: lazy rendering
* `web/render/viewport_culler.js`
* `web/render/lod.js`
Level of detail:
far zoom: hide labels
mid zoom: show labels
close zoom: full metadata

-----------------------------------

# serve.py Refactor

The new flow should be:

```text
Build Graph
   ↓
interactive_renderer.py
   ↓
Graph JSON
   ↓
serve.py
   ↓
graph_viewer.html
   ↓
GraphViewer
   ↓
SVG Renderers
```

## Composition After Refactor

```text
serve.py
    ↓
/api/graph
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
SVG
```

---

# One Architecture Improvement Before `interaction.js`

Currently `drag.js` performs:

```javascript
renderer.render();
```

on every pointer move.

That is acceptable for:

```text
100–300 nodes
```

but becomes expensive later.

A better future direction is:

```text
DragController
      ↓
state update
      ↓
renderer.updateNode(...)
renderer.updateEdge(...)
renderer.updateCluster(...)
```

instead of full rerender.

For now, keep the full rerender until the interaction stack is complete.

## `web/interaction/interaction.js`

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

---

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

## Interactive engine
GraphData ──→ InteractiveRenderer ──→ JSON ──→ graph_viewer.html (server-injected)

## Mermaid engine  
GraphData ──→ MermaidRenderer ──→ text ──→ mermaid_view.html (server-injected)

## Interactive Call graph loading issue

Browser shows alert that page is consuming too much resources. One cpu core running at 100% while call graph loading. Takes too much time. How to fix and render call graph using less resources so that it loads fast.

### Files for context to solve call graph loading bottleneck
* web/core/storage.js
* web/graph_viewer.js
* web/render/clusters.js
* web/render/edges.js
* web/render/nodes.js
* web/render/renderer.js

---

# Session Summary - 2026-06-30

### 1. `serve.py` — Refactored into 3 functions
- `create_app(dep_graph, call_graph)` — renders `GraphData` → JSON/mermaid at startup, delegates to `_build_app()`
- `create_app_from_dir(output_dir)` — loads pre-saved `interactive_dep.json` / `interactive_call.json` / `mermaid_dep.txt` / `mermaid_call.txt` directly
- `_build_app(dep_json, call_json, dep_mermaid, call_mermaid)` — shared Flask route definitions

### 2. `main.py` — `--serve` path saves 6 files to `atlas_output/`
- `graphdata_dep.json` / `graphdata_call.json` — canonical `GraphData` via `GraphSerializer.save_json()`
- `interactive_dep.json` / `interactive_call.json` — frontend-ready via `InteractiveRenderer.render()`
- `mermaid_dep.txt` / `mermaid_call.txt` — mermaid text via `MermaidRenderer.render()`

---

# Session Summary — 2026-07-01

## Problems fixed

### 1. Call graph infinite loop in `hierarchical()` layout
- **Root cause**: BFS level-assignment loop never terminated on cyclic call graphs (recursion, mutual recursion). 50-node graph with one cycle hung indefinitely.
- **Fix**: Rewrote `hierarchical()` with DFS + visiting-set to detect back-edges and skip them (`layout/layout.js`).

### 2. Double full render on startup (performance)
- **Root cause**: `GraphRenderer.initialize()` called `render()` synchronously before SVG was measured, then `whenMeasured` triggered a second chunked render.
- **Fix**: Removed the eager `this.render()` from `initialize()` (`render/renderer.js`). Switched chunking decision from `graphType === "call"` to `nodeCount >= LARGE_GRAPH_THRESHOLD` (`graph_viewer.js`).

### 3. LOD culling for fit-to-view zoom
- **Fix**: Added `computeLod()` to `ViewportCuller` (`render/viewport_culler.js`). Nodes tagged as `"dot"`, `"simple"`, or `"full"` based on screen-space size. `NodeRenderer.createNode()` skips `<text>` labels for sub-28px nodes and renders a single `<circle>` for sub-4px nodes (`render/nodes.js`).

### 4. Event system: `GraphState.emit()` didn't reach `EventEmitter` listeners
- **Root cause**: `GraphState` overrode `emit()` (uses `this.listeners`) but inherited `on()` from `EventEmitter` (uses `this._listeners`). Renderer listeners registered via `state.on()` were never called.
- **Fix**: `GraphState.emit()` now calls `super.emit()` after dispatching its own pool (`core/state.js`).

### 5. Viewport changes not persisted
- **Root cause**: `ViewportController._syncState()` set `state.zoom/panX/panY` directly without emitting events, so storage auto-save never triggered.
- **Fix**: `_syncState()` now emits `"viewportChanged"` through `state.emit()` (`viewport/viewport.js`).

### 6. Graph type switch didn't restore saved positions
- **Root cause**: `setGraphData()` called `applyInitialLayout()` but never called `restoreState()`, so saved positions were lost when switching graphs.
- **Fix**: Added `restoreState()` call after layout in `setGraphData()` (`graph_viewer.js`).

### 7. Shared localStorage key between graph types
- **Root cause**: Both `"dependency"` and `"call"` graphs saved under the same `localStorage` key, overwriting each other.
- **Fix**: Storage namespace is now `"interactive-graph:{graph_type}"`. `setGraphData()` updates the namespace on switch (`graph_viewer.js`).

### 8. Drag positions not persisted to disk
- **Root cause**: Positions were only in `localStorage` (browser-only).
- **Fix**: Added `POST /api/save-positions` route (`serve.py`). Frontend POSTs positions on every `"nodes:moved"` event (`graph_viewer.js`). On server start, saved positions are merged into graph data from `node_pos_dep.json` / `node_pos_call.json`.

### 9. `forceDirected()` O(n²) landmine
- **Fix**: Added size guard — falls back to `grid` layout if >200 nodes (`layout/layout.js`).

### 10. Removed PixiJS viewer
- Removed `pixi_view.html`, `pixi_viewer.js`, `pixi_renderer.js`, and all route/print references (`serve.py`, `main.py`).

## Files modified
- `graph/backend/serve.py`
- `graph/web/core/state.js`
- `graph/web/core/storage.js`
- `graph/web/graph_viewer.js`
- `graph/web/render/renderer.js`
- `graph/web/render/nodes.js`
- `graph/web/render/viewport_culler.js`
- `graph/web/render/edges.js`
- `graph/web/viewport/viewport.js`
- `graph/web/viewport/navigation.js`
- `graph/web/layout/layout.js`
- `graph/web/interaction/drag.js`
- `graph/web/interaction/events.js`
- `graph/web/interaction/interaction.js`
- `codebase_atlas/main.py`

