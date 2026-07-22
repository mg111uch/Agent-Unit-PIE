# 🎯 Roadmap

### Phase 1: Core
- ✅ Multi-language parsing
- ✅ Dependency analysis
- ✅ 3-layer output
- ✅ Unified agent/human format
- ✅ Docstrings as semantic source of truth

### Phase 2: Impact Analysis 
- ✅ Function call tracking
- ✅ Variable usage tracking
- ✅ Risk scoring
- ✅ Inline impact matrix

### Phase 3: Graph explorer
- ✅ **Graph serve**: Standalone `--serve` CLI command that starts a local browser-based interactive graph viewer.
- ✅ **JSON/GraphML export**: Machine-readable atlas for external tools
- ⏳ **Dead code / unreached node detection** — nodes with no incoming edges and not marked `entry_point` are candidates for unused code; a filter or highlight for these is cheap given you already compute in-degree in `hierarchical()`.

- **Search and filter**
  * `web/search/search.js`
  For large graphs. Provides: find node,jump to node,highlight matches, path search, dependency tracing, impact tracing
  * `search/filters.js`
  * `search/algorithms.js`
  Algorithms: shortest path,strongly connected components, cycle detection, dependency depth, impact propagation

- **Intelligence**
* `web/interaction/highlight.js`
Very useful for code graphs.Provides: upstream path, downstream path, shortest path, dependency chain, impact analysis
* `web/interaction/focus.js`
Provides: focus mode, hide unrelated nodes, show neighborhood, dependency cone

# Graph Addons - Unwanted features - Not needed yet

- ⏳ **Web UI export**: Generate a self-contained HTML report with search, filtering, and expand/collapse navigation
- ⏳ **Hot path detection**: Identify frequently-called functions and deep call chains as performance risks
- ⏳ **Transitive impact chains**: N-level "what breaks if I change X" with full transitive closure
- ⏳ **Architecture conformance**: Define allowed dependency rules (e.g., "utils must not import api") and flag violations
- ⏳ **Layered architecture view**: Auto-detect layering (presentation → business → data) and flag layer breaks
- ⏳ **Circular dependency resolution hints**: Suggest refactoring paths for breaking circular deps
- ⏳ **Interactive CLI dashboard**: Terminal TUI (Textual/Rich) for browsing atlas data without opening markdown files
- ⏳ **Git-aware atlas**: Track last-modified timestamps, commit frequency, and author ownership per function
- ⏳ **Diff atlas**: `--diff` mode that compares two atlases and highlights new, changed, and removed functions
- ⏳ **CI pipeline hook**: Auto-generate atlas on PR, post diff as comment showing what changed and what breaks
- ⏳ **Pre-commit guard**: Warn if a commit touches a HIGH-risk function without test changes
- ⏳ **Cyclomatic complexity**: Per-function complexity score in the atlas output
- ⏳ **Test coverage mapping**: Cross-reference functions with test files; flag untested functions
- ⏳ **Security analysis**: Detect dangerous patterns (eval, exec, raw SQL) and flag vulnerable dependency versions
- ⏳ **Module coupling score**: Quantitative coupling metrics (efferent/influent coupling per module)
- ⏳ **Neo4j / graph database import**: Load the dependency graph into a graph DB for complex queries
- ⏳ **OpenTelemetry integration**: Correlate runtime traces with static call graphs
- ⏳ **API surface extraction**: Generate OpenAPI/Swagger spec from route decorators and docstrings
- ⏳ **Architecture decision records (ADR)**: Link ADRs to affected modules in the atlas

### Collaboration
- **Shareable deep links** — encode selected node, expanded files, and viewport (zoom/pan) into the URL so a link reproduces exactly what someone is looking at, useful for code review / pairing discussions.
- **Annotations/comments pinned to nodes** — lightweight sticky notes attached to a node id, persisted alongside positions, for team notes like "this needs refactoring" directly on the graph.

### Export & reporting
- **Export current view as SVG/PNG** — since everything's already SVG, serializing the current viewport (or the full graph) to a static image for docs/slides is close to free.
- **Export a filtered subgraph as JSON** — e.g. "just this file's call graph" as a standalone file, useful for feeding into other tools or attaching to a ticket.

### Diffing & history
- **Graph diff between two builds** — Not needed
- **Position history / undo** — since node drag persists to the server, a simple undo stack (even just "revert to last saved layout") avoids users being stuck after an accidental drag-everything-around.

### Navigation & orientation
- **Minimap** —  small fixed-position overview panel showing the whole graph with a viewport rectangle, since at 5,000+ nodes it's easy to get lost after a few pans/zooms. Reuses the same node position data you already have; render it once per viewport change as a tiny separate SVG, not a scaled copy of the main one.
- **Breadcrumb / focus trail** — when a file is expanded and its modal is open, show a small trail of "how did I get here" (e.g. search → file X → function Y) so users can retrace exploration.
- **"Jump to node" search-as-you-type** — A fuzzy-match search over node labels that pans/zooms/highlights on select is one of the highest-value additions for any graph over a few hundred nodes.
- **Keyboard navigation** — arrow keys to step between a selected node's neighbors (follow an edge), Tab to cycle through search results. Cheap to add given selection state already exists.

### Analysis-oriented overlays
- **Path highlighting** — select two nodes, highlight the shortest (or all) call/dependency paths between them. Very useful for "how does A eventually reach B" questions, which is the whole point of a call graph.
- **Impact/blast-radius view** — select a node, dim everything except its transitive callers (upstream) or callees (downstream), with a toggle for direction and depth limit. You already compute `impact_nodes` on the backend (seen in `graph_builder.py`) — this may just be exposing existing data.
- **Cycle detection & highlighting** — given you just fixed a layout hang caused by an undetected cycle, surfacing "these N functions form a recursive/mutual-recursion cluster" as a visual callout (colored border, or a dedicated "cycles" panel) turns a bug you had to fix into a feature users can see directly.
- **Risk-level filtering** — you already have `risk_level` per node; add a sidebar filter to show only medium/high-risk nodes and their immediate neighborhood, rather than requiring users to scan the whole graph for colored borders.

### Performance / scale (natural extensions of what you already built)
- **Server-side search index** — for very large graphs, doing fuzzy search over thousands of labels client-side is fine now, but if this grows, a small backend endpoint for search avoids shipping every label up front.
- **Edge bundling for dense regions** — once you have thousands of edges even after dedup, bundling near-parallel edges into curved bundles (a well-known graph-drawing technique) reduces visual clutter more than dedup alone can.
- **Persisted view presets** — "default view," "high-risk only," "entry points only" as named, saved viewport+filter combinations, so users don't have to reconstruct a useful filtered view every session.

### Data model extensions
- **Multiple edge types visualized distinctly** — you already style by `edge_type` (`EDGE_STYLES`); a legend toggle to show/hide by type (imports vs inherits vs calls) would make the existing styling more actionable rather than purely decorative.
- **Test coverage overlay** — if coverage data is available elsewhere in the codebase-analysis tooling, coloring nodes by test coverage percentage alongside risk level would combine two of the most useful signals for "where should I be careful."

---

# Codebase Atlas — Improvement Plan

## 1. Improving Codebase Exploration Mechanism

The current 3-layer navigation (base.md → children/*.md → source) works but has gaps the agent feels. Concrete upgrades:

- **Semantic, not directory, grouping.** Replace directory-based children/ with clusters built from the call graph (strongly connected components + entry-point reachability). Functionally related code that lives in different folders should land in the same child file.
- **Progressive disclosure by intent.** Add a query-aware view: "show me what touches `auth`" returns a slice containing only the matching subgraph with the impact matrix, not the whole module.
- **Bidirectional links everywhere.** Every `F012` in any child file should be a clickable reference (and a machine-readable id) that jumps to its definition and its callers. Right now ids exist but aren't navigable in plain markdown rendering.
- **Stable incremental regeneration.** Hash-based diff so the atlas re-scans only changed files; cache parser results keyed by AST hash. Today's "regenerate everything" doesn't scale to 50K+ LOC.
- **Search index alongside the atlas.** A small inverted index (function name → module → line → risk) co-located with the markdown, so an agent can ask "who calls `process_payment`?" without grepping all child files.

## 2. Human + Agent Comprehension

The unified format is the right foundation; the missing piece is *layered explanations*, not a single dump.

- **Two-track output per function.** Same function, two views in the child file:
  - **Agent track** — the existing compact `F: name(args)→ret / ↳Called by / ↳Impact` notation.
  - **Human track** — a 1–2 line plain-English "what & why" derived from the docstring + a "where this fits in the system" pointer to its cluster's purpose.
- **Why-it-exists annotations.** Currently the atlas says *what* a function does (from the docstring). Add a "Why" field generated from call-site context — "called by `checkout` to enforce rate limits before persisting order". Humans especially need this to skip reading source.
- **Cluster purpose cards.** Each `children/X.md` should open with a 5-line "Purpose / Owns / Doesn't own / Known risks" header. Currently a child file is just a flat list of `F001│…` rows — humans can't tell at a glance what the module is for.
- **Example traces.** For top-N entry points, embed a concrete call trace (`F005 → F012 → F040 → F089`) as a worked example. This is what humans actually want when onboarding to a new module.
- **Docstring quality signal.** Flag functions with missing, stale, or "TODO" docstrings as a low-confidence row — the atlas should not silently treat an undocumented function as understood.
- **Visualization parity.** The graph viewer exists for browsing; surface the same query ("show impact of F040") in the markdown atlas as a Mermaid block so humans reading markdown get the same answer without launching `--serve`.

## 3. Dead Code Recognition

This is explicitly Phase 3 and still ⏳ pending. The signal already exists in the impact analyzer (0 dependents = ⚪ SAFE); what's missing is the *interpretation layer* that turns "0 callers" into "dead".

**Definition, in priority order:**

1. **Hard dead** — function with 0 callers *and* not reachable from any detected entry point (no `__main__`, no CLI handler, no exported route, no plugin registration). Highest confidence, safe to delete after one final grep for dynamic use.
2. **Reachable-but-unused** — reachable from an entry point but no live caller in the current code (e.g., exposed in `__all__` but no import consumes it, or registered in a config that no longer exists). Needs a follow-up check.
3. **Soft dead / zombie** — last meaningful commit > N months ago, no tests reference it, and 0 callers. Likely abandoned; surface but don't auto-flag for deletion.
4. **Public API surface** — exported via package `__init__`, `setup.py` entry points, or route decorators. These are 0-callers *internally* but may be consumed externally. Report as "potentially dead — public surface, verify downstream".

**Detection signals to combine (none alone is sufficient):**

- Call graph: 0 in-edges from non-test code.
- Entry-point reachability: BFS from detected entry points; unreached = suspect.
- Test coverage mapping (Phase 5): untested + 0 callers = strong signal.
- Export/registration analysis: anything in `__all__`, `urls.py`, `Blueprint.register`, decorator-registered routes, plugin manifests.
- Dynamic-attribute access heuristic: flag if name appears only inside `getattr`/`__import__`/string-keyed dispatch.
- Git history: `git log -1 -- <symbol>` age, last author's commit message.
- Cross-file string references: scan for the function name appearing as a literal string in config, route table, or template.

**Output format** (fits the existing notation):

```markdown
DEAD│F089│utils.py:213│⚪
S: Helper to format legacy IDs (no callers, no tests, last touched 2024-08)
↳Reason: 0 callers + not in any entry-point BFS
↳Safe-to-delete: HIGH (no dynamic refs, not exported)
↳Action: confirm with `git grep -nE "fmt_legacy_id" -- .` then remove
```

**Workflow guardrails (human-in-the-loop, per the harness principles):**

- Atlas **never deletes**; it produces a `dead_code_candidates.md` report.
- Each candidate carries: confidence score, dynamic-use risk, public-surface flag, last-touched date, owning module.
- Pre-commit hook (already on the roadmap) cross-checks: a commit touching a HIGH-risk function that *also* makes a dead-code candidate newly-unused should warn the author they're about to delete live code or leave more dead code.
- Diff atlas (roadmap) should show "dead-code delta" between commits so cleanup progress is visible.

---

# Compare my graph from other graph libraries

## Features worth adopting, mapped to source

**From Graphify (highest relevance — same domain)**
- **Auto-detected "god nodes" / centrality ranking** — you already have `risk_level` and `entry_point`; adding a computed betweenness or degree-centrality score per node (cheap to compute server-side once per build) and visually emphasizing the top N would surface architectural chokepoints without the user having to go looking.
- **Community/cluster detection beyond your current file-based `cluster_id`** — Leiden or a similar modularity-based clustering over the *call* graph specifically (not just "grouped by file") could reveal functional subsystems that cut across file boundaries, which your current file-scoped clustering structurally can't show.
- **A companion text report** — a generated Markdown summary (central nodes, largest clusters, notable cycles — you already detect these from the layout fix) as a sibling artifact to the interactive graph, useful for anyone who wants the gist without opening the viewer.
- **Incremental re-extraction cache** — directly applicable to your builder given repos change incrementally; avoids full re-parse on every build.
- **MCP/queryable export** — given this is a codebase tool, exposing the same graph data as queryable structure for an AI coding assistant (not just a human-facing viewer) is a natural, high-value addition given how this ecosystem is trending.

**From Obsidian**
- **Local/neighborhood graph mode** — a one-click "show only this node + N hops" view, distinct from your full-graph pan/zoom. Cheap to implement given you already compute incoming/outgoing edge maps in `state.js`.
- **Query-based highlight groups** — let users type a filter expression (by risk level, file, node type) and get matched nodes color-highlighted in place, rather than requiring a full filter/hide. Softer and more exploratory than an on/off filter.
- **Orphan node highlighting** — nodes with no incoming or outgoing edges and not marked `entry_point`, called out visually — overlaps with the dead-code idea from before, but framed as a general graph-hygiene signal rather than code-specific.

**From NotebookLM**
- **Node-grounded Q&A** — since this is specifically a *code* graph with an AI coding assistant nearby, "select a node → ask a question about this function/file" wired to your assistant (with the node's metadata as context) is a more natural fit here than in a general note-taking tool, and reuses the modal you already built for expand/collapse as the UI surface.

**From Neo4j Bloom**
- **Perspectives (saved, named views)** — bundle your existing filters (risk level, LOD thresholds, hidden node sets) plus a viewport into a named, reusable preset ("Security review," "New engineer onboarding") — this is a refinement of the "persisted view presets" idea from last time, now backed by a concrete reference implementation pattern to follow.
- **Search phrases** — a small set of canned query templates ("show callers of X", "show unused functions") exposed as one-click actions rather than requiring the user to know what's filterable — lighter-weight than a full query language.
- **Data-driven styling thresholds via histograms** — instead of fixed risk-level color buckets, show the actual distribution (e.g., of call counts or file sizes) and let styling thresholds be set relative to that distribution.

## Where I'd actually start

Given what you've already built (LOD, culling, expand/collapse, risk coloring), the highest-leverage next additions are probably: **local/neighborhood view** (Obsidian) and **god-node/centrality highlighting** (Graphify) — both are cheap given your existing edge maps and metadata, and both directly address the "5,000-node graph is overwhelming" problem better than more filtering UI would. **Node-grounded Q&A** (NotebookLM-style) is the most novel/high-ceiling one given you're already inside an AI-coding-assistant context, but it's a bigger scope item — happy to turn any of these into a concrete implementation plan like we did for expand/collapse.

---

















If you want, I can help scope any one of these into a concrete implementation plan the way we did for the expand/collapse feature — happy to start with whichever feels highest-value for how this tool actually gets used.