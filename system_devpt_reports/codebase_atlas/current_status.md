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

## Interactive engine
GraphData ─> InteractiveRenderer ─> JSON ─> graph_viewer.html (server-injected)

## Mermaid engine  
GraphData ─> MermaidRenderer ─> text ─> mermaid_view.html (server-injected)

---

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

---

# Session Summary — 2026-07-02

### 1. Removed duplicate node-position storage from `localStorage`
- **Root cause**: `GraphStorage` persisted/restored `nodePositions` to/from browser `localStorage`, causing coordinates from deleted layout experiments to stick even after deleting `node_pos_*.json`.
- **Fix**: Removed `nodePositions` extraction in `createSnapshot()`, removed `nodePositions` restoration in `restore()`, and removed `nodes:moved` auto-save. Bumped `STORAGE_VERSION` from `1` to `2`. Node positions are now authoritative only in server-side JSON files.

### 2. Cluster-aware initial layout for call graphs
- **Fix**: Added `GraphLayoutEngine.clusterGrid()` in `layout/layout.js`. It treats each `cluster_id` as a macro-node, runs `hierarchical()` on the cluster graph, then lays out member nodes locally within each cluster. Added `_resolveClusterOverlaps()` to push intersecting cluster bounding boxes apart. Wired `graph_viewer.js` to use `clusterGrid` automatically when `graph_type === "call"` and clusters exist.

### 3. Project-scoped position files
- **Root cause**: `node_pos_dep.json` / `node_pos_call.json` were keyed only by graph type, so reusing `atlas_output` for a different project leaked stale positions.
- **Fix**: Added `atlas_meta.json` with `project_id` (resolved absolute path). Position files now store `{"project_id": "...", "positions": {...}}`. Save and merge paths validate the embedded `project_id`. Legacy plain-dict files are accepted once, then upgraded on next save.

### 4. Removed mermaid renderer, viewer, and intermediate artifacts
- **Removed**: `graph/backend/renderers/mermaid_renderer.py`, `graph/web/mermaid_view.html`, `create_app_from_dir()`, `_merge_positions_into_json()`.
- **Removed writes**: `interactive_dep.json`, `interactive_call.json`, `mermaid_dep.txt`, `mermaid_call.txt` are no longer generated. `--serve` and `--load` now rely exclusively on canonical `graphdata_*.json` plus project-scoped persistent positions.

### 5. Preserved position files across atlas regeneration
- Updated `clean_directory()` call in `main.py` to keep `node_pos_dep.json` and `node_pos_call.json` during output-directory cleanup, so manual rearrangements survive atlas regeneration.
