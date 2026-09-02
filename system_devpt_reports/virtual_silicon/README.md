# VSE — Virtual Silicon Engine

VSE (Virtual Silicon Engine) is a software simulator for designing and evaluating **dedicated AI inference silicon** before physical hardware exists. It asks a deliberately different question from the rest of the industry:

> Not *"how fast can this model run on a GPU?"* — but *"what hardware would be required to execute this fixed model as fast as physically possible?"*

The model is treated as part of the hardware architecture. A fixed neural network is compiled into a dedicated execution graph, mapped onto a virtual chip (PE array, memory hierarchy, interconnect), and run on a cycle-level simulator to produce latency, throughput, utilization, and feasibility numbers.

Today VSE is a complete **MVP analytical/cycle-oriented simulator** covering every stage of the roadmap below. It is intentionally modular: analytical models can later be replaced by more accurate hardware models as the project evolves toward a cycle-accurate virtual accelerator, FPGA prototype, RTL, and eventually custom ASIC.

---

## Why VSE exists

General-purpose LLM inference on GPUs is bounded by the very generality that makes GPUs programmable. Instruction fetch, dynamic scheduling, kernel launch, and a memory system designed for arbitrary workloads all add overhead that a *fixed* model does not need.

VSE explores the opposite extreme: **model-specific silicon**. If the model never changes, its structure can be hard-wired — routing, expert placement, weights, precision, and the execution schedule are all known at compile time.

Target architectures may look like:

```text
300B total parameters       30B active parameters/token
INT4 / FP4 / lower precision   Fixed model
Dedicated silicon              Extreme parallelism
```

The performance exploration targets — deliberately beyond GPU speeds, and stated as **research targets, not claims**:

```text
10K tok/s
100K tok/s
1M tok/s
10M tok/s
```

A 1M+ tok/s number is never accepted just because the virtual compute array looks big enough. VSE verifies compute, memory, NoC, SRAM, router, pipeline, and (eventually) power simultaneously — see [roadmap.md](roadmap.md) for the physical limits still missing.

---

## Core idea

A conventional LLM deployment:

```text
LLM → CUDA/runtime → GPU → Memory → Compute
```

VSE's architecture:

```text
Fixed neural network
        ↓
Model-specific compiler
        ↓
Virtual hardware architecture
        ↓
Specialized datapaths
        ↓
On-chip SRAM / distributed memory
        ↓
NoC / routing
        ↓
Massively parallel execution
        ↓
Output tokens
```

---

## What VSE does today

One command compiles a model + hardware description into a fixed task graph and simulates it cycle-by-cycle:

```text
model → operation costs → compile-time plan → task graph → cycle schedule → benchmark report
```

**Capabilities (all implemented):**

- **Transformer & MoE modeling** — configurable dense Transformer (attention, gated MLP, KV-cache) and Mixture-of-Experts layers (top-k routing, per-expert compute and weights).
- **Cycle-level parallel engine** — tasks run concurrently on capacity units of the same resource, with dependencies, per-resource pipeline latency, a per-cycle activity trace, and peak-concurrency tracking.
- **Memory hierarchy** — SRAM/HBM levels with per-level bandwidth and banks; weight residency (HBM streaming vs DMA cold-load into banked SRAM), double-buffered weight streaming, KV-cache routing, and activation movement.
- **Network-on-Chip** — ring/mesh topologies with hop-distance routing, link-bandwidth contention, multicast/broadcast, congestion, and deadlock checks; full MoE `router → NoC → expert → NoC → combine` flow.
- **Model-specific compilation** — compiles the exact model + hardware into a fixed execution graph with an explicit, auditable `COMPILE PLAN`: precision, PE allocation, expert placement, memory placement, routing, pipeline depth, and operation fusion.
- **Architecture search** — explores a design space of candidate chips (PE count, SRAM, bandwidth, precision, NoC topology, pipeline depth, batch size, expert replication/placement, process node, …), ranks them by tokens/sec, and returns the Pareto frontier against real die area and power. Supports explicit grids and random sampling (`--sample`) for 10k-scale spaces.
- **Power & area estimation** — die area (PE + SRAM + NoC, mm²), dynamic energy/power plus static leakage from the simulated activity, and thermal-density (W/mm²) feasibility. Energy/token and tokens/Watt form the real design objective (`tokens/sec ÷ power`).
- **Analytical benchmarking** — MACs, memory traffic, arithmetic intensity, roofline compute/memory-bound analysis, and target tok/s feasibility checks.
- **FPGA prototype (pure-Python)** — turns a chip config into a concrete hardware specification (`vse/fpga/spec.py`), emits plain SystemVerilog RTL (`vse/fpga/rtl.py`), and validates the scheduler's assumptions on a small PE array with a cycle-accurate RTL simulator (`vse/fpga/sim.py` + `validate.py`) — scheduler, datapath, memory, routing, quantization, and pipeline — before any physical FPGA work.
- **Full RTL generation** — `vse/rtl.py` generates the complete synthesizable SystemVerilog for the architecture: PE arrays, SRAM controllers, NoC routers, DMA, expert dispatch, accumulators, and activation units.
- **ASIC physical estimation & closed loop** — `vse/asic/physical.py` estimates gates, die area, critical path, achievable frequency, and timing closure from the generated RTL; `vse/asic/loop.py` feeds those results back into the architecture (deepening pipelines / slowing clocks until timing closes), so reported tokens/sec are physically plausible.

---

## Current status

All roadmap stages are complete and working together:

- **End-to-end pipeline** — model → costs → task graph → cycle schedule → benchmark report.
- **Cycle-level parallel engine** — concurrent execution with pipeline latency, trace, and peak concurrency.
- **Memory hierarchy** — SRAM/HBM with bandwidth, banks, residency, and distributed tiles (`--num-tiles`).
- **Network-on-Chip** — ring/mesh, hop latency, link contention, and multicast/broadcast.
- **Model-specific compilation** — fixed graphs with auditable `COMPILE PLAN` including per-tensor precision.
- **Architecture search** — grid/random search over PEs, SRAM, bandwidth, precision, topology, etc., with Pareto frontier on real area/power.
- **Power, area and timing** — `~7 nm` estimates from activity (dynamic + leakage, thermal density) and RTL-based critical path.
- **Physics gate** — 14 checks (compute, SRAM BW/latency/banks, NoC, wire, clock, power, leakage, thermal, area, capacity, timing) with `--physics off/warn/fail`, `PHYSICALLY PLAUSIBLE` report and JSON `physics`.
- **FPGA prototype, RTL and ASIC loop** — pure-Python spec/RTL/sim/validation and closed-loop timing closure.

See `usage.md` for CLI, API and detailed findings.

### Implemented components

```text
vse/
├── workload.py, cli.py, cli_cmds/   end-to-end run, CLI and subcommands
├── core/          core, types, engine, compute, memory, memory_hierarchy, noc, tile
├── models/        ops, transformer, moe, vse_s1   cost models
├── graphs/        graph, graph_moe               task graphs
├── silicon/       process, area, power, sram     physical estimation
├── compiler/      compiler, precision            compilation
├── search/        architecture, search           design-space search
├── physics/       gate                           feasibility gate
├── report/        result, formatting             reporting
├── benchmark/     roofline, target               roofline analysis
├── fpga/          spec, rtl, sim, validate       FPGA prototype
├── rtl.py, asic/  physical, loop                RTL and ASIC loop
```

The architecture is intentionally modular so individual components can be replaced by more accurate models without disturbing the rest.

### Quick start

```bash
# 32-layer Transformer decode, 4096 context
python -m vse.cli transformer --hidden-dim 4096 --heads 32 \
    --layers 32 --intermediate 11008 --sequence 4096

# 128-expert MoE layer, 32 tokens
python -m vse.cli moe --hidden-dim 4096 --intermediate 14336 \
    --experts 128 --top-k 2 --tokens 32

# Validate an FPGA prototype on a small PE array
python -m vse.cli fpga --num-pes 8 --macs-per-pe 2 --pipeline 3 --rtl

# Generate full RTL + close the physical loop (timing closure)
python -m vse.cli asic --model transformer --hidden-dim 128 --heads 4 \
    --layers 2 --intermediate 256 --sequence 16 --num-pes 256 --freq 5e9 --rtl
```

See **[usage.md](usage.md)** for the full CLI reference, every flag, expected outputs and their meaning, and the Python API. **[roadmap.md](roadmap.md)** describes the remaining work ahead.

---

## Key findings so far

The full story is in [usage.md §5 — Findings](usage.md). The simulator keeps rediscovering the same lesson: moving data costs more than computing.

Transformer decode at 4096 context is KV-cache bound, and the MoE layer is weight-streaming bound — both are memory-bound rather than compute-bound. Keeping data on-chip is what actually moves throughput: on-chip KV adds ~11%, and fusing activations to stay on-chip gives the largest single gain at ~3.6×. Precision tracks memory traffic directly, so halving bits halves HBM bytes and latency. That same traffic dominates energy, while die area is dominated by SRAM — large on-chip residency is physically expensive. In practice, HBM bandwidth, SRAM capacity and banking matter far more than adding PEs. When bandwidth is modeled physically, unrealistic `TB/s` requests are exposed immediately — honest bandwidth must be built from banks, ports and access width.

See `usage.md §5` for the current quantitative findings.

---

## Architecture

Current conceptual pipeline:

```text
            ┌──────────────┐
            │ Transformer  │
            │    Model     │
            └──────┬───────┘
                   ▼
            ┌──────────────┐
            │     MoE      │
            │   Routing    │
            └──────┬───────┘
                   ▼
            ┌──────────────┐
            │     Ops      │
            │   Compiler   │   (compile-time plan)
            └──────┬───────┘
                   ▼
            ┌──────────────┐
            │  Scheduler   │
            │ Cycle Engine │
            └──────┬───────┘
         ┌──────────┴──────────┐
         ▼                     ▼
   ┌────────────┐        ┌────────────┐
   │  Compute   │        │   Memory   │
   │   Arrays   │        │   System   │
   └─────┬──────┘        └─────┬──────┘
         └──────────┬──────────┘
                    ▼
            ┌──────────────┐
            │  Benchmark   │
            │  Report      │
            └──────────────┘
```

### Components at a glance

- **`vse/core/`** — clock, scheduler, compute array, memory hierarchy and NoC.
- **`vse/models/`** — Transformer, MoE and VSE-S1 cost models.
- **`vse/graphs/`, `vse/compiler/`** — task graphs and model-specific compilation with auditable plan.
- **`vse/silicon/`, `vse/physics/`** — process, area, power and physical feasibility.
- **`vse/search/`** — architecture space and Pareto search.
- **`vse/workload.py`, `vse/report/`, `vse/benchmark/`** — orchestration, reporting and roofline.
- **`vse/cli.py`, `vse/fpga/`, `vse/rtl.py`, `vse/asic/`** — CLI, FPGA validation, RTL and ASIC loop.

---

## Long-term architecture

The eventual VSE pipeline:

```text
                   MODEL
                     │
                     ▼
             Model Compiler
                     │
                     ▼
             Execution Graph
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
   Compute Graph             Memory Graph
        │                         │
        └────────────┬────────────┘
                     ▼
                  NoC Graph
                     │
                     ▼
              Virtual Silicon
                     │
                     ▼
              Cycle Simulator
                     │
                     ▼
              Performance Data
                     │
                     ▼
            Architecture Search
```

---

## Development philosophy

> **Do not optimize the simulator for today's hardware. Optimize the simulator for discovering tomorrow's hardware.**

The simulator must therefore allow architectures that do not resemble GPUs:

```text
Thousands → millions of tiny processing elements
Central memory          → distributed memory
GPU-style kernels       → static model-specific datapaths
General-purpose exec    → compile-time scheduled execution
Dynamic software routing → dedicated hardware routing
```

VSE must also be disciplined about claims: it distinguishes **algorithmic savings** from **actual physical silicon savings**, and treats any simulated `10M tok/s` as a theoretical workload number until power, area, and physical-implied constraints are modeled (see `roadmap.md`).

---

## Installation

```bash
git clone <repository>
cd codebase/modules/virtual_silicon

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the tests:

```bash
pytest tests/
```

---

## Documentation map

- **`README.md`** (this file) — project vision, what VSE does, current status.
- **[`usage.md`](usage.md)** — how to run the CLI, expected results and what they mean, flags, Python API, and summary findings.
- **[`Findings.md`](Findings.md)** — detailed quantitative findings and implementation status (external agent can understand project from this file alone, <500 lines).
- **[`IssuesFix.md`](IssuesFix.md)** — unified remaining plan (was `IMPLEMENTATION_PLAN.md` + strategic report; `IMPLEMENTATION_PLAN.md` removed).
- **[`roadmap.md`](roadmap.md)** — the work that remains: HDL toolchain integration, PE architecture space, data layout, distributed memory, cycle-accurate modeling, packaging, and more.

---

## Final vision

> Given a fixed neural network, what is the fastest physically plausible silicon architecture for executing it?

VSE's goal is to become a virtual laboratory for discovering specialized AI silicon — not simply to simulate an LLM, but to close the loop from fixed model → compiled hardware → cycle simulation → architecture search → physical estimation → back to simulation.
