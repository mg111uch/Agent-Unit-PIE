# VSE — Virtual Silicon Engine

VSE (Virtual Silicon Engine) is a software simulator for designing and evaluating **dedicated AI inference silicon** before physical hardware exists.

The project starts as a lightweight Python architectural simulator and is intended to evolve toward a **cycle-accurate virtual accelerator**, FPGA prototype, RTL implementation, and eventually a custom ASIC design.

The long-term objective is to investigate whether a neural network can be **hard-wired into specialized silicon** so aggressively that conventional GPU limitations are removed and extremely high inference throughput becomes possible.

Target architectures may include extremely large sparse/MoE models such as:

```text
300B total parameters
30B active parameters/token
INT4 / FP4 / lower precision
Fixed model
Dedicated silicon
Extreme parallelism
```

The ultimate performance exploration target is not limited to conventional GPU speeds. VSE should allow investigation of architectures targeting:

```text
10K tok/s
100K tok/s
1M tok/s
10M tok/s
```

These are research targets, not claims of achievable performance.

---

# 1. Core Idea

A conventional LLM deployment looks approximately like:

```text
LLM
 ↓
CUDA / runtime
 ↓
GPU
 ↓
Memory
 ↓
Compute
```

VSE explores a different architecture:

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

The model is treated as part of the hardware architecture.

Instead of asking:

> "How fast can this model run on a GPU?"

VSE asks:

> "What hardware would be required to execute this fixed model as fast as physically possible?"

---

# 2. Current Status

VSE is currently an **MVP analytical/cycle-oriented simulator**.

Implemented components:

```text
vse/
├── core.py
├── memory.py
├── compute.py
├── ops.py
├── transformer.py
├── moe.py
├── benchmark.py
└── scheduler.py
```

The architecture is intentionally modular so individual components can later be replaced by more accurate hardware models.

---

# 3. Architecture

Current conceptual pipeline:

```text
                    ┌──────────────┐
                    │ Transformer  │
                    │    Model     │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │     MoE      │
                    │   Routing    │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │     Ops      │
                    │ Workload     │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  Scheduler   │
                    │ Cycle Model  │
                    └──────┬───────┘
                           │
                 ┌─────────┴─────────┐
                 ▼                   ▼
          ┌────────────┐      ┌────────────┐
          │  Compute   │      │   Memory   │
          │   Arrays   │      │   System   │
          └─────┬──────┘      └─────┬──────┘
                └──────────┬────────┘
                           ▼
                    ┌──────────────┐
                    │  Benchmark   │
                    └──────────────┘
```

---

# 4. Components

## `vse/core.py`

Provides the basic simulation infrastructure.

Responsibilities:

* Simulation state
* Virtual clock
* Component registration
* Basic simulation control
* Foundation for future cycle-accurate execution

Future improvements:

* Event queue
* Parallel events
* deterministic event ordering
* simulation checkpoints
* waveform generation
* hardware trace generation

---

## `vse/memory.py`

Models virtual memory systems.

The initial implementation provides the foundation for:

* Memory capacity
* Read bandwidth
* Write bandwidth
* Latency
* Outstanding operations

Future memory hierarchy:

```text
Registers
   ↓
PE-local SRAM
   ↓
Cluster SRAM
   ↓
Global SRAM
   ↓
HBM
   ↓
External memory
```

Future work:

* SRAM banks
* bank conflicts
* multicast
* broadcast
* cache behavior
* DMA
* prefetching
* double buffering
* memory compression
* weight streaming
* expert residency
* HBM channels
* memory controllers

---

# 5. `vse/compute.py`

Models virtual compute hardware.

Current abstraction:

```text
Processing Elements
        ↓
MAC operations
        ↓
cycles
```

Future architecture should support:

```text
INT2
INT4
INT8
FP4
FP8
BF16
custom fixed-point
binary operations
```

Future improvements:

* PE clusters
* vector units
* systolic arrays
* tensor arrays
* accumulator precision
* pipeline depth
* utilization
* sparsity
* structured sparsity
* fused operations
* activation units
* normalization units
* custom nonlinear units

---

# 6. `vse/ops.py`

Defines computational workload.

The purpose is to translate neural-network operations into hardware work.

Examples:

```text
Matrix multiplication
Attention
Softmax
RoPE
RMSNorm
MLP
MoE routing
Quantization
Dequantization
```

Future work should model:

* operation fusion
* quantized kernels
* sparse operations
* lookup operations
* activation functions
* communication operations
* tensor reshaping
* routing
* reductions

---

# 7. `vse/transformer.py`

Represents Transformer architecture.

It should eventually support configurable:

```text
Layers
Hidden dimension
Attention heads
KV heads
Context length
MLP dimension
RoPE
Normalization
Attention variants
MoE layers
Quantization
```

Future architectures:

```text
Dense Transformer
MoE Transformer
Hybrid Dense/MoE
Multi-head attention
Grouped-query attention
Multi-query attention
Sliding-window attention
Sparse attention
Custom attention
```

---

# 8. `vse/moe.py`

Models Mixture-of-Experts architectures.

The key distinction is:

```text
TOTAL PARAMETERS
        ≠
ACTIVE PARAMETERS
```

For example:

```text
300B total
30B active
```

Only a subset of experts is executed for each token.

The simulator tracks:

* Number of experts
* Top-K routing
* Expert parameters
* Active parameters
* Weight storage
* Expert token distribution
* Load imbalance
* Expert compute
* Router workload

Example:

```text
128 experts
Top-2 routing

Token
 ├── Expert 17
 └── Expert 92
```

Future improvements:

* Real router simulation
* Top-K selection cost
* capacity factors
* expert overflow
* expert parallelism
* expert replication
* expert locality
* expert caching
* expert-specific hardware
* NoC routing
* token dispatch
* token combine
* load balancing

---

# 9. `vse/benchmark.py`

Provides analytical performance estimation.

Current model considers:

```text
MACs
Memory traffic
Compute throughput
Memory bandwidth
Latency
Token/s
Arithmetic intensity
```

The benchmark can estimate whether a target such as:

```text
10,000 tok/s
1,000,000 tok/s
10,000,000 tok/s
```

is compatible with a proposed virtual architecture.

It also provides a basic roofline-style analysis.

---

# 10. `vse/scheduler.py`

The scheduler is the bridge between analytical modeling and actual virtual hardware simulation.

Current scheduler models:

* Tasks
* Dependencies
* Resources
* Start cycles
* End cycles
* Resource utilization
* Basic MoE execution graphs
* Transformer execution graphs

Example:

```text
Router
   │
   ├──── Expert 1
   ├──── Expert 5
   ├──── Expert 9
   └──── Expert 27
           │
           ▼
        Combine
```

Future versions should evolve this into a real cycle-level hardware scheduler.

---

# 11. Installation

Currently VSE is intended to be a lightweight Python project.

Example:

```bash
git clone <repository>
cd vse

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

Run tests:

```bash
pytest tests/
```

---

# 12. Example

A basic virtual compute architecture:

```python
from vse.scheduler import (
    Scheduler,
    Resource,
    ResourceType,
    Task,
)

scheduler = Scheduler(
    frequency_hz=1e9
)

scheduler.add_resource(
    Resource(
        name="compute",
        resource_type=ResourceType.COMPUTE,
        capacity=4096,
        throughput=1,
    )
)

scheduler.add_task(
    Task(
        task_id="matmul",
        name="Transformer MatMul",
        resource_type=ResourceType.COMPUTE,
        work=1_000_000_000,
    )
)

result = scheduler.schedule()

print(result.report())
```

---

# 13. Development Philosophy

VSE should follow one important principle:

> **Do not optimize the simulator for today's hardware. Optimize the simulator for discovering tomorrow's hardware.**

The simulator should therefore allow architectures that do not resemble GPUs.

Examples:

```text
Thousands → millions of tiny processing elements

Central memory
      ↓
Distributed memory

GPU-style kernels
      ↓
Static model-specific datapaths

General-purpose execution
      ↓
Compile-time scheduled execution

Dynamic software routing
      ↓
Dedicated hardware routing
```

---

# 14. Long-Term Architecture

The eventual VSE architecture should look more like:

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

# 15. Major Future Roadmap

## Phase 1 — MVP

Current phase.

### Goals

* [x] Basic simulator
* [x] Compute model
* [x] Memory model
* [x] Operation model
* [x] Transformer model
* [x] MoE model
* [x] Benchmark model
* [x] Basic scheduler
* [ ] End-to-end simulation
* [ ] CLI

---

# Phase 2 — Real Cycle-Level Simulator

Replace the simplified scheduler with an actual cycle engine.

Implement:

```text
Cycle 0
Cycle 1
Cycle 2
...
```

Each cycle should track:

```text
PE availability
Memory transactions
NoC transfers
DMA
Router activity
SRAM bank conflicts
Pipeline stages
```

Important improvement:

### True parallel execution

Currently the MVP scheduler is intentionally simplified.

Future scheduler:

```text
                Cycle
                  │
      ┌───────────┼───────────┐
      ▼           ▼           ▼
    PE 0         PE 1        PE 2
      │           │           │
      ▼           ▼           ▼
   Expert A    Expert B    Expert C
```

This is essential for realistic extreme-throughput estimates.

---

# Phase 3 — Hardware Memory Hierarchy

Implement:

```text
PE registers
↓
PE SRAM
↓
Cluster SRAM
↓
Global SRAM
↓
HBM
```

Add:

* bank conflicts
* bandwidth contention
* multicast
* broadcast
* DMA
* prefetch
* double buffering
* weight residency
* KV-cache
* activation movement

This phase is especially important because **memory movement may become the dominant limitation**, not compute.

---

# Phase 4 — Network-on-Chip

Build a virtual NoC.

Possible topologies:

```text
Mesh
Torus
Ring
Tree
Crossbar
Hierarchical mesh
Custom topology
```

Simulate:

```text
Router
Packet
Link
Bandwidth
Latency
Congestion
Deadlock
Multicast
Broadcast
```

For MoE:

```text
Token
  ↓
Router
  ↓
NoC
  ↓
Expert cluster
  ↓
NoC
  ↓
Combine
```

---

# Phase 5 — Model-Specific Hardware Compilation

Create:

```text
model → hardware graph
```

Instead of executing a generic Transformer, compile the exact model into a fixed execution graph.

Example:

```text
Layer 0
  ↓
Layer 1
  ↓
Layer 2
  ↓
Expert 7
Expert 19
  ↓
Layer 3
...
```

Compile-time decisions:

* PE allocation
* expert placement
* memory placement
* routing
* operation fusion
* pipeline scheduling
* precision
* data layout

---

# Phase 6 — Hardware Architecture Search

This is one of the most important future capabilities.

Automatically search:

```text
PE count
PE architecture
frequency
SRAM size
HBM bandwidth
NoC topology
expert replication
expert placement
pipeline depth
precision
batch size
```

Objective:

```text
maximize tokens/sec
```

subject to:

```text
area
power
memory
bandwidth
thermal limits
manufacturing constraints
```

Eventually:

```text
Architecture Search
        ↓
10,000 candidates
        ↓
VSE simulation
        ↓
Pareto frontier
        ↓
best architecture
```

---

# Phase 7 — Power and Area Modeling

Add:

```text
Area
Power
Energy/token
Thermal density
Memory power
NoC power
Compute power
```

The real objective becomes:

```text
tokens/sec
        /
power
```

rather than raw throughput alone.

Important metric:

```text
tokens / Joule
```

Also:

```text
tokens / mm²
```

and:

```text
tokens / Watt
```

---

# Phase 8 — FPGA Prototype

Once VSE produces a stable architecture:

```text
Python VSE
     ↓
Hardware specification
     ↓
RTL
     ↓
FPGA
```

The FPGA prototype should validate:

* scheduler assumptions
* datapath
* memory architecture
* routing
* quantization
* pipeline behavior

The FPGA does not need to implement the full giant model initially.

Start with:

```text
small model
small number of experts
small PE array
```

and scale the architecture conceptually.

---

# Phase 9 — RTL Generation

Introduce:

```text
VSE architecture
      ↓
RTL generator
      ↓
SystemVerilog
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

The goal is to make the virtual architecture sufficiently concrete that it can eventually become synthesizable hardware.

---

# Phase 10 — ASIC Exploration

Eventually connect VSE to ASIC tooling.

Potential flow:

```text
VSE
 ↓
RTL
 ↓
Synthesis
 ↓
Place & Route
 ↓
Area
Power
Timing
 ↓
Feed results back into VSE
```

This creates a powerful closed loop:

```text
Architecture
     ↓
Simulation
     ↓
RTL
     ↓
Physical estimation
     ↓
Updated architecture
     ↓
Simulation
```

---

# 16. Extreme Throughput Research

The project should explicitly investigate the physical requirements of extreme token rates.

For a target:

```text
T tokens/sec
```

and workload:

```text
M MACs/token
```

required compute is approximately:

```text
required MAC/s = T × M
```

For memory:

```text
required bandwidth =
tokens/sec × bytes/token
```

Therefore a 1M tok/s target should never be accepted merely because the virtual compute array appears large enough.

VSE must verify:

```text
Compute
Memory
NoC
SRAM
Router
Pipeline
Power
```

simultaneously.

---

# 17. Fixed-Model Silicon

One major research direction is **model-specific silicon**.

Instead of:

```text
General accelerator
       ↓
Any model
```

investigate:

```text
One fixed model
       ↓
Dedicated hardware
```

Potential optimizations:

```text
Remove unused operations
Remove unused precision
Hard-wire routing
Hard-wire expert placement
Fuse operations
Pre-place weights
Eliminate general instruction overhead
Static schedule
Dedicated datapaths
Dedicated activation functions
```

This could theoretically provide major efficiency improvements.

However, VSE must distinguish:

```text
algorithmic savings
```

from:

```text
actual physical silicon savings
```

and should never assume that hard-wiring a model automatically produces unlimited speed.

---

# 18. Important Missing Physics

Before trusting extreme throughput results, VSE must eventually model:

### Compute

* PE utilization
* pipeline bubbles
* accumulator dependencies
* precision conversion

### Memory

* SRAM bandwidth
* HBM bandwidth
* bank conflicts
* memory latency
* weight movement

### Communication

* NoC bandwidth
* routing congestion
* multicast
* synchronization

### Power

* switching activity
* memory energy
* NoC energy
* leakage
* thermal constraints

### Physical implementation

* wire delay
* clock distribution
* SRAM area
* routing congestion
* achievable frequency

Without these, a simulated:

```text
10M tok/s
```

should be treated as a **theoretical workload number**, not a physically achievable silicon result.

---

# 19. Testing Strategy

Every major component should have unit tests.

```text
tests/
├── test_core.py
├── test_memory.py
├── test_compute.py
├── test_ops.py
├── test_transformer.py
├── test_moe.py
├── test_benchmark.py
└── test_scheduler.py
```

Later:

```text
tests/
├── integration/
├── architecture/
├── performance/
└── regression/
```

Every architecture change should have regression benchmarks.

---

# 20. Recommended Next Files

After the current MVP files, development should proceed approximately in this order:

```text
1. vse/cli.py
2. vse/workload.py
3. vse/scheduler.py          ← improve substantially
4. vse/noc.py
5. vse/sram.py
6. vse/dma.py
7. vse/pipeline.py
8. vse/router.py
9. vse/compiler.py
10. vse/architecture.py
11. vse/power.py
12. vse/area.py
13. vse/search.py
14. vse/rtl.py
```

The most important immediate improvement is **not another model feature**.

It is making the scheduler genuinely parallel and cycle-accurate.

---

# 21. Final Vision

VSE should eventually become a research platform where the following question can be answered quantitatively:

> Given a fixed neural network, what is the fastest physically plausible silicon architecture for executing it?

The complete loop becomes:

```text
             ┌─────────────┐
             │ Fixed Model │
             └──────┬──────┘
                    ▼
             Model Compiler
                    │
                    ▼
             Hardware Graph
                    │
       ┌────────────┼────────────┐
       ▼            ▼            ▼
    Compute       Memory        NoC
       │            │            │
       └────────────┼────────────┘
                    ▼
              VSE Simulator
                    │
                    ▼
          Performance / Power
                    │
                    ▼
            Architecture Search
                    │
                    ▼
                  RTL
                    │
                    ▼
                  FPGA
                    │
                    ▼
                  ASIC
```

The ultimate goal is not simply to simulate an LLM.

**The goal is to build a virtual laboratory for discovering specialized AI silicon architectures.**
