## KERNEL MEMORY

The kernel provides persistent memory across sessions. Use it to recall past work and store important context.

- **Before** exploring a new area, call `kernel_retrieve` with keywords about the task to find relevant past decisions, architectures, or findings.
- **After** a non-obvious discovery, user decision, or important architecture fact, call `kernel_store_context` or `kernel_emit_signal` with descriptive tags so future sessions can retrieve it.
- Do not spam memory every step. Only store information at or above a moderate importance threshold (0.5+).
- If the kernel is unavailable, proceed normally — do not claim memory operations succeeded when they did not.
