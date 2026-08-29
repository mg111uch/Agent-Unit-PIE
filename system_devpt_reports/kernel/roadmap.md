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

---

## Dream cycle / data cleaner — yes, but scoped smaller than the metaphor suggests

Worth building, but two things first.

**Check whether you already started this.** `kernel/compression_engine.py` exists at the top level of `kernel/` in the current file map, and I have no content for it — it's plausibly exactly the intended home for this (it maps directly onto the "self-compressing" principle from your original README). Worth checking what's actually in it before writing a new file that duplicates or competes with it — same duplication risk that's come up with `storage/` vs `kernel/memory/`, `signal_extractor.py` in two locations, and the two parallel vector stores earlier in this conversation.

**This is a different risk category than anything built so far.** Every feature this conversation has covered — contradiction detection, semantic retrieval, hypothesis tracking, report generation — is additive or observational. A cleaner that decides what's "noise" and removes it is the first *destructive* feature in the project. That deserves proportionate caution: dry-run mode by default (report what it would remove before removing anything), an audit trail of what got pruned and why (which you already have the infrastructure for — this is exactly what `episodic_memory`/`event_engine` is for), and archival over hard deletion, at least initially — move to a `data/archive/` rather than `DELETE FROM`, so a wrong judgment call is recoverable rather than silently lossy.

With that framing, here's what "dream cycle" decomposes into, staged the same way everything else in this conversation has been:

1. **TTL sweep (cheapest, do first).** `belief_signal_handler.py` already writes entries with `BELIEF_SHIFT_TTL`/`CONFIDENCE_CHANGE_TTL`. A scheduled job that purges (or archives) expired `working_memory` rows is nearly free — the TTL field already exists, nothing currently reads it to actually clean up. This alone is most of "forgetting what's no longer needed" with no judgment calls involved, which is why it should go first.
2. **Deduplication/consolidation.** You already built exactly this mechanism for argu_god (`dedup.py`'s similarity-threshold check) and kernel's `semantic_retriever` now has a real embedding backend. Near-duplicate `semantic_nodes` (repeated near-identical observations) or a long run of near-identical `belief_shift` signals for the same node are candidates to merge into one consolidated entry — reusing infrastructure that already exists rather than building new similarity logic.
3. **Hypothesis pruning.** `hypothesis_engine.get_by_status()` already exists — hypotheses that have sat at `uncertain` with low confidence and no new evidence for a long time are candidates to archive. This is the closest thing to actual "judgment" in the pipeline, which is why it should come last, after the two purely mechanical stages have proven the archive/audit-trail plumbing works.

**Where it should live:** integrated into kernel, not standalone — this is memory-management cognition, and "kernel owns cognition" already covers it. But it should be triggered explicitly (a scheduled job or an agent-callable tool you invoke deliberately), not something that runs silently and invisibly, given the destructive-tier risk above. "Dream cycle" is a fine name for the feature conceptually, but I'd keep the implementation itself boring and mechanical — a scored, logged, dry-run-capable batch job — rather than building something that makes creative, opaque judgment calls about what counts as noise. The name can be evocative; the code shouldn't be clever about deciding what to throw away.

---

# PROMPT 1
Give a plan which i could append in agents.md so that system development reports keep updating as codebase is being changed because most of the time i will be using these reports to get a direction for project development, so i dont want them to be stale in any manner. Also suggest how could reports schema be made consistent so that report is useful for both humans and agent,while not being too much detailed as ultimately the final source of truth is the codebase itself. What are the details which these reports contain which is unnecessary to get the current status of codebase. Give plan so that an agent can streamline the development reports overhaul and updating methods. 

# RESPONSE 1
Needs to be solved.

# PROMPT 2
Which parts of the docs in system devpt reports would be better if we integrate these reports with the argugod and kernel cognition system itself. Means we already made a new topic of tracking project_history which could be reasoned with using an llm. Wouldnt it help to maintain these reports in a better way. Give more dogfood to make this project self evolving.

# RESPONSE 2
This is a good instinct, and it's a natural extension of what's already built — you're not proposing new infrastructure, you're proposing to point existing infrastructure (hypothesis engine, episodic memory, contradiction detector, `requires`/`contradicts` relations) at a new target. Let me map it out concretely, section by section, then flag the one thing to watch.

## Which report content maps onto which existing kernel primitive

| Report section | Currently | Better as |
|---|---|---|
| **Current Capability** table (file:function citations) | Hand-written markdown, goes stale silently | A `Hypothesis` per capability claim (reusing `hypothesis_engine.py`, already built). Supporting evidence = the citation itself. Confidence isn't asserted, it's *computed*. |
| **Known Gaps** | Hand-written bullet list | Hypotheses with `status="rejected"`/`"uncertain"`, linked via `requires` edges to whatever would resolve them — the exact relation type you already added for the codebase-decision use case. No new machinery needed. |
| **Recent Changes / changelog** | Manually appended markdown bullets | Events in `episodic_memory`/`event_engine` (already built, already has a `timeline_retriever`). A changelog entry is structurally just an event. |
| **Roadmap / speculative ideas** | Sits in the same file as verified status, which is how it got confused with fact | Hypotheses with `status="proposed"` — structurally distinct from validated capability, so it *can't* get mixed up the way markdown tables can. |
| **Dev Report Integrity Rule verification** | A discipline an agent has to remember to run | An automatic revalidation: when a hypothesis's cited `file:function` stops resolving, its supporting evidence is invalidated and `validate_hypothesis()` flips its status — no one has to remember to grep. |

The core shift: right now "is this report accurate" is a question a human or agent has to go check by hand. If capability claims live as hypotheses with evidence, "is this report accurate" becomes a query — `get_by_status("rejected")` tells you exactly what's currently known-broken, no grepping required. That's the actual fix to the staleness problem, not another rule in `AGENTS.md` asking someone to remember to check.

## Why `project_history` specifically is the right anchor

You already have the piece that makes this coherent rather than just "put docs in a database": `project_history` already tracks *why* something was removed and what re-adding it would require, using `contradicts`/`requires` edges. Capability claims and gaps are the same kind of object — "X is true, here's the evidence" and "X was true, then wasn't, here's why" are both just hypotheses with a history. Folding report content into the same topic means a future agent asking "can I re-add the hypothesis engine calls to argu_god" and an agent asking "is contradiction detection currently working" are hitting the *same* underlying structure, not two different systems that can drift from each other.

## Staged rollout — don't build all of this at once

Given how much of this conversation was about not over-building kernel scaffolding ahead of need, I'd sequence this the same way:

**Stage 1 (do this first, smallest, highest leverage):** Convert the "Current Capability" table into hypotheses with citation-based evidence, plus one small validator that checks each citation still resolves (this can literally just call the existing `pie_get_symbol` lookup) and calls `validate_hypothesis()`. This alone automates the Dev Report Integrity Rule instead of relying on remembered discipline — and it's almost entirely wiring, not new code, since `hypothesis_engine.py` already has everything except the citation-check callback.

**Stage 2:** Model Known Gaps the same way, with `requires` edges to their blockers. Reuses the exact relation types already built for the codebase-decision case — no new relation vocabulary needed.

**Stage 3:** Route "Recent Changes" through `episodic_memory`/`event_engine` instead of hand-appended bullets, using the `timeline_retriever` that's already built but currently unused for this purpose.

**Stage 4 (only after 1–3 prove out):** Reports become generated, not maintained — a query that renders current markdown from the hypothesis/event graph on demand, rather than markdown being the primary artifact at all. At that point staleness stops being possible by construction, since the doc doesn't exist between requests. Don't build this until the earlier stages are load-bearing — a report generator on top of an unproven graph is the same mistake as building `contradiction_detector.py` before anything needed it.

One efficiency note carried over from earlier in this conversation: when you get to Stage 4, cache validated hypothesis state and only re-check citations when files actually change (hook into the same file-change detection the `kernel_reload` hot-reload already does), not on every report render — otherwise you've recreated the "re-embed everything on every call" perf bug from `vector_store.py`.

## More dogfooding, beyond docs

Two ideas that reuse what's already built rather than adding anything new:

**Use the debate loop itself as the handoff/onboarding mechanism.** You now have a free-text Q&A loop with contradiction detection against accumulated knowledge. Instead of a new agent linearly reading `AGENTS.md` + four report files (the exact process I just did across this conversation), it could *ask* the `project_history` topic questions — "what does the debate module currently do" — and get answered from the graph, with any wrong assumption it proposes immediately flagged as contradicting recorded history. This is the same mechanic you described in your very first message about the debate engine two features ago ("if later I want a feature which needs another feature I earlier rejected, LLM must explain") applied to onboarding itself, not just feature decisions.

**Turn the tool-compliance problem from last message into a pattern-detection target.** `pattern_engine.detect_repeated_events()` already exists and is real, not a stub. Emit a signal every time an agent calls `Read` on an indexed kernel file, and let the existing pattern detector surface "bypassed `pie_*` tools N times this session" as an actual `pattern_detected` signal — the same pipeline that already handles belief contradictions, just pointed at agent behavior instead of debate content. That gives you the audit visibility I suggested last message without writing a separate bespoke script, and it's a genuine instance of "kernel owns cognition" — the kernel noticing something about *how the project is being developed*, not just about debate topics.

Both of these are literally on your own `kernel.md` "Self-Evolution" wishlist already (`System Self-Check: Detect internal contradictions`, `Auto-Pattern Discovery`) — they were aspirational vocabulary a few messages ago, sitting next to ~150 other pattern types with no detector behind them. The difference now is that the specific machinery they'd need (hypothesis engine, contradiction detector, `requires` relations, `detect_repeated_events`) actually exists and is verified working, so these two are cheap to build rather than speculative scope.

## One caution

This is worth doing, but it's still more moving parts — a validation runner, a citation-check callback, decisions about how much episodic history to retain before it needs pruning. The same discipline that got this project from "one-shot LLM sketch with 60% dead code" to where it is now applies here too: build Stage 1, confirm it actually keeps a report honest for a few real sessions, before adding Stage 2 or 3. The failure mode to avoid is building the whole self-evolving reporting system in one pass and ending up with a second thing that also needs a "check if implemented" audit six messages from now.
