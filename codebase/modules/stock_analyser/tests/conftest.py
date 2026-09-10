"""Stock analyser test tiers: fast gate vs slow real-data lane.

Standard gate (fast, synthetic/temp-DB only): pytest -m "not slow"
Slow lane (real market.db panels/training, background/nightly or pre-sweep).
"""


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: real-data tests (market.db panels/training)")
