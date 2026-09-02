# VSE — Future Roadmap

Work that remains after Phases 0–F are done. For what was built and measured see `Findings.md` (detailed numbers) and `usage.md §5` (short summary). Before Phase 0 the stack already had the end-to-end simulator, cycle engine, memory hierarchy, NoC, compilation, search, power/area, FPGA/RTL/ASIC. Phases 0–F added the physics limit: splits `<500 LOC`, physical SRAM `BW=banks×ports×bits/8×freq`, per-tensor `Q2/Q3/Q4` + VSE-S1, distributed tiles, families/CIM, co-search, and a 14-check fail-closed gate. This file now keeps only where the project should evolve next.

---

## What is already done (Phases 0–F)

All of the near-term phases that were open at writing are now implemented (see `Findings.md §4` for numbers, `IssuesFix.md` for the unified remaining plan):

- **Phase 0–A** — splits `<500 LOC`, physical SRAM `SRAMArray` `BW=banks×ports×bits/8×freq` with area/wire/latency/energy, `off/warn/fail`.
- **Phase B** — per-tensor `Q2/Q3/Q4` (`Q2Block` 2b+8b/32), VSE-S1 presets `490M/701M/1.01B`, heuristic accuracy, `--precision-map`.
- **Phase C** — distributed tiles `TiledHierarchy` `tile{i}_sram`, per-tile `SRAMArray`/`NoC`, `--num-tiles` (shared HBM still limits).
- **Phase D** — families `scalar/simd/vector/systolic/cim/near_memory` (`PEFamilyConfig` effective MACs/latency) and CIM fused `vse_cim_cell` (`HBM→0`).
- **Phase E** — `ModelArchSpec` + `run_co_search` + `DistillEngine` + `codesign` multi-objective `tok/s vs area vs accuracy`.
- **Phase F** — 14-check gate `compute/sram_bw/latency/banks/noc_bw/latency/wire/clock/power/leakage/thermal/area/capacity/timing` → `off/warn/fail` + JSON.

Remaining work is now **Phase G** and the further-out packaging/frontend.

---

## Remaining — Phase G and beyond (do next)

### G1 — PDK calibration (new `vse/physics/pdk.py`)
Pluggable `ProcessTechnology` fed by Yosys/Verilator/OpenROAD synthesis/P&R vs `for_node`. Without this, area/timing/power stay analytical. Add `--toolchain` CLI that lints, synthesizes, and imports measured `mm²/ns/W` to re-calibrate.

### G2 — Per-tile HBM
Tiles already shard SRAM/PEs but share one HBM port → replication stays BW-neutral. Add per-tile `HBM BW = tiles × link_bw` and `expert-aware placement` so `replicas` truly parallelize weight streams.

### G3 — Cycle-accurate vs analytical
Keep analytical fast path for `search --sample 10k`, add slow accurate path for verification:
```
analytical schedule → cycle-accurate pipeline (fill/drain, accumulator deps)
analytical memory   → bank-conflict/latency cycle model
analytical NoC      → flit-level routing
```
`fpga/sim.py` is the reference.

### G4 — General model frontend (Phase 18)
ONNX or small graph IR beyond hand-built Transformer/MoE, so any fixed network can be compiled.

### G5 — Packaging (Phases 14,17)
Add only when it becomes the limiter: torus/tree/crossbar for NoC; 2.5D/3D, chiplets, HBM stacks, interposer routing, per-die power/thermal coupling.

### G6 — Joint physical co-optim (Phase 19) + Silicon validation (Phase 20)
Search precision+layout+pipeline+floorplan together (not sequential) so every reported `tok/s` is timing-closed. Keep `tests/regression/test_golden_numbers.py` and calibrate estimators against a real PDK/tape-out library.

---

## Research directions (updated)

### Extreme-throughput physics — now checked by the gate

For `T` tok/s and `M` MACs/token: `compute = T×M`, `bandwidth = T×bytes/token`. The 14-check gate now enforces `compute, sram_bw/latency/banks, noc_bw/latency, wire, clock, power, leakage, thermal, area, capacity, timing` together. A `10M tok/s` claim is `PHYSICALLY PLAUSIBLE` only if all pass (`--physics warn` shows `✓/✗`).

### Fixed-model silicon — now the co-search objective

`remove unused ops/precision, hard-wire routing/placement, fuse, pre-place weights, static schedule, dedicated datapaths` are now compile-time decisions (`precision_map`, `placement`, `fusion`). The gate distinguishes algorithmic vs physical savings; the next step is to keep the model and silicon evolving together (`codesign`) rather than optimizing hardware for a frozen model.

### What is still missing (before trusting 100K+ tok/s)

Most items are now modeled (PE utilization via families, bank conflicts via `peak_banks`, wire via `SRAMArray`, leakage/thermal via `ProcessTechnology`), but these remain analytical:

- **PDK-measured** area/timing/power vs `for_node` estimates.
- **Per-tile HBM** BW (tiles still share one port).
- **Cycle-accurate** flit-level NoC and bank-conflict latency vs analytical `throughput`.
- **Clock distribution** beyond `pipeline+wire`.

Without PDK calibration they remain theoretical workload numbers.

---

## Testing strategy

Every major component has unit tests (`tests/`). As the project grows:

```text
tests/
├── integration/
├── architecture/
├── performance/
└── regression/
```

Every architecture change should keep regression benchmarks — especially
the flagship Transformer-decode and MoE numbers documented in `usage.md`.

---

## Recommended next files (remaining)

```text
1. vse/physics/pdk.py          ← PDK calibration (G1)
2. vse/core/memory_hierarchy.py ← per-tile HBM (G2)
3. vse/core/noc.py, vse/core/tile.py ← flit-level, packaging (G3/G5)
4. vse/graphs/                  ← ONNX IR frontend (G4)
5. vse/asic/physical.py, vse/silicon/process.py ← gate-calibrated (G1/G6)
```

---

## Final vision

VSE should eventually become a research platform where the following
question can be answered quantitatively:

> Given a fixed neural network, what is the fastest physically plausible
> silicon architecture for executing it?

The complete loop:

```text
 Fixed Model → Model Compiler → Hardware Graph
                 (compute / memory / NoC)
                          ↓
                  VSE Simulator
                          ↓
                Performance / Power
                          ↓
                 Architecture Search
                          ↓
                     RTL → FPGA → ASIC
```

The ultimate goal is not simply to simulate an LLM. **The goal is to build
a virtual laboratory for discovering specialized AI silicon
architectures.**
