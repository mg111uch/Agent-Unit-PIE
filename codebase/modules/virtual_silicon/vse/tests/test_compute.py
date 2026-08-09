from vse.core import Simulator
from vse.compute import ComputeArray, ComputeConfig


def make_compute(sim):
    return ComputeArray(
        sim,
        "INT4_ARRAY",
        ComputeConfig(
            num_pes=1024,
            macs_per_pe_per_cycle=1,
            frequency_hz=1e9,
            pipeline_latency=2,
            data_bits=4,
        ),
    )


def test_mac_latency():
    sim = Simulator()
    compute = make_compute(sim)

    completed = []

    compute.submit(
        macs=1024,
        callback=lambda: completed.append(sim.cycle),
    )

    sim.run()

    # 1024 MACs / 1024 MACs per cycle = 1 cycle
    # + 2 cycles pipeline latency.
    assert completed == [3]


def test_large_workload():
    sim = Simulator()
    compute = make_compute(sim)

    compute.submit(macs=10_000)

    sim.run()

    # ceil(10000 / 1024) + 2
    assert sim.cycle == 12


def test_peak_throughput():
    sim = Simulator()

    compute = ComputeArray(
        sim,
        "ARRAY",
        ComputeConfig(
            num_pes=4096,
            macs_per_pe_per_cycle=2,
            frequency_hz=2e9,
        ),
    )

    # 4096 × 2 MACs/cycle × 2 GHz × 2 operations/MAC
    # = 32 TOPS.
    assert compute.peak_tops == 32.0


def test_report():
    sim = Simulator()
    compute = make_compute(sim)

    compute.submit(macs=2048)
    sim.run()

    report = compute.report()

    assert report["macs_completed"] == 2048
    assert report["operations_completed"] == 1
    assert report["num_pes"] == 1024


def test_int4_factory():
    sim = Simulator()

    compute = __import__(
        "vse.compute",
        fromlist=["make_int4_array"],
    ).make_int4_array(
        sim,
        "INT4",
        num_pes=4096,
        frequency_ghz=2.0,
    )

    assert compute.config.data_bits == 4
    assert compute.config.frequency_hz == 2e9
