"""
VSE - Virtual Silicon Engine
vse/fpga/

Phase 8: FPGA prototype toolchain (pure-Python, no HDL simulator needed).

    Python VSE → FPGASpec (hardware specification) → SystemVerilog RTL
    → cycle-accurate RTL simulation → validation report

The RTL simulator validates the assumptions the VSE scheduler relies on
(scheduler, datapath, memory, routing, quantization, pipeline) on a
small model / small PE array before any physical FPGA work begins.
"""
