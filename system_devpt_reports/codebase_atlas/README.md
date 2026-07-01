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

### CLI Usage

```bash
# Generate atlas
python -m codebase_atlas.main \
    --project-dir /path/to/your/project \
    --output-dir ./atlas_output \
    --ignore-dirs agent_tools cache data

# Generate atlas and launch interactive graph explorer - Default port 8080
python -m codebase_atlas.main \
    --project-dir /path/to/your/project \
    --serve \
    --port 9090 --host 0.0.0.0 

# Serve a previously generated atlas (skips regeneration)
python -m codebase_atlas.main \
    --output-dir ./atlas_output \
    --load

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

---

## 🕸️ Graph Explorer

**Interactive browser-based visualization of dependency and call graphs.**

After generating the atlas, use `--serve` to start a local web server 

### Features

- **Dependency Graph** — File-level import/require relationships with color-coded risk
- **Call Graph** — Function-level call relationships grouped by file
- **Risk Color Coding** — Entry points (green), High risk (red), Medium (orange), Low (yellow), Circular deps (purple)
- **Interactive** — Pan, zoom, and toggle between graph views in your browser


### Language Support
- ✅ Python (AST-based parsing)
- ✅ JavaScript/TypeScript (regex + pattern matching)
- ✅ React (JSX/TSX component detection)
- ✅ HTML (template engine detection)
- ✅ JSON/YAML (config file analysis)

---

## 🏗️ Architecture

```
project_dir/
├── atlas_output/
│   ├── code_atlas.md           # Layer 1: Project overview (~100 LOC, <1000 tokens) - Agent reads this FIRST                         
│   ├── children/
│   │   ├── core.md             # Layer 2: Core module details (200-400 LOC)
│   │   ├── api.md              # Layer 2: API module details
│   │   ├── utils.md            # Layer 2: Utils module details
│   │   └── tests.md            # Layer 2: Tests module details
│   └── graph.json          
└── codebase/                      # Layer 3: Agent reads only when implementing
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

# 📚 Project Structure

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
