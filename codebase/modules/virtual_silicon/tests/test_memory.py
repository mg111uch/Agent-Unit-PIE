from vse.core import Simulator
from vse.memory import Memory, MemoryConfig

def make_memory(sim):
    return Memory(
        sim,
        "SRAM",
        MemoryConfig(
            capacity_bytes=64 * 1024,
            read_bandwidth_bytes_per_cycle=64,
            write_bandwidth_bytes_per_cycle=64,
            read_latency_cycles=10,
            write_latency_cycles=10,
            max_outstanding=16,
        ),
    )

def test_read_latency():
    sim = Simulator()
    memory = make_memory(sim)

    completed = []

    memory.read(
        address=0,
        size_bytes=64,
        callback=lambda: completed.append(sim.cycle),
    )

    sim.run()

    # 10 cycles latency + 1 cycle transfer.
    assert completed == [11]

def test_write_latency():
    sim = Simulator()
    memory = make_memory(sim)

    completed = []

    memory.write(
        address=0,
        size_bytes=128,
        callback=lambda: completed.append(sim.cycle),
    )

    sim.run()

    # 10 cycles latency + 2 cycles transfer.
    assert completed == [12]

def test_capacity_check():
    sim = Simulator()
    memory = make_memory(sim)

    try:
        memory.read(
            address=64 * 1024 - 10,
            size_bytes=20,
        )
        assert False
    except ValueError:
        pass

def test_concurrent_requests():
    sim = Simulator()
    memory = make_memory(sim)

    completed = []

    for i in range(4):
        memory.read(
            address=i * 64,
            size_bytes=64,
            callback=lambda: completed.append(sim.cycle),
        )

    sim.run()

    assert len(completed) == 4
    assert all(cycle == 11 for cycle in completed)
    assert memory.stats.completed_reads == 4

