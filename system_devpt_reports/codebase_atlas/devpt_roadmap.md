# 🎯 Roadmap

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

## Unwanted features

### Git & CI Integration
- ⏳ **Git-aware atlas**: Track last-modified timestamps, commit frequency, and author ownership per function
- ⏳ **Diff atlas**: `--diff` mode that compares two atlases and highlights new, changed, and removed functions
- ⏳ **CI pipeline hook**: Auto-generate atlas on PR, post diff as comment showing what changed and what breaks
- ⏳ **Pre-commit guard**: Warn if a commit touches a HIGH-risk function without test changes

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