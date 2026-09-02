# VSE → Physics-Limit AI Silicon: Remaining Issues & Plan

> **Unified from `IssuesFix.md` + `IMPLEMENTATION_PLAN.md`.** Phases A–F are implemented and detailed in `Findings.md` (external agent can understand status from that file alone). `IMPLEMENTATION_PLAN.md` has been removed; this file now keeps the single remaining plan.

Original short version (still true):
> **Change optimization target from “simulate specialized hardware” to “co-design a tiny fixed model and the physically realizable silicon that executes it.”** Architecture already treats model as hardware and supports compilation, banked SRAM, NoC, search, RTL/FPGA, ASIC estimation.

Source: `README.md`, `usage.md` (§5), `roadmap.md` (11,16,20), `Findings.md` consolidated status.

---

## Status: Done vs Remaining

| Phase | Status | One-line |
| --- | --- | --- |
| Phase 0 — Foundation | ✓ Done | Splits `<500 LOC`, stubs, regression `203 passed` |
| Phase A — Physics Core | ✓ Done | `SRAMArray` `BW=banks×ports×bits/8×freq`, `validate_physical()` |
| Phase B — Mixed Precision/VSE-S1 | ✓ Done | `Q2Block` per-tensor map, `VSES1Config` 490M/701M/1.01B, heuristic accuracy |
| Phase C — Distributed Tiles | ✓ Done | `TiledHierarchy` `tile{i}_sram`, per-tile NoC, `--num-tiles` |
| Phase D — Families/CIM | ✓ Done | `ArchFamily` effective MACs, CIM fused task + `vse_cim_cell`, `--arch-family` |
| Phase E — Co-search | ✓ Done | `ModelArchSpec` + `run_co_search` + `codesign`, multi-objective Pareto |
| Phase F — Physics Gate | ✓ Done | 14 checks, `off/warn/fail`, JSON `physics:{plausible}` |
| **Phase G — Validation** | **TODO** | **Below** |

All phases kept `analytical` green behind flags; `usage.md` 496 lines.

---

## Where the project was (now done)

Original loop `Model→Compiler→Graph→Compute/Memory/NoC→Sim→Search→RTL→Physical` was already correct. Implemented items that were open at report time are now done: Transformer/MoE, banked SRAM/HBM, KV cache, DMA/double-buffer, NoC, fusion, precision, search, power/area/thermal, RTL/FPGA, ASIC timing. See `Findings.md §5` for numbers.

---

## Implemented — now one-line (see Findings.md for numbers)

- **§4 VSE-S1 target model** — ✓ Done: `VSES1Config` presets 490M/701M/1.01B, teacher→distill loop heuristic, hardware-aware.
- **§5 Q2 non-uniform precision** — ✓ Done: `Q2Block` 2b+8b/32, per-tensor map `attn:Q3 mlp:Q2 head:Q4 kv:Q3`, mixed MoE -44%.
- **§6 Distributed SRAM** — ✓ Done: `TiledHierarchy` `tile{i}_sram`, per-tile `SRAMArray` (shared HBM still limits, needs per-tile HBM).
- **§7 SRAM physical modeling** — ✓ Done: `SRAMArray` `BW=banks×ports×bits/8×freq`, area/wire/latency/energy, not free `8 TB/s`.
- **§8 Physical bandwidth equation** — ✓ Done: `validate_physical()` `requested vs derived`.
- **§9 CIM family** — ✓ Done: `ArchFamily{scalar,simd,vector,systolic,cim,near_memory}` + `vse_cim_cell`, fused task `HBM→0, 8.8×`.
- **§10 Metrics per token** — ✓ Done: `weight/act/kv/NoC bytes/token` via `report`.
- **§11 Physics Gate** — ✓ Done: 14 checks `compute, sram_bw/latency/banks, noc_bw/latency, wire, clock, power, leakage, thermal, area, capacity, timing` → `off/warn/fail` + JSON.

---

## SWOT — remaining

### Strengths (kept)
- Model-as-hardware philosophy, end-to-end stack, memory-first insight, search, fixed-model specialization, FPGA/RTL bridge — all now physics-validated.

### Weaknesses still open
- No commercial PDK calibration (still analytical `~7 nm` estimates).
- Not yet cycle-accurate (analytical schedule vs flit-level NoC/bank conflicts).
- Per-tile HBM not yet (tiles still share single HBM port).

### Opportunities still open
- **AI Silicon Compiler category** — now possible via `codesign` (model+chip Pareto).
- **USB-C device** — `Tiny controller + ASIC (distributed SRAM/Q2/KV/NoC/static schedule)` → `USB → inference API`, model never in host RAM. Needs per-tile HBM + PDK + packaging before product.
- **Fixed-model Q2** — now hardware-designed around fixed layout/scales, but needs PDK area/power to prove economics.

### Threats still open
1. **SRAM physics** — 1 GiB still `~430 mm²` + `25 W` leakage; large KV/weights may be uneconomic. Needs PDK + 2.5D/chiplets.
2. **Thermal density** — 100K tok/s still risks `>1 W/mm²` even if compute/memory pass. Gate now flags, but cooling budget still tight.
3. **Autoregression** — `token N→N+1→N+2` sequential; needs model-architecture evolution (not just more PEs).
4. **Model obsolescence** — fixed silicon vs new model → family/partial programmability required.
5. **Manufacturing cost** — `RTL→verification→synthesis→P&R→DRC/LVS→masks` expensive; FPGA/RTL path mitigates but not yet PDK-proven.

---

## Revised roadmap — remaining only (Phase G, roadmap 11,16,20)

All of original Phases A–E are done (see Findings.md). Do next, in order:

1. **PDK calibration (`vse/physics/pdk.py`)** — pluggable constants fed by Yosys/Verilator/OpenROAD synthesis/P&R vs `ProcessTechnology.for_node`. Without this, area/timing/power stay estimates.
2. **Cycle-accurate vs analytical** — `fpga/sim.py` vs `engine.py` equivalence, flit-level NoC, bank-conflict cycle model (roadmap Phase 16).
3. **Per-tile HBM + advanced packaging** — `banks×ports` per tile truly scales BW; add 2.5D/3D, chiplets, HBM stacks (Phase 17). Currently tiles shard SRAM but share single HBM port (C limitation).
4. **General model frontend** — ONNX/small IR beyond hand-built Transformer/MoE (Phase 18).
5. **Joint physical co-optim** — precision+layout+pipeline+floorplan in one loop (Phase 19).
6. **Silicon validation** — real PDK library vs tape-out regression, keep `tests/regression/test_golden_numbers.py` (Phase 20).

---

## What I would do next — updated

| Priority | Work | Why | Status |
| --- | --- | --- | --- |
| **1** | Physical SRAM/bank/port model | Biggest missing physics | **✓ Done** |
| **2** | Build ~700M–1B Python/JS benchmark model | Actual target | **✓ Done** |
| **3** | Q2/Q3 mixed-precision compiler | Memory footprint | **✓ Done** |
| **4** | Distributed SRAM tiles + NoC | Bandwidth scaling | **✓ Done (shared HBM limits)** |
| **5** | Model ↔ hardware co-optimization | Breakthrough | **✓ Done (heuristic distill)** |
| **Next** | PDK calibration + per-tile HBM + cycle-accurate | Make claims measured | **TODO** |

Then re-ask VSE:
> **What is the smallest, coolest, lowest-power physically realizable chip for 1K/10K/50K/100K/1M tok/s?**

---

## DAG (remaining)

```
Phase G ← Phase F (done) — single agent, then loop back to Findings.md
```

Parallelizable before was `A1∥A2, B1∥B2, C1∥C2`; D waited for C, E for B+C+D, F for A+E.

---

## Verification (remaining)

- `conda run -n myenv pytest tests/ -q` (currently 203) + `tests/regression/test_golden_numbers.py`.
- CLI smokes: `transformer`, `moe`, `search --sample 20`, `fpga --rtl`, `asic --max-iters 4`, `codesign --sample 4`.
- Gate smoke: `--physics fail` rejects `sram_bw 8192, 1 bank` when physical.

---

## Open questions (still open for Phase G)

1. PDK default — `7nm` or `7/5/3` presets?
2. VSE-S1 fidelity — code-only spec vs tiny checkpoint?
3. Gate default — `warn` vs `fail` after PDK calibration?
4. Persistence — JSON-only vs SQLite frontier replay?

---

## Cross-cutting principles (still apply)

- `<500 LOC/file`, one persistence path (SQLite), no hard toolchain dep, CLI compat (`--physics`, `--sram-model`, `--arch-family`, `--num-tiles`), `off/warn/fail` defaults.

---

## File impact (remaining only)

| New | Modified (remaining) |
| --- | --- |
| `vse/physics/pdk.py` | `vse/silicon/process.py`, `vse/asic/physical.py`, `vse/core/engine.py`, `vse/core/noc.py` |

For completed file map see `Findings.md §7` and `README.md:113`.

---

## Final assessment (still true)

**SWOT verdict:** Strong research foundation, now a physics-validated discovery system (was “hardware exploration platform”). Findings already point to memory/SRAM/precision/locality/fusion over PEs. Biggest conceptual shift is done: **evolving model and ASIC together toward the physical optimum**, now implemented as `codesign` loop `Teacher→Candidate→Distill→Accuracy→VSE→Pareto→RTL/FPGA/ASIC` (see Findings.md §5).
