# VSE — Virtual Silicon Engine

VSE (Virtual Silicon Engine) is a software simulator for designing and evaluating **dedicated AI inference silicon** before physical hardware exists. It asks a deliberately different question from the rest of the industry:

> Not *"how fast can this model run on a GPU?"* — but *"what hardware would be required to execute this fixed model as fast as physically possible?"*

The model is treated as part of the hardware architecture. A fixed neural network is compiled into a dedicated execution graph, mapped onto a virtual chip (PE array, memory hierarchy, interconnect), and run on a cycle-level simulator to produce latency, throughput, utilization, and feasibility numbers.

Today VSE is a complete **MVP analytical/cycle-oriented simulator** covering the first five roadmap phases (below). It is intentionally modular: analytical models can later be replaced by more accurate hardware models as the project evolves toward a cycle-accurate virtual accelerator, FPGA prototype, RTL, and eventually custom ASIC.

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

**Capabilities (Phases 1–5, all implemented):**

- **Transformer & MoE modeling** — configurable dense Transformer (attention, gated MLP, KV-cache) and Mixture-of-Experts layers (top-k routing, per-expert compute and weights).
- **Cycle-level parallel engine** — tasks run concurrently on capacity units of the same resource, with dependencies, per-resource pipeline latency, a per-cycle activity trace, and peak-concurrency tracking.
- **Memory hierarchy** — SRAM/HBM levels with per-level bandwidth and banks; weight residency (HBM streaming vs DMA cold-load into banked SRAM), double-buffered weight streaming, KV-cache routing, and activation movement.
- **Network-on-Chip** — ring/mesh topologies with hop-distance routing, link-bandwidth contention, multicast/broadcast, congestion, and deadlock checks; full MoE `router → NoC → expert → NoC → combine` flow.
- **Model-specific compilation** — compiles the exact model + hardware into a fixed execution graph with an explicit, auditable `COMPILE PLAN`: precision, PE allocation, expert placement, memory placement, routing, pipeline depth, and operation fusion.
- **Architecture search** — explores a design space of candidate chips (PE count, SRAM, bandwidth, precision, NoC topology, pipeline depth, batch size, expert replication/placement, process node, …), ranks them by tokens/sec, and returns the Pareto frontier against real die area and power. Supports explicit grids and random sampling (`--sample`) for 10k-scale spaces.
- **Power & area estimation** — die area (PE + SRAM + NoC, mm²), dynamic energy/power plus static leakage from the simulated activity, and thermal-density (W/mm²) feasibility. Energy/token and tokens/Watt form the real design objective (`tokens/sec ÷ power`).
- **Analytical benchmarking** — MACs, memory traffic, arithmetic intensity, roofline compute/memory-bound analysis, and target tok/s feasibility checks.

---

## Current status

Phases 1–5 of the roadmap are complete and working together. Each added a layer of fidelity to the same end-to-end pipeline:

- **Phase 1 — end-to-end pipeline.** Model → operation costs → scheduler task graph → cycle schedule → benchmark report (`vse/models/*`, `vse/graphs/graph.py`, `vse/workload.py`, `vse/cli.py`).
- **Phase 2 — cycle-level parallel engine.** True parallel execution on capacity units, dependencies, pipeline latency, per-cycle trace, peak concurrency (`vse/core/engine.py`).
- **Phase 3 — memory hierarchy.** SRAM/HBM levels, bandwidth contention, bank conflicts, weight residency, KV-cache routing, activation movement, DMA, double buffering (`vse/core/memory_hierarchy.py`).
- **Phase 4 — Network-on-Chip.** Ring/mesh topologies, hop-distance routing, link bandwidth, multicast/broadcast, congestion, deadlock (`vse/core/noc.py`).
- **Phase 5 — model-specific hardware compilation.** Fixed execution graphs with an explicit compile plan: precision, PE allocation, expert placement, memory placement, routing, fusion (`vse/compiler/compiler.py`).
- **Phase 6 — hardware architecture search.** Declarative candidate chips (`vse/search/architecture.py`) that compile and simulate through the existing pipeline, with an explicit `SearchSpace` grid plus random sampling (`vse/search/search.py`) and a Pareto frontier on **real** die area and power (not a proxy). Search dimensions: PE count, frequency, SRAM size, HBM/SRAM bandwidth, banks, precision (weight/activation/kv bits), fusion, NoC topology (ring/mesh), pipeline depth, double buffering, batch size, expert replication/placement (round-robin/contiguous), and process node (`node_nm`). Objective: **maximize tokens/sec ÷ power** subject to die area, power, memory, bandwidth, and thermal limits (W/mm²). CLI `vse search` supports `--dim NAME=V1,V2,...` and `--sample N` (random, with `--seed`) for 10,000-candidate searches.
- **Phase 7 — power and area.** Die-area (PE + SRAM + NoC, mm²) and energy/power models from `ProcessTechnology` constants (default ~7 nm): dynamic energy (compute/memory/NoC per bit), static/leakage (`leakage_density_mw_per_mm²` — dominates on large SRAMs), average power from the simulated schedule, thermal-density feasibility, energy/token, and tokens/Watt. Node scaling via `ProcessTechnology.for_node` (energy ∝ node, area ∝ node²). Metrics (`tokens/Joule`, `tokens/mm²`) and the `ENERGY & POWER` / `AREA` report sections are detailed in `usage.md §4.1`; the search frontier ranks on these real estimates.

### Implemented components

```text
vse/
├── scheduler.py         public scheduler facade
├── workload.py          end-to-end simulation entry points
├── cli.py               command-line interface (transformer / moe)
├── cli_args.py          shared hardware CLI argument declarations
├── cli_search.py        command-line interface (search subcommand)
├── core/                simulation primitives + hardware resources
│   ├── core.py          virtual clock, components
│   ├── types.py         shared datatypes (Task, Resource, ScheduleResult)
│   ├── engine.py        parallel cycle engine (Phase 2)
│   ├── builders.py      scheduler task-graph helpers
│   ├── compute.py       compute-array model (PEs, MACs/cycle)
│   ├── memory.py        baseline memory model (benchmark support)
│   ├── memory_hierarchy.py SRAM/HBM levels, banks, residency (Phase 3)
│   └── noc.py           interconnect: ring/mesh, multicast, congestion (Phase 4)
├── models/              workload cost models
│   ├── ops.py           operation cost models (matmul, attention, routing…)
│   ├── transformer.py   Transformer cost model
│   └── moe.py           MoE cost model (experts, top-k)
├── graphs/              task-graph construction
│   ├── graph.py         task-graph builders + fusion transform
│   └── graph_moe.py     MoE graph builder (replication/placement)
├── silicon/             physical estimation (Phase 7)
│   ├── process.py       process technology constants (~7 nm)
│   ├── area.py          die-area estimation, mm²
│   └── power.py         energy/power estimation
├── compiler/            model-specific compilation (Phase 5)
│   └── compiler.py
├── search/              architecture search (Phase 6)
│   ├── architecture.py  candidate chip descriptions + search space
│   └── search.py        architecture search + Pareto frontier
├── report/
│   ├── result.py        EndToEndResult
│   └── formatting.py    report / trace formatting
└── benchmark/           analytical roofline estimates + target checks
    └── benchmark.py
```

The architecture is intentionally modular so individual components can later be replaced by more accurate hardware models without disturbing the rest.

### Quick start

```bash
# 32-layer Transformer decode, 4096 context
python -m vse.cli transformer --hidden-dim 4096 --heads 32 \
    --layers 32 --intermediate 11008 --sequence 4096

# 128-expert MoE layer, 32 tokens
python -m vse.cli moe --hidden-dim 4096 --intermediate 14336 \
    --experts 128 --top-k 2 --tokens 32
```

See **[usage.md](usage.md)** for the full CLI reference, every flag, expected outputs and their meaning, and the Python API. **[roadmap.md](roadmap.md)** describes the future phases (architecture search, power/area, FPGA, RTL, ASIC).

---

## Key findings so far

The full write-up lives in [usage.md §5 — Findings](usage.md). In short:

- **Memory movement, not compute, is the dominant limitation.** Both flagship workloads are memory-bound on a 4096-PE chip at 256 B/cycle.
- **Transformer decode is KV-cache-bound** (~237 tok/s on-HBM); on-chip KV raises it ~11% — long-context inference demands large SRAM.
- **MoE sparsity hides a weight-streaming cost**: 64 experts × top-2 × 32 tokens stream 5.25 GiB of weights → ~24.5M cycles.
- **Fusion is the strongest single optimization**: keeping activations on-chip cuts the 8-layer decode 4.2M → 1.16M cycles (~3.6×).
- **Precision is a first-class lever**: doubling weight bits doubles HBM traffic and latency 1:1.
- **Energy follows memory traffic**: HBM streaming dominates dynamic energy (~95%+) on weight-streamed workloads, so energy/token improves with the same residency/precision levers as latency.
- **Area is an SRAM problem**: 1 GiB of SRAM (~430 mm²) dwarfs the PE array — a real constraint on how much KV/weight residency a die can afford.
- **The levers that matter**: HBM bandwidth, SRAM capacity, banks — not PE count.

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
            │   Compiler   │   (Phase 5: compile-time plan)
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

- **`vse/core/`** — simulation primitives and hardware resources:
  - **`core.py` / `types.py` / `scheduler.py`** — simulation primitives, shared datatypes, and the public scheduling facade.
  - **`engine.py`** — the Phase-2 cycle engine: greedy per-cycle dispatch, dependency gating on result-ready cycles, resource capacity units, pipeline latency, activity trace, peak concurrency, cycle detection.
  - **`compute.py` / `memory.py` / `memory_hierarchy.py`** — compute-array, baseline memory, and per-level (SRAM/HBM) read/write resources with bandwidth and bank counts; weight residency decisions; per-level traffic reporting.
  - **`noc.py`** — hop-distance routing for ring/mesh, point-to-point/multicast/broadcast transfers, link contention, congestion metrics, deadlock check.
- **`vse/models/`** — analytical cost models: **`ops.py`** (MACs, bytes by precision), **`transformer.py`**, **`moe.py`** (KV-cache traffic, expert token distribution).
- **`vse/graphs/`** — task-graph builders for Transformer and MoE, including the NoC flow, expert replication/placement, and the fusion transform.
- **`vse/compiler/compiler.py`** — model-specific compilation: precision overrides, PE/expert placement, memory plan, fusion, and the `COMPILE PLAN`.
- **`vse/silicon/`** — Phase-7 physical estimation: **`process.py`** technology constants, **`area.py`** die-area, **`power.py`** energy/power.
- **`vse/search/`** — Phase-6 architecture search: **`architecture.py`** candidate chips, **`search.py`** grid/random search + Pareto frontier.
- **`vse/workload.py` / `vse/report/`** — end-to-end orchestration, result datatypes (`result.py`), and text/JSON report rendering (`formatting.py`).
- **`vse/cli.py`** — the command-line interface (see `usage.md`).

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
- **[`usage.md`](usage.md)** — how to run the CLI, expected results and what they mean, flags, Python API, and findings.
- **[`roadmap.md`](roadmap.md)** — remaining work: Phase 6 architecture search through Phase 10 ASIC exploration.

---

## Final vision

> Given a fixed neural network, what is the fastest physically plausible silicon architecture for executing it?

VSE's goal is to become a virtual laboratory for discovering specialized AI silicon — not simply to simulate an LLM, but to close the loop from fixed model → compiled hardware → cycle simulation → architecture search → physical estimation → back to simulation.
