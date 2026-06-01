### Phase 1 — Foundation (Highest Priority)

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

#### Stage 1 — Composition (✅ Completed)

* graph/backend/
    ├── graph_models.py
    ├── graph_builder.py
    ├── graph_serializer.py
    └── serve.py

* graph/backend/renderers/
    ├── mermaid_renderer.py
    └── interactive_renderer.py

* graph/web/
    ├── graph_viewer.html
    └── graph_viewer.js

#### Stage 2 — Core Engine (✅ Completed)

* graph/web/core/
    ├── types.js
    ├── state.js
    ├── storage.js
    ├── constants.js
    └── events.js

#### Stage 3 — Rendering (✅ Completed)

* graph/web/render/
    ├── renderer.js
    ├── nodes.js
    ├── edges.js
    ├── clusters.js
    └── styles.js

You already have a formal backend graph model. 
The frontend is no longer merely rendering SVG.
You have a complete vertical slice::

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

#### Stage 4 — Navigation

```text
9. graph_viewport.js
10. graph_navigation.js
```

Reason: Zoom/pan must exist before interactions.

#### Stage 5 — Interaction

```text
11. graph_drag.js
12. graph_selection.js
13. graph_events.js
14. graph_interaction.js
```

Reason: These consume renderer + viewport + state.

#### Stage 6 — Search & Filtering

```text
15. graph_search.js
16. graph_filters.js
17. graph_algorithms.js
```

Reason: Need state already available.

#### Stage 7 — UI

```text
18. graph_toolbar.js
19. graph_sidebar.js
```

---