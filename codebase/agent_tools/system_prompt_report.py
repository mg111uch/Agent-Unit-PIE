"""System-prompt truth report (PlanFixes3 #1).

Resolves the "899 vs 1,288 tokens" ambiguity by measuring the EXACT prompt the
runtime sends, through the same load path used by the server and the P3
benchmark (load_system_prompt with resolve_active_tool_packs / mode / core_only).

Counts are printed in three explicitly-labeled units:
  - chars
  - tiktoken(cl100k) via agent_core.tokenizer (the wire estimator's unit)
  - the same tiktoken count expressed as the wire-estimator build_budget total

Usage:
  conda run -n myenv python codebase/agent_tools/system_prompt_report.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agent_core.prompts import load_system_prompt
from agent_core.config import (
    resolve_active_tool_packs,
    resolve_active_tool_mode,
    SYSTEM_PROMPT_CORE_ONLY,
)
from agent_core.tokenizer import count_tokens


def main() -> None:
    packs = resolve_active_tool_packs()
    mode = resolve_active_tool_mode()
    prompt = load_system_prompt(
        active_packs=packs, mode=mode, core_only=SYSTEM_PROMPT_CORE_ONLY,
    )
    core = load_system_prompt(active_packs=packs, mode=mode, core_only=True)

    tok = count_tokens(prompt)
    print("=== Deployed system prompt (runtime path) ===")
    print(f"load args        : active_packs={packs} mode={mode!r} core_only={SYSTEM_PROMPT_CORE_ONLY}")
    print(f"chars            : {len(prompt)}")
    print(f"tiktoken (est)   : {tok}")
    print(f"estimate_total   : {tok}   (context_budget.build_budget; same encoder)")
    print()
    print(f"core_only variant: {count_tokens(core)} tokens / {len(core)} chars "
          f"(drop full-deploy by {tok - count_tokens(core)} tokens)")
    print()
    budget = 1024
    print(f"target <= {budget} tokens: {'OK' if tok <= budget else f'over by {tok - budget}'}")
    print("unit note: tiktoken(cl100k) estimates ONLY — provider-reported counts")
    print("(Gemini tokenizer) are never mixed in; see context_budget formatters.")


if __name__ == "__main__":
    main()