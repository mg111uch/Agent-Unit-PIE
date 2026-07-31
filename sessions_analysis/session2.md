## Where tokens went

**#1 consumer:** Reading `__init__.py` (546 lines) **5 times** — each re-read to verify registration positioning after edits. Total: ~2500+ lines.

**#2 consumer:** Reading `file_ops.py` (593 lines) **3 times** — same reason.

**#3 consumer:** Re-reading files after small edits to verify correctness, even though I should have trusted `edit`'s "success" return.

---

## Behaviors that wasted tokens (no new tool needed)

| Waste | Fix (already possible) |
|---|---|
| Re-reading full files after edits | Trust `edit`'s success return + the diff it returns |
| Reading whole `__init__.py` to find one function | Use `read_section` with pattern `def _register_file_tools` |
