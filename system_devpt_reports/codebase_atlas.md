### Phase 1 — Foundation 

#### 1. `graph_models.py`
Single source of truth for graph structure.
Contains: GraphData,Node,Edge,Cluster,NodeType,EdgeType

#### 2. `graph_builder.py`
AtlasData -> GraphBuilder -> GraphData
Moves graph extraction logic out of renderers.

#### 3. `mermaid_renderer.py`
GraphData -> Mermaid

#### 4. `graph_serializer.py`
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

#### 5. `interactive_renderer.py`
GraphData -> InteractiveGraphJSON
Produces browser-consumable graph data.

#### 6. `graph_viewer.js`
Real graph engine. Features:
* node drag
* edge tracking
* zoom
* pan
No SVG path hacking.

#### 7. `graph_layout.js`
Layout algorithms
* dagre
* force layout
* hierarchical layout

#### 8. `graph_interaction.js`
Purpose: Search, Highlight, Selection, Focus, Collapse

#### 9. `serve.py` refactor
Current: AtlasData -> MermaidGenerator -> HTML
New: AtlasData -> GraphBuilder-> GraphData -> MermaidRenderer or InteractiveRenderer

### Phase 5 — Advanced Features

#### 10. `graph_search.py`

Features:

* node search
* path search
* dependency tracing
* impact tracing

#### 11. `graph_algorithms.py`

Algorithms:

* shortest path
* strongly connected components
* cycle detection
* dependency depth
* impact propagation

#### 12. `graph_state.py`

Persistent state:

```text
Pinned nodes
Saved layouts
Bookmarks
Filters
User preferences
```

---

#### Stage 1 — Graph Backend (✅ Completed)

graph/backend/
    ├── renderers/
    │   ├── mermaid_renderer.py
    │   └── interactive_renderer.py
    ├── graph_models.py
    ├── graph_builder.py
    ├── graph_serializer.py
    └── serve.py
   
#### Stage 2 — Graph Web Frontend (✅ Completed)

graph/web/
├── core/
│   ├── types.js
│   ├── state.js
│   ├── events.js
│   ├── constants.js
│   └── storage.js
│
├── render/
│   ├── renderer.js
│   ├── nodes.js
│   ├── edges.js
│   ├── clusters.js
│   └── styles.js
│
├── viewport/
│   ├── viewport.js [Provides: mouse wheel zoom,trackpad zoom,middle mouse pan,space+drag pan,fit to view,center on node, coordinate transforms]
│   └── navigation.js  [Responsibilities:focus node, go to node, jump to cluster, zoom to selection, zoom to bounds, fitGraph. Consumes: viewport, state, renderer]
│
├── interaction/  [Reason: These consume renderer + viewport + state.]
│   ├── drag.js  [Provides: node dragging,multi-node dragging,position updates,state updates. Uses:events,selection,viewport,state]
│   ├── selection.js  [Almost every interaction starts with selection.Purpose: click node, shift-click, ctrl-click, multi-select, box selection, clear selection]
│   ├── events.js  [Unified DOM→State event translation.Handles: SVG click, node click,edge click,cluster click,background click,hover,selection, pointerdown, pointermove, pointerup, wheel, keyboard]
│   └── interaction.js  [Composition layer. Wires together: selection, drag, navigation, viewport, events]
│
├── layout/
│   └── layout.js  [Only if backend positions are missing or poor. Provides: force layout, hierarchical layout, cluster layout]
│
├── utils/
│   └── geometry.js
│
├── graph_viewer.js
└── graph_viewer.html

The frontend is no longer merely rendering SVG.
You have a complete vertical slice:

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


---


## Advanced Features 

### Search and filter

* `web/search/search.js`
For large graphs. Provides: find node,jump to node,highlight matches

* `search/filters.js`

* `search/algorithms.js`

### UI

* `web/sidebar/sidebar.js`
Display: selected node details, metadata, neighbors, incoming edges, outgoing edges, cluster info

* `web/toolbar/toolbar.js`
Provides: fit view, zoom in, zoom out, reset, toggle clusters, search button

### Intelligence

* `web/interaction/highlight.js`
Very useful for code graphs.Provides: upstream path, downstream path, shortest path, dependency chain, impact analysis

* `web/interaction/focus.js`
Provides: focus mode, hide unrelated nodes, show neighborhood, dependency cone

### Performance

* `web/render/virtual_renderer.js`
Provides: viewport culling, lazy rendering

* `web/render/lod.js`
Level of detail:
far zoom: hide labels
mid zoom: show labels
close zoom: full metadata

-----------------------------------

# serve.py Refactor

The new `serve.py` should have a very different responsibility than the old Mermaid-based version.

The old flow was approximately:

```text
Mindmap
   ↓
Mermaid text
   ↓
Mermaid SVG
   ↓
Inject JS
   ↓
Manipulate SVG
```

The new flow should be:

```text
Mindmap
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

# Even Better Architecture

For long-term maintainability, I would split serving into:

```text
serve.py
    ↓

routes/
├── graph_api.py
├── page_routes.py
└── static_routes.py
```

because your project is already evolving beyond a simple graph viewer into:

```text
agent_unit_pie
    ↓
simulation
    ↓
knowledge graph
    ↓
interactive explorer
```

and `serve.py` will otherwise become another 1500-3000 line file like the original implementation.

-----------

At this stage, `serve.py` should become extremely small.

Its job is only:

```text
Build Graph
      ↓
InteractiveRenderer
      ↓
JSON API
      ↓
graph_viewer.html
```

Recommended flow:

```python
graph = GraphBuilder.build(...)

interactive_json =
    InteractiveRenderer.render(graph)

return jsonify(interactive_json)
```

Routes:

```text
/
    -> graph_viewer.html

/api/graph
    -> InteractiveRenderer JSON

/api/health
    -> status
```

No SVG generation.

No Mermaid.

No DOM injection.

No JavaScript string generation.

No SVG patching.

No graph interaction logic.

---

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

## One Architecture Improvement Before `interaction.js`

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

### At this point the graph engine contains

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

This is a complete non-advanced interactive graph engine. The next work should be integration/refactoring:

```text
1. Refactor graph_viewer.js
2. Refactor graph_viewer.html
3. Refactor serve.py
4. Verify InteractiveRenderer JSON compatibility
5. End-to-end test
```

before adding any new features.
