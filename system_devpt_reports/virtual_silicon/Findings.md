# VSE — Detailed Findings

This is the consolidated record of what the Virtual Silicon Engine has measured across its evolution. `usage.md §5` keeps a short summary; this file keeps the numbers, commands, and interpretation that justify each claim. All commands assume `myenv` and `virtual_silicon` directory (`conda run -n myenv python -m vse.cli ...`).

---

## Methodology

- Analytical models for MACs/bytes feed a compile-time task graph (`model → ops → graph → schedule`), executed on the cycle engine (`vse/core/engine.py`) with bandwidth, banks, pipeline, and NoC contention.
- Power/area from `ProcessTechnology` (~7 nm, `for_node` scales energy linear, area quadratic) plus leakage `50 mW/mm²` and thermal `1 W/mm²`.
- Regression pinned in `tests/regression/test_golden_numbers.py`: `transformer decode 4,213,488 cyc / 237 tok/s`, `fused 1,157,595 / 863 tok/s`, `MoE 24,514,592 / 1.3K tok/s` at the flagship configs.

---

## Legacy findings (pre-Phase 0)

**1. Memory, not compute, limits the flagships.** On 4096 PEs at 256 B/cyc both workloads report memory-bound (`Memory ~100% / 89%`, `Compute ~10%`).

**2. Decode is KV-cache bound.** `4096` context: `4,213,488 cyc / 237 tok/s` at `mem-bw 1024`. With `8 GiB SRAM at 8192 B/cyc` → `3,754,624 cyc / 266 tok/s` (+11%). Long context needs on-chip KV, not more PEs.

```bash
python -m vse.cli transformer --hidden-dim 4096 --heads 32 --layers 8 --intermediate 11008 --sequence 4096 --mem-bw 1024
python -m vse.cli transformer --hidden-dim 4096 --heads 32 --layers 8 --intermediate 11008 --sequence 4096 --mem-bw 1024 --sram-gb 8 --sram-bw 8192
```

**3. MoE sparsity hides weight-streaming.** `64×top-2, 32 tok` touches all 64 experts → `5.25 GiB` of 4-bit weights stream from HBM (256 B/cyc) → `24.5M cyc / 1.3K tok/s`; compute-only would be `~2.7M`. Double-buffer `chunks=4` overlaps but saves only `~258K` (~1%) because the single HBM port is the bottleneck.

**4. Residency pays across forwards.** Resident `sram-gb 6, sram-bw 2048, banks 16` → `peak banks 16`, HBM still shows the one-time cold load `5.6G`. Benefit appears when experts are reused, not within a single forward.

**5. Fusion is the biggest single win.** `--compile` keeps activations on-chip: `4,213,488 → 1,157,595 cyc` (3.6×, `237→863 tok/s`), MoE SRAM writes →0 (`plan: saved 15`).

**6. Precision is 1:1 with HBM.** MoE `w8` doubles `5.6→11.3G` and `24.5M→46.3M`; `w2` halves. Exposed via `--weight-bits/--activation-bits/--kv-bits` and later per-tensor.

**7. NoC not bottleneck for this shape.** `32 tok, 16 nodes mesh` → `128 transfers 1.049M 384 hops, 0.02%` (tiny vs `5.6G` HBM). Broadcast `9` vs `16` p2p at `557K vs 65K` (8.5×).

**8. Energy follows memory, area follows SRAM.** `~7 nm`: HBM `1.01 mJ` vs compute `0.025 mJ` (~95% memory) for 16-expert MoE; `1 GiB SRAM ~430 mm²` dwarfs `1k PEs ~1 mm²`. Leakage `50 mW/mm²` → `1 GiB ~25 W` always-on, dies become leakage-bound, thermal `1 W/mm²` flags.

---

## Phase A — Physical SRAM (BW must be built)

**What changed:** `MemoryLevel` was free (`capacity+read_bw+banks`). `SRAMArray` now enforces `BW = banks × ports × bits_access/8 × freq` (`ports 1..4, bits 8..512`), plus `area = bytes×0.05µm²×1.2+ports×0.01 mm²`, `wire = 0.1×√(cap/4K)×node/7 ns`, `lat = 3+ceil(wire×freq)`, `energy = bits×0.005 pJ`. `MemoryHierarchy.default(sram_model="physical", ...)` derives BW; `physical_bandwidth_report()` shows `requested vs derived vs achievable`; `validate_physical()`.

**New flags:** `--sram-model {analytical,physical}` (default `analytical`), `--sram-ports`, `--sram-bits-per-access`; `HardwareConfig.sram_model/ports/bits`.

**Finding:** Fake `TB/s` disappears. Example `8 GiB, 1024-hidden, sram-bw 8192`:
- Analytical `banks16` → `348,840 cyc / 2866 tok/s` (free).
- Physical `banks1×1×32/8=4` → `derived 4, requested 8192, achievable=False` → `33,895,072 cyc / 29.5 tok/s` (~100× slower).
- Honest `32×4×512/8=8192` restores `348,840` at cost `area ~515 mm²/GiB`, `lat ~16 cyc` (`wire 0.18 ns`). `power.py` and `area.py` now use `SRAMArray`, `physical.py` adds `wire×0.5` and `lat` to critical path. All 203 tests still green with analytical default; `--physics` path shows `sram_physical_energy_uj`.

---

## Phase B — Mixed precision and VSE-S1

**What changed:** Global `weight_bits` replaced by `precision_map` (`vse/compiler/precision.py:Q2Block 2b+8b scale/32 → packed+scale`, `parse_precision_map`, `precision_to_bytes`, `effective_bits`). `CompileOptions(precision_map={'attn':3,'mlp':Q2Block})` → `plan["precision"]=w2/3`. CLI `--precision-map '{"attn":3,"mlp":2}'`, `--q2-group-size/--q2-scale-bits`; `VSES1Config` presets `500M (490M L16/H1536), 700M (701M), 1B (1.01B)` via `4H²+3HI` per layer (`vse_s1/costs.py`).

**Finding:** Per-tensor beats uniform. `MoE 64×top2/32tok`: `w4 5.63 GB /24.5M → w8 11.27G/46.2M → mix Q2 MLP + Q3 attn 3.17G (-44%) /14.9M (-39%,1.64×,2.25b avg)`. Heuristic `accuracy.py:estimate_accuracy` (`attn 1.0 > kv 0.8 > mlp 0.5`) → `pass@k 0.85→0.80` for that mix. Still `4,213,488` golden with global `w4`.

---

## Phase C — Distributed tiles

**What changed:** `TiledHierarchy.build_tiled_hierarchy(HardwareConfig:num_tiles 1..64)` shards `num_pes/sram_bytes` evenly, each tile owns `SRAMArray`. `to_hierarchy()` emits `tile0..N_sram + hbm`; `VirtualMachine` + `graph_moe:build_moe_tasks(tile_hierarchy)` route `wchunk` and `act_read/write` to `tile{t}_sram`. `NoCConfig:num_tiles` adds `effective_bandwidth=link_bw×tiles` and `per_tile_utilization`. `area.py` sums `tile.area`, `power.py` sums tile `sram_read_bytes`. CLI/search `--num-tiles`, `--tile-banks/--tile-ports/--tile-bits`, `--sram-per-tile-gb/--pes-per-tile`; dims `num_tiles/sram_per_tile/...`.

**Finding:** Locality without per-tile HBM still HBM-bound. `moe 8×top2/8tok 1 tile 285k/28K tok/s (hbm 25M)` → `4 tiles (4×256 MiB) 286k similar, TILE{i}_SRAM 8K each`. `replicas=2` stays `880k cyc` both — needs per-tile HBM (roadmap Phase 15).

---

## Phase D — Architecture families and CIM

**What changed:** `vse/core/pe_families.py:ArchFamily{scalar,simd,vector,systolic,weight_stationary,output_stationary,cim,near_memory}` + `PEFamilyConfig(effective_macs, gate_overhead, latency_extra, area_factor)`. `ComputeConfig(family,vector_width 1..16,systolic_dim 0..64,simd_lanes 1..8,dataflow)` drives `macs_per_cycle` and `cycles_for_macs + latency`. Graphs add `cim` fused `read→compute` → `kind:cim` (`hbm 0`), `power.py` halves HBM energy for CIM, `physical.py` `+500 gates/PE`, RTL adds `vse_cim_cell`. `workload.py:HardwareConfig` carries `arch_family/vector_width/systolic_dim/simd_lanes/dataflow`; `VirtualMachine` sets scheduler `throughput = effective_macs_per_pe` and pipeline `+dim` for systolic. CLI `--arch-family/--vector-width/--systolic-dim/--simd-lanes/--dataflow` and search dims.

**Finding:** Families move the bottleneck. Fused transformer `8 GiB SRAM 8192 B/cyc`: `scalar 339k → vector4 91k (3.7×) → systolic 8×8 15k (21×)` when compute-bound. Same families barely move weight-streaming MoE (`24.5M→22.4M vector, 8%`) — the big shift is CIM: `hbm 5.6G→0`, `577→321` tasks, `24.5M→2.7M cyc (8.8×)`, now `Family` is a first-order search variable alongside banks/cap/precision.

---

## Phase E — Co-search (model + silicon)

**What changed:** `vse/search/model_space.py:ModelArchSpec(layers,hidden,heads,intermediate)` + `ModelSearchSpace` and `vse/search/co_search.py:CoSearchResult(model,arch,result,accuracy)` + `run_co_search`/`run_random_co_search` (`product(model_specs,hw_specs) → compile→execute → accuracy`). `vse/distill/engine.py` heuristic loop `Teacher→candidate→synthetic→distill→VSE→mutate`. `search.py:pareto_frontier` now multi-objective (`maximize=[tok/s,accuracy], minimize=[area]`). New CLI `codesign --model-dim hidden_dim=1024,2048 --dim num_pes=... --sample N` (frontier `tok/s vs area vs accuracy`).

**Finding:** Searching only chips misses the smallest model that meets accuracy under a silicon budget. Example `ModelSpace{1024/2048,8/12}×Space{1024/4096}` → `16 cands, frontier 3`; `codesign --sample 4` frontier favors `8L 1024H (102M, 4757 tok/s, 0.85 acc)`. The objective becomes `tok/s vs area vs accuracy` (e.g., `tokens_per_watt`, `tokens_per_mm²`) not just `tok/s vs area`.

---

## Phase F — Hard physics gate (fail-closed)

**What changed:** `vse/physics/gate.py:PhysicsGate.check(result,chip)` 14 checks `compute, sram_bw/sram_latency/bank_conflicts, noc_bw/noc_latency, wire_delay, clock, power, leakage, thermal, area, capacity, timing_closure` → `GateCheck(✓/✗)` + `PHYSICALLY PLAUSIBLE`. `search.py` `run_search(..., physics off/warn/fail)` filters `fail`; `asic/loop.py` tries `banks*2` on `sram_bw` fail before pipeline; `report/formatting.py` renders gate section; `workload.py` attaches `result.gate` when `physics!="off"`; `result.py` adds `physics:{plausible,checks[]}` to JSON. CLI `--physics off/warn/fail` on `transformer/moe/search/asic/codesign`.

**Finding:** Previously a report could claim `10M tok/s` while ignoring power/area/timing. With `--physics warn` a typical `512-hidden, 2-layer` already shows `thermal fail` (`PHYSICALLY IMPLAUSIBLE`), impossible `sram_model physical 1×1×32` requesting `8192` fails `sram_bw 8192 vs 1`; `--physics fail` filters those candidates from the frontier, and JSON carries the 14 checks for toolchains.

---

## How to use findings

- `usage.md §5` keeps a 1-line summary of each of the 7 bullets above for quick reference.
- This file keeps the commands and numbers to reproduce. Run the listed CLI lines and compare `Total cycles`, `HBM read`, `area`, `power`, `THERMALLY fit`, and `PHYSICS GATE` to verify.

Regression: `tests/regression/test_golden_numbers.py` still pins `4,213,488` etc.; change only with justification.
