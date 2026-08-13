"""
Phase 6 tests: architecture search.
"""

import pytest

from vse.search.architecture import (
    ArchitectureSpec,
    DIM_FIELDS,
    SearchSpace,
)
from vse.compiler.compiler import CompileOptions
from vse.search.search import (
    SearchResult,
    pareto_frontier,
    run_random_search,
    run_search,
)


class _StubResult:
    """Minimal EndToEndResult-like object for SearchResult."""

    def __init__(self, tokens=0.0, cycles=0):
        self.tokens = tokens
        self.cycles = cycles
        self.total_macs = 0
        self.memory_traffic = {}
        self.noc = {}
        self.latency_seconds = cycles / 1e9
        self.compute_utilization = 0.5
        self.memory_utilization = 0.5

    @property
    def tokens_per_second(self):
        return self.tokens

    @property
    def total_cycles(self):
        return self.cycles


class _AreaOverride(SearchResult):
    """SearchResult with a fixed area for Pareto tests."""

    def __init__(self, tokens, area):
        super().__init__(
            spec=ArchitectureSpec(),
            result=_StubResult(tokens=tokens),
        )
        self._area = area

    @property
    def area_mm2(self):
        return self._area


def test_spec_to_hardware_config_roundtrip():
    spec = ArchitectureSpec(
        num_pes=2048,
        sram_bytes=1024**3,
        hbm_bytes_per_cycle=512,
    )

    config = spec.to_hardware_config()

    assert config.num_pes == 2048
    assert config.sram_bytes == 1024**3
    assert config.hbm_bytes_per_cycle == 512
    assert config.memory_bytes_per_cycle == 512


def test_spec_to_compile_options():
    spec = ArchitectureSpec(
        weight_bits=8,
        activation_bits=4,
        kv_bits=8,
        fusion=False,
    )

    options = spec.to_compile_options()

    assert isinstance(options, CompileOptions)
    assert options.weight_bits == 8
    assert options.fusion is False


def test_area_and_power_proxies_monotonic():
    small = ArchitectureSpec(num_pes=1024, sram_bytes=0)
    large = ArchitectureSpec(
        num_pes=8192,
        sram_bytes=8 * 1024**3,
    )

    assert large.area_proxy > small.area_proxy
    assert large.power_proxy > small.power_proxy
    assert small.area_proxy == pytest.approx(1024.0)


def test_search_space_cross_product():
    space = SearchSpace(
        {
            "num_pes": ["1024", "2048"],
            "sram_gb": ["0", "1"],
        }
    )

    specs = space.specs(ArchitectureSpec())

    assert len(specs) == 4
    assert space.size == 4

    pes = {spec.num_pes for spec in specs}
    srams = {spec.sram_bytes for spec in specs}
    assert pes == {1024, 2048}
    assert srams == {0, 1024**3}


def test_search_space_inherits_base():
    space = SearchSpace({"banks": [2, 4]})

    specs = space.specs(ArchitectureSpec(num_pes=512))

    assert len(specs) == 2
    assert all(spec.num_pes == 512 for spec in specs)


def test_search_space_empty_single_candidate():
    space = SearchSpace({})

    specs = space.specs(ArchitectureSpec())

    assert len(specs) == 1


def test_search_space_validates_unknown_dim():
    with pytest.raises(ValueError):
        SearchSpace({"bogus": [1, 2]})


def test_search_space_validates_empty_dim():
    with pytest.raises(ValueError):
        SearchSpace({"num_pes": []})


def test_dim_fields_have_parsers():
    for name, (field_name, parser) in DIM_FIELDS.items():
        assert field_name in ArchitectureSpec.__dataclass_fields__
        assert callable(parser)


def test_sram_gb_converter():
    parser = DIM_FIELDS["sram_gb"][1]
    assert parser("2") == 2 * 1024**3


def test_run_search_simulates_each_candidate():
    from vse.compiler.compiler import compile_transformer
    from vse.models.transformer import (
        TransformerConfig,
        TransformerModel,
    )

    model = TransformerModel(
        TransformerConfig(
            hidden_dim=256,
            num_heads=4,
            intermediate_dim=512,
        ),
        num_layers=2,
    )

    space = SearchSpace(
        {
            "num_pes": [256, 512],
            "hbm_bw": [64, 128],
        }
    )

    def build(spec):
        return compile_transformer(
            model,
            sequence_length=32,
            config=spec.to_hardware_config(),
            options=spec.to_compile_options(),
        )

    results = run_search(space, build)

    assert len(results) == 4
    assert all(isinstance(item, SearchResult) for item in results)
    assert all(item.total_cycles > 0 for item in results)
    assert all(item.tokens_per_second > 0 for item in results)


def test_run_search_moe_candidates():
    from vse.compiler.compiler import compile_moe
    from vse.models.moe import MoE, MoEConfig

    moe = MoE(
        MoEConfig(
            hidden_dim=256,
            intermediate_dim=512,
            num_experts=8,
            top_k=2,
        )
    )

    space = SearchSpace(
        {
            "num_pes": [128, 256],
            "weight_bits": [4, 8],
        }
    )

    def build(spec):
        return compile_moe(
            moe,
            tokens=8,
            config=spec.to_hardware_config(),
            options=spec.to_compile_options(),
        )

    results = run_search(space, build)

    assert len(results) == 4
    assert len({item.spec.weight_bits for item in results}) == 2


def test_pareto_frontier_keeps_non_dominated():
    results = [
        _AreaOverride(tokens=100, area=100),
        _AreaOverride(tokens=200, area=100),  # dominates first
        _AreaOverride(tokens=150, area=50),   # dominates first, not second
        _AreaOverride(tokens=50, area=20),    # cheap but slow
    ]

    frontier = pareto_frontier(results)

    assert len(frontier) == 3
    assert results[0] not in frontier
    assert {id(item) for item in frontier} == {
        id(results[1]),
        id(results[2]),
        id(results[3]),
    }


def test_pareto_frontier_equal_points_both_kept():
    a = _AreaOverride(tokens=100, area=50)
    b = _AreaOverride(tokens=100, area=50)

    assert pareto_frontier([a, b]) == [a, b]


def test_search_result_report_fields():
    spec = ArchitectureSpec(num_pes=512)
    item = SearchResult(
        spec=spec,
        result=_StubResult(tokens=42.0, cycles=100),
    )

    report = item.report()

    assert report["arch"] == spec.label()
    assert report["num_pes"] == 512
    assert report["tokens_per_second"] == 42.0
    assert report["total_cycles"] == 100
    assert report["area_mm2"] > 0
    assert report["power_watts"] >= 0
    assert report["tokens_per_watt"] >= 0


def test_new_search_dimensions_exist():
    for name in (
        "pipeline",
        "double_buffer",
        "noc_topology",
        "tokens",
        "replicas",
        "placement",
        "node_nm",
    ):
        assert name in DIM_FIELDS

    space = SearchSpace(
        {
            "pipeline": [0, 4],
            "double_buffer": [2, 4],
            "noc_topology": ["ring", "mesh"],
            "tokens": [8, 16],
            "replicas": [1, 2],
            "placement": ["round_robin", "contiguous"],
            "node_nm": [7.0, 14.0],
        }
    )

    specs = space.specs(ArchitectureSpec())

    assert len(specs) == 128
    assert {s.noc_topology for s in specs} == {"ring", "mesh"}
    assert {s.node_nm for s in specs} == {7.0, 14.0}
    assert {s.pipeline_latency for s in specs} == {0, 4}


def test_sample_specs_random():
    space = SearchSpace(
        {
            "num_pes": [128, 256, 512, 1024],
            "hbm_bw": [64, 128, 256],
        }
    )

    sampled = space.sample_specs(
        20,
        base=ArchitectureSpec(),
        seed=42,
    )

    assert len(sampled) == 20
    assert all(s.num_pes in {128, 256, 512, 1024} for s in sampled)
    assert all(s.hbm_bytes_per_cycle in {64, 128, 256} for s in sampled)

    # Deterministic under a fixed seed.
    again = space.sample_specs(20, seed=42)
    assert [s.num_pes for s in sampled] == [s.num_pes for s in again]


def test_sample_specs_validates_n():
    space = SearchSpace({})
    with pytest.raises(ValueError):
        space.sample_specs(0)


def test_run_random_search():
    from vse.compiler.compiler import compile_transformer
    from vse.models.transformer import (
        TransformerConfig,
        TransformerModel,
    )

    model = TransformerModel(
        TransformerConfig(
            hidden_dim=256,
            num_heads=4,
            intermediate_dim=512,
        ),
        num_layers=2,
    )

    space = SearchSpace(
        {
            "num_pes": [128, 256, 512],
            "hbm_bw": [64, 128],
        }
    )

    def build(spec):
        return compile_transformer(
            model,
            sequence_length=32,
            config=spec.to_hardware_config(),
            options=spec.to_compile_options(),
        )

    results = run_random_search(space, build, n=10, seed=7)

    assert len(results) == 10
    assert all(item.total_cycles > 0 for item in results)
