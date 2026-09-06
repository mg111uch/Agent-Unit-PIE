"""Scenario engine (FeatureIdeas #6/#10, Phase B): baseline → policy branches.

`branch()` runs baseline + each policy (per-step `at_step` params, no sim edits)
and compares SocietyState outcomes. `score_policy()` is the multi-objective
gate: welfare subject to inequality/food/fiscal constraints. Welfare here is a
documented proxy (food + wealth/capita − inequality), not a moral claim.
"""
from __future__ import annotations
from typing import Any, Callable, Dict, List
from .policy import compile as _compile, at_step as _at_step
from .policy import policy_id as _policy_id
from .society import society_state as _society


def _run(make_model: Callable[[Dict[str, Any]], Any], base: Dict[str, Any],
         compiled: Dict[str, Any] | None) -> Dict[str, Any]:
    years = int(base.get("years", 50))
    m = make_model(dict(base))
    for i in range(years):
        if compiled is not None:
            m.params = _at_step(base, compiled, i)
        m.step()
    m.params = dict(base)
    soc = _society(m)
    return {"society": soc, "population": soc["population"],
            "fiscal": round(compiled["fiscal_cost"], 1) if compiled else 0.0}


def score_policy(outcome: Dict[str, Any], cfg: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """welfare = capped food + capped wealth/capita − gini; constraints gate."""
    cfg = cfg or {}
    s = outcome["society"]
    pop = max(1, s["population"])
    welf = (min(s["food_security"], 1.5) + min(s["wealth_total"] / pop / 20.0, 1.0)
            - s["gini"])
    viol = []
    if s["gini"] > float(cfg.get("max_gini", 0.4)):
        viol.append(f"gini {s['gini']}")
    if s["food_security"] < float(cfg.get("min_food", 0.5)):
        viol.append(f"food {s['food_security']}")
    if outcome["fiscal"] > float(cfg.get("max_fiscal", 1e9)):
        viol.append(f"fiscal {outcome['fiscal']}")
    return {"welfare": round(welf, 3), "pass": not viol, "violations": viol,
            "fiscal": outcome["fiscal"]}


def branch(make_model: Callable[[Dict[str, Any]], Any], base_params: Dict[str, Any],
           policies: List[Dict[str, Any]], cfg: Dict[str, Any] | None = None,
           registry_path: str | None = None) -> Dict[str, Any]:
    """Baseline + one branch per policy. `registry_path` (JSON) memoizes by
    policy_id: identical proposals hit the registry instead of re-running."""
    import json as _json
    memo: Dict[str, Any] = {}
    if registry_path:
        try:
            with open(registry_path) as f:
                memo = _json.load(f)
        except Exception:
            memo = {}
    base_ver = str(base_params.get("epoch", "")) + str(base_params.get("seed", ""))
    base = _run(make_model, base_params, None)
    rows = [{"name": "baseline:no_intervention", **score_policy(base, cfg),
             "society": base["society"]}]
    for p in policies:
        pid = _policy_id(p, base_ver)
        if pid in memo:
            rows.append({**memo[pid], "dedup": True})
            continue
        c = _compile(p, base_params)
        o = _run(make_model, base_params, c)
        row = {"name": f"policy:{p.get('mechanism')}", "policy_id": pid,
               **score_policy(o, cfg), "society": o["society"]}
        memo[pid] = row
        rows.append(row)
    if registry_path:
        try:
            with open(registry_path, "w") as f:
                _json.dump(memo, f)
        except Exception:
            pass
    rows.sort(key=lambda r: r["welfare"], reverse=True)
    rows.sort(key=lambda r: r["welfare"], reverse=True)
    lines = ["policy | welfare | pass | fiscal | pop | gini | food"]
    for r in rows:
        s = r["society"]
        lines.append(f"{r['name']} | {r['welfare']} | {r['pass']} | {r['fiscal']}"
                     f" | {s['population']} | {s['gini']} | {s['food_security']}")
    return {"rows": rows, "table": "\n".join(lines)}


# Phase C (FeatureIdeas #9/#11): unintended effects + sensitivity.
PRIMARY_METRIC = {"food_subsidy": "food_security", "fertility_incentive": "population",
                  "healthcare": "health_index", "education_expansion": "skilled_share",
                  "industrial_policy": "wealth_total"}


def effect_chains(mechanism: str, base_soc: Dict[str, Any],
                 pol_soc: Dict[str, Any]) -> Dict[str, Any]:
    """Decompose policy delta: DIRECT (target metric) / SECONDARY (pop+wealth) /
    DISTRIBUTIONAL (gini) / UNINTENDED (non-target metric degraded ≥10% while
    target improved). Actively searches the side-effect chain."""
    def _d(k: str) -> float:
        b = base_soc.get(k, 0) or 0
        return ((pol_soc.get(k, 0) or 0) - b) / max(1e-9, abs(b)) if b else 0.0

    target = PRIMARY_METRIC.get(mechanism, "population")
    direct = _d(target)
    secondary = {"population": _d("population"), "wealth_total": _d("wealth_total"),
                 "food_security": _d("food_security")}
    distrib = _d("gini")  # gini up = worse distribution
    unintended = [k for k in ("population", "wealth_total", "food_security",
                              "health_index", "gini")
                  if k != target and (( _d(k) <= -0.10 and k != "gini")
                                       or (k == "gini" and _d(k) >= 0.10))]
    return {"direct": {target: round(direct, 3)}, "secondary": secondary,
            "distributional_gini_delta": round(distrib, 3),
            "unintended": unintended,
            "target_improved": bool(direct > 0)}


def sensitivity(make_model: Callable[[Dict[str, Any]], Any],                base_params: Dict[str, Any], policy: Dict[str, Any],
                axes: Dict[str, List[Any]] | None = None,
                cfg: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Policy × assumptions grid (pop/resource/seed). Robust = pass rate high;
    fragile = works only under one assumption set."""
    axes = axes or {"initial_pop": [10, 30], "seed": [7, 99]}
    c = _compile(policy, base_params)
    outs, wins = [], 0
    import itertools
    keys = sorted(axes)
    for combo in itertools.product(*[axes[k] for k in keys]):
        b = dict(base_params)
        b.update(dict(zip(keys, combo)))
        o = _run(make_model, b, c)
        sc = score_policy(o, cfg)
        outs.append({"assumptions": dict(zip(keys, combo)), "welfare": sc["welfare"],
                     "pass": sc["pass"]})
        wins += bool(sc["pass"])
    rate = wins / max(1, len(outs))
    return {"pass_rate": round(rate, 3), "robust": bool(rate >= 0.75),
            "outcomes": outs}


def screen_policy(policy: Dict[str, Any], base_params: Dict[str, Any],
                  cfg: Dict[str, Any] | None = None,
                  registry_path: str | None = None) -> Dict[str, Any]:
    """Cheap analytical screen before a full branch run (FeatureIdeas #12).

    Milliseconds, no simulation: (1) registry hit → memoized verdict;
    (2) static gates — supported mechanism (via compile), fiscal within cap,
    positive duration. Pass means 'worth simulating', not 'good policy'."""
    import json as _json
    cfg = cfg or {}
    try:
        c = _compile(policy, base_params)
    except ValueError as e:
        return {"pass": False, "source": "static", "reason": str(e)[:120]}
    pid = _policy_id(policy, str(base_params.get("epoch", ""))
                     + str(base_params.get("seed", "")))
    if registry_path:
        try:
            with open(registry_path) as f:
                hit = _json.load(f).get(pid)
            if hit:
                return {"pass": bool(hit.get("pass")), "source": "registry",
                        "policy_id": pid, "welfare": hit.get("welfare")}
        except Exception:
            pass
    if c["fiscal_cost"] > float(cfg.get("max_fiscal", 1e9)):
        return {"pass": False, "source": "static", "policy_id": pid,
                "reason": f"fiscal {c['fiscal_cost']} over cap"}
    if c["schedule"]["duration"] <= 0:
        return {"pass": False, "source": "static", "policy_id": pid,
                "reason": "non-positive duration"}
    return {"pass": True, "source": "static", "policy_id": pid,
            "fiscal": c["fiscal_cost"], "note": "worth simulating"}
