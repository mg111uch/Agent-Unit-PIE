from vse.core import Simulator, PipelineStage

def test_event_timing():
    sim = Simulator(frequency_hz=1e9)

    completed = []

    sim.schedule(
        10,
        lambda: completed.append(sim.cycle),
    )

    sim.run()

    assert completed == [10]
    assert sim.cycle == 10

def test_pipeline():
    sim = Simulator(frequency_hz=1e9)

    completed = []

    stage = PipelineStage(
        sim,
        "test_stage",
        latency_cycles=20,
    )

    stage.process(
        lambda: completed.append(sim.cycle)
    )

    sim.run()

    assert completed == [20]
    assert stage.operations == 1