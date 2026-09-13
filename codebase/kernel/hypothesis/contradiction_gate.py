"""Block contradictory claims until user resolves prior hypothesis."""
from typing import Dict, List, Tuple
from functools import lru_cache

def _tokens(s: str) -> set:
    return set(s.lower().split())

def _jaccard(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)

_ST_MODEL = None
_ST_FAILED = False
_CACHE_PATH = str(__import__("pathlib").Path(__file__).resolve().parents[2] / "encoding_cache" / "all-MiniLM-L6-v2")

@lru_cache(maxsize=512)
def _embed(text: str):
    global _ST_MODEL, _ST_FAILED
    if _ST_FAILED:
        return None
    if _ST_MODEL is None:
        try:
            from sentence_transformers import SentenceTransformer
            _ST_MODEL = SentenceTransformer(_CACHE_PATH, local_files_only=True)
        except Exception:
            _ST_FAILED = True
            return None
    try:
        return _ST_MODEL.encode(text).tolist()
    except Exception:
        return None

def _cosine(a, b) -> float:
    if a is None or b is None:
        return 0.0
    try:
        import math
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(x * x for x in b))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)
    except Exception:
        return 0.0

def _similar(a: str, b: str) -> float:
    j = _jaccard(a, b)
    try:
        ea, eb = _embed(a), _embed(b)
        c = _cosine(ea, eb)
        # embedding in [ -1,1], map to [0,1] and take max with jaccard
        c_norm = (c + 1) / 2 if c != 0 else 0
        return max(j, c_norm)
    except Exception:
        return j

_NEG_WORDS = frozenset({
    "not", "no", "never", "n't", "nt", "without", "fail", "failed",
    "incorrect", "opposite", "contradict", "contradicts", "contradicted",
    "false", "wrong", "denies", "refutes",
})
_NEG_WINDOW = 2
# Generic adjectives: negating them never constitutes propositional
# opposition ("no new checkpoint" vs "new champ" share nothing but the word).
_GENERIC_WORDS = frozenset({
    "new", "old", "best", "better", "good", "high", "low", "higher", "lower",
    "more", "less", "most", "big", "small", "fast", "slow", "first", "last",
    "next", "same", "other", "own", "full", "total", "avg", "min", "max",
    "mean", "overall", "current", "previous", "single", "multiple", "several",
})

def _word_tokens(s: str) -> list:
    import re
    return re.findall(r"[a-z0-9']+", (s or "").lower())

def _negated_positions(toks: list) -> set:
    """Indices of tokens falling inside a negation window."""
    negs = set()
    for i, t in enumerate(toks):
        if t in _NEG_WORDS or t.endswith("n't"):
            for j in range(i + 1, min(len(toks), i + 1 + _NEG_WINDOW)):
                negs.add(j)
    return negs

def _is_opposite(a: str, b: str) -> bool:
    # Genuine opposition = a SHARED proposition negated on exactly one side.
    # Whole-premise negation-XOR plus bag overlap false-fires on domain
    # vocab (death/fail/not appear in nearly every premise of a topic).
    ta, tb = _word_tokens(a), _word_tokens(b)
    if not ta or not tb:
        return False
    shared = (set(ta) & set(tb)) - _NEG_WORDS - _GENERIC_WORDS
    shared = {t for t in shared if len(t) > 2}
    if not shared:
        return False
    na, nb = _negated_positions(ta), _negated_positions(tb)
    for t in shared:
        ia = [i for i, tok in enumerate(ta) if tok == t]
        ib = [i for i, tok in enumerate(tb) if tok == t]
        # tri-state per side: negated-only / asserted-only / mixed. Mixed
        # (quote-then-assert) is ambiguous, never opposition on its own.
        a_neg = any(i in na for i in ia)
        a_pos = any(i not in na for i in ia)
        b_neg = any(i in nb for i in ib)
        b_pos = any(i not in nb for i in ib)
        if (a_neg and not a_pos and b_pos and not b_neg) or \
           (b_neg and not b_pos and a_pos and not a_neg):
            return True
    return False

_REF_PATTERNS = (
    r"gen\s*\d+", r"gens?\s*\d+\s*[-–]\s*\d+",
    r"run_[a-z0-9_]+", r"phase[- ]?\d+",
)

def _referents(text: str) -> set:
    """Measurement identifiers (gen/run/phase) cited by a premise."""
    import re
    t = (text or "").lower()
    out = set()
    for pat in _REF_PATTERNS:
        out.update(re.sub(r"\s+", " ", m) for m in re.findall(pat, t))
    return out

def _disjoint_measurements(new_text: str, existing_text: str) -> bool:
    """True when both sides cite measurement ids with zero overlap.

    A new measurement (gen7) cannot contradict an old one (gen6) — that is
    progress/refinement, not logical opposition. Resemblance across disjoint
    referents must never block.
    """
    new_refs, ex_refs = _referents(new_text), _referents(existing_text)
    return bool(new_refs and ex_refs and new_refs.isdisjoint(ex_refs))

# --- Symbolic observation layer (FixesIssues.md) ---
OBSERVATION_TYPES = {"observation", "simulation_observation", "experiment_observation"}
# verdict opposition table
_OPPOSITE_VERDICTS = {
    "IMPROVED": {"COLLAPSED", "DEGRADED"},
    "COLLAPSED": {"IMPROVED", "STABLE"},
    "DEGRADED": {"IMPROVED", "STABLE"},
    "STABLE": {"COLLAPSED", "DEGRADED"},
}
# direction mapping from verdict
_VERDICT_TO_DIRECTION = {
    "IMPROVED": "INCREASE",
    "DEGRADED": "DECREASE",
    "COLLAPSED": "DECREASE",
    "STABLE": "STABLE",
}

def _infer_verdict(text: str) -> str:
    t = text.upper()
    for v in ("IMPROVED", "COLLAPSED", "DEGRADED", "STABLE"):
        if v in t:
            return v
    return ""

# Verdict-word inference defaults to the population metric, so it is only
# meaningful for population-simulation topics. Firing it globally lets a
# subordinate clause ("uniq collapsed 3->1") masquerade as a population
# COLLAPSED verdict and hard-block unrelated topics.
_POP_TOPICS = {"popu_sim", "sim_stock"}
# Nouns whose collapse/degradation is NOT a population verdict.
_NON_POP_NOUNS = frozenset({
    "uniq", "unique", "diversity", "entropy", "reward", "rewards", "loss",
    "losses", "fitness", "lap", "laps", "step", "steps", "death", "deaths",
    "drift", "variance", "gradient", "gradients", "weight", "weights",
    "accuracy", "sharpe", "drawdown", "return", "returns", "profit", "price",
    "policy", "training", "curve", "rate", "score", "scores",
})

def _verdict_is_pop_claim(text: str, verdict: str) -> bool:
    """Verdict word must not be governed by a non-population metric noun."""
    import re
    toks = re.findall(r"[a-z0-9']+", (text or "").lower())
    for i, t in enumerate(toks):
        if t == verdict.lower():
            window = toks[max(0, i - 2):i]
            if any(w in _NON_POP_NOUNS for w in window):
                return False
    return True

def _extract_observation_meta(node) -> Dict | None:
    """Return observation dict if node carries structured metadata, else infer."""
    md = getattr(node, "metadata", {}) or {}
    # direct observation payload
    if isinstance(md, dict) and "observation" in md:
        obs = md["observation"]
        if isinstance(obs, dict) and "metric" in obs:
            return obs
    # flat metadata with metric keys
    if isinstance(md, dict) and "metric" in md and "outcome" in md:
        return md
    # fallback infer from content (population topics only; elsewhere the
    # population default is meaningless and verdict words misfire)
    if getattr(node, "topic_id", "") not in _POP_TOPICS:
        return None
    verdict = _infer_verdict(getattr(node, "content", "") or "")
    if verdict and _verdict_is_pop_claim(getattr(node, "content", "") or "", verdict):
        return {
            "metric": "population",
            "outcome": verdict,
            "direction": _VERDICT_TO_DIRECTION.get(verdict, ""),
            "baseline": md.get("baseline", "") if isinstance(md, dict) else "",
            "scenario": md.get("scenario", {}) if isinstance(md, dict) else {},
        }
    return None

def _extract_new_meta(premise: str, new_metadata: Dict | None, topic: str | None = None) -> Dict | None:
    if new_metadata and isinstance(new_metadata, dict):
        # allow wrapped or flat
        if "observation" in new_metadata:
            obs = new_metadata["observation"]
            if isinstance(obs, dict) and "metric" in obs:
                return obs
        if "metric" in new_metadata and "outcome" in new_metadata:
            return new_metadata
    if topic is not None and topic not in _POP_TOPICS:
        return None
    v = _infer_verdict(premise)
    if v and _verdict_is_pop_claim(premise, v):
        return {"metric": "population", "outcome": v, "direction": _VERDICT_TO_DIRECTION.get(v, ""), "baseline": (new_metadata or {}).get("baseline", "") if isinstance(new_metadata, dict) else "", "scenario": (new_metadata or {}).get("scenario", {}) if isinstance(new_metadata, dict) else {}}
    return None

def _symbolic_contradicts(a: Dict, b: Dict) -> bool:
    if not a or not b:
        return False
    # metric must match (default population)
    if a.get("metric", "population") != b.get("metric", "population"):
        return False
    # baseline must be compatible: same baseline id if both present
    ba, bb = a.get("baseline", ""), b.get("baseline", "")
    if ba and bb and ba != bb:
        return False
    # outcome opposition
    oa, ob = a.get("outcome", "").upper(), b.get("outcome", "").upper()
    if oa and ob:
        if ob in _OPPOSITE_VERDICTS.get(oa, set()) or oa in _OPPOSITE_VERDICTS.get(ob, set()):
            # horizon check: if years present, must be comparable (±60% relaxed for popu_sim)
            ya, yb = a.get("horizon"), b.get("horizon")
            if ya and yb:
                try:
                    if abs(int(ya) - int(yb)) / max(int(ya), int(yb), 1) > 0.6:
                        return False
                except Exception:
                    pass
            return True
    # direction opposition fallback
    da, db = a.get("direction", "").upper(), b.get("direction", "").upper()
    if da and db and da != db and {da, db} == {"INCREASE", "DECREASE"}:
        return True
    return False

def _compatible_for_contradiction(new_meta: Dict, existing_node) -> bool:
    try:
        from kernel.simulation_version import is_compatible
        md = getattr(existing_node, "metadata", {}) or {}
        obs = md.get("observation", {}) or {}
        sim_new = new_meta.get("simulator")
        sim_ex = obs.get("simulator") or md.get("validity", {}).get("simulator")
        if sim_new and sim_ex and sim_new != sim_ex:
            return False
        # HISTORICAL not comparable
        validity = md.get("validity", {}) if isinstance(md, dict) else {}
        if validity.get("status") == "HISTORICAL":
            return False
        # superseded nodes are settled history, never block refinements
        if isinstance(md, dict) and md.get("status") == "superseded":
            return False
        # version compatibility per-sim
        new_ver = new_meta.get("version_id")
        ex_ver = obs.get("version_id") or validity.get("valid_for_version")
        if new_ver and ex_ver and sim_new and sim_ex and sim_new == sim_ex:
            if not is_compatible(ex_ver, new_ver, simulator=sim_new):
                return False
    except Exception:
        pass
    return True

def check_observation_contradiction(topic: str, new_meta: Dict) -> Tuple[bool, List[Dict]]:
    from kernel.memory.semantic_memory import semantic_memory
    conflicts = []
    for n in semantic_memory.search_by_topic(topic):
        if not _compatible_for_contradiction(new_meta, n):
            continue
        existing_meta = _extract_observation_meta(n)
        if _symbolic_contradicts(new_meta, existing_meta):
            conflicts.append({"node_id": n.node_id, "title": n.title, "premise": n.content[:120], "symbolic": True, "reason": f"opposite outcome {new_meta.get('outcome')} vs {existing_meta.get('outcome')}", "baseline": new_meta.get("baseline")})
    return (len(conflicts) > 0, conflicts)

def check_hypothesis_contradiction(title: str, description: str, category: str, predictions: List[str] = None) -> Tuple[bool, List[Dict]]:
    from kernel.hypothesis.hypothesis_engine import hypothesis_engine
    conflicts = []
    for h in hypothesis_engine.hypotheses.values():
        if category != "general" and h.category != category:
            continue
        sim_title = _similar(title, h.title)
        sim_desc = _similar(description, h.description)
        sim = max(sim_title, sim_desc)
        if sim < 0.6:
            continue
        # if existing is validated (supported/rejected/uncertain) and not proposed
        # Resemblance is agreement, not contradiction: opposition required.
        opp = _is_opposite(description, h.description) or _is_opposite(title, h.title)
        if h.status in ("supported", "rejected", "uncertain"):
            # opposite predictions or negation indicates contradiction
            if opp and sim > 0.6:
                conflicts.append({"hypothesis_id": h.hypothesis_id, "title": h.title, "status": h.status, "similarity": round(sim, 2)})
        elif opp and sim > 0.8:
            conflicts.append({"hypothesis_id": h.hypothesis_id, "title": h.title, "status": h.status, "similarity": round(sim, 2)})
    return (len(conflicts) > 0, conflicts)

def _load_stored_embedding(node_id: str):
    try:
        from kernel.persistence.db import kernel_db
        import struct
        blob = kernel_db.load_semantic_embedding(node_id)
        if blob is None:
            return None
        return list(struct.unpack(f"{len(blob)//4}f", blob))
    except Exception:
        return None

def _similar_stored(new_vec, node_id: str, node_text: str, new_text: str) -> float:
    j = _jaccard(new_text, node_text)
    try:
        stored = _load_stored_embedding(node_id)
        if stored is not None and new_vec is not None:
            c = _cosine(new_vec, stored)
            c_norm = (c + 1) / 2 if c != 0 else 0
            return max(j, c_norm)
    except Exception:
        pass
    # fallback to on-fly
    return _similar(new_text, node_text)

def check_topic_contradiction(topic: str, name: str, premise: str, new_metadata: Dict | None = None) -> Tuple[bool, List[Dict]]:
    from kernel.memory.semantic_memory import semantic_memory
    conflicts: List[Dict] = []
    dup_hints: List[Dict] = []  # resemblance-only; never blocks
    # --- symbolic tier for observations (FixesIssues.md) ---
    new_meta = _extract_new_meta(premise, new_metadata, topic)
    is_observation_topic = topic == "popu_sim" or (new_meta is not None)
    # symbolic check first: embeddings only retrieve, never decide for observations
    if new_meta:
        blocked, sym = check_observation_contradiction(topic, new_meta)
        # for observations, symbolic opposition IS the contradiction signal
        # but we do NOT block on symbolic alone for popu_sim — we surface as conflict
        # so kernel can create contradicts edge. For blocking, require opposite outcome.
        for c in sym:
            # mark symbolic conflict; caller (topic_store) will decide block vs edge hint
            conflicts.append({**c, "similarity": 0.95})
        # if symbolic found, we can return early without expensive embedding gate
        # but still allow semantic fallback for non-observation layers
        if is_observation_topic and conflicts:
            # also check contradicts edge proximity (same as before but symbolic-triggered)
            return (True, conflicts)

    new_combined = f"{name} {premise}"
    new_vec = _embed(new_combined)
    for n in semantic_memory.search_by_topic(topic):
        if isinstance(getattr(n, "metadata", {}), dict) and n.metadata.get("status") == "superseded":
            continue  # settled history never blocks refinements
        existing_combined = f"{n.title} {n.content}"
        if _disjoint_measurements(new_combined, existing_combined):
            continue  # distinct runs/gens: resemblance is progress, not opposition
        is_obs_node = n.node_type in OBSERVATION_TYPES or _extract_observation_meta(n) is not None
        # use stored BLOB if available for fast path
        sim = _similar_stored(new_vec, n.node_id, existing_combined, new_combined) if new_vec else _similar(new_combined, existing_combined)
        opp = _is_opposite(premise, n.content)
        # tiered gate: observations require symbolic, not pure similarity
        if is_obs_node or n.node_type in OBSERVATION_TYPES:
            # per-sim + version compatibility + HISTORICAL filter for observations
            if new_meta and not _compatible_for_contradiction(new_meta, n):
                continue
            # for observations, only symbolic or explicit opposite+high-sim triggers
            if new_meta and _extract_observation_meta(n) and _symbolic_contradicts(new_meta, _extract_observation_meta(n)):
                if not any(c.get("node_id") == n.node_id for c in conflicts):
                    conflicts.append({"node_id": n.node_id, "title": n.title, "premise": n.content[:120], "similarity": 0.95, "symbolic": True})
                continue
            # suppress sim>0.85 false positive for observations
            if opp and sim > 0.6:
                # also check compatibility for opposite case
                if new_meta and not _compatible_for_contradiction(new_meta, n):
                    continue
                conflicts.append({"node_id": n.node_id, "title": n.title, "premise": n.content[:120], "similarity": round(sim, 2)})
            continue
        # non-observation (hypothesis/interpretation) keeps semantic gate.
        # Resemblance alone NEVER blocks: high similarity without opposition
        # is agreement/redundancy. It is returned as a non-blocking duplicate
        # hint so callers may suggest a supports/supersedes edge instead.
        if opp and sim > 0.6:
            conflicts.append({"node_id": n.node_id, "title": n.title, "premise": n.content[:120], "similarity": round(sim, 2)})
        elif sim > 0.85:
            dup_hints.append({"node_id": n.node_id, "title": n.title, "premise": n.content[:120], "similarity": round(sim, 2), "duplicate_hint": True})
        # NOTE: resemblance to a contradicts-edge endpoint is NOT a
        # contradiction (a correction-rich topic would otherwise self-poison
        # all future same-domain writes: embedding sim > 0.6 is near-certain
        # within a topic). Explicit contradicts edges still fire detection at
        # add-edge time via check_contradictions/emit_contradiction_signal.
    return (len(conflicts) > 0, conflicts + dup_hints)
