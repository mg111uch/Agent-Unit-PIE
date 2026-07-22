# Debate Module — Development Roadmap

## Current State

- One topic (`theism_atheism`) with 12 arguments, 24 edges
- `debate_step` composite tool drives the loop — one LLM turn per iteration
- Questions from pre-defined `graph.json` (zero LLM cost for generation)
- Belief tracking, contradiction detection, kernel signals active
- Counter-arg retrieval via ChromaDB (vector embeddings)
- Session persistence with resume support

---

## Phase 1 — Foundation Hardening

### 1.1 Topic Expansion Tool (`/argu add-topic`)

**Problem:** Adding a new topic requires manually creating `graph.json` with nodes/edges, plus `raw/` and `wiki/` files. Currently only one topic exists.

**Solution:** A tool or slash command that:
- Accepts a topic name + optional seed description
- LLM researches the topic, generates candidate arguments (pro/con/neutral)
- Creates `raw/` source notes, compiles `wiki/index.md`, exports `graph.json`
- Validates the graph structure (no duplicate names, valid edge refs)

**Impact:** Enables organic knowledge base growth without manual file editing.

### 1.2 LLM-Generated Question Batching

**Problem:** When `graph.json` arguments for a topic are exhausted, the debate stops. No mechanism to continue with new content.

**Solution:** A `debate_expand` tool that batches LLM-generated questions when the graph runs out:
1. LLM generates N new arguments on the topic (as structured JSON)
2. Stored in a `pending_questions.json` queue
3. `debate_step` picks from this queue when graph.json is exhausted
4. New arguments can later be reviewed and merged into `graph.json`

**Impact:** Infinite debate depth — structured graph first, LLM expansion as fallback.

### 1.3 Vector Store Resilience

**Problem:** `vector_store.py` has module-level chromadb initialization that crashes on import when chromadb is unavailable or disk is unwritable.

**Solution:** Already partially fixed (lazy init). Additional hardening:
- Graceful fallback to simple text-matching when chromadb unavailable
- Configurable persist directory (env var instead of hardcoded `./chroma_db`)
- Cache sentence-transformer model to avoid repeated downloads

**Impact:** Debate works even without vector DB — counter-arg retrieval becomes best-effort.

---

## Phase 2 — Deeper Intelligence

### 2.1 Belief Change Timeline

**Problem:** Current belief tracking is point-in-time (latest stance). No visualization of how beliefs evolved within a session or across sessions.

**Solution:** Leverage the kernel's `event_engine` and `timeline_engine` (already imported but underused):
- `emit_debate_event()` already creates events for `belief_changed`, `contradiction_detected`, etc.
- Build a `/argu timeline` command that queries event history and renders a timeline
- Show: argument presented → user responded → stance changed → contradiction flagged

**Impact:** Users can see their thinking evolve in real-time across a session.

### 2.2 Cross-Topic Belief Linking

**Problem:** Beliefs are scoped per-topic. A user's stance on "free will" in a philosophy topic has no connection to their stance on "moral responsibility" in an ethics topic.

**Solution:**
- Map belief stances across topics via shared concepts (extracted from argument premises)
- Kernel's `semantic_memory` can store cross-topic vectors
- `/argu reflect` detects cross-topic contradictions (e.g., "You argued for determinism in topic A but moral responsibility in topic B")
- Update the human mindmap with cross-topic edges

**Impact:** Turns isolated topic debates into a connected personal belief graph.

### 2.3 Argument Quality Scoring

**Problem:** All arguments are treated equally. No feedback loop on which arguments are effective or weak.

**Solution:**
- Add an optional 5th response: "Rate this argument (1-5)"
- Track: did this argument change the user's stance? (before/after confidence delta)
- Store quality scores in `belief_state.json` per argument
- `debate_step` can prioritize high-quality or underexplored arguments

**Impact:** Data-driven argument selection — the system learns which arguments resonate.

### 2.4 Confidence-Weighted Contradictions

**Problem:** Contradiction detection is binary — it fires if user agrees with two refuting arguments, regardless of confidence level.

**Solution:** Only flag contradictions when both stances exceed a confidence threshold (e.g., 0.6):
- Low-confidence "agree" means the user is exploring, not committed
- Add contradiction severity score: `min(confidence_a, confidence_b) * refute_weight`
- Surface only contradictions above a configurable threshold

**Impact:** Less noise — only meaningful contradictions are surfaced.

---

## Phase 3 — Advanced Features

### 3.1 Debate Modes

**Problem:** Single mode (`explore`) with fixed 3-option format. No variety in interaction style.

**Solution:** Multiple debate modes selectable via `/argu`:

| Mode | Behavior |
|------|----------|
| `explore` | Current — guided exploration with belief tracking |
| `socratic` | LLM asks probing questions instead of presenting arguments. User's answers are challenged with follow-ups |
| `devil` | LLM argues the opposite side of whatever the user believes. Force-test positions |
| `tutorial` | Explain each argument in-depth before asking for stance. Educational mode |
| `rapid` | Quick-fire mode — show arguments faster, skip contradictions, compress session |
| `compare` | Two users debate the same topic, compare belief outcomes |

**Impact:** Caters to different user goals — learning, testing, teaching.

### 3.2 Debate Summary and Export

**Problem:** After a debate session, there's no digest of what happened — just raw state files.

**Solution:** `/argu summary` command that:
- LLM reads `belief_state.json`, `interaction_log.json`, and session events
- Generates a structured summary:
  - Arguments the user agreed/disagreed with
  - Belief shifts and what triggered them
  - Contradictions found and resolved
  - Overall stance on the topic (weighted by confidence)
- Export as markdown, JSON, or shareable link

**Impact:** Tangible output from each debate session — users walk away with insight.

### 3.3 Belief Hypothesis Validation Loop

**Problem:** `create_belief_hypothesis()` is called but the validation loop is incomplete — hypotheses are created but not systematically tested.

**Solution:** Full hypothesis-driven debate:
1. After N responses, create a belief hypothesis: "User believes X with confidence Y"
2. Select arguments that specifically test this hypothesis (counter-evidence)
3. After testing, call `validate_belief_hypothesis()` with the result
4. Track hypothesis status: `supported` / `rejected` / `uncertain`
5. Surface hypothesis status in the debate flow

**Impact:** Debate becomes a scientific process — forming and testing hypotheses about the user's own beliefs.

---

## Phase 4 — Ecosystem & Platform

### 4.1 Multi-User Comparison

**Problem:** Debate is single-user. No way to compare belief structures across users.

**Solution:**
- Store per-user belief state under `mindmaps/{user_id}/` instead of `local_user/`
- `/argu compare <user_id>` overlays two users' belief graphs
- Highlight: same stance, opposite stance, both uncertain, contradictions unique to each user
- Kernel's `pattern_engine` can detect cross-user patterns

**Impact:** Enables social learning — see how others think about the same topic.

### 4.2 Topic Discovery and Recommendations

**Problem:** No way to discover topics beyond knowing their names. No topic recommendations based on beliefs.

**Solution:**
- Topic metadata (difficulty, discipline, argument count, completion rate)
- `/argu suggest` recommends topics based on:
  - Unexplored disciplines
  - Topics related to existing beliefs (shared concepts)
  - Topics where the user's stance conflicts with majority
- Topic search: `/argu search <keyword>`

**Impact:** Organic topic discovery — the system guides users to relevant debates.

### 4.3 Persistent Learning Over Time

**Problem:** No long-term learning across sessions. The kernel stores signals, but no mechanism reviews past debates.

**Solution:**
- Weekly/periodic `retrospective` signal: "Based on your debates this week, your views on X have shifted Y%"
- Kernel's `pattern_engine` detects long-term trends in belief signals
- `/argu reflect --deep` retrieves episodic memories across all sessions
- Track: arguments that most frequently change minds, topics with highest uncertainty

**Impact:** The system becomes a personal intellectual growth tracker.

---

## Effort vs Impact Matrix

| Feature | Effort | Impact | Phase |
|---------|--------|--------|-------|
| Topic expansion tool | Medium | High (content growth) | 1 |
| LLM question batching | Medium | High (infinite depth) | 1 |
| Vector store hardening | Low | Medium (reliability) | 1 |
| Belief change timeline | Medium | Medium (insight) | 2 |
| Cross-topic belief linking | High | High (connected thinking) | 2 |
| Argument quality scoring | Medium | Medium (adaptive) | 2 |
| Confidence-weighted contradictions | Low | Medium (less noise) | 2 |
| Debate modes (socratic, devil, etc.) | High | High (variety) | 3 |
| Debate summary / export | Medium | High (tangible output) | 3 |
| Hypothesis validation loop | Medium | Medium (scientific) | 3 |
| Multi-user comparison | High | Medium (social) | 4 |
| Topic discovery | Low | Medium (discovery) | 4 |
| Persistent learning over time | High | High (long-term growth) | 4 |

---

## Implementation Notes

### Integration Points with Existing Infrastructure

| Feature | Key Files to Modify |
|---------|-------------------|
| Topic expansion | New `agent_core/tools/debate_expand.py`, `ws_handler.py` |
| Question batching | `debate_ops.py` (read from pending queue), new `pending_questions.json` path |
| Vector store hardening | `vector_store.py` (already partially done) |
| Timeline | `kernel_bridge.py` (already emits events), new `debate_timeline.py` |
| Cross-topic linking | `kernel_bridge.py`, `storage.py`, `analyzer.py` |
| Quality scoring | `storage.py` (score field), `loop.py` (argument selection) |
| Debate modes | `debate_ops.py` (mode switch), `question_builder.py` (per-mode formatting) |
| Summary | New `agent_core/tools/debate_summary.py` |
| Multi-user | `ws_handler.py` (user_id-based paths), `storage.py` |

### Dependencies to Be Aware Of

- **ChromaDB + sentence-transformers**: Heavy dependencies, network-dependent on first use. Consider making them optional (graceful fallback).
- **Kernel modules**: `kernel_bridge.py` already imports 4 kernel subsystems. Adding more (pattern_engine, episodic_memory) may introduce circular imports — test carefully.
- **Graph.json schema**: If adding fields (e.g., `quality_score`), ensure backward compatibility with existing graph files via `dict.get()` defaults.
