"""ChainMiner: observe tool-call sequences and mine repeated patterns into chains.

Feed calls via feed() (in-loop) or mine a session from its message store (batch).
A repeated contiguous sub-sequence of tool names (>= min_occurrences times) becomes
a ChainSpec: constant args stay literal, varying args become $input.<key> params.
Read-only chains auto-promote (live registration + approved); chains with any write
step are persisted as pending and need explicit approval via chain_admin.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from agent_core.config import (
    WORKFLOW_LEARN_ENABLED,
    WORKFLOW_LEARN_MIN_OCCURRENCES,
    WORKFLOW_LEARN_MAX_SEQUENCE,
    WORKFLOW_LEARN_MIN_SAVINGS_TOKENS,
)
from agent_core.tools.chain.chain_spec import ChainSpec, Step
from agent_core.tools.chain.chain_store import chain_store
from agent_core.tools.chain.chains import CHAIN_SPECS

# Tools that mutate state; a chain containing any of these is not auto-promoted.
WRITE_TOOLS = frozenset({
    "Write", "edit_file", "execute_command", "todo",
    "undo_last_edit", "git_commit", "kernel_store_context",
    "kernel_create_event", "kernel_emit_signal", "cross_file_edit",
    "safe_edit", "extract_symbols_to_file", "minimal_context_dump",
})

_SKIP_TOOLS = frozenset({
    "ask_user_question", "hot_reload", "tool_stats", "file_stats",
    "user_reading_budget", "checkpoint_info", "undo_last_edit",
})

_MIN_BUFFER = 4  # need at least 2 occurrences of a 2-tool gram
_MAX_BUFFER = 500  # bound per-session in-loop scan cost


def signature_of(seq: List[str]) -> str:
    return " -> ".join(seq)


def is_read_only(seq: List[str]) -> bool:
    return all(t not in WRITE_TOOLS for t in seq)


def _infer_param(key: str, values: List[Any], present: int, total: int) -> Dict[str, Any]:
    if all(isinstance(v, list) for v in values):
        spec = {"t": "array", "desc": f"Values for {key}", "items": {"t": "string"}}
    elif all(isinstance(v, int) and not isinstance(v, bool) for v in values):
        spec = {"t": "integer", "desc": f"Value for {key}"}
    elif all(isinstance(v, bool) for v in values):
        spec = {"t": "boolean", "desc": f"Value for {key}"}
    else:
        spec = {"t": "string", "desc": f"Value for {key}"}
    if present == total:
        spec["r"] = True
    return spec


def _generalize_args(occurrences: List[Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """From per-occurrence args for ONE step position, produce (args, params).

    Constant values stay literal; varying values bind to $input.<key> and a
    matching param is added. Requires dict args in every occurrence.
    """
    args_out: Dict[str, Any] = {}
    params: Dict[str, Any] = {}
    keys: List[str] = []
    for o in occurrences:
        if not isinstance(o, dict):
            return {}, {}
        for k in o:
            if k not in keys:
                keys.append(k)
    for key in keys:
        vals = []
        present = 0
        for o in occurrences:
            if key in o:
                vals.append(o[key])
                present += 1
        if present == len(occurrences) and all(v == vals[0] for v in vals):
            args_out[key] = vals[0]
        else:
            args_out[key] = f"$input.{key}"
            params[key] = _infer_param(key, vals, present, len(occurrences))
    return args_out, params


def _name_for(seq: List[str], taken: set) -> str:
    base = "mine_" + "_".join(seq)
    if len(base) > 60:
        base = "mine_" + "_".join(s[:12] for s in seq)
        if len(base) > 60:
            base = base[:60]
    name, i = base, 2
    while name in taken:
        name = f"{base}_{i}"
        i += 1
    return name


def _contains(inner: Tuple[str, ...], outer: Tuple[str, ...]) -> bool:
    if len(inner) > len(outer):
        return False
    for i in range(len(outer) - len(inner) + 1):
        if outer[i:i + len(inner)] == inner:
            return True
    return False


def _periodic_base(gram: Tuple[str, ...]) -> Tuple[str, ...]:
    """Smallest prefix that, repeated, equals the gram (e.g. (a,b,a,b) -> (a,b))."""
    n = len(gram)
    for L in range(1, n + 1):
        if n % L == 0 and gram == gram[:L] * (n // L):
            return gram[:L]
    return gram


_DEFAULT_TOOL_TOKENS = 400  # fallback avg tokens for unseen tools


def _avg_tokens_map() -> Dict[str, int]:
    """Per-tool average output tokens from tool_stats (empty -> {} on any failure)."""
    try:
        from kernel.persistence.db import kernel_db
        return {r["tool_name"]: int(r.get("avg_tokens") or 0) for r in kernel_db.get_tool_stats()}
    except Exception:
        return {}


def estimate_savings(gram: Tuple[str, ...], occurrences: int,
                     avg_tokens: Optional[Dict[str, int]] = None) -> int:
    """Estimated tokens saved by replacing the repeated sequence with one chain call.

    savings ≈ (sum of per-step output tokens − one chain output) × occurrences.
    Chain output is approximated as the largest single step (the combined result is
    budget-capped and dominated by the biggest step). Uses real avg output tokens
    from tool_stats when available; falls back to a constant for unseen tools.
    """
    avg = avg_tokens if avg_tokens is not None else _avg_tokens_map()
    step_tokens = [avg.get(t, _DEFAULT_TOOL_TOKENS) for t in gram]
    if not step_tokens:
        return 0
    per_call = sum(step_tokens) - max(step_tokens)
    return max(0, per_call * max(occurrences, 1))


class ChainMiner:
    def __init__(self, store=None):
        self._store = store or chain_store
        self._buffers: Dict[str, List[Tuple[str, Any]]] = {}
        self._proposed: set = set()
        self._promoted: Dict[Tuple[str, ...], str] = {}  # gram -> chain name

    # --- input plumbing ---

    def feed(self, session_id: str, tool: str, args: Any):
        if not WORKFLOW_LEARN_ENABLED or tool in _SKIP_TOOLS:
            return
        buf = self._buffers.setdefault(session_id, [])
        buf.append((tool, args))
        if len(buf) > _MAX_BUFFER:
            del buf[:-_MAX_BUFFER]
        if len(buf) >= _MIN_BUFFER:
            self.scan_and_promote(buf)

    def flush(self, session_id: str):
        self._buffers.pop(session_id, None)

    # --- mining core ---

    def scan(self, sequence: List[Tuple[str, Any]]) -> List[ChainSpec]:
        names = [t for t, _ in sequence]
        grams = [g for g, _ in self._repeated_grams(names)]
        specs = []
        for gram in grams:
            indices = [i for i in range(len(names) - len(gram) + 1)
                       if tuple(names[i:i + len(gram)]) == gram]
            spec = self._build_spec(gram, sequence, indices)
            if spec is not None:
                specs.append(spec)
        return specs

    def scan_and_promote(self, sequence: List[Tuple[str, Any]]):
        names = [t for t, _ in sequence]
        avg = _avg_tokens_map()
        for gram, count in self._repeated_grams(names):
            savings = estimate_savings(gram, count, avg)
            if gram in self._promoted:
                # already live this process — refresh evidence + demote supersets
                self._demote_overlapping(gram, count)
                self._store.upsert_candidate(signature_of(list(gram)), list(gram), savings)
                continue
            indices = [i for i in range(len(names) - len(gram) + 1)
                       if tuple(names[i:i + len(gram)]) == gram]
            spec = self._build_spec(gram, sequence, indices)
            if spec is not None:
                self._promote(spec, count, savings)

    def _repeated_grams(self, names: List[str]) -> List[Tuple[Tuple[str, ...], int]]:
        max_len = min(WORKFLOW_LEARN_MAX_SEQUENCE, len(names))
        min_occ = WORKFLOW_LEARN_MIN_OCCURRENCES
        counts: Dict[Tuple[str, ...], int] = {}
        for L in range(2, max_len + 1):
            for i in range(len(names) - L + 1):
                gram = tuple(names[i:i + L])
                counts[gram] = counts.get(gram, 0) + 1
        qualifying = [g for g, c in counts.items() if c >= min_occ]
        qualifying.sort(key=lambda g: (-len(g), g))
        maximal: List[Tuple[str, ...]] = []
        for g in qualifying:
            if any(_contains(g, m) for m in maximal):
                continue
            maximal.append(g)
        # Collapse periodic repeats: [a,b,a,b] is really [a,b] observed twice.
        collapsed: Dict[Tuple[str, ...], int] = {}
        for g in maximal:
            base = _periodic_base(g)
            if base in collapsed:
                continue
            collapsed[base] = sum(1 for i in range(len(names) - len(base) + 1)
                                  if tuple(names[i:i + len(base)]) == base)
        return sorted(collapsed.items(), key=lambda x: (-x[1], -len(x[0]), x[0]))

    def _build_spec(self, gram: Tuple[str, ...], sequence, indices) -> Optional[ChainSpec]:
        if any(s in _SKIP_TOOLS for s in gram):
            return None
        if self._already_known(gram):
            return None
        steps = []
        params: Dict[str, Any] = {}
        seen: Dict[str, int] = {}
        for pos, tool in enumerate(gram):
            seen[tool] = seen.get(tool, 0) + 1
            step_name = tool if seen[tool] == 1 else f"{tool}_{seen[tool]}"
            occs = [sequence[i + pos][1] for i in indices]
            args, p = _generalize_args(occs)
            if not args and occs and not all(o == {} for o in occs):
                return None  # non-dict args — can't bind cleanly
            steps.append(Step(tool=tool, name=step_name, args=args))
            params.update(p)
        if not steps:
            return None
        taken = self._taken_names()
        name = _name_for(list(gram), taken)
        return ChainSpec(
            name=name,
            category="chain",
            description=(
                f"Mined: repeated sequence {', '.join(gram)} (observed across sessions). "
                "Composite of existing tools — same workflow, one call."
            ),
            steps=steps,
            params=params,
            budget_tokens=16000,
            step_cap_chars=8000,
        )

    # --- dedup / naming ---

    def _existing_signatures(self) -> set:
        sigs = {tuple(s.tool for s in spec.steps) for spec in CHAIN_SPECS}
        for row in self._store.list_specs():
            sigs.add(tuple(s["tool"] for s in row["steps"]))
        return sigs

    def _already_known(self, gram: Tuple[str, ...]) -> bool:
        return gram in self._existing_signatures() or gram in self._promoted

    def _taken_names(self) -> set:
        names = {spec.name for spec in CHAIN_SPECS}
        names.update(r["name"] for r in self._store.list_specs())
        return names

    # --- promotion ---

    def _promote(self, spec: ChainSpec, count: int = 1, savings: int = 0):
        gram = tuple(s.tool for s in spec.steps)
        self._store.upsert_candidate(signature_of(list(gram)), list(gram), savings)
        read_only = is_read_only(list(gram))
        if not read_only:
            status = "pending"
        elif WORKFLOW_LEARN_MIN_SAVINGS_TOKENS > 0 and savings < WORKFLOW_LEARN_MIN_SAVINGS_TOKENS:
            status = "pending"  # below savings bar — hold for approval
        else:
            status = "approved"
        self._store.upsert_spec(spec, source="mined", status=status, read_only=read_only)
        self._promoted[gram] = (spec.name, count)
        self._demote_overlapping(gram, count)
        if status == "approved":
            self._register_live(spec)

    def _demote_overlapping(self, gram: Tuple[str, ...], count: int):
        """Drop a promoted chain H that gram subsumes: gram is fully contained in H
        and has strictly more occurrences (gram is the dominant repeated pattern)."""
        try:
            from agent_core.tools import registry
            doomed = [g for g, (_, c) in self._promoted.items()
                      if g != gram and _contains(gram, g) and count > c]
            for g in doomed:
                name = self._promoted.pop(g, (None, 0))[0]
                if name:
                    self._store.delete_spec(name)
                    registry.unregister(name)
        except Exception:
            pass  # cleanup never breaks the loop

    def _register_live(self, spec: ChainSpec):
        try:
            from agent_core.tools import registry, tool_call
            from agent_core.tools.chain.chain_engine import make_chain_tool
            from agent_core.tools.registry import CAT_CHAIN
            if registry.has_tool(spec.name):
                return
            registry.register(spec.name, tool_call(make_chain_tool(spec)),
                              description=spec.description, params=spec.params, category=CAT_CHAIN)
        except Exception:
            pass  # registration must never break the loop

    # --- session-end batch ---

    def mine_session(self, session_id: str, msg_store) -> int:
        """Batch-mine a session from its stored messages. Returns chains promoted."""
        if not WORKFLOW_LEARN_ENABLED:
            return 0
        sequence = self._extract_sequence(msg_store, session_id)
        if len(sequence) < _MIN_BUFFER:
            return 0
        promoted = 0
        for spec in self.scan(sequence):
            if self._promote_batch(spec):
                promoted += 1
        return promoted

    def _promote_batch(self, spec: ChainSpec) -> bool:
        gram = tuple(s.tool for s in spec.steps)
        savings = estimate_savings(gram, 2)
        self._store.upsert_candidate(signature_of(list(gram)), list(gram), savings)
        read_only = is_read_only(list(gram))
        if not read_only:
            status = "pending"
        elif WORKFLOW_LEARN_MIN_SAVINGS_TOKENS > 0 and savings < WORKFLOW_LEARN_MIN_SAVINGS_TOKENS:
            status = "pending"
        else:
            status = "approved"
        self._store.upsert_spec(spec, source="mined", status=status, read_only=read_only)
        self._promoted[gram] = (spec.name, 2)
        if status == "approved":
            self._register_live(spec)
            return True
        return False

    def _extract_sequence(self, msg_store, session_id: str) -> List[Tuple[str, Any]]:
        try:
            messages = msg_store.get_messages(session_id, limit=10000)
        except Exception:
            return []
        sequence = []
        for msg in messages:
            for tc in msg.get("tool_calls") or []:
                name = tc.get("name")
                if not name:
                    continue
                args = tc.get("arguments")
                sequence.append((name, args))
        return sequence


miner = ChainMiner()
