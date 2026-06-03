# 🗺️ Codebase Atlas

**AI-powered codebase mapping for intelligent agent navigation**

Generate compact, hierarchical documentation that helps LLM agents understand your codebase structure, dependencies, and impact analysis—without reading every file.

---

## 🎯 Why Codebase Atlas?

**The Problem:**
- Reading entire codebases eats 10,000+ tokens for medium projects
- LLM agents waste time scanning irrelevant files
- No impact analysis: "If I change X, what breaks?"
- Docstrings (the semantic source of function behavior) are locked inside source files

**The Solution:**
- **3-Layer Navigation**: base.md (100 LOC) → children/*.md (300 LOC) → source code
- **60-70% Context Reduction**: Ultra-compact notation eliminates redundancy
- **Impact Analysis**: Inline "what breaks if" matrix for every function
- **Docstrings Inline**: Every function includes its docstring so agents understand behavior without reading source files
- **Multi-Language**: Python, JavaScript/TypeScript, React, HTML

---

## ⚡ Quick Start

### Basic Usage

```python
from codebase_atlas.main import generate_atlas

# Generate atlas for your project
generate_atlas(
    project_dir="/path/to/your/project",
    output_dir="./atlas_output"
)
```

### CLI Usage

```bash
# Generate atlas
python -m codebase_atlas.main \
    --project-dir /path/to/your/project \
    --output-dir ./atlas_output

# Generate atlas and launch interactive graph explorer
python -m codebase_atlas.main \
    --project-dir /path/to/your/project \
    --serve \
    --port 8080

# Serve a previously generated atlas (skips regeneration)
python -m codebase_atlas.main \
    --output-dir ./atlas_output \
    --load

# Ignore specific directories
python -m codebase_atlas.main \
    --project-dir /path/to/your/project \
    --output-dir ./atlas_output \
    --ignore-dirs agent_tools cache data
```

---

## 🕸️ Graph Explorer

**Interactive browser-based visualization of dependency and call graphs.**

After generating the atlas, use `--serve` to start a local web server 

### Features

- **Dependency Graph** — File-level import/require relationships with color-coded risk
- **Call Graph** — Function-level call relationships grouped by file
- **Risk Color Coding** — Entry points (green), High risk (red), Medium (orange), Low (yellow), Circular deps (purple)
- **Interactive** — Pan, zoom, and toggle between graph views in your browser

### Usage

```bash
# Default port 8080
python -m codebase_atlas.main --project-dir . --serve

# Custom host and port
python -m codebase_atlas.main --project-dir . --serve --host 0.0.0.0 --port 9090
```

## 🎛️ Configuration

Edit `codebase_atlas/config.py` to customize:

```python
# Key settings
MAX_FILES_PER_CHILD = 10        # Files per children/*.md
BASE_MAX_LOC = 100              # Base.md line limit
IMPACT_DEPTH = 3                # Track call chains 3 levels deep
RISK_THRESHOLD_HIGH = 3         # 3+ dependents = HIGH risk
```

### Language Support
- ✅ Python (AST-based parsing)
- ✅ JavaScript/TypeScript (regex + pattern matching)
- ✅ React (JSX/TSX component detection)
- ✅ HTML (template engine detection)
- ✅ JSON/YAML (config file analysis)

---

## 🏗️ Architecture

```
atlas_output/
├── code_atlas.md           # Layer 1: Project overview (~100 LOC, <1000 tokens)
│                           # Agent reads this FIRST
├── children/
│   ├── core.md             # Layer 2: Core module details (200-400 LOC)
│   ├── api.md              # Layer 2: API module details
│   ├── utils.md            # Layer 2: Utils module details
│   └── tests.md            # Layer 2: Tests module details
└── [source files]          # Layer 3: Agent reads only when implementing
```

### Navigation Flow
```
1. Agent reads code_atlas.md → Gets overview, entry points, critical deps
2. Agent identifies relevant module → Reads specific children/X.md
3. Agent reads actual source file only when line-level implementation is needed
```

## 📖 Output Format

A single unified format designed for both LLM agents and human readers.
Every function includes its signature, impact analysis, and docstring inline.

```markdown
F001│main.py│250│⚡
S: Application entry point and initialization
D: ►F002,F005 ●pygame,numpy
C: GameManager│[start,update,render,shutdown]
   S: Manages game state and lifecycle
F: calculate_damage(attacker,target,crit=False)→int
   ↳Called by: F012,F045 | Calls: F024,F025
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F012,F045,F050]
   S: Calculates final damage after applying armor, resistances,
   S: and critical hit modifiers.
```

### Symbol Legend
```
│  = Separator
►  = Internal dependency
●  = External library
⚡ = Entry point
⚛  = React component
↔  = Circular dependency
↳  = Impact analysis
S:  = Summary / docstring
🔴 = HIGH risk (3+ dependents)
🟡 = MEDIUM risk (2 dependents)
🟢 = LOW risk (1 dependent)
⚪ = SAFE (0 dependents)
```

---

## 🔍 Impact Analysis

Every function includes inline impact data showing who calls it, what it calls, and what breaks if changed:

```markdown
F: process_payment(user_id, amount)→bool
   ↳Called by: F023,F045,F067 | Calls: F089,F090
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F023,F045,F067]
   S: Validates payment method, processes transaction, and
   S: updates user balance and transaction log.
```

**Risk Scoring:**
- 🔴 **HIGH** (3+ dependents): Critical function, extensive testing needed
- 🟡 **MEDIUM** (2 dependents): Important function, verify callers
- 🟢 **LOW** (1 dependent): Limited impact, safer to modify
- ⚪ **SAFE** (0 dependents): Unused or leaf function

---

## 🚀 How LLM Agents Use It

### Scenario 1: "Add a new feature"
```
1. Agent reads code_atlas.md → Identifies relevant module: "api"
2. Agent reads children/api.md → Finds entry points, key functions, and docstrings
3. Agent understands behavior from docstrings → Reads source only for implementation
```

### Scenario 2: "Refactor calculate_damage()"
```
1. Agent searches code_atlas.md → Finds calculate_damage in [F023]
2. Agent reads children/combat.md → Sees impact analysis:
   - 🔴 HIGH risk (3 callers)
   - Breaks: [F001, F012, F045]
   - Docstring explains exactly what the function does
3. Agent plans:
   - Update calculate_damage signature
   - Fix all 3 callers
   - Update tests for F050 (reads output)
```

### Scenario 3: "Understand authentication flow"
```
1. Agent reads code_atlas.md → Entry point: [F005] auth.py:login()
2. Agent reads children/auth.md → Sees login() docstring explaining the flow
3. Agent understands full flow from docstrings without reading implementation
```

---

## 📊 Performance

| Project Size | Atlas Generation | Context Saved | Agent Speed |
|--------------|------------------|---------------|-------------|
| 5K LOC | ~2 sec | 70% | 3x faster |
| 10K LOC | ~5 sec | 65% | 3x faster |
| 50K LOC | ~20 sec | 75% | 4x faster |

---

## 🛠️ Advanced Configuration

### Ignore Directories

Additional directories can be ignored via CLI or config:

```bash
# CLI: pass directory names (space-separated)
python -m codebase_atlas.main --ignore-dirs docs examples deprecated
```

```python
# codebase_atlas/config.py

# Ignore additional directories
IGNORE_DIRS.update({'docs', 'examples', 'deprecated'})
```

# Add custom entry point patterns
ENTRY_POINT_PATTERNS['python'].append('app.run')

# Adjust impact depth (default: 3)
IMPACT_DEPTH = 5  # Track deeper call chains (slower)

# Change risk thresholds
RISK_THRESHOLD_HIGH = 5    # More lenient
RISK_THRESHOLD_MEDIUM = 3
```

### Group Files by Functionality

```python
# Override default directory-based grouping
CUSTOM_GROUPING = {
    'core': ['entities.py', 'components.py', 'systems.py'],
    'api': ['routes.py', 'handlers.py', 'middleware.py'],
    'data': ['models.py', 'database.py', 'migrations/']
}
```

---

## 📚 Project Structure

```
codebase_atlas/
├── config.py                # Configuration & constants
├── models.py                # Data structures
├── scanner.py               # File discovery
├── parsers/
│   ├── base_parser.py       # Abstract parser
│   ├── python_parser.py     # AST-based Python
│   ├── javascript_parser.py # JS/TS/React
│   ├── config_parser.py     # JSON/YAML
│   └── html_parser.py       # HTML templates
├── analyzers/
│   ├── dependency_analyzer.py   # Build dep graph
│   ├── impact_analyzer.py       # What-breaks-if
│   └── entry_point_detector.py  # Entry points
├── generators/
│   ├── base_generator.py        # Generate code_atlas.md
│   ├── detail_generator.py      # Generate children/*.md
├── utils/
│   ├── formatting.py            # Unified format with docstrings
│   └── io_helpers.py            # File I/O
├── graph/
│   ├── backend/
│   │   ├── renderers/
│   │   │   ├── mermaid_renderer.py
│   │   │   └── interactive_renderer.py
│   │   ├── graph_models.py
│   │   ├── graph_builder.py
│   │   ├── graph_serializer.py
│   │   └── serve.py
│   └── web/
│       ├── core/
│       │   ├── types.js
│       │   ├── state.js         # Persistent state: Pinned nodes, Saved layouts, Bookmarks, Filters ,User preferences
│       │   ├── events.js
│       │   ├── constants.js
│       │   └── storage.js
│       │
│       ├── render/
│       │   ├── renderer.js
│       │   ├── nodes.js
│       │   ├── edges.js
│       │   ├── clusters.js
│       │   └── styles.js
│       │
│       ├── viewport/
│       │   ├── viewport.js         # Provides: mouse wheel zoom,trackpad zoom,middle mouse pan,space+drag pan,fit to view,center on node, coordinate transforms
│       │   └── navigation.js       # Responsibilities:focus node, go to node, jump to cluster, zoom to selection, zoom to bounds, fitGraph. Consumes: viewport, state, renderer
│       │
│       ├── interaction/            # Reason: These consume renderer + viewport + state.
│       │   ├── drag.js             # Provides: node dragging,multi-node dragging,position updates,state updates. Uses:events,selection,viewport,state
│       │   ├── selection.js        # Almost every interaction starts with selection.Purpose: click node, shift-click, ctrl-click, multi-select, box selection, clear selection
│       │   ├── events.js           # Unified DOM→State event translation.Handles: SVG click, node click,edge click,cluster click,background click,hover,selection, pointerdown, pointermove, pointerup, wheel, keyboard
│       │   └── interaction.js      # Composition layer. Wires together: selection, drag, navigation, viewport, events
│       │
│       ├── layout/
│       │   └── layout.js           # Only if backend positions are missing or poor. Provides: force layout, hierarchical layout, cluster layout
│       │
│       ├── utils/
│       │   └── geometry.js
│       │
│       ├── mermaid_view.html
│       ├── graph_viewer.html
│       └── graph_viewer.js
└── main.py                      # CLI entry point
```

## 🎯 Roadmap

### Phase 1: Core (Current)
- ✅ Multi-language parsing
- ✅ Dependency analysis
- ✅ 3-layer output
- ✅ Unified agent/human format
- ✅ Docstrings as semantic source of truth

### Phase 2: Impact Analysis (Current)
- ✅ Function call tracking
- ✅ Variable usage tracking
- ✅ Risk scoring
- ✅ Inline impact matrix

### Phase 3 (Next)
- ✅ **Graph explorer**: Standalone `--serve` CLI command that starts a local browser-based Mermaid graph viewer for human exploration of dependency and call graphs
- ⏳ **Dead code detection**: Flag functions with 0 callers and no entry-point path

### Phase 4: Later features 
- ⏳ **Interactive CLI dashboard**: Terminal TUI (Textual/Rich) for browsing atlas data without opening markdown files
- ⏳ **Web UI export**: Generate a self-contained HTML report with search, filtering, and expand/collapse navigation

### Phase 5: Code Quality & Analysis
- ⏳ **Cyclomatic complexity**: Per-function complexity score in the atlas output
- ⏳ **Test coverage mapping**: Cross-reference functions with test files; flag untested functions
- ⏳ **Hot path detection**: Identify frequently-called functions and deep call chains as performance risks
- ⏳ **Security analysis**: Detect dangerous patterns (eval, exec, raw SQL) and flag vulnerable dependency versions

### Phase 6: Advanced Impact & Architecture
- ⏳ **Transitive impact chains**: N-level "what breaks if I change X" with full transitive closure
- ⏳ **Architecture conformance**: Define allowed dependency rules (e.g., "utils must not import api") and flag violations
- ⏳ **Module coupling score**: Quantitative coupling metrics (efferent/influent coupling per module)
- ⏳ **Layered architecture view**: Auto-detect layering (presentation → business → data) and flag layer breaks
- ⏳ **Circular dependency resolution hints**: Suggest refactoring paths for breaking circular deps

### Phase 7: Data Interoperability
- ⏳ **JSON/GraphML export**: Machine-readable atlas for external tools
- ⏳ **Neo4j / graph database import**: Load the dependency graph into a graph DB for complex queries
- ⏳ **OpenTelemetry integration**: Correlate runtime traces with static call graphs
- ⏳ **API surface extraction**: Generate OpenAPI/Swagger spec from route decorators and docstrings
- ⏳ **Architecture decision records (ADR)**: Link ADRs to affected modules in the atlas

## Unwanted features

### Git & CI Integration
- ⏳ **Git-aware atlas**: Track last-modified timestamps, commit frequency, and author ownership per function
- ⏳ **Diff atlas**: `--diff` mode that compares two atlases and highlights new, changed, and removed functions
- ⏳ **CI pipeline hook**: Auto-generate atlas on PR, post diff as comment showing what changed and what breaks
- ⏳ **Pre-commit guard**: Warn if a commit touches a HIGH-risk function without test changes

## 💡 Tips for Best Results

1. **Write good docstrings**: The atlas surfaces docstrings as the explanation of what each function does—make them descriptive
2. **Run regularly**: Generate atlas after major changes
3. **Update config**: Customize for your project's structure

---

# Current Development status

## Phase 1 — Backend (✅ Completed)

* `graph_models.py`
Single source of truth for graph structure.
Contains: GraphData,Node,Edge,Cluster,NodeType,EdgeType

* `graph_builder.py`
AtlasData -> GraphBuilder -> GraphData
Moves graph extraction logic out of renderers.

* `mermaid_renderer.py`
GraphData -> Mermaid

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

## Advanced Features (Not needed yet)

### Search and filter

* `web/search/search.js`
For large graphs. Provides: find node,jump to node,highlight matches, path search, dependency tracing, impact tracing
* `search/filters.js`
* `search/algorithms.js`
Algorithms: shortest path,strongly connected components, cycle detection, dependency depth, impact propagation

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

# At this point the graph engine contains

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

// Interactive engine
GraphData ──→ InteractiveRenderer ──→ JSON ──→ graph_viewer.html (server-injected)

// Mermaid engine  
GraphData ──→ MermaidRenderer ──→ text ──→ mermaid_view.html (server-injected)