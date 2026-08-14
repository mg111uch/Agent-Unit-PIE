"""
VSE - Virtual Silicon Engine
vse/asic/

Phase 10: ASIC exploration (pure-Python, no synthesis toolchain).

    VSE → RTL → Synthesis → Place & Route → Area / Power / Timing

The `physical` model estimates the physical cost of the generated RTL
(gates, die area, critical path, achievable frequency, timing closure).
The `loop` module feeds those results back into the architecture,
closing the loop:

    Architecture → Simulation → RTL → Physical estimation
    → Updated architecture → Simulation
"""
