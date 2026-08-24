# VSE — Usage Guide

This file is the practical reference for the VSE (Virtual Silicon Engine)
module: how to run it, what the CLI modes and flags do, what the expected
results are and what they mean, the Python API, and summary findings.

For the project overview (why VSE exists, what it does, current status)
see `README.md`; for detailed findings and status see `Findings.md`;
for remaining plan see `IssuesFix.md`; for future work see `roadmap.md`.

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

Interpretation:

- The MoE layer is now **memory-bound** (`Memory 89.82%`, `Compute 11.23%`).
- **Expert weight traffic**: with 64 experts × 1 token each, all
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
conda run -n myenv python -m vse.cli moe --hidden-dim 4096 --intermediate 14336 --experts 64 --top-k 2 --tokens 32 --sram-gb 6 --sram-bw 2048 --banks 16
# → Weights resident (SRAM), peak banks 16 vs streamed HBM
```

Resident weights read from 16 banks;
the remaining HBM traffic is the one-time cold load. In a single forward the
cold load still dominates, so residency pays off across multiple forwards
(weight reuse) rather than within one.

### 2.2c KV-cache residency (transformer)

By default (`--sram-gb 0`) the KV-cache streams from HBM, which is why the
single-token decode is memory-bound (`Memory 100%`). When the KV-cache fits
on-chip it is read/written at SRAM bandwidth instead:

```bash
conda run -n myenv python -m vse.cli transformer --hidden-dim 4096 --heads 32 --layers 8 --intermediate 11008 --sequence 4096 --mem-bw 1024 --sram-gb 8 --sram-bw 8192
# 4,213,488 → 3,754,624 cyc (+11%)
```

The off-chip traffic drops from ~4.32 GB to the weights + activations only,
so the decode speeds up ~11%. This is why a large on-chip SRAM matters for
long-context inference: the KV-cache grows with sequence length and must stay
on-chip to avoid HBM-bound decode.

### 2.2d Network-on-Chip

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
conda run -n myenv python -m vse.cli moe --hidden-dim 1024 --intermediate 2048 --experts 8 --top-k 2 --tokens 8 --num-pes 512 --noc-nodes 16 --noc-broadcast
# 9 transfers vs 16 p2p, 557K vs 65K bytes
```

**Multicast** is exposed in the Python API: `noc.transfer_task(..., dests=[...])`
sends a copy to each destination, scaling link work by the copy count and
charging latency for the farthest destination.

### 2.3 Common hardware flags

| Flag | Default | Meaning |
| --- | --- | --- |
| `--num-pes`/`--mem-bw`/`--sram-gb` | 4096/256/0 | PEs, BW, SRAM |
| `--banks`/`--hbm/sram-bw` | 1/0 | Banks, per-level BW |
| `--noc-*`/`--compile`/`--precision-map` | — | NoC, fixed graph, per-tensor |
| `--sram-model`/`--num-tiles`/`--arch-family`/`--physics` | analytical/1/scalar/off | Physical, tiles, family, gate `off/warn/fail` |
### 2.4 Parallel execution and `--trace`

The parallel cycle engine (`vse/core/engine.py`) replaces the list
scheduler. Tasks with explicit `units` run concurrently on different PE
slices. MoE experts are split across the array, so the per-cycle trace
shows the array ramping up and draining down. With weight streaming,
experts start computing as their first weight chunks arrive, so the ramp
happens in chunked steps:

```bash
conda run -n myenv python -m vse.cli moe \
    --hidden-dim 1024 --intermediate 2048 --experts 8 --top-k 2 \
    --tokens 8 --num-pes 512 --trace
```

```text
cycle 3k: 64/512 → ... → 89k: 512/512  PEAK 512
```

### 2.5 Model-specific compilation

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

### 2.7 Hardware architecture search

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
- `--dim NAME=V1,V2` repeats: `num_pes/macs_per_pe/freq/sram_gb/hbm_bw/sram_bw/banks/noc_nodes/noc_bw/weight_bits/activation_bits/kv_bits/fusion/pipeline/double_buffer/noc_topology/tokens/replicas/placement/node_nm/num_tiles/arch_family/...`.
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
  the die-area estimate, `W` the simulated average power,
  `cmp`/`mem` are compute and memory utilization.
- A **`*`** marks candidates on the Pareto frontier: no other candidate is
  both cheaper (area) and faster (tokens/sec). The **frontier table**
  lists exactly those — the designs worth keeping.
- If all candidates are Pareto-optimal the report says so — that means
  the objectives did not trade off within the space (e.g. adding SRAM
  changed nothing because the workload was already HBM-bound).
- `--json` prints `{"candidates": [...], "frontier": [...]}` with one
  entry per chip (architecture, cycles, tokens/sec, utilizations, area,
  power, energy/token, tokens/Watt).

Area and power are analytical estimates from `ProcessTechnology`
(defaults ~7 nm); the frontier is a relative ranking, not a silicon
guarantee.

### 2.8 FPGA/RTL/ASIC/codesign — `fpga` 6 checks, `rtl.py` SoC, `asic` timing loop; `codesign --model-dim hidden_dim=1024,2048 --dim num_pes=...` co-searches model+chip (frontier tok/s vs area vs accuracy). See `vse:fpga/rtl/asic`.

---

### 2.9 ASIC exploration & the closed loop

`asic` combines RTL generation and physical exploration in one command:
it simulates the compiled model, generates the RTL, estimates the
physical cost of that RTL, and — if the requested clock does **not**
close timing — updates the architecture and re-simulates, until the
reported tokens/sec is physically plausible:

```text
Architecture → Simulation → RTL → Physical estimation → Updated architecture → Simulation
```

```bash
conda run -n myenv python -m vse.cli asic --model transformer \
    --hidden-dim 128 --heads 4 --layers 2 --intermediate 256 \
    --sequence 16 --num-pes 256 --freq 5e9
```

```text
ASIC loop 256PE 5GHz: Step1 open (2027 MHz achievable, slack -293ps) → deepen pipeline → Step4 CLOSED (slack +7ps) in 4 iters
```

How the loop fixes an open design:

- **deepen the pipeline** — each pipeline register splits the critical
  path, so `achievable freq` rises; this is tried first (it preserves
  throughput) up to `--max-iters`.
- **slow the clock** — when pipelines are exhausted the requested
  frequency is dropped to 0.95× the achievable frequency.

Physical: gates×density→area (SRAM dominates), critical path (logic+wire)→freq, slack→closure.

Flags (subset): `--model`, `--freq` (requested clock, the loop must
close timing at it), `--pipeline` (starting depth), `--sram-gb`,
`--node-nm`, `--max-iters`, `--rtl` (print the full SystemVerilog),
`--json` (machine-readable report). The loop keeps the architecture
object that closed timing in `result.final_spec`.

---

## 3. Python API

```python
from vse.models.transformer import TransformerConfig, TransformerModel
from vse.workload import HardwareConfig, simulate_transformer
m=TransformerModel(TransformerConfig(4096,32,11008),8)
r=simulate_transformer(m,4096,HardwareConfig(4096,memory_bytes_per_cycle=1024))
print(r.total_cycles, r.tokens_per_second)  # + HardwareConfig(sram_model="physical", arch_family="cim", num_tiles=4)
```

`r`: `total_cycles/latency/tok/s`, `schedule` (trace/peak), `memory` (traffic/banks), `benchmark` (roofline), `power/area`, `physics` (gate checks when `--physics warn`).

---

## 4. Metrics — `cycles/tok/s`, `compute/memory_util`, `hbm/sram_bytes`, `Energy mJ/W/mm²` (leakage 50 mW/mm², thermal 1 W/mm²). See `vse:report`.

---

## 5. Findings

1. **Memory-bound** — KV 4.3G→237 tok/s, on-chip +11%; MoE 5.25G→24.5M vs 2.7M.
2. **Residency & buffering** — cold load dominates; double-buffer ~1%.
3. **Levers: HBM/SRAM/banks** — fusion 3.6×, precision 1:1.
4. **NoC 1 MB vs 5.6 GB**, energy 95% HBM, area 430 mm²/GiB, leakage 25 W/GiB.
5. **Physical BW** 1×1×32=4 vs 32×4×512=8192; mixed precision -44%, tiles shard but HBM limits; vector 3.7×/systolic 21×, CIM 8.8×.
6. **Co-search** — smallest model meeting accuracy wins; frontier is `tok/s` vs `area` vs `accuracy`, not just chips (see `codesign`).
7. **Gate closes the loop** — 14 checks (compute, SRAM BW/latency/banks, NoC BW/latency, wire, clock, power, leakage, thermal, area, capacity, timing) must all pass; `--physics warn` shows `✓/✗` and `PHYSICALLY PLAUSIBLE`, `fail` filters search/loop, JSON carries `physics:{plausible,checks}`.

---

## 6. Tests


```bash
conda run -n myenv python -m pytest tests/ -q
```