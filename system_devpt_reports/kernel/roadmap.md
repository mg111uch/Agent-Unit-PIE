# Kernel Roadmap — Speculative / Planned
_Not verified. This file tracks future directions, not current status._

## Full Kernel Cognition

| Item | Description |
|------|-------------|
| Simulation → Pattern Pipeline | Trigger patterns from sim signals |
| Digital Twin + Simulation | Run scenarios from twin data |
| Policy Injection | Test policies via simulation |
| Recursive Hypothesis Testing | Generate sims from hypotheses |

## Kernel Hot-Reload

| Item | Description |
|------|-------------|
| `kernel_reload` tool | Reloads sim_ops, kernel_ops, code_rag, and tools/__init__.py from disk without restart |
| Auto-reload (MCP) | MCP server detects `st_mtime_ns` changes and re-imports modules on next tool call |
| Use case | Edit simulation/kernel code → next `pie_*` call picks up changes — no server restart |

## Enhanced Debate Features

| Item | Description |
|------|-------------|
| Multi-Person Debate | Multiple users/perspectives |
| Debate Analytics | Show session stats (arguments seen, time, belief changes) |
| Multiple Perspectives | Store beliefs per user/persona |
| Side Tracking | Track which side user favors |
| Argument Quality | Score arguments by evidence strength |
| Debate Summary | Generate summary report |
| Progress Indicator | "5/23 arguments explored" |
| Export Belief Graph | Export as JSON |
| Argument Quality Scoring | Score by evidence |
| Topic Browser | List and select from available topics |
| Cross-Topic Linking | Connect beliefs across topics |
| Recursive Counterarguments | Explore counter-counterarguments |
| Evidence Search | Auto-find supporting evidence |
| belief_graph Visualization | Render belief network |

## Self-Evolution

| Item | Description |
|------|-------------|
| Auto-Pattern Discovery | Discover new patterns |
| Hypothesis Auto-Generation | Auto-generate from signals |
| Auto-Topic Generation | Generate new topics from knowledge |
| Self-Contradiction Detection | Check consistency |
| Knowledge Compression | Auto-summarization |
| System Self-Check | Detect internal contradictions |


## Dream cycle / data cleaner — yes, but scoped smaller than the metaphor suggests

Worth building, but two things first.

**Check whether you already started this.** `kernel/compression_engine.py` exists at the top level of `kernel/` in the current file map, and I have no content for it — it's plausibly exactly the intended home for this (it maps directly onto the "self-compressing" principle from your original README). Worth checking what's actually in it before writing a new file that duplicates or competes with it — same duplication risk that's come up with `storage/` vs `kernel/memory/`, `signal_extractor.py` in two locations, and the two parallel vector stores earlier in this conversation.

**This is a different risk category than anything built so far.** Every feature this conversation has covered — contradiction detection, semantic retrieval, hypothesis tracking, report generation — is additive or observational. A cleaner that decides what's "noise" and removes it is the first *destructive* feature in the project. That deserves proportionate caution: dry-run mode by default (report what it would remove before removing anything), an audit trail of what got pruned and why (which you already have the infrastructure for — this is exactly what `episodic_memory`/`event_engine` is for), and archival over hard deletion, at least initially — move to a `data/archive/` rather than `DELETE FROM`, so a wrong judgment call is recoverable rather than silently lossy.

With that framing, here's what "dream cycle" decomposes into, staged the same way everything else in this conversation has been:

1. **TTL sweep (cheapest, do first).** `belief_signal_handler.py` already writes entries with `BELIEF_SHIFT_TTL`/`CONFIDENCE_CHANGE_TTL`. A scheduled job that purges (or archives) expired `working_memory` rows is nearly free — the TTL field already exists, nothing currently reads it to actually clean up. This alone is most of "forgetting what's no longer needed" with no judgment calls involved, which is why it should go first.
2. **Deduplication/consolidation.** You already built exactly this mechanism for argu_god (`dedup.py`'s similarity-threshold check) and kernel's `semantic_retriever` now has a real embedding backend. Near-duplicate `semantic_nodes` (repeated near-identical observations) or a long run of near-identical `belief_shift` signals for the same node are candidates to merge into one consolidated entry — reusing infrastructure that already exists rather than building new similarity logic.
3. **Hypothesis pruning.** `hypothesis_engine.get_by_status()` already exists — hypotheses that have sat at `uncertain` with low confidence and no new evidence for a long time are candidates to archive. This is the closest thing to actual "judgment" in the pipeline, which is why it should come last, after the two purely mechanical stages have proven the archive/audit-trail plumbing works.

**Where it should live:** integrated into kernel, not standalone — this is memory-management cognition, and "kernel owns cognition" already covers it. But it should be triggered explicitly (a scheduled job or an agent-callable tool you invoke deliberately), not something that runs silently and invisibly, given the destructive-tier risk above. "Dream cycle" is a fine name for the feature conceptually, but I'd keep the implementation itself boring and mechanical — a scored, logged, dry-run-capable batch job — rather than building something that makes creative, opaque judgment calls about what counts as noise. The name can be evocative; the code shouldn't be clever about deciding what to throw away.