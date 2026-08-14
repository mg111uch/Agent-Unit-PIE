# VSE — Future Roadmap

Work still ahead. Everything already built — the end-to-end simulator,
cycle engine, memory hierarchy, network-on-chip, model-specific
compilation, architecture search, power/area modeling, FPGA prototyping,
RTL generation, and ASIC physical exploration — is documented in
[README.md](README.md) and [usage.md](usage.md). This file only describes
what is left to do.

---

## Near-term future phases

### Phase 11 — Real HDL toolchain integration

The generated SystemVerilog is plain and toolchain-ready, but nothing has
synthesized it yet. Wire the RTL into real open-source tools to confirm it
is correct and calibrate the physical estimates:

```text
Verilator / Icarus    — lint + cycle simulation of the emitted RTL
Yosys                 — logic synthesis into a standard-cell / FPGA netlist
OpenROAD / OpenLane   — place-and-route with realistic PDK timing/area
```

Goals:
- prove the RTL is lint-clean and synthesizes as-is;
- feed measured synthesis area/timing back into the physical estimator
  (currently analytical) to close the accuracy gap;
- add a `--toolchain` mode to the CLI that drives an external flow and
  imports its results.

No toolchain is installed today; this phase is optional and
environment-dependent.

---

### Phase 12 — PE architecture space

The compute array models uniform scalar PEs (`num_pes × macs_per_pe`).
Explore the PE design space so throughput, area, and timing trade-offs are
first-class search dimensions:

```text
SIMD width             — multiple lanes per PE
vector PEs             — per-PE vector datapaths
systolic variants      — register-level dataflow
multi-level pipelines  — deeper per-MAC pipelining
dataflow               — weight-stationary vs output-stationary
```

Each variant changes MAC density, gate count, and critical path — the
search and the physical estimator must model the difference.

---

### Phase 13 — Data layout & tiling

Add compile-time data layout so memory traffic drops:

```text
blocked layout / tiling — keep tiles resident, minimize re-fetch
layout-aware scheduling — order tasks by physical data placement
weight-stationary tiles — feed arrays without re-streaming weights
```

---

### Phase 14 — Additional NoC topologies

Only if the topology becomes a limiting factor:

```text
torus                  — short average hop distance
tree / fat-tree        — broadcast-friendly expert routing
crossbar               — low latency at small scale
```

Include topology-aware routing and expert placement in the search.

---

### Phase 15 — Distributed memory

Give each NoC node its own HBM/SRAM bandwidth so expert replication and
NoC locality actually pay off (expert replication is currently
bandwidth-neutral because all nodes share one HBM port):

```text
per-node bandwidth     — bandwidth scales with the node count
expert-aware placement — co-locate an expert's weights with its compute
multi-die SRAM         — distributed on-chip capacity and banks
```

---

## Further-out future phases

### Phase 16 — Cycle-accurate simulation

Replace the analytical models with cycle-accurate datapath, memory, and
NoC models, validated against the RTL simulator:

```text
analytical schedule  →  cycle-accurate pipeline model
analytical memory    →  bank / conflict / latency cycle model
analytical NoC       →  flit-level routing model
```

The RTL simulator is the reference for equivalence checks, keeping the
fast analytical path for search and the slow accurate path for
verification.

---

### Phase 17 — Advanced packaging & multi-chip

Extend the physical model beyond a single die:

```text
2.5D / 3D stacking     — die-to-die bandwidth, thermal coupling
chiplets / multi-die   — interposer routing, per-die power budgets
HBM stacks             — realistic DRAM bandwidth/capacity per package
```

---

### Phase 18 — General model frontend

Beyond the hand-built Transformer/MoE cost models, accept arbitrary fixed
networks via a standard intermediate representation (ONNX or a small graph
IR) so VSE can compile and simulate any model, not just the built-ins.

---

### Phase 19 — Physical-aware co-optimization

Search precision, layout, pipeline, floorplan, and physical implementation
jointly — one closed loop instead of sequential passes — so the reported
tokens/sec is always timing-closed at the physical level.

---

### Phase 20 — Validation against real silicon

Calibrate the power/area/timing estimators against measured results from a
real tape-out or a commercial PDK library, and keep a regression set of
known-good workloads so model changes never silently break the numbers.

---

## Research directions

### Extreme-throughput physics

For a target `T` tokens/sec and a workload of `M` MACs/token:

```text
required compute  = T × M            (MAC/s)
required bandwidth = T × bytes/token (bytes/s)
```

Therefore a 1M tok/s target should never be accepted merely because the
virtual compute array appears large enough. VSE must verify compute,
memory, NoC, SRAM, router, pipeline, and power **simultaneously**.

### Fixed-model silicon

The core research direction: instead of a general accelerator that runs
any model, investigate one fixed model on dedicated hardware. Potential
optimizations:

```text
remove unused operations
remove unused precision
hard-wire routing
hard-wire expert placement
fuse operations
pre-place weights
eliminate general instruction overhead
static schedule
dedicated datapaths
```

VSE must distinguish **algorithmic savings** from **actual physical
silicon savings**, and never assume that hard-wiring a model automatically
produces unlimited speed.

### Important missing physics

Before trusting extreme-throughput results, VSE must model:

- **Compute** — PE utilization, pipeline bubbles, accumulator
  dependencies, precision conversion.
- **Memory** — SRAM/HBM bandwidth, bank conflicts, latency, weight
  movement.
- **Communication** — NoC bandwidth, routing congestion, synchronization.
- **Power** — switching activity, memory/NoC energy, leakage, thermal
  constraints.
- **Physical implementation** — wire delay, clock distribution, SRAM area,
  achievable frequency.

Without these, a simulated `10M tok/s` is a **theoretical workload
number**, not a physically achievable silicon result.

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

## Recommended next files

Development should proceed approximately in this order (remaining work):

```text
1. Phase 11      ← drive the generated RTL through Verilator/Icarus + Yosys
2. Phase 12      ← PE SIMD/vector dimension in the search space
3. Phase 13      ← data layout & tiling
4. Phase 15      ← per-node distributed memory
5. Phase 16      ← cycle-accurate models against the RTL simulator
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
