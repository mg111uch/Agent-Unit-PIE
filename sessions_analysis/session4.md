## Token Spend Analysis & Tool Proposals

### Where most tokens were spent

| Activity | Est. tokens | % of session |
|---|---|---|
| Reading `engine.py` (765 lines) × 4+ passes | ~14,000 | 35% |
| Reading `file_ops.py` (464 lines) × 2 passes | ~4,000 | 10% |
| Exploring provider/model config (5+ files) | ~6,000 | 15% |
| Reading prompt fragments + config.json | ~2,000 | 5% |
| Reading/planning discussions (stepper.py design) | ~8,000 | 20% |
| Edit operations (stepper.py rewrite, engine.py refactor) | ~6,000 | 15% |
| **Total** | **~40,000** | |

**The single biggest sink:** re-reading large files to *understand* them before editing. I read `engine.py` ~4 times fully when a 30-line structural summary would have sufficed for 3 of those passes.

---

### Proposed novel tools

#### 4. `smart_read` — Scenario-aware file reading

Read a file with a purpose hint to automatically optimize reading: for editing, include line numbers; for understanding, return structure instead of content; for searching, highlight matches.

```
smart_read(path="stepper.py", purpose="edit")
  → [full content with line numbers for precise editing]
smart_read(path="stepper.py", purpose="structure")
  → [structural summary like reduce_file]
smart_read(path="engine.py", purpose="find", query="dispatch_step")
  → [only lines 267-281 where dispatch_step is called, with context]
```

**vs existing tools:**
- `read_file` — always returns raw content, always with line numbers (by default)
- `grep_search` — returns matching lines from all files, not contextual reads
- `read_section` — needs explicit line numbers

**Novelty:** Single tool that adapts output format to the use case, reducing token waste from irrelevant content.


