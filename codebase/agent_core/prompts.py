"""System prompt assembly from capability-aware fragments."""

from __future__ import annotations

import os
import re
from typing import List, Optional

from agent_core.config import CODEBASE_ROOT, AGENTS_MD_ENABLED, ALLOWED_COMMANDS, resolve_active_tool_mode
from agent_core.workspace import WORKSPACE_ROOT
from agent_core.tools import log_output
from agent_core.tools.registry import CAT_FILE, CAT_KERNEL, CAT_SIM, CAT_META, CAT_CODE_RAG, CAT_DEBATE, CAT_GIT, CAT_OBSERVER

DEFAULT_SYSTEM_PROMPT = "You are a helpful assistant."
PROMPT_FRAGMENTS_DIR = os.path.join(CODEBASE_ROOT, "prompt_fragments")

_cache: dict[str, tuple[float, str]] = {}  # cache_key → (mtime_sum, prompt)

_GATE_OPEN_RE = re.compile(r"^\s*<!--\s*read_only\s*-->\s*$")
_GATE_CLOSE_RE = re.compile(r"^\s*<!--\s*/read_only\s*-->\s*$")

# (filename, requires_categories, blocks_categories, modes)
FRAGMENT_ORDER: List[tuple[str, Optional[List[str]], Optional[List[str]], Optional[List[str]]]] = [
    ("base_persona.md",       None,         None,   None),
    ("efficiency_rules.md",   None,         None,   None),
    ("implementation_guardrails.md", None,  None,   None),
    ("file_ops_workflow.md",  [CAT_FILE],   None,   ["all", "read_only"]),
    ("meta_playbook.md",      [CAT_META],   None,   None),
    ("code_rag.md",           [CAT_CODE_RAG], None, None),
    ("kernel_playbook.md",    [CAT_KERNEL], None,   None),
    ("debate_playbook.md",    [CAT_DEBATE], None,   None),
    ("sim_playbook.md",       [CAT_SIM],    None,   None),
    ("git_playbook.md",       [CAT_GIT],    None,   None),
    ("observer_playbook.md",  [CAT_OBSERVER], None, None),
    ("response_contract.md",  None,         None,   None),
]


def load_agents_md() -> str:
    if not AGENTS_MD_ENABLED:
        return ""
    agents_path = os.path.join(WORKSPACE_ROOT, "AGENTS.md")
    if not os.path.exists(agents_path):
        return ""
    try:
        with open(agents_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if content:
            return f"\n---\n## Project Context (from AGENTS.md)\n{content}\n---\n"
    except Exception:
        pass
    return ""


def _include_fragment(
    requires: Optional[List[str]],
    blocks: Optional[List[str]],
    modes: Optional[List[str]],
    active_packs: List[str],
    mode: str,
) -> bool:
    if modes is not None and mode not in modes:
        return False
    if requires is not None:
        if not any(p in active_packs for p in requires):
            return False
    if blocks is not None:
        if any(p in active_packs for p in blocks):
            return False
    return True


def _filter_mode_block(content: str, mode: str) -> str:
    lines = content.split("\n")
    if mode == "all":
        return "\n".join(
            l for l in lines
            if not (_GATE_OPEN_RE.match(l) or _GATE_CLOSE_RE.match(l))
        ).strip()
    if not any(_GATE_OPEN_RE.match(l) for l in lines):
        return content
    keep, out = False, []
    for line in lines:
        if _GATE_OPEN_RE.match(line):
            keep = True
            continue
        if _GATE_CLOSE_RE.match(line):
            keep = False
            continue
        if keep:
            out.append(line)
    return "\n".join(out).strip()


def _fragments_mtime(fragments_dir: str, active_packs: List[str], mode: str) -> float:
    total = 0.0
    for filename, requires, blocks, modes in FRAGMENT_ORDER:
        if not _include_fragment(requires, blocks, modes, active_packs, mode):
            continue
        fpath = os.path.join(fragments_dir, filename)
        try:
            total += os.path.getmtime(fpath)
        except OSError:
            total += 0
    return total


def load_system_prompt(
    path: Optional[str] = None,
    active_packs: Optional[List[str]] = None,
    mode: Optional[str] = None,
) -> str:
    if active_packs is None:
        active_packs = [CAT_FILE, CAT_KERNEL, CAT_SIM, CAT_META, CAT_GIT, CAT_DEBATE, CAT_OBSERVER, CAT_CODE_RAG]
    if mode is None:
        mode = resolve_active_tool_mode()

    fragments_dir = path if path else PROMPT_FRAGMENTS_DIR
    cache_key = f"{fragments_dir}:{','.join(sorted(active_packs))}:{mode}"
    mtime = _fragments_mtime(fragments_dir, active_packs, mode)

    cached = _cache.get(cache_key)
    if cached is not None and cached[0] == mtime:
        return cached[1]

    parts: List[str] = []
    for filename, requires, blocks, modes in FRAGMENT_ORDER:
        if not _include_fragment(requires, blocks, modes, active_packs, mode):
            continue
        fragment_path = os.path.join(fragments_dir, filename)
        try:
            with open(fragment_path, "r", encoding="utf-8") as f:
                content = f.read()
            content = _filter_mode_block(content, mode)
            if content.strip():
                parts.append(content.strip())
        except FileNotFoundError:
            log_output(f"WARNING: prompt fragment {filename} not found")
        except Exception as e:
            log_output(f"ERROR reading {filename}: {e}")

    template = "\n\n".join(parts)
    agents_md = load_agents_md()
    template = template.replace("{AGENTS_MD}", agents_md)
    template = template.replace(
        "{ALLOWED_COMMANDS}", ", ".join(sorted(ALLOWED_COMMANDS))
    )

    _cache[cache_key] = (mtime, template)
    return template
