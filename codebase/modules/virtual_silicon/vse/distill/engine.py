"""Distillation engine stub — Phase E.

Teacher → candidate 1B archs → synthetic → distill → accuracy → VSE hardware analysis → mutate.
Heuristic only, deterministic, no ML training.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, replace
from typing import Dict, List, Optional

from vse.models.accuracy import AccuracyEstimate, accuracy_for_spec
from vse.search.model_space import ModelArchSpec, ModelSearchSpace

TEACHER_SCORES: Dict[str, float] = {
    "300B": 0.92,
    "30B": 0.88,
    "7B": 0.82,
    "1B": 0.75,
    "vse-s1": 0.80,
}


@dataclass
class DistillCandidate:
    model_spec: ModelArchSpec
    accuracy: AccuracyEstimate
    synthetic_dataset_size: int
    teacher_score: float


@dataclass
class DistillResult:
    candidate: DistillCandidate
    trained_score: AccuracyEstimate
    vse_result: Optional[object] = None
    pareto_rank: int = 0


def _resolve_hw(hw_spec) -> object:
    """Convert ArchitectureSpec|HardwareConfig|None to HardwareConfig."""
    if hw_spec is None:
        from vse.workload import HardwareConfig

        return HardwareConfig()
    # ArchitectureSpec has to_hardware_config
    if hasattr(hw_spec, "to_hardware_config"):
        try:
            return hw_spec.to_hardware_config()
        except Exception:
            pass
    # already HardwareConfig
    if hasattr(hw_spec, "num_pes") and hasattr(hw_spec, "frequency_hz"):
        return hw_spec
    from vse.workload import HardwareConfig

    return HardwareConfig()


def _pareto_ranks(results: List[DistillResult]) -> List[DistillResult]:
    """Nondominated sorting on (coding_score↑, tokens_per_second↑) vs param count proxy.

    Uses tokens_per_second vs parameter count when area not available.
    Assigns pareto_rank 1..N.
    """
    if not results:
        return results

    def tps(r: DistillResult) -> float:
        if r.vse_result is not None:
            try:
                return float(getattr(r.vse_result, "tokens_per_second", 0) or 0)
            except Exception:
                return 0.0
        return 0.0

    def acc(r: DistillResult) -> float:
        try:
            return float(getattr(r.trained_score, "coding_score", 0) or 0)
        except Exception:
            return 0.0

    def cost(r: DistillResult) -> float:
        # minimize param count / area proxy
        if r.vse_result is not None and hasattr(r.vse_result, "area"):
            try:
                a = r.vse_result.area
                if isinstance(a, dict) and "total_area_mm2" in a:
                    return float(a["total_area_mm2"])
            except Exception:
                pass
        try:
            return float(r.candidate.model_spec.parameter_count())
        except Exception:
            return float("inf")

    remaining = list(results)
    rank = 1
    ranked: List[DistillResult] = []
    while remaining:
        frontier: List[DistillResult] = []
        for item in remaining:
            dominated = False
            for other in remaining:
                if other is item:
                    continue
                # other dominates item if >= on both objectives and <= cost and strictly better on one
                if acc(other) >= acc(item) and tps(other) >= tps(item) and cost(other) <= cost(item):
                    if acc(other) > acc(item) or tps(other) > tps(item) or cost(other) < cost(item):
                        dominated = True
                        break
            if not dominated:
                frontier.append(item)
        if not frontier:
            frontier = remaining[:1]
        for f in frontier:
            f.pareto_rank = rank
            ranked.append(f)
        remaining = [r for r in remaining if r not in frontier]
        rank += 1
    # preserve dominance order but return ranked sorted by rank then acc desc
    ranked.sort(key=lambda x: (x.pareto_rank, -acc(x)))
    return ranked


class DistillEngine:
    """Heuristic distillation engine.

    Teacher provides synthetic data; candidate 1B-scale archs are sampled,
    distilled (accuracy heuristic + synthetic boost), benchmarked via VSE,
    then mutated.
    """

    def __init__(
        self,
        teacher: str = "300B",
        base_model: Optional[ModelArchSpec] = None,
        seed: Optional[int] = 0,
        hw_config=None,
    ):
        self.teacher = teacher
        self.teacher_score = TEACHER_SCORES.get(teacher, 0.85)
        self.base_model = base_model if base_model is not None else ModelArchSpec()
        self.seed = seed
        self.rng = random.Random(seed)
        self.hw_config = hw_config

    # --- helpers ---
    def _random_spec(self) -> ModelArchSpec:
        """Randomly perturb base_model within valid ranges."""
        # sample hidden_dim multiples of num_heads
        heads_choices = [8, 12, 16, 24, 32]
        layers_choices = list(range(8, 25))
        hidden_choices = [1024, 1280, 1536, 1792, 2048, 2560, 3072, 4096]
        # use rng to pick
        layers = self.rng.choice(layers_choices)
        hidden = self.rng.choice(hidden_choices)
        heads = self.rng.choice(heads_choices)
        # fix hidden % heads ==0
        if hidden % heads != 0:
            # adjust hidden to nearest divisible
            hidden = (hidden // heads) * heads
            if hidden < 1024:
                hidden = heads * (1024 // heads + 1)
            if hidden > 4096:
                hidden = 4096 - (4096 % heads)
        interm = self.rng.choice([2048, 2816, 3584, 4096, 4608, 5504, 8192, 11008])
        wbits = self.rng.choice([2, 3, 4])
        try:
            return ModelArchSpec(
                layers=layers,
                hidden_dim=hidden,
                num_heads=heads,
                intermediate_dim=interm,
                weight_bits=wbits,
            )
        except ValueError:
            return replace(self.base_model)

    def generate_candidates(self, n: int, space=None) -> List[DistillCandidate]:
        if n < 1:
            raise ValueError("n must be >=1")
        specs: List[ModelArchSpec]
        if space is None:
            specs = [self._random_spec() for _ in range(n)]
        elif isinstance(space, ModelSearchSpace):
            # use deterministic seed derived from engine rng
            seed = self.rng.randint(0, 2**31 - 1)
            specs = space.sample_specs(n, base=self.base_model, seed=seed)
        elif hasattr(space, "sample_specs"):
            try:
                seed = self.rng.randint(0, 2**31 - 1)
                specs = space.sample_specs(n, self.base_model, seed)  # type: ignore
            except Exception:
                specs = [self._random_spec() for _ in range(n)]
        elif hasattr(space, "specs"):
            try:
                all_specs = space.specs(self.base_model)  # type: ignore
                if len(all_specs) >= n:
                    # random sample without replacement deterministic
                    specs = self.rng.sample(all_specs, n)
                else:
                    specs = all_specs
                    while len(specs) < n:
                        specs.append(self._random_spec())
            except Exception:
                specs = [self._random_spec() for _ in range(n)]
        else:
            specs = [self._random_spec() for _ in range(n)]

        candidates: List[DistillCandidate] = []
        for spec in specs:
            acc = accuracy_for_spec(spec)
            size = 30000 + self.rng.randint(0, 30000)
            candidates.append(
                DistillCandidate(
                    model_spec=spec,
                    accuracy=acc,
                    synthetic_dataset_size=size,
                    teacher_score=self.teacher_score,
                )
            )
        return candidates

    def synthetic_dataset(self, candidate: DistillCandidate) -> dict:
        size = candidate.synthetic_dataset_size
        python = int(size * 0.5)
        js = int(size * 0.3)
        english = size - python - js
        return {
            "size": size,
            "python": python,
            "js": js,
            "english": english,
            "teacher": self.teacher,
        }

    def distill(self, candidate: DistillCandidate) -> DistillResult:
        base = candidate.accuracy
        # heuristic synthetic boost: larger dataset -> higher boost, teacher gap matters
        boost = min(0.04, candidate.synthetic_dataset_size / 500000.0)
        teacher_gap = max(0.0, self.teacher_score - base.coding_score)
        teacher_boost = teacher_gap * 0.25
        new_coding = min(0.99, base.coding_score + boost * 0.8 + teacher_boost + 0.01)
        new_pass = min(0.99, base.pass_at_k + boost * 0.7 + teacher_boost * 0.8 + 0.008)
        new_ppl = base.ppl_delta - boost * 0.5 - teacher_boost * 0.3
        new_ppl = max(-0.5, min(1.0, new_ppl))
        trained = AccuracyEstimate(
            ppl_delta=round(float(new_ppl), 6),
            pass_at_k=round(float(new_pass), 6),
            coding_score=round(float(new_coding), 6),
            bits_avg=round(float(base.bits_avg), 4),
        )
        vse_result = None
        try:
            hw = _resolve_hw(self.hw_config)
            model = candidate.model_spec.to_transformer_model()
            from vse.workload import simulate_transformer

            vse_result = simulate_transformer(model, sequence_length=512, config=hw, mode="decode")
        except Exception:
            vse_result = None
        return DistillResult(candidate=candidate, trained_score=trained, vse_result=vse_result, pareto_rank=0)

    def mutate(self, spec: ModelArchSpec) -> ModelArchSpec:
        dl = self.rng.choice([-2, -1, 1, 2])
        nl = max(8, min(24, spec.layers + dl))
        dh = self.rng.choice([-256, -128, 128, 256])
        nh = spec.hidden_dim + dh
        nh = max(1024, min(4096, nh))
        # keep divisible by num_heads
        heads = spec.num_heads
        if nh % heads != 0:
            nh = (nh // heads) * heads
            if nh < 1024:
                nh = 1024 + (1024 % heads)
                nh = (nh // heads) * heads
            if nh > 4096:
                nh = 4096 - (4096 % heads)
            if nh < 1024:
                nh = 1024
        # also maybe mutate intermediate slightly
        interm = spec.intermediate_dim
        if self.rng.random() < 0.3:
            di = self.rng.choice([-512, -256, 256, 512])
            interm = max(2048, min(11008, interm + di))
        try:
            return replace(spec, layers=nl, hidden_dim=nh, intermediate_dim=interm)
        except ValueError:
            try:
                return replace(spec, layers=nl)
            except Exception:
                return replace(spec)

    def loop(
        self,
        n: int = 4,
        space=None,
        hw_spec=None,
        generations: int = 2,
    ) -> List[DistillResult]:
        """Teacher → candidates → synthetic → distill → VSE → mutate → re-distill."""
        if hw_spec is not None:
            # allow per-loop hw override
            old_hw = self.hw_config
            self.hw_config = hw_spec
        else:
            old_hw = None
        candidates = self.generate_candidates(n, space)
        all_results: List[DistillResult] = []
        for g in range(generations):
            gen_results: List[DistillResult] = []
            for c in candidates:
                _ = self.synthetic_dataset(c)
                r = self.distill(c)
                gen_results.append(r)
            gen_results = _pareto_ranks(gen_results)
            all_results.extend(gen_results)
            if g < generations - 1:
                # select top half by trained_score for mutation
                sorted_top = sorted(gen_results, key=lambda x: x.trained_score.coding_score, reverse=True)
                top = sorted_top[: max(1, n // 2)]
                next_candidates: List[DistillCandidate] = []
                while len(next_candidates) < n:
                    parent = self.rng.choice(top).candidate.model_spec
                    ns = self.mutate(parent)
                    acc = accuracy_for_spec(ns)
                    size = 30000 + self.rng.randint(0, 30000)
                    next_candidates.append(
                        DistillCandidate(
                            model_spec=ns,
                            accuracy=acc,
                            synthetic_dataset_size=size,
                            teacher_score=self.teacher_score,
                        )
                    )
                candidates = next_candidates
        if old_hw is not None or hw_spec is not None:
            # restore if we overrode
            if hw_spec is not None:
                self.hw_config = old_hw
        all_results = _pareto_ranks(all_results)
        return all_results

    # alias for compatibility
    run = loop


def run_distillation(
    space=None,
    n: int = 4,
    hw_spec=None,
    teacher: str = "300B",
    base_model: Optional[ModelArchSpec] = None,
    seed: Optional[int] = 0,
    generations: int = 2,
) -> List[DistillResult]:
    """Top-level helper matching IssuesFix §4 loop."""
    engine = DistillEngine(teacher=teacher, base_model=base_model, seed=seed, hw_config=hw_spec)
    return engine.loop(n=n, space=space, hw_spec=hw_spec, generations=generations)


__all__ = [
    "DistillCandidate",
    "DistillResult",
    "DistillEngine",
    "run_distillation",
    "TEACHER_SCORES",
]
