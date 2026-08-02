Here's what's actually going on: this codebase has already built a surprising amount of what you're asking for — a self-evolving chain/graph system (`chain_miner.py`, `graph_evolver.py`, the `workflow_learn` config block) that mines tool-call sequences into deterministic, LLM-free chains and rebuilds a SQLite-backed graph at session end. So a lot of my answer is "here's how to finish and extend what's already 80% built," not "build this from scratch." Let me go through your four asks in order, then flag some gaps I noticed in the dump along the way.## 1. Self-analysis → deciding what to hardcode

This is essentially already built, and it's worth being precise about the mechanism because it's cleverer than a typical "auto-optimize" loop: `chain_miner.py` watches tool-call n-grams (both in-loop via `_feed_chain_miner` and in a session-end batch), and the promotion is **inline in the miner, not an LLM judgment call** — read-only sequences that clear `min_occurrences`/`min_savings_tokens` get auto-registered live (`_register_live`); anything with a write step sits `pending` until `chain_admin approve`. That's the "no LLM involved" decision you're asking for — it's already frequency + determinism + a static safety rule (read vs. write), not a model deciding.

Where I'd extend it is by turning the binary chain/no-chain decision into a **three-tier ladder**, because right now everything that gets promoted still costs a tool-call turn:

| Tier | Trigger | Example | LLM cost |
|---|---|---|---|
| Chain tool | Repeated sequence, some parameter variance | `probe_module`, `orient_symbols` | One tool call, LLM still chooses to invoke it |
| Hook | Same sequence, fires at a fixed point (post-`edit_file`, session-end), zero parameter variance | the `verify_edit`/`report_freshness` pattern from `sessions_analysis/session1.md` | Zero — runs automatically, never enters context |
| Backlog (new tool needed) | Pattern needs logic that doesn't exist in any current tool | `module_profile`, `context_budget` | N/A until someone writes it |

Concretely: add a `variance` and `trigger_position` score alongside the existing `savings_est` in the candidate table. A candidate with zero arg variance and a consistent trigger point (e.g., "always the 2nd call after `edit_file` on a `.py` file") should promote to a **hook wired into `loop/engine.py`**, not a chain tool the LLM has to remember to call — this is literally the "Post-edit import/syntax check hook" idea already sitting in `session1.md`/`session8.md`. Chains save tokens on execution; hooks save the tool-selection decision itself, which is the bigger lever for smaller models per your own `session7.md` note about drift.

## 2. Merging workflow files into the main graph as subgraphs

The mechanism for this is already fully built at the renderer level — `render_graph.py`'s template does `g.setParent(id, clusterId)` and reads a `clusters` array straight out of `graph_clusters`, and P4's plan explicitly says `minimal_context.html`/`implement_fix.html` become cluster nodes this way.

To make that automatic rather than one-off:
- Write a small ingester that parses each `data/workflows/*.html` file's embedded `const data = {...}` JS block (it's just JSON — `re.search(r'const data = ({.*?});', text)`), inserts a `graph_clusters` row keyed by filename, and tags each node/edge with that `cluster_id` + a `source_file` field.
- Run it as part of `graph_evolver.evolve()`, gated by `workflow_learn.graph_evolve` like everything else, so any new file dropped into `data/workflows/` gets absorbed on the next evolve — you never hand-maintain the merge.
- Keep chain-mined clusters and hand-authored workflow-file clusters visually distinct (solid border for hand-authored, dashed for mined) so a human glancing at the graph can tell "this part is documented convention" from "this part the agent invented."

## 3. Turning session-file optimizations into agent-driven work

This is the interesting gap. `chain_miner.py` mines **tool-call telemetry** — structured `{tool, args, ts}` events. But most of the value in `sessions_analysis/*.md` is **prose recommendations for tools that don't exist yet** (`tool_surface`, `md_outline`, `smart_read`, `file_facts`, `module_profile`, `context_budget`, `compact_history`). I checked the current Meta Tools table against these — `tool_anatomy` made it in, but `tool_surface`/`md_outline`/`smart_read`/`file_facts` were each proposed independently in sessions 1, 4, and 7 and are *still* not implemented. That's a real, visible cost of the current setup: the agent keeps re-discovering the same gap across sessions because nothing persists the recommendation itself, only the raw telemetry.

The fix parallels what already exists for chains, applied one level up:
- A lightweight "proposal miner" (mostly regex over the `.md` tables, since these files are already structured — you don't need an LLM call for this) that extracts `{proposed_name, category, replaces_pattern, est_savings}` from each session file and writes it into a `tool_proposals` table, deduping by name so a 3rd mention of `tool_surface` increments a `times_proposed` counter instead of being lost again.
- Render these as **ghost nodes** in the same graph — dashed grey diamonds like the existing mining-candidate convention, but labeled with the proposed tool name and a `×N proposed` badge. This reuses `graph_evolver`'s existing dashed-diamond idiom instead of inventing a second UI.
- Keep code-writing itself outside the auto-loop. Your own `config.json`/AGENTS.md principles already say "ask before installing modules," "ask before running tests" — a genuinely new primitive tool is exactly the kind of change that should stay human-gated, same as write-chains today. What the agent *can* do autonomously is the surfacing and deduplication, not the implementation.

## 4. Graph as a state machine with per-node prompt injection

Right now `workflow_hints()` already injects live chains + top DO/AVOID notes into every turn — but it's a **blanket broadcast**, the same list regardless of where in the workflow the agent actually is. What you're describing is closer to giving each graph node its own scoped prompt fragment, injected only when the agent is inferred to be "at" that node.

Two pieces needed:
- **Schema**: add a `prompt_fragment` column to `graph_nodes` (or a pointer into `prompt_fragments/*.md`). The AVOID notes already living in the `Agent_graph.html` side panel — "don't recurse `get_callers_callees` past depth 2," "check `get_symbols_meta` before `get_symbol`" — are natural candidates to move from the always-shown panel into per-node fragments.
- **State inference**: reuse `chain_miner`'s n-gram matching logic in "lookup" mode instead of "mine" mode — after each tool call, match the trailing window against known chain/graph paths and set a `current_node`. Then swap `workflow_hints()`'s static list for `graph_nodes[current_node].prompt_fragment`, capped small (~100-200 tokens).

One guardrail I'd insist on: keep this a **soft hint, not a hard gate**. State inference from a tool-call window is a heuristic, not ground truth — if you let the FSM state restrict which tools are callable, a legitimately unusual task will fight the graph instead of being served by it. The existing chain-promotion pipeline already draws this line correctly (deterministic *promotion*, but the LLM still chooses whether to call the resulting tool) — the state-scoped injection should follow the same pattern: advisory, never load-bearing.

## Risks worth flagging

- **Runaway self-modification**: `graph_state.version` already increments on every evolve and `sweep_stale_chains()` demotes unused chains after 14 days — good instincts already in place. I'd add an explicit node/cluster cap and a "diff before commit" step (show what `evolve()` is about to add/remove) rather than silent auto-apply, especially once ghost proposals and hook promotion widen what evolve can touch.
- **Validate against real sessions**: your own `FixesIssues.md` already flags this — "mining was validated with synthetic feeds; validating against the 8 real transcripts in `sessions_analysis/` is a natural next step." That's the single highest-leverage thing to do before adding any of the above, since it'll tell you whether the existing miner even fires correctly on real usage.
- **`tool_packs.chain` is off by default**, which makes the whole pipeline invisible to the LLM until someone flips it — worth reconsidering as "on once N approved chains exist and token budget allows" rather than a static default.