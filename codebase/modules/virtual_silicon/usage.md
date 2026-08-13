# VSE — Usage Guide

This file is the practical reference for the VSE (Virtual Silicon Engine)
module: how to run it, what the CLI modes and flags do, what the expected
results are and what they mean, the Python API, and the findings from the
experiments so far.

For the project overview (why VSE exists, what it does, current status)
see `README.md`; for future work see `roadmap.md`.

All commands assume the `myenv` conda environment:

```bash
conda run -n myenv <command>
```

and must be run from the `virtual_silicon` directory:

```bash
cd codebase/modules/virtual_silicon
```

---

## 1. Quick example — `compute_example.py`

A minimal virtual compute architecture: one 1e9-MAC matmul on a 4096-PE array clocked at 1 GHz.

```bash
conda run -n myenv python compute_example.py
```

Output:

```text
{'total_cycles': 244141,
 'latency_us': 244.14100000000002,
 'latency_seconds': 0.000244141,
 'frequency_hz': 1000000000.0,
 'events': 1,
 'resource_utilization': {'compute': 0.9999984640023593}}
```

Interpretation:

- The compute array sustains `4096 PEs × 1 MAC/cycle = 4096 MAC/cycle`.
- One matmul needs `1e9 / 4096 ≈ 244,141` cycles → **244 µs**.
- `resource_utilization = 0.99999` means the array was saturated (~100% of its peak capability) for the entire run.

---

## 2. End-to-end simulation — CLI

The `vse.cli` module connects model → operation costs → scheduler task graph → cycle schedule → benchmark report.

### 2.1 Transformer decode

Generate one token on a decoder-only Transformer:

```bash
conda run -n myenv python -m vse.cli transformer \
    --hidden-dim 4096 --heads 32 --layers 8 \
    --intermediate 11008 --sequence 4096 --mem-bw 1024
```

Output:

```text
VSE END-TO-END SIMULATION
============================================================
Model            : transformer
Tokens           : 1
Sequence length  : 4,096

EXECUTION
------------------------------------------------------------
Total cycles     : 4,213,488
Latency          : 4,213.488 us
Throughput       : 237.333 tok/s

WORKLOAD
------------------------------------------------------------
Total MACs       : 1887.437M
Memory bytes     : 4317.581M
Arithmetic inten : 0.437 MAC/B

UTILIZATION
------------------------------------------------------------
Compute          :  10.94%
Memory           : 100.00%
```

Interpretation:

- Single-token decode at 4096 context is **memory-bound** (`Memory 100%`, `Compute 10.94%`).
- 1.89G MACs per token but 4.3GB of traffic (dominated by KV-cache reads) → ~237 tok/s on this virtual chip.
- Adding a target feasibility check shows how far away a goal is:

```bash
conda run -n myenv python -m vse.cli transformer \
    --hidden-dim 4096 --heads 32 --layers 8 \
    --intermediate 11008 --sequence 4096 --mem-bw 1024 \
    --target 1000000
```

```text
TARGET ANALYSIS
------------------------------------------------------------
Target           : 1,000,000 tok/s
Reached          : no
```

### 2.2 MoE layer

Run one Mixture-of-Experts layer (64 experts, top-2) on 32 tokens:

```bash
conda run -n myenv python -m vse.cli moe \
    --hidden-dim 4096 --intermediate 14336 \
    --experts 64 --top-k 2 --tokens 32 --target 1000000
```

Output:

```text
VSE END-TO-END SIMULATION
============================================================
Model            : moe
Tokens           : 32
Sequence length  : 0

EXECUTION
------------------------------------------------------------
Total cycles     : 24,514,592
Latency          : 24,514.592 us
Throughput       : 1.305K tok/s

WORKLOAD
------------------------------------------------------------
Total MACs       : 11282.678M
Memory bytes     : 1.311M
Arithmetic inten : 8606.319 MAC/B

UTILIZATION
------------------------------------------------------------
Compute          :  11.23%
Memory           :  89.82%

MEMORY HIERARCHY
------------------------------------------------------------
SRAM  read       524,288 B  write       524,288 B  peak banks 1
HBM   read 5,637,144,576 B  write             0 B  peak banks 0
Weights       : streamed (HBM)
HBM total     : 5,637,144,576 B

TARGET ANALYSIS
------------------------------------------------------------
Target           : 1,000,000 tok/s
Reached          : no
```

Interpretation (Phase 3):

- The MoE layer is now **memory-bound** (`Memory 89.82%`, `Compute 11.23%`).
- Phase 3 adds **expert weight traffic**: with 64 experts × 1 token each, all
  5.25 GiB of expert weights stream from HBM (256 B/cycle) because they do not
  fit on-chip (`Weights: streamed (HBM)`).
- Streaming dominates: ~24.5M cycles vs the ~2.75M cycles compute alone would
  need → ~1.3K tok/s; target 1M tok/s not reached.
- Weight streaming is double-buffered by default (`--double-buffer 4`):
  compute for chunk c overlaps the stream of chunk c+1, trimming ~258K cycles
  vs no double buffering (`--double-buffer 1`).

### 2.2b Making weights resident

If the working set fits in SRAM, weights are cold-loaded once from HBM (via
the DMA engine) then read from SRAM across many banks:

```bash
conda run -n myenv python -m vse.cli moe \
    --hidden-dim 4096 --intermediate 14336 \
    --experts 64 --top-k 2 --tokens 32 \
    --sram-gb 6 --sram-bw 2048 --banks 16
```

```text
MEMORY HIERARCHY
------------------------------------------------------------
SRAM  read 5,637,144,576 B  write             0 B  peak banks 16
HBM   read 5,637,144,576 B  write             0 B  peak banks 0
Weights       : resident (SRAM)
HBM total     : 5,637,144,576 B
```

Resident weights are read concurrently from 16 SRAM banks (`peak banks 16`);
the remaining HBM traffic is the one-time cold load. In a single forward the
cold load still dominates, so residency pays off across multiple forwards
(weight reuse) rather than within one.

### 2.2c KV-cache residency (transformer)

By default (`--sram-gb 0`) the KV-cache streams from HBM, which is why the
single-token decode is memory-bound (`Memory 100%`). When the KV-cache fits
on-chip it is read/written at SRAM bandwidth instead:

```bash
conda run -n myenv python -m vse.cli transformer \
    --hidden-dim 4096 --heads 32 --layers 8 \
    --intermediate 11008 --sequence 4096 --mem-bw 1024 \
    --sram-gb 8 --sram-bw 8192
```

```text
Total cycles     : 3,754,624      (vs 4,213,488 with KV on HBM)
Throughput       : 266.338 tok/s  (vs 237.333)
```

The off-chip traffic drops from ~4.32 GB to the weights + activations only,
so the decode speeds up ~11%. This is why a large on-chip SRAM matters for
long-context inference: the KV-cache grows with sequence length and must stay
on-chip to avoid HBM-bound decode.

### 2.2d Network-on-Chip (Phase 4a/4b)

The MoE layer can route token activations and expert results across an
interconnect (`--noc-nodes > 1`): `router → NoC → expert → NoC → combine`.
Experts are placed round-robin across the nodes. Ring wraps around; mesh
uses Manhattan distance. Each transfer pays `hops × --noc-hop-cycles` of
pipeline latency and contends for a shared bandwidth resource:

```bash
conda run -n myenv python -m vse.cli moe \
    --hidden-dim 4096 --intermediate 14336 --experts 64 --top-k 2 \
    --tokens 32 --noc-nodes 16 --noc-topology mesh
```

```text
NETWORK (NoC)
------------------------------------------------------------
Transfers       : 128
Bytes           : 1.049M
Hops            : 384
Latency        : 5,632 cyc
Congestion      :   0.02% link util, 1 peak transfers
Deadlock        : none (acyclic)
```

The report also shows **congestion** (link-bandwidth utilization + peak
in-flight transfers) and a **deadlock** check (the scheduler only runs
acyclic graphs, so it is always `none` unless a cyclic graph is supplied).

For 32 tokens the ~1 MB of activation traffic over the NoC is ~0.02% of
the HBM weight stream, so the NoC is not the bottleneck here. It becomes
visible when expert activations are large relative to weights (small hidden
dim / many tokens) or when the NoC bandwidth is constrained
(`--noc-bw`).

**Broadcast** (`--noc-broadcast`) changes the interconnect from
point-to-point sends to a single broadcast of the full token tensor to
every node — 8.5× the traffic but one task instead of one per expert:

```bash
conda run -n myenv python -m vse.cli moe \
    --hidden-dim 1024 --intermediate 2048 --experts 8 --top-k 2 \
    --tokens 8 --num-pes 512 --noc-nodes 16 --noc-broadcast
```

```text
Transfers       : 9            (vs 16 point-to-point)
Bytes           : 557.056K     (vs 65.536K)
Broadcasts      : 1
```

**Multicast** is exposed in the Python API: `noc.transfer_task(..., dests=[...])`
sends a copy to each destination, scaling link work by the copy count and
charging latency for the farthest destination.

### 2.3 Common hardware flags

| Flag | Default | Meaning |
| --- | --- | --- |
| `--num-pes` | `4096` | Processing elements in the compute array |
| `--macs-per-pe` | `1` | MACs per PE per cycle |
| `--mem-bw` | `256` | Memory bandwidth in bytes/cycle (off-chip default) |
| `--freq` | `1e9` | Clock frequency in Hz |
| `--pipeline` | `0` | Compute pipeline latency in cycles |
| `--sram-gb` | `0.0` | On-chip SRAM capacity in GiB |
| `--banks` | `1` | Independent banks per memory level |
| `--hbm-bw` | `0` | HBM bandwidth bytes/cycle (`0` = `--mem-bw`) |
| `--sram-bw` | `0` | SRAM bandwidth bytes/cycle (`0` = `--mem-bw`) |
| `--dma-bw` | `0` | DMA transfer bandwidth bytes/cycle (`0` = `--mem-bw`) |
| `--double-buffer` | `4` | Weight streaming double-buffer depth (`1` disables) |
| `--noc-topology` | `ring` | NoC topology: `ring` or `mesh` |
| `--noc-nodes` | `1` | NoC router nodes (`1` disables cross-node traffic) |
| `--noc-bw` | `256` | NoC link bandwidth bytes/cycle |
| `--noc-hop-cycles` | `4` | NoC pipeline latency per hop |
| `--noc-broadcast` | — | Broadcast tokens to all NoC nodes instead of per-expert sends |
| `--compile` | — | Compile the model into a fixed graph (Phase 5) |
| `--weight-bits` | model | Compiled weight precision in bits |
| `--activation-bits` | model | Compiled activation precision in bits |
| `--kv-bits` | model | Compiled KV-cache precision in bits |
| `--no-fusion` | — | Disable activation fusion when compiling |
| `--expert-placement` | `round_robin` | Expert → NoC node placement strategy |
| `--target` | — | Target tok/s feasibility check |
| `--trace` | — | Print the per-cycle activity trace |
| `--json` | — | Machine-readable JSON output |

### 2.4 Parallel execution and `--trace`

Phase 2 replaces the list scheduler with a parallel cycle engine
(`vse/core/engine.py`). Tasks with explicit `units` run concurrently on
different PE slices. MoE experts are split across the array, so the
per-cycle trace shows the array ramping up and draining down. With
Phase 3 weight streaming, experts start computing as their first weight
chunks arrive, so the ramp happens in chunked steps:

```bash
conda run -n myenv python -m vse.cli moe \
    --hidden-dim 1024 --intermediate 2048 --experts 8 --top-k 2 \
    --tokens 8 --num-pes 512 --trace
```

```text
compute
------------------------------------------------------------
cycle     3,072 | busy     64/   512 | tasks 1
cycle    15,360 | busy    128/   512 | tasks 2
cycle    27,648 | busy    192/   512 | tasks 3
cycle    39,936 | busy    256/   512 | tasks 4
cycle    52,224 | busy    256/   512 | tasks 4
cycle    64,512 | busy    384/   512 | tasks 6
cycle    76,800 | busy    448/   512 | tasks 7
cycle    89,088 | busy    512/   512 | tasks 8
...
PEAK CONCURRENCY (max busy units per resource)
------------------------------------------------------------
compute                  512
```

### 2.5 Model-specific compilation (Phase 5)

`--compile` compiles the exact model + hardware into a fixed execution
graph and prints a `COMPILE PLAN` recording every decision (precision,
PE allocation, expert placement, memory placement, routing, pipeline,
fusion).

- **Precision** — `--weight-bits`/`--activation-bits`/`--kv-bits`
  override the model's precision. Weight bytes scale proportionally:
  8-bit weights double MoE HBM traffic (5.6 → 11.3 GB) and latency
  (24.5M → 46.3M cycles) vs the 4-bit default.

```bash
conda run -n myenv python -m vse.cli moe \
    --hidden-dim 4096 --intermediate 14336 --experts 64 --top-k 2 \
    --tokens 32 --compile --weight-bits 8 --noc-nodes 16
```

- **Fusion** (on by default) — intermediate activations never round-trip
  memory. MoE expert results skip the SRAM write (SRAM write traffic
  drops to 0); the transformer keeps only the model input read and output
  write. `--no-fusion` disables it.

```bash
conda run -n myenv python -m vse.cli transformer \
    --hidden-dim 4096 --heads 32 --layers 8 \
    --intermediate 11008 --sequence 4096 --mem-bw 1024 --compile
```

```text
Total cycles     : 1,157,595      (vs 4,213,488 unfused)
Throughput       : 863.860 tok/s  (vs 237.333)
...
COMPILE PLAN (model-specific)
------------------------------------------------------------
Precision       : w4b a16b kv16b
PE allocation   : 4,096 PEs total, 0 per expert
Memory plan     : weights streamed (hbm, not modeled), KV hbm
Pipeline        : 1 stage(s), 8 layers, double-buffer n/a
Fusion          : on (saved 15 SRAM round-trips)
```

The fused decode is compute-bound: by eliminating ~4.3 GB of HBM
activation traffic per token, it drops from the memory-bound 237 tok/s to
864 tok/s. This is the strongest single optimization in the simulator so
far — real chips get the same effect from keeping activations on-chip.

### 2.6 Prefill and gating

- `--mode prefill` (transformer only) processes an entire prompt in parallel instead of one token.
- `--no-gated` disables the gated (SwiGLU) MLP, reducing projections from 3 to 2.

### 2.7 Hardware architecture search (Phase 6)

`search` compiles and simulates the same fixed model on many candidate
chips and reports the best by tokens/sec plus the Pareto frontier
(tokens/sec vs a silicon-area proxy).

```bash
conda run -n myenv python -m vse.cli search --model moe \
    --hidden-dim 4096 --intermediate 14336 --experts 64 --top-k 2 \
    --tokens 32 \
    --dim num_pes=1024,2048,4096,8192 \
    --dim hbm_bw=128,256,512 \
    --dim weight_bits=4,8
```

- `--model {transformer,moe}` selects the workload (model args are the
  same as the `transformer`/`moe` commands).
- `--dim NAME=V1,V2,...` (repeatable) expands one search dimension.
  Supported dimensions: `num_pes`, `macs_per_pe`, `freq`, `sram_gb`,
  `hbm_bw`, `sram_bw`, `banks`, `noc_nodes`, `noc_bw`, `weight_bits`,
  `activation_bits`, `kv_bits`, `fusion`, plus Phase 6/7 dimensions:
  - `pipeline` — pipelined stage execution depth.
  - `double_buffer` — weight stream chunks (overlaps compute with
    streaming).
  - `noc_topology` — `ring` / `mesh`.
  - `tokens` — batch size (MoE `--tokens`).
  - `replicas` — expert replication factor.
  - `placement` — `round_robin` / `contiguous` expert-node mapping.
  - `node_nm` — process node (energy scales ~linearly, area ~quadratically
    vs the 7 nm default).
- Flags like `--num-pes`/`--sram-gb`/`--hbm-bw` set the fixed base chip
  that the varied dimensions are applied on top of. MoE search also
  accepts `--expert-replicas`, `--expert-placement`, `--pipeline`,
  `--double-buffer`, `--noc-topology`, and `--node-nm` on the base spec.
- `--sample N` replaces the Cartesian product with `N` random draws from
  the `--dim` space (fixed `--seed` for reproducibility). Use it when the
  space is too large to enumerate (thousands of candidates).

```text
VSE ARCHITECTURE SEARCH
============================================================
Candidates        : 6
Search space      : num_pes=128,256,512, weight_bits=4,8

TOP 5 BY TOKENS/SEC
------------------------------------------------------------
  #  tok/s      cycles     area(mm²)  W       cmp   mem   arch
* 1    83.333K     96.000K      0.674   10.749  51.2  51.2 512PE x1MAC 1.0GHz 0MB 256B/cy w4b
  2    56.004K    142.848K      0.674   10.616  34.4  68.8 512PE x1MAC 1.0GHz 0MB 256B/cy w8b
* 3    55.115K    145.152K      0.337    5.744  67.7  33.9 256PE x1MAC 1.0GHz 0MB 256B/cy w4b
  4    41.667K    192.000K      0.337    5.638  51.2  51.2 256PE x1MAC 1.0GHz 0MB 256B/cy w8b
* 5    32.860K    243.456K      0.168    3.372  80.8  20.2 128PE x1MAC 1.0GHz 0MB 256B/cy w4b

PARETO FRONTIER (tokens/sec vs die area)
------------------------------------------------------------
  #  tok/s      cycles     area(mm²)  arch
  1    83.333K     96.000K      0.674 512PE x1MAC 1.0GHz 0MB 256B/cy w4b
  2    55.115K    145.152K      0.337 256PE x1MAC 1.0GHz 0MB 256B/cy w4b
  3    32.860K    243.456K      0.168 128PE x1MAC 1.0GHz 0MB 256B/cy w4b

* = candidate is on the Pareto frontier
```

- The **top table** ranks every candidate by tokens/sec. `area(mm²)` is
  the Phase-7 die-area estimate, `W` the simulated average power,
  `cmp`/`mem` are compute and memory utilization.
- A **`*`** marks candidates on the Pareto frontier: no other candidate is
  both cheaper (area) and faster (tokens/sec). The **frontier table**
  lists exactly those — the designs worth keeping for Phase 8+.
- If all candidates are Pareto-optimal the report says so — that means
  the objectives did not trade off within the space (e.g. adding SRAM
  changed nothing because the workload was already HBM-bound).
- `--json` prints `{"candidates": [...], "frontier": [...]}` with one
  entry per chip (architecture, cycles, tokens/sec, utilizations, area,
  power, energy/token, tokens/Watt).

Area and power are analytical estimates from `ProcessTechnology`
(defaults ~7 nm); the frontier is a relative ranking, not a silicon
guarantee.

---

## 3. Python API

### 3.1 End-to-end simulation

```python
from vse.models.moe import MoE, MoEConfig
from vse.models.transformer import TransformerConfig, TransformerModel
from vse.workload import (
    HardwareConfig,
    simulate_moe,
    simulate_transformer,
)

model = TransformerModel(
    TransformerConfig(
        hidden_dim=4096,
        num_heads=32,
        intermediate_dim=11008,
    ),
    num_layers=8,
)

result = simulate_transformer(
    model,
    sequence_length=4096,
    config=HardwareConfig(
        num_pes=4096,
        memory_bytes_per_cycle=1024,
        frequency_hz=1e9,
    ),
)

print(result.report())
```

### 3.2 Result object

`simulate_transformer()` / `simulate_moe()` return an `EndToEndResult` with:

- `total_cycles`, `latency_us`, `latency_seconds`
- `tokens_per_second`
- `compute_utilization`, `memory_utilization`
- `schedule` — the `ScheduleResult` with per-event start/result cycles, `units` per task, per-resource utilization, `peak_concurrency`, `peak_banks`, and the per-cycle activity `trace`
- `memory` — the memory-hierarchy report: per-level (SRAM/HBM) read/write bytes, peak bank usage, and weight residency
- `benchmark` — the analytical roofline `BenchmarkResult` (MACs, memory bytes, compute/memory bound, required bandwidth, target feasibility)

Call `result.report()` for a combined dictionary, or `print(result.schedule.report())` / `print(result.benchmark.report())` for the sub-reports.

### 3.3 Architecture search

```python
from vse.search.architecture import ArchitectureSpec, SearchSpace
from vse.compiler.compiler import compile_moe
from vse.search.search import run_search, run_random_search, pareto_frontier

space = SearchSpace(
    {
        "num_pes": [1024, 2048, 4096],
        "hbm_bw": [128, 256, 512],
        "weight_bits": [4, 8],
    }
)

def build(spec: ArchitectureSpec):
    return compile_moe(
        moe,
        tokens=32,
        config=spec.to_hardware_config(),
        options=spec.to_compile_options(),
    )

results = run_search(space, build)            # exhaustive grid
results = run_random_search(space, build, n=100, seed=1)  # or sampled
frontier = pareto_frontier(results)           # tokens/sec vs die area
```

`ArchitectureSpec` describes one chip + its compile-time decisions and
turns them into the `HardwareConfig`/`CompileOptions` the compiler
consumes. `SearchResult` exposes `tokens_per_second`, `total_cycles`,
`area_mm2`, `power_watts`, `tokens_per_watt`, and a `report()` dict;
`pareto_frontier` keeps only non-dominated candidates.

The search objective is **tokens/sec ÷ power** — throughput per watt —
subject to die area, memory, bandwidth, and thermal limits. Every
dimension accepted by `--dim` on the CLI (`pipeline`, `double_buffer`,
`noc_topology`, `tokens`, `replicas`, `placement`, `node_nm`, …) is also
a `SearchSpace` key, and `spec.sample_specs(n, seed)` draws random
candidates for large spaces.

---

## 4. Understanding the numbers

| Metric | Meaning |
| --- | --- |
| `total_cycles` | Wall-clock cycles the virtual chip needs for the workload |
| `latency_us` | `total_cycles / frequency_hz` |
| `tokens_per_second` | `tokens / latency_seconds` |
| `compute_utilization` | Work done ÷ peak compute capability = `MACs / (PEs × MAC/PE/cycle × cycles)` |
| `memory_utilization` | Bytes moved ÷ peak memory capability |
| `peak_concurrency` | Maximum `units` busy on each resource (how much of the array was ever active in parallel) |
| `peak_banks` | Maximum banks in use on a memory resource (bank conflicts stall when this saturates) |
| `hbm_read_bytes` / `sram_read_bytes` | Bytes moved at each hierarchy level (weight streaming vs on-chip access) |
| `arithmetic_intensity` | `MACs / bytes moved` — low values imply memory-bound behavior |
| `compute_bound` / `memory_bound` | Which resource limits throughput (roofline analysis) |

A saturated resource reports ~100% utilization. Values like `Memory 100%` with `Compute 10%` indicate the memory subsystem is the bottleneck and adding PEs will not help.

### 4.1 Power and area (Phase 7)

Every end-to-end result now also carries physical estimates in the
`ENERGY & POWER` and `AREA` sections of the report:

| Metric | Meaning |
| --- | --- |
| `Energy` (mJ) | Dynamic energy = compute (total MACs × MAC energy) + memory (per-level bits × bit energy) + NoC (bits × bit energy) |
| `Energy/token` (µJ) | Total energy ÷ tokens — the fixed-model silicon cost per token |
| `Power` (W) | Energy ÷ measured latency — true average power from the *simulated* schedule, not a roofline |
| `static` (W) | Leakage = die area × `leakage_density_mw_per_mm²`; for large SRAMs leakage dominates (1 GiB SRAM ≈ 25 W) |
| `Tokens/Watt` | `tokens_per_second ÷ power` — the Phase-7 objective (`tokens/sec / power`) |
| `Thermal density` (W/mm²) | Power ÷ area, checked against `thermal_limit_w_per_mm²`; `Thermally fit: no` flags a design that exceeds the cooling budget |
| `Total` (mm²) | Die area = PE array + SRAM + NoC routers × routing overhead |
| `Compute` / `SRAM` / `NoC` (mm²) | Area breakdown |

Derived efficiency metrics (`tokens / Joule`, `tokens / mm²`,
`tokens / Watt`) follow directly from energy/token and area — they are
how the search ranks candidate dies once power and area are known.

The constants live in `ProcessTechnology` (defaults ~7 nm, order-of-magnitude
estimates). Everything is duck-typed, so the same models run on the
simulated activity (`EndToEndResult`) or on a bare `ArchitectureSpec`:

```python
from vse.silicon.process import ProcessTechnology
from vse.silicon.area import estimate_area
from vse.silicon.power import estimate_power

tech = ProcessTechnology(node_nm=16)  # coarser node, higher energy/area
area = estimate_area(spec, tech=tech)
power = estimate_power(result, tech=tech, chip=spec)
```

Process-node scaling: `ProcessTechnology.for_node(node_nm)` scales energy
≈ linearly and area ≈ quadratically from the 7 nm baseline, so the
`node_nm` search dimension trades density against efficiency. Leakage and
thermal density are only computed when a chip (`ArchitectureSpec` /
`HardwareConfig`) is passed in — without one, only the dynamic terms are
reported.

Note: the `--json` output of the `search` command still includes the old
Phase-6 `area_proxy`/`power_proxy` for compatibility, but the displayed
ranking and the Pareto frontier use the real `area_mm2` and `power_watts`.

---

## 5. Findings (Phases 1–5)

Key conclusions from the virtual-chip experiments:

1. **Memory movement, not compute, is the dominant limitation** (Phase 3
   hypothesis confirmed). Both flagship workloads are memory-bound on a
   4096-PE chip at 256 B/cycle off-chip bandwidth.

2. **Transformer decode is KV-cache-bound.** One token at 4096 context needs
   ~4.3 GB of traffic (mostly KV reads): 4,213,488 cycles / 237 tok/s at
   1024 B/cycle. The fix is on-chip KV: with 8 GiB SRAM at 8192 B/cycle the
   decode drops to 3,754,624 cycles / 266 tok/s (~11%). Long-context
   inference therefore demands large on-chip SRAM, not more PEs.

3. **MoE sparsity hides a weight-streaming cost.** 64 experts × top-2 with
   32 tokens touches all 64 experts (1 token each). The 5.25 GiB of 4-bit
   expert weights streams from HBM and makes the layer memory-bound:
   24,514,592 cycles / 1.3K tok/s. Compute alone would take ~2.75M cycles.

4. **Weight residency pays off across forwards, not within one.** In a single
   forward the one-time HBM cold load dominates regardless of SRAM size; the
   benefit of resident weights (DMA cold load once, then banked SRAM reads)
   materializes when the same experts are reused across tokens/requests.

5. **Double buffering helps only when compute is the tail.** Chunked
   streaming (`--double-buffer 4`) overlaps compute with the weight stream,
   trimming ~1% (24,772,640 → 24,514,592 cycles) because the single HBM port
   is the hard bottleneck. Raising `--hbm-bw`/`--banks` (more channels)
   matters far more than buffering depth.

6. **The levers that matter:** off-chip HBM bandwidth, on-chip SRAM capacity
   (KV-cache + weight residency), and memory banks. PEs are rarely the
   constraint at these workloads.

7. **Fusion is the strongest single optimization.** Keeping intermediate
   activations on-chip (model-specific compilation) cuts the 8-layer
   transformer decode from 4,213,488 → 1,157,595 cycles (~3.6×) and drops
   MoE SRAM activation writes to zero.

8. **Precision is a first-class hardware lever.** Halving weight precision
   halves HBM weight traffic and MoE latency 1:1 (24.5M → 46.3M cycles at
   8-bit vs 4-bit). The compiler exposes `--weight-bits`/`--activation-bits`/
   `--kv-bits` as compile-time decisions.

9. **The NoC is not a bottleneck for MoE activation traffic.** Token
   activations are tiny next to the weight stream (~1 MB vs 5.6 GB HBM), so
   interconnect utilization stays near 0% and only becomes visible when
   activations are large relative to weights or `--noc-bw` is constrained.
   Broadcast (`--noc-broadcast`) trades ~8.5× the NoC traffic for a single
   transfer when the token tensor is replicated to all nodes.

10. **Memory movement dominates *energy* too, not just latency.** With
    ~7 nm process constants, HBM traffic accounts for ~95%+ of the dynamic
    energy of a streamed-weight workload (1.01 mJ memory vs 0.025 mJ
    compute for a 16-expert MoE layer). Energy/token is a memory problem:
    `tokens/Joule` improves with on-chip residency, precision, and
    bandwidth — the same levers as latency. Meanwhile **area is an SRAM
    problem**: 1 GiB of on-chip SRAM (~430 mm² at ~7 nm) dwarfs a
    thousand-PE compute array (~1 mm² per 1k PEs), which caps how much KV
    or weight residency a realistic die can afford.

11. **Expert replication is bandwidth-neutral without extra memory ports.**
    Replicating experts (`--expert-replicas`) splits weight streams and
    MACs across copies, but with a single shared HBM port the total weight
    traffic and total power are unchanged, so end-to-end cycles barely
    move. The graph model is correct — replicas genuinely need per-node
    memory bandwidth to pay off, which is a distributed-memory extension
    (see roadmap), not a compile-time flag.

12. **Static/leakage power flips the power picture on big SRAMs.** At
    ~7 nm, leakage density (~50 mW/mm²) turns a 1 GiB SRAM into ~25 W of
    always-on power — more than the dynamic power of a 16-expert MoE layer.
    Small compute-only chips stay dynamically bound; dies with large
    on-chip storage become leakage-bound. Thermal density (W/mm²) then
    flags designs that outrun a ~1 W/mm² cooling budget.

---

## 6. Tests

```bash
conda run -n myenv python -m pytest tests/ -q
```