"""
Phase 5 tests: model-specific hardware compilation.
"""

import pytest

from vse.compiler.compiler import (
    CompileOptions,
    compile_moe,
    compile_transformer,
    execute,
)
from vse.models.moe import MoE, MoEConfig
from vse.models.transformer import (
    TransformerConfig,
    TransformerModel,
)
from vse.workload import HardwareConfig


def make_moe():
    return MoE(
        MoEConfig(
            hidden_dim=1024,
            intermediate_dim=2048,
            num_experts=8,
            top_k=2,
        )
    )


def make_transformer():
    return TransformerModel(
        TransformerConfig(
            hidden_dim=512,
            num_heads=8,
            intermediate_dim=2048,
        ),
        num_layers=4,
    )


def test_compile_moe_plan_records_decisions():
    program = compile_moe(
        make_moe(),
        tokens=8,
        config=HardwareConfig(num_pes=512),
    )

    assert program.name == "moe"
    assert program.plan["precision"]["weight_bits"] == 4
    assert program.plan["fusion"]["enabled"] is True
    assert program.plan["pe_allocation"]["expert_pes"] == 64


def test_compile_moe_fusion_removes_act_writes():
    fused = compile_moe(
        make_moe(),
        tokens=8,
        config=HardwareConfig(num_pes=512),
        options=CompileOptions(fusion=True),
    )

    unfused = compile_moe(
        make_moe(),
        tokens=8,
        config=HardwareConfig(num_pes=512),
        options=CompileOptions(fusion=False),
    )

    fused_writes = [
        t for t in fused.tasks
        if t.task_id.endswith("_act_write")
    ]
    unfused_writes = [
        t for t in unfused.tasks
        if t.task_id.endswith("_act_write")
    ]

    assert len(unfused_writes) == 8
    assert fused_writes == []


def test_compile_moe_precision_scales_weight_bytes():
    base = compile_moe(
        make_moe(),
        tokens=8,
        config=HardwareConfig(num_pes=512),
    )

    wide = compile_moe(
        make_moe(),
        tokens=8,
        config=HardwareConfig(num_pes=512),
        options=CompileOptions(weight_bits=8),
    )

    assert wide.plan["precision"]["weight_bits"] == 8
    assert wide.weight_bytes == 2 * base.weight_bytes


def test_compile_moe_noc_placement():
    program = compile_moe(
        make_moe(),
        tokens=8,
        config=HardwareConfig(num_pes=512, noc_nodes=16),
    )

    placement = program.plan["expert_placement"]
    assert placement["nodes"] == 16
    assert program.plan["routing"]["transfers"] == 16


def test_compile_transformer_plan():
    program = compile_transformer(
        make_transformer(),
        sequence_length=128,
        config=HardwareConfig(num_pes=1024),
    )

    assert program.name == "transformer"
    assert program.plan["precision"]["kv_bits"] == 16
    assert program.plan["memory_placement"]["kv"] in (
        "sram",
        "hbm",
    )
    assert program.plan["pipeline"]["layers"] == 4


def test_compile_transformer_fusion_removes_intermediate_round_trips():
    fused = compile_transformer(
        make_transformer(),
        sequence_length=128,
        config=HardwareConfig(num_pes=1024),
        options=CompileOptions(fusion=True),
    )

    unfused = compile_transformer(
        make_transformer(),
        sequence_length=128,
        config=HardwareConfig(num_pes=1024),
        options=CompileOptions(fusion=False),
    )

    read_kinds = lambda tasks: sum(
        1 for t in tasks if t.metadata.get("kind") == "read"
    )
    write_kinds = lambda tasks: sum(
        1 for t in tasks if t.metadata.get("kind") == "write"
    )

    assert read_kinds(unfused.tasks) == 8
    assert read_kinds(fused.tasks) == 1
    assert write_kinds(unfused.tasks) == 8
    assert write_kinds(fused.tasks) == 1


def test_execute_moe_returns_plan_in_result():
    program = compile_moe(
        make_moe(),
        tokens=8,
        config=HardwareConfig(num_pes=512),
    )

    result = execute(program)

    assert result.total_cycles > 0
    assert result.plan == program.plan


def test_execute_transformer_returns_plan_in_result():
    program = compile_transformer(
        make_transformer(),
        sequence_length=128,
        config=HardwareConfig(num_pes=1024),
    )

    result = execute(program)

    assert result.total_cycles > 0
    assert result.name == "transformer"
    assert result.plan["fusion"]["enabled"] is True


def test_execute_fusion_speeds_up_transformer():
    config = HardwareConfig(num_pes=1024)

    fused = execute(
        compile_transformer(
            make_transformer(),
            sequence_length=128,
            config=config,
            options=CompileOptions(fusion=True),
        )
    )

    unfused = execute(
        compile_transformer(
            make_transformer(),
            sequence_length=128,
            config=config,
            options=CompileOptions(fusion=False),
        )
    )

    assert fused.total_cycles < unfused.total_cycles


def test_execute_kv_bits_reduces_traffic():
    config = HardwareConfig(num_pes=1024)

    base = execute(
        compile_transformer(
            make_transformer(),
            sequence_length=128,
            config=config,
        )
    )

    low = execute(
        compile_transformer(
            make_transformer(),
            sequence_length=128,
            config=config,
            options=CompileOptions(kv_bits=8),
        )
    )

    assert low.plan["precision"]["kv_bits"] == 8
    assert low.total_cycles < base.total_cycles


def test_compile_options_validates_placement():
    with pytest.raises(ValueError):
        CompileOptions(expert_placement="bogus")


def test_compile_options_validates_replicas():
    with pytest.raises(ValueError):
        CompileOptions(replicas=0)


def test_compile_moe_replication_splits_work_and_weights():
    base = compile_moe(
        make_moe(),
        tokens=8,
        config=HardwareConfig(num_pes=512),
    )

    replicated = compile_moe(
        make_moe(),
        tokens=8,
        config=HardwareConfig(num_pes=512),
        options=CompileOptions(replicas=2),
    )

    base_compute_work = sum(
        t.work
        for t in base.tasks
        if t.resource_type.name == "compute"
    )
    repl_compute_work = sum(
        t.work
        for t in replicated.tasks
        if t.resource_type.name == "compute"
    )

    # Total MACs are unchanged by replication.
    assert repl_compute_work == base_compute_work

    base_expert_ids = {
        t.task_id
        for t in base.tasks
        if t.task_id.startswith("expert_0_")
    }
    repl_expert_ids = {
        t.task_id
        for t in replicated.tasks
        if t.task_id.startswith("expert_0_")
    }

    # Expert 0 now has two replicas.
    assert any("_r0_" in tid for tid in repl_expert_ids)
    assert any("_r1_" in tid for tid in repl_expert_ids)
    assert not any("_r1_" in tid for tid in base_expert_ids)

    assert replicated.plan["expert_placement"]["replicas"] == 2
    assert replicated.plan["pe_allocation"]["expert_pes"] == 32


def test_compile_moe_replication_halves_weight_stream_per_replica():
    config = HardwareConfig(num_pes=512, noc_nodes=16)

    base = compile_moe(
        make_moe(),
        tokens=8,
        config=config,
        options=CompileOptions(replicas=1),
    )

    replicated = compile_moe(
        make_moe(),
        tokens=8,
        config=config,
        options=CompileOptions(replicas=2),
    )

    def weight_bytes(program):
        return sum(
            t.work
            for t in program.tasks
            if t.task_id.endswith("_wchunk_0")
        )

    # Total weight traffic is unchanged (replicas split, not duplicate).
    assert weight_bytes(replicated) == weight_bytes(base)

    # Each replica streams half the weights per chunk.
    base_max_chunk = max(
        t.work for t in base.tasks if "_wchunk_" in t.task_id
    )
    repl_max_chunk = max(
        t.work
        for t in replicated.tasks
        if "_wchunk_" in t.task_id
    )
    assert repl_max_chunk == base_max_chunk // 2


def test_compile_moe_contiguous_placement():
    program = compile_moe(
        make_moe(),
        tokens=8,
        config=HardwareConfig(num_pes=512, noc_nodes=16),
        options=CompileOptions(
            replicas=2,
            expert_placement="contiguous",
        ),
    )

    assert program.plan["expert_placement"]["strategy"] == "contiguous"

    send_dsts = {
        int(t.metadata.get("dst", -1))
        for t in program.tasks
        if t.task_id.endswith("_noc_send")
    }
    # Expert i replicas on nodes {2i, 2i+1}; 8 experts × 2 = 16 nodes.
    assert send_dsts == set(range(16))
