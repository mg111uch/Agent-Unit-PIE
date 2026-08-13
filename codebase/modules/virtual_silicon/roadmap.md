# VSE — Future Roadmap

Work still ahead. The completed stages of the project (simulator core,
cycle engine, memory hierarchy, interconnect, model-specific compilation,
architecture search, and power/area modeling) are covered in
[README.md](README.md) and [usage.md](usage.md) — this file only
describes what is left to do.

---

## Phase 6 — Hardware Architecture Search

**Implemented and documented** — declarative candidate chips
(`ArchitectureSpec`), grid + random search (`SearchSpace`, `run_search`,
`run_random_search`), and a Pareto frontier on real die area and power.
The search dimensions, the objective (`tokens/sec ÷ power`), the
constraints, and the CLI/API are covered in [README.md](README.md) and
[usage.md](usage.md) (§2.7, §3.3).

Remaining in this phase:

```text
PE architecture           — (e.g. SIMD width, vector PE variants)
data layout               — (blocked-layout / tiling, compile-time)
additional NoC topologies — (torus, tree, crossbar; only if topology
                             becomes a limiting factor)
distributed memory        — (per-node HBM/SRAM bandwidth so expert
                             replication and NoC locality pay off)
```

---

## Phase 7 — Power and Area Modeling

**Implemented and documented** — die area (mm²), dynamic + static
energy/power, thermal density (W/mm² vs cooling budget), and process-node
scaling (`ProcessTechnology.for_node`). The metrics (energy/token,
tokens/Watt, tokens/Joule, tokens/mm²), the `ENERGY & POWER` / `AREA`
report sections, and the search frontier on real power/area are covered
in [README.md](README.md) and [usage.md](usage.md) (§4.1). Nothing
remaining in this phase.

---

## Phase 8 — FPGA Prototype

Once VSE produces a stable architecture:

```text
Python VSE → Hardware specification → RTL → FPGA
```

The FPGA prototype should validate:

```text
scheduler assumptions
datapath
memory architecture
routing
quantization
pipeline behavior
```

The FPGA does not need to implement the full giant model initially. Start
with a small model, small number of experts, and a small PE array, and
scale the architecture conceptually.

---

## Phase 9 — RTL Generation

```text
VSE architecture → RTL generator → SystemVerilog
```

Generate:

```text
PE arrays
SRAM controllers
NoC routers
DMA
expert dispatch
accumulators
activation units
```

The goal is to make the virtual architecture sufficiently concrete that it
can eventually become synthesizable hardware.

---

## Phase 10 — ASIC Exploration

```text
VSE → RTL → Synthesis → Place & Route → Area / Power / Timing
```

Feed results back into VSE, closing the loop:

```text
Architecture → Simulation → RTL → Physical estimation → Updated architecture → Simulation
```

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
1. Phase 6 leftovers   ← PE architecture dim, torus/tree/crossbar NoC
2. Phase 8 (toolchain) ← RTL codegen + Verilator/Icarus sim; confirm
                          before installing heavy toolchains
3. Phase 9            ← vse/rtl.py
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
