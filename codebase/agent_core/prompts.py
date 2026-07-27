"""System prompt assembly from capability-aware fragments."""

from __future__ import annotations

import os
from typing import List, Optional

from agent_core.config import CODEBASE_ROOT, AGENTS_MD_ENABLED
from agent_core.workspace import WORKSPACE_ROOT
from agent_core.tools import log_output
from agent_core.tools.registry import CAT_FILE, CAT_KERNEL, CAT_SIM, CAT_META, CAT_CODE_RAG

DEFAULT_SYSTEM_PROMPT = "You are a helpful assistant."
PROMPT_FRAGMENTS_DIR = os.path.join(CODEBASE_ROOT, "prompt_fragments")

FRAGMENT_ORDER: List[tuple[str, Optional[List[str]], Optional[List[str]]]] = [
    ("00_base_persona.md",       None,         None),
    ("10_tool_list.md",          None,         None),
    ("20_file_ops_workflow.md",  [CAT_FILE],   None),
    ("25_code_rag.md",          [CAT_CODE_RAG], None),
    ("30_kernel_playbook.md",    [CAT_KERNEL], None),
    ("40_sim_playbook.md",       [CAT_SIM],    None),
    ("51_file_io_details.md",    [CAT_FILE],   None),
    ("60_response_contract.md",  None,         None),
    ("70_embed_mode.md",         None,         [CAT_FILE]),
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
    active_packs: List[str],
) -> bool:
    if requires is not None:
        if not any(p in active_packs for p in requires):
            return False
    if blocks is not None:
        if any(p in active_packs for p in blocks):
            return False
    return True


def load_system_prompt(
    path: Optional[str] = None,
    active_packs: Optional[List[str]] = None,
) -> str:
    if active_packs is None:
        from agent_core.tools.registry import CAT_FILE, CAT_KERNEL, CAT_SIM, CAT_META, CAT_GIT
        active_packs = [CAT_FILE, CAT_KERNEL, CAT_SIM, CAT_META, CAT_GIT]

    fragments_dir = path if path else PROMPT_FRAGMENTS_DIR
    parts: List[str] = []

    for filename, requires, blocks in FRAGMENT_ORDER:
        if not _include_fragment(requires, blocks, active_packs):
            continue
        fragment_path = os.path.join(fragments_dir, filename)
        try:
            with open(fragment_path, "r", encoding="utf-8") as f:
                content = f.read()
            if content.strip():
                parts.append(content.strip())
        except FileNotFoundError:
            log_output(f"WARNING: prompt fragment {filename} not found")
        except Exception as e:
            log_output(f"ERROR reading {filename}: {e}")

    template = "\n\n".join(parts)

    agents_md = load_agents_md()
    template = template.replace("{AGENTS_MD}", agents_md)

    return template
