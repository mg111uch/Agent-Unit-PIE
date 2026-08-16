#!/usr/bin/env python3
"""E4: link known_gap hypotheses to near-term roadmap bullets.

Creates semantic nodes (roadmap_item, known_gap) and both directed edges:
    roadmap_item --requires--> gap
    gap --required_by--> roadmap_item
Matching is keyword/identifier overlap; ids are deterministic so re-runs are
idempotent (create_node/create_edge overwrite by id).
"""

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "codebase"))

from kernel.hypothesis.hypothesis_engine import hypothesis_engine
from kernel.memory.semantic_memory import semantic_memory
from scripts.seed_hypotheses import seed_all

ROADMAP_DIR = PROJECT_ROOT / "system_devpt_reports"
COMMON = {"agent", "tools", "tool", "loop", "low", "med", "high", "not",
          "for", "the", "in", "on", "of", "and", "across", "manual",
          "features", "blocker"}
GENERIC = {"memory", "question", "integration", "test", "system", "model",
           "project", "feature", "support", "session", "generation"}

_WORD_RE = re.compile(r"[a-z0-9]{3,}")
_IDENT_RE = re.compile(r"/[\w-]+|[\w./-]*_[a-z0-9][\w.]*|[\w./-]+\.py")


def _tokens(text: str) -> set:
    return {m for m in _WORD_RE.findall(text.lower()) if m not in COMMON}


def _identifiers(text: str) -> set:
    return set(_IDENT_RE.findall(text.lower()))


def _near_term_bullets(roadmap_path: Path) -> list:
    lines = roadmap_path.read_text(encoding="utf-8", errors="replace").splitlines()
    bullets, in_sec = [], False
    for line in lines:
        s = line.strip()
        if s.startswith("## "):
            in_sec = "Near-term" in s
            continue
        if in_sec and s.startswith("- "):
            bullets.append(s[2:].strip())
    return bullets


def _matches(gap_text: str, bullet: str) -> bool:
    g_tok, g_ids = _tokens(gap_text), _identifiers(gap_text)
    b_tok, b_ids = _tokens(bullet), _identifiers(bullet)
    if g_ids & b_ids:
        return True
    shared = g_tok & b_tok
    if len(shared) >= 2:
        return True
    return len(shared) == 1 and len(next(iter(shared))) >= 6 \
        and next(iter(shared)) not in GENERIC


def link_gap_blockers(engine=None, memory=None, persist: bool = True) -> list:
    engine = engine or hypothesis_engine
    memory = memory or semantic_memory
    if not engine.hypotheses:
        seed_all(engine)
    created = []
    for roadmap_path in sorted(ROADMAP_DIR.glob("*/roadmap.md")):
        module = roadmap_path.parent.name
        for i, bullet in enumerate(_near_term_bullets(roadmap_path), 1):
            item_id = f"roadmap_{module}_{i}"
            if memory.get_node(item_id) is None:
                memory.create_node(
                    node_id=item_id, node_type="roadmap_item", title=bullet,
                    source_refs=[str(roadmap_path.relative_to(PROJECT_ROOT))],
                    metadata={"module": module}, persist=persist,
                )
            for gap in engine.get_by_type("known_gap"):
                if not _matches(gap.title + " " + gap.description, bullet):
                    continue
                gap_id = gap.hypothesis_id
                if memory.get_node(gap_id) is None:
                    memory.create_node(
                        node_id=gap_id, node_type="known_gap", title=gap.title,
                        metadata={"module": gap_id.split("_")[1],
                                  "source_file": gap.metadata.get("source_file", "")},
                        persist=persist,
                    )
                rels = (
                    (f"{item_id}_requires_{gap_id}", item_id, gap_id, "requires"),
                    (f"{gap_id}_required_by_{item_id}", gap_id, item_id, "required_by"),
                )
                for edge_id, src, tgt, rel in rels:
                    if memory.get_edge(edge_id) is None:
                        memory.create_edge(edge_id=edge_id, source_node_id=src,
                                           target_node_id=tgt, relation_type=rel,
                                           persist=persist)
                created.append({"gap": gap_id, "roadmap": item_id,
                                "bullet": bullet, "module": module})
    return created


def main():
    quiet = "--quiet" in sys.argv or "-q" in sys.argv
    persist = "--dry-run" not in sys.argv
    if quiet:
        import logging
        logging.getLogger("agent_unit_pie").setLevel(logging.WARNING)
        logging.getLogger("agent_unit_pie").handlers.clear()
    links = link_gap_blockers(persist=persist)
    print(f"Linked {len(links)} gap->roadmap blocker(s)")
    if not quiet:
        for l in links:
            print(f"  {l['gap']}  blocks  {l['bullet'][:60]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())