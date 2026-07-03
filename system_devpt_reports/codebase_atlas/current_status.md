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


