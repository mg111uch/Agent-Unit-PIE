## Token Burn Analysis 1

**#1 consumer:** Reading `__init__.py` (546 lines) **5 times** — each re-read to verify registration positioning after edits. Total: ~2500+ lines.

**#2 consumer:** Reading `file_ops.py` (593 lines) **3 times** — same reason.

**#3 consumer:** Re-reading files after small edits to verify correctness, even though I should have trusted `edit`'s "success" return.

## Token Burn Analysis 2

| Step | Tokens | Why |
|------|--------|-----|
| Explore agent for tool call architecture | ~8-10K | Returned full code of engine.py (712 lines), executor.py, ws_handler.py, registry.py — I had to skim through massive output |
| Reading engine.py in chunks | ~5 reads × 60-200 lines each | Had to re-read same file 5+ times to find exact edit locations |
| Edit failures / re-reads | ~2-3 cycles | `old_string` match failures because I didn't have precise line context |
| Understanding registration patterns | Grep + read __init__.py multiple times | Had to manually trace which `_register_*` function a tool belongs to |
---

## Behaviors that wasted tokens (no new tool needed)

| Waste | Fix (already possible) |
|---|---|
| Re-reading full files after edits | Trust `edit`'s success return + the diff it returns |
| Reading whole `__init__.py` to find one function | Use `read_section` with pattern `def _register_file_tools` |
