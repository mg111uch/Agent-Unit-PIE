"""Resumable research: families compete via adaptive bandit, screen cheap, retire the dead.

- Seeds: base strategies (symbolic + ML). Allocator weights families by prior ×
  success-rate + exploration bonus (research/allocate.py); explore/exploit/validate split.
- Screen: alpha gate + 1 cheap backtest; only passers pay for full validation (locked OOS).
- Retirement: a family with `retire_after` consecutive REJECTs stops spawning;
  `screened_retire_after` consecutive SCREENEDs (cheap-gate stall, no learning)
  retires it too — screens now count.
- Ledger (market.db): runs, candidates (with family + verdict), hash dedup.
"""
from __future__ import annotations
import hashlib
import json
import random
import time
from datetime import datetime, timezone
from typing import Any, Dict, List
from ..connector import StockConnector
from ..config import load_capital
from ..data.store import connect, ensure_schema
from ..data.universe import resolve_universe
from ..data.universe import snapshot_hash as _snaphash
from ..strategies.model import strategy_from_dict
from ..strategies.genome import mutate, mutate_ml, MUTATIONS, ML_MUTATIONS
from ..backtest.validation import validate_strategy

LEDGER_ALTER = "ALTER TABLE research_candidates ADD COLUMN family TEXT DEFAULT ''"
LEDGER_ALTER2 = "ALTER TABLE research_candidates ADD COLUMN data_hash TEXT DEFAULT ''"
LEDGER_ALTER3 = "ALTER TABLE research_candidates ADD COLUMN code_version TEXT DEFAULT ''"
LEDGER_ALTER4 = "ALTER TABLE research_candidates ADD COLUMN feature_set_hash TEXT DEFAULT ''"
LEDGER_ALTER5 = "ALTER TABLE research_candidates ADD COLUMN model_config_hash TEXT DEFAULT ''"
LEDGER_ALTER6 = "ALTER TABLE research_candidates ADD COLUMN random_seed TEXT DEFAULT ''"
LEDGER_ALTER7 = "ALTER TABLE research_candidates ADD COLUMN dataset_id TEXT DEFAULT ''"
LEDGER_ALTER8 = "ALTER TABLE research_candidates ADD COLUMN signal_hash TEXT DEFAULT ''"
LEDGER_ALTER9 = "ALTER TABLE research_candidates ADD COLUMN score_is REAL DEFAULT NULL"
LEDGER_ALTER10 = "ALTER TABLE research_candidates ADD COLUMN n_is INTEGER DEFAULT NULL"
LEDGER_ALTER11 = "ALTER TABLE research_candidates ADD COLUMN eval_regime TEXT DEFAULT ''"
EPOCH_OVERRIDE_DDL = ("CREATE TABLE IF NOT EXISTS epoch_overrides(dataset_id TEXT PRIMARY KEY,"
                      " reason TEXT DEFAULT '', hashes_json TEXT DEFAULT '[]',"
                      " created_at TEXT DEFAULT '', used_by TEXT DEFAULT '')")


def data_fingerprint(bars: Dict[str, List]) -> str:
    fp = {s: (len(bl), bl[0]["ts"] if bl else "", bl[-1]["ts"] if bl else "")
          for s, bl in sorted(bars.items())}
    return hashlib.sha256(json.dumps(fp, sort_keys=True).encode()).hexdigest()[:16]


def code_version() -> str:
    try:
        from kernel.git_version import sim_commit
        return str(sim_commit("stock_analyser"))
    except Exception:
        return "unknown"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


_STAGE_ORDER = ("iter_start", "mutated", "gated", "alpha", "stage1", "screen",
                "validated", "ladder", "backtest", "recorded")
_STAGE_LABEL = {"mutated": "choose_mutate", "gated": "dedup_seal_sigfp",
                "alpha": "alpha_gate", "stage1": "stage1_ic", "screen": "quick_screen",
                "validated": "validate", "ladder": "ladder",
                "backtest": "backtest", "recorded": "record"}


def _flush_time(rid: str, i: int, name: str, mutation: str, verdict: str,
                ts: Dict[str, float]) -> None:
    """One JSONL line per candidate: per-stage seconds + total. Best-effort."""
    try:
        keys = [k for k in _STAGE_ORDER if k in ts]
        stages = {_STAGE_LABEL[keys[j + 1]]: round(ts[keys[j + 1]] - ts[keys[j]], 2)
                  for j in range(len(keys) - 1)}
        with open(f"/tmp/opencode/research_timing_{rid}.jsonl", "a") as f:
            f.write(json.dumps({"rid": rid, "i": i, "strategy": name,
                                "mutation": mutation, "verdict": verdict,
                                "stages": stages,
                                "total_s": round(ts[keys[-1]] - ts[keys[0]], 2)
                                if len(keys) > 1 else 0.0}) + "\n")
    except Exception:
        pass


def _hash(strategy_d: Dict[str, Any]) -> str:
    from ..features.algebra import canonical as _canon
    m = strategy_d.get("meta", {}) or {}
    canon = {k: (_canon(v) if k in ("entry", "features") else v)
             for k, v in strategy_d.items() if k not in ("name", "meta")}
    if m.get("family") == "ml":  # core ML choices live in meta: hash them too
        canon["_ml"] = {k: m.get(k) for k in ("model", "top_n", "max_depth", "features",
                                              "stop_atr", "take_atr", "max_hold",
                                              "position_frac", "max_positions")}
    return hashlib.sha256(json.dumps(canon, sort_keys=True).encode()).hexdigest()[:16]


def signal_fingerprint(strategy_d: Dict[str, Any],
                       bars: Dict[str, List]) -> str:
    """Behavioral duplicate key: hash of the entry signal stream on current bars."""
    from ..features.algebra import columns_from_bars, evaluate
    hot = []
    for s in sorted(bars):
        cols = columns_from_bars(bars[s])
        hot.append("".join("1" if x is True else "0"
                           for x in evaluate(strategy_d.get("entry", {}), cols)))
    return hashlib.sha256("|".join(hot).encode()).hexdigest()[:16]


def family_of(d: Dict[str, Any]) -> str:
    m = d.get("meta", {}) or {}
    if m.get("family"):
        return str(m["family"])
    return "sym:" + str(d.get("name", "?")).split("~")[0]


def _con(db_path: str | None = None):
    ensure_schema(db_path)
    con = connect(db_path)
    for _alter in (LEDGER_ALTER, LEDGER_ALTER2, LEDGER_ALTER3, LEDGER_ALTER4,
                   LEDGER_ALTER5, LEDGER_ALTER6, LEDGER_ALTER7, LEDGER_ALTER8,
                   LEDGER_ALTER9, LEDGER_ALTER10, LEDGER_ALTER11):
        try:
            con.execute(_alter)
        except Exception:
            pass
    try:
        con.execute(EPOCH_OVERRIDE_DDL)
    except Exception:
        pass
    try:  # Q10: tag pre-regime rows once. Cost flip deployed ~08:15 UTC
        # 2026-10-03 (sweep-6 and earlier ran flat; sweep-7+ realistic).
        con.execute("UPDATE research_candidates SET eval_regime='flat'"
                    " WHERE (eval_regime IS NULL OR eval_regime='')"
                    " AND created_at < '2026-10-03T08:15'")
        con.execute("UPDATE research_candidates SET eval_regime='realistic'"
                    " WHERE eval_regime IS NULL OR eval_regime=''")
        con.commit()
    except Exception:
        pass
    return con


def grant_epoch_override(dataset_id: str, reason: str, hashes: List[str],
                         db_path: str | None = None) -> Dict[str, Any]:
    """Auditable one-run override of the epoch cap (round-2 Q10): for
    re-evaluating already-tested hypotheses under a new regime (e.g. the
    rank-gauss ridge finalist under the corrected tariff) — not a fresh
    sweep. Consumed on use; the frozen hash list documents scope."""
    import json as _j
    con = _con(db_path)
    try:
        con.execute(EPOCH_OVERRIDE_DDL)
        con.execute("INSERT OR IGNORE INTO epoch_overrides(dataset_id,reason,hashes_json,"
                    "created_at,used_by) VALUES(?,?,?,?,?)",
                    (dataset_id, reason, _j.dumps(hashes), _now(), ""))
        con.commit()
        return {"dataset_id": dataset_id, "reason": reason, "n_hashes": len(hashes)}
    finally:
        con.close()


def start_run(objective: str, universe: str, mode: str, budget: int,
              db_path: str | None = None, run_id: str | None = None) -> str:
    rid = run_id or f"res_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    con = _con(db_path)
    try:
        con.execute("INSERT OR IGNORE INTO research_runs(id,objective,universe,mode,budget,"
                    "done,status,created_at) VALUES(?,?,?,?,?,?,'RUNNING',?)",
                    (rid, objective, universe, mode, budget, 0, _now()))
        con.execute("UPDATE research_runs SET status='RUNNING',mode=?,budget=? WHERE id=?",
                    (mode, budget, rid))  # resume flips back to RUNNING
        con.commit()
    finally:
        con.close()
    return rid


def tested_hashes(run_id: str, db_path: str | None = None) -> set:
    con = _con(db_path)
    try:
        return {r[0] for r in con.execute(
            "SELECT strategy_hash FROM research_candidates WHERE run_id=?", (run_id,)).fetchall()}
    finally:
        con.close()


def best_candidates(run_id: str, limit: int = 5, db_path: str | None = None,
                    regime: str | None = None) -> List[Dict]:
    """Resume elites ranked on score_is (pre-OOS rank reproducible from the
    ledger), never OOS: ranking on the sealed window would fit it adaptively
    across restarts. regime filters out other cost-basis eras (Q10)."""
    con = _con(db_path)
    try:
        cols = ["strategy_json", "parent", "mutation", "verdict", "avg_net", "oos_net",
                "score_is", "n_is"]
        q = (f"SELECT {','.join(cols)} FROM research_candidates WHERE run_id=?"
             " AND verdict NOT IN ('SCREENED','DUPLICATE')")
        args: list = [run_id]
        if regime:
            q += " AND eval_regime=?"
            args.append(regime)
        q += " ORDER BY COALESCE(score_is,avg_net,-1e18) DESC LIMIT ?"
        args.append(limit)
        rows = con.execute(q, args).fetchall()
        return [dict(zip(cols, r)) for r in rows]
    finally:
        con.close()


def family_rejects(run_id: str, family: str, db_path: str | None = None) -> int:
    """Leading consecutive REJECTs for a family (SCREENED doesn't count)."""
    con = _con(db_path)
    try:
        rows = con.execute("SELECT verdict FROM research_candidates WHERE run_id=? AND family=?"
                           " ORDER BY id DESC", (run_id, family)).fetchall()
    finally:
        con.close()
    n = 0
    for (v,) in rows:
        if v == "REJECT":
            n += 1
        elif v in ("SCREENED", "DUPLICATE"):
            continue
        else:
            break
    return n


def family_stalls(run_id: str, family: str, db_path: str | None = None) -> int:
    """Leading consecutive SCREENEDs for a family (DUPLICATE skipped, REJECT breaks).

    A family that never passes the cheap gate is not learning — stall streaks
    count toward retirement via `screened_retire_after`."""
    con = _con(db_path)
    try:
        rows = con.execute("SELECT verdict FROM research_candidates WHERE run_id=? AND family=?"
                           " ORDER BY id DESC", (run_id, family)).fetchall()
    finally:
        con.close()
    n = 0
    for (v,) in rows:
        if v == "SCREENED":
            n += 1
        elif v == "DUPLICATE":
            continue
        else:
            break
    return n


def _fam_retired(fam: str, cap: Dict[str, Any] | None = None) -> bool:
    """PlanFixes3 #9: retired families (prefix match, e.g. "sym:") never
    enter the bandit. Checked per-iteration so all-retired lands on the
    existing ALL_RETIRED terminal state."""
    ret = (cap or {}).get("retired_families", []) or []
    return any(fam == r or fam.startswith(r) for r in ret)


def _prepare_base(base_d: Dict[str, Any], cap: Dict[str, Any]) -> Dict[str, Any]:
    d = dict(base_d)
    d.setdefault("max_positions", cap.get("max_positions", 8))
    d.setdefault("flat_cost", cap.get("flat_cost_per_roundtrip", 60))
    return d


def _pilot_bars(bars: Dict[str, List], k: int) -> Dict[str, List]:
    names = sorted(bars)
    stride = max(1, len(names) // k)  # stratified: every stride-th symbol
    pick = names[::stride][:k] if len(names) > k else names
    return {s: bars[s] for s in pick}


def _pilot_or_full(cand_d: Dict[str, Any], bars: Dict[str, List], start_cash: float,
                   is_ml: bool, k: int, enabled: bool,
                   dataset_id: str = "", db_path: str | None = None) -> Dict[str, Any]:
    """Pilot gate: only structural LOW_N_IS on a stratified subset skips full.

    NEG_IS never pilot-kills (bench showed pilot NEG_IS vs full UNSTABLE:
    subset sign flips, would risk killing future winners)."""
    if not enabled or len(bars) <= k:
        from ..ml.strategies import validate_ml as _vml
        if is_ml:
            return _vml(cand_d, bars, start_cash, dataset_id=dataset_id, db_path=db_path)
        return validate_strategy(strategy_from_dict(cand_d), bars, start_cash=start_cash,
                                 dataset_id=dataset_id, db_path=db_path)
    pb = _pilot_bars(bars, k)
    from ..ml.strategies import validate_ml as _vml
    pv = (_vml(cand_d, pb, start_cash, dataset_id=dataset_id, db_path=db_path) if is_ml
          else validate_strategy(strategy_from_dict(cand_d), pb, start_cash=start_cash,
                                 dataset_id=dataset_id, db_path=db_path))
    if pv.get("verdict") == "REJECT" and pv.get("reason") == "LOW_N_IS":
        pv = dict(pv)
        pv["pilot_kill"] = True
        return pv
    return (_vml(cand_d, bars, start_cash, dataset_id=dataset_id, db_path=db_path) if is_ml
            else validate_strategy(strategy_from_dict(cand_d), bars, start_cash=start_cash,
                                   dataset_id=dataset_id, db_path=db_path))


def run_job(objective: str, base_strategy: Dict[str, Any] | None = None,
            symbols: List[str] | None = None, universe: str = "MY_RESEARCH_UNIVERSE",
            budget: int = 20, seed: int = 1, timeframe: str = "1D", dataset: str = "csv",
            db_path: str | None = None, mode: str = "day", run_id: str | None = None,
            max_hours: float = 0, seeds: List[Dict[str, Any]] | None = None,
            start: str = "", end: str = "", n: int = 252,
            pilot_symbols: int = 50, pilot_enable: bool = True) -> Dict[str, Any]:
    """budget<=0 + max_hours>0 = overnight open-ended until time cap or Ctrl-C.

    start/end/n scope the bars window (regime-scoped research, e.g. 2020–2023).
    pilot: screen-passers first validate on sorted(bars)[:pilot_symbols]; only
    pilot IS-survivors pay for the full-universe validate (3-4x saving)."""
    cap = load_capital()
    _reg = str(cap.get("cost_basis", "realistic") or "realistic")
    _rhs = ":r" if _reg == "realistic" else ":f"  # regime-keyed hashes:
    # re-evaluations under a new cost regime never collide with old rows
    syms = symbols or resolve_universe(universe) or ["RELIANCE"]
    fam_bases = [_prepare_base(s, cap) for s in (seeds or ([base_strategy] if base_strategy else []))]
    if not fam_bases:
        raise ValueError("seeds (or base_strategy) required")
    retire_after = int(cap.get("retire_after", 25))
    screened_retire_after = int(cap.get("screened_retire_after", 40))
    rid = start_run(objective, universe, mode, budget, db_path, run_id)
    seen = tested_hashes(rid, db_path)
    con0 = _con(db_path)
    try:
        seen_signals = {r[0] for r in con0.execute(
            "SELECT DISTINCT signal_hash FROM research_candidates WHERE run_id=? AND signal_hash!=''",
            (rid,)).fetchall()}
    finally:
        con0.close()
    conn = StockConnector(db_path=db_path)
    start_cash = float(cap.get("capital", 50000))
    t_setup = time.perf_counter()
    from ..constants import is_tradable as _tr
    _syms, _idx_drop = [s for s in syms if _tr(s)], sorted(s for s in syms if not _tr(s))
    bars = conn._bars({"dataset": dataset, "symbols": _syms, "n": n, "timeframe": timeframe,
                       "seed": seed, "universe": universe, "start": start, "end": end})
    data_hash, code_ver = data_fingerprint(bars), code_version()
    dataset_id = f"{dataset}:{timeframe}:{data_hash}"
    quality = getattr(conn, "_quality", {})
    if dataset != "synthetic":
        from ..data.quality import gate as _qgate
        g = _qgate(bars, cap)
        bars, quality = g["bars"], {"excluded": g["excluded"], "mixed": g["mixed"],
                                    "dropped_forming": g["dropped_forming"]}
        from ..research.liquidity import tradable_filter as _tradfilter
        bars, _untrad = _tradfilter(bars, start_cash * 0.2, cap)
        quality.update({k: v for k, v in (("untradable", _untrad),
                                          ("indices_dropped", _idx_drop)) if v})
        data_hash = data_fingerprint(bars)  # lineage covers the tradable set
        dataset_id = f"{dataset}:{timeframe}:{data_hash}"
        if not g["ok"]:
            con = _con(db_path)
            try:
                con.execute("UPDATE research_runs SET status='INSUFFICIENT_DATA' WHERE id=?", (rid,))
                con.commit()
            finally:
                con.close()
            return {"run_id": rid, "status": "INSUFFICIENT_DATA", "reason": g["reason"],
                    "quality": quality, "tested_this_session": 0, "paper_ready": 0,
                    "results": []}
    t_end = time.time() + max_hours * 3600 if max_hours > 0 else 0
    open_ended = budget <= 0
    _cap_trials = cap.get("epoch_max_trials", 30)
    _cap_trials = 30 if _cap_trials is None else int(_cap_trials)
    from .stats import trial_count as _tcount
    _prior_trials = _tcount(dataset_id, db_path)
    _override = ""
    if _prior_trials > _cap_trials:
        try:  # one-run auditable override (re-evaluation, not a fresh sweep)
            con = _con(db_path)
            try:
                _ov = con.execute("SELECT reason FROM epoch_overrides WHERE dataset_id=?"
                                  " AND (used_by IS NULL OR used_by='')",
                                  (dataset_id,)).fetchone()
                if _ov:
                    con.execute("UPDATE epoch_overrides SET used_by=? WHERE dataset_id=?",
                                (rid, dataset_id))
                    con.commit()
                    _override = str(_ov[0] or "override")
            finally:
                con.close()
        except Exception:
            pass
    if _prior_trials > _cap_trials and not _override:
        # PlanFixes3 #10: bounded hypotheses per dataset epoch (deflation
        # scales with M); fresh bars open a new epoch, not more sweeps.
        # Override explicitly via epoch_max_trials (auditable), not silently.
        con = _con(db_path)
        try:
            con.execute("UPDATE research_runs SET status='EPOCH_CAPPED' WHERE id=?", (rid,))
            con.commit()
        finally:
            con.close()
        return {"run_id": rid, "status": "EPOCH_CAPPED", "dataset_id": dataset_id,
                "reason": f"{_prior_trials} trials on {dataset_id} >= cap {_cap_trials}"
                          " (grant_epoch_override for auditable re-evaluation)",
                "tested_this_session": 0, "paper_ready": 0, "results": []}
    if dataset != "synthetic" and any(
            (s.get("meta", {}) or {}).get("family") == "ml" for s in fam_bases):
        try:  # warm shared panel once (~100s cold); all ML candidates reuse it
            from ..ml.strategies import _panel_rows as _warm_panel
            _warm_panel(bars)
        except Exception:
            pass
    _flush_time(rid, 0, "_setup", "-", "SETUP",
                {"iter_start": t_setup, "recorded": time.perf_counter()})
    results, i, status = [], 0, "COMPLETE"
    _hist: List[float] = []  # run population for median shrinkage
    try:  # seed progression survives budget refunds (Q7): step counts every
        con = _con(db_path)  # attempt, i counts only budget-consuming trials
        try:
            _d0 = con.execute("SELECT done FROM research_runs WHERE id=?", (rid,)).fetchone()
            step = int((_d0 or [0])[0])
        finally:
            con.close()
    except Exception:
        step = 0
    elites: Dict[str, Dict] = {}
    try:
        for b in best_candidates(rid, 20, db_path, _reg):
            try:
                d = json.loads(b["strategy_json"])
                fam = family_of(d)
                if fam not in elites:
                    # resume seeds raw score_is (median unknown cross-run;
                    # in-loop comparisons use shrunk keys consistently)
                    elites[fam] = {"strategy_json": b["strategy_json"],
                                   "_score": (b.get("score_is")
                                              if b.get("score_is") is not None else -1e18),
                                   "_tries": 0}
            except Exception:
                pass
    except Exception:
        pass
    live_fams = list(range(len(fam_bases)))
    try:
        while open_ended or i < budget:
            if t_end and time.time() > t_end:
                status = "PAUSED_TIME"
                break
            live_fams = [f for f in live_fams
                         if family_rejects(rid, family_of(fam_bases[f]), db_path) < retire_after
                         and family_stalls(rid, family_of(fam_bases[f]), db_path) < screened_retire_after
                         and not _fam_retired(family_of(fam_bases[f]), cap)]
            if not live_fams:
                status = "ALL_RETIRED"
                break
            from .allocate import choose as _choose, family_stats as _fstats
            from .allocate import novelty_kind as _nkind
            ts = {"iter_start": time.perf_counter()}
            rng = random.Random(seed + step)
            live_names = [family_of(fam_bases[f]) for f in live_fams]
            stats = _fstats(rid, sorted(set(live_names)), db_path, _reg)
            fam_pick, mode, novelty = _choose(sorted(set(live_names)), stats, cap, rng)
            fi = rng.choice([f for f in live_fams if family_of(fam_bases[f]) == fam_pick])
            base_d = fam_bases[fi]
            fam = family_of(base_d)
            is_ml = (base_d.get("meta", {}) or {}).get("family") == "ml"
            kinds = ML_MUTATIONS if is_ml else MUTATIONS
            if novelty:
                kind = _nkind(is_ml, rng)
            elif mode == "exploit" and is_ml:
                # PlanFixes3 #4: exploit searches structure/regularisation
                # only; execution knobs (top_n/exit/hold/position) are fixed
                # once — neighbour fitness diffs sit inside noise
                kind = rng.choice(("features", "model", "depth"))
            else:
                kind = rng.choice(kinds)
            if novelty:
                mode = "explore-novelty"
            elite = elites.get(fam)
            parent_d = base_d
            if mode == "exploit" and elite is not None:
                try:
                    parent_d = json.loads(elite["strategy_json"])
                    elite["_tries"] = elite.get("_tries", 0) + 1
                except Exception:
                    pass
            if mode == "exploit" and elite is not None and elite.get("_tries", 0) >= 3:
                # stale elite: force a structural move, not another knob tweak
                kind = _nkind(is_ml, rng)
            elif mode == "validate" and elite is not None:
                try:
                    parent_d = json.loads(elite["strategy_json"])
                    kind = "validate"
                except Exception:
                    pass
            if mode == "validate" and elite is not None:
                cand_d = dict(parent_d)  # re-emit elite unchanged (stability check)
            elif i == 0 and elite is None:
                cand_d = dict(parent_d)
            else:
                cand_d = mutate_ml(parent_d, seed + step, kind) if is_ml else \
                    mutate(strategy_from_dict(parent_d), seed + step, kind).to_dict()
            h, fam_now = _hash(cand_d) + _rhs, family_of(cand_d)
            if h in seen and mode == "validate":
                # elite already tested: fall back to exploit-mutate, don't burn budget
                cand_d = mutate_ml(parent_d, seed + step + 999, kind if kind != "validate" else None) if is_ml else \
                    mutate(strategy_from_dict(parent_d), seed + step + 999, None).to_dict()
                h, fam_now, kind = _hash(cand_d) + _rhs, family_of(cand_d), "exploit-fallback"
            if mode != "validate":
                # duplicate retries: bounded seed bumps before burning budget
                # on a DUPLICATE record (sweep-7 wasted 11/20 this way)
                from .dedup import seen_global as _sg
                _att = 0
                while (h in seen or _sg(h, db_path)) and _att < 5:
                    _att += 1
                    _rk = ("features" if (is_ml and _att >= 3)
                           else (kind if kind in (kinds or ()) else None))
                    cand_d = mutate_ml(parent_d, seed + step + 997 * _att, _rk) if is_ml else \
                        mutate(strategy_from_dict(parent_d), seed + step + 997 * _att, _rk).to_dict()
                    h, fam_now = _hash(cand_d) + _rhs, family_of(cand_d)
                    if not is_ml:  # same signal stream = same idea: keep bumping
                        try:
                            _rsig = signal_fingerprint(cand_d, bars)
                            if _rsig and _rsig in seen_signals:
                                continue
                        except Exception:
                            pass
            i += 1
            step += 1  # every attempt advances seed progression, refund or not
            ts["mutated"] = time.perf_counter()
            from .dedup import seen_global as _seen_global, record_dup as _record_dup
            if h in seen or _seen_global(h, db_path):
                seen.add(h)
                results.append(_record_dup(rid, h, cand_d, fam_now, kind, mode, db_path,
                                           data_hash, code_ver, dataset_id, seed + step, _reg))
                _flush_time(rid, i, cand_d.get("name", "?"), kind, "DUPLICATE", ts)
                i -= 1  # Q7: revisits don't consume budget (SPACE_EXHAUSTED bounds loops)
                if len(results) >= 10 and sum(
                        1 for r in results[-10:] if r.get("verdict") == "DUPLICATE") / 10 > 0.3:
                    status = "SPACE_EXHAUSTED"  # structural space exhausted,
                    break  # distinct from learning stalls (retire_after counts REJECTs)
                continue
            seen.add(h)
            from .firewall import fingerprints as _fps, check_seal_binding as _sealbind
            from .alpha_screen import screen as alpha_gate
            _fp = _fps(cand_d, seed + step, dataset_id, data_hash, code_ver)
            _prov = (_fp["feature_set_hash"], _fp["model_config_hash"],
                     _fp["random_seed"], _fp["dataset_id"])
            # P15 behavioral dedup: identical signal stream = redundant (symbolic only; cheap)
            _sigfp = ""
            if not is_ml:
                try:
                    _sigfp = signal_fingerprint(cand_d, bars)
                except Exception:
                    pass
            if _sigfp and _sigfp in seen_signals:
                _record(rid, h, cand_d, fam_now, kind, "DUPLICATE",
                        None, None, 0.0, db_path, data_hash, code_ver, *_prov, _sigfp,
                        eval_regime=_reg)
                results.append({"strategy": cand_d.get("name"), "mutation": kind,
                                "verdict": "DUPLICATE", "alloc": mode,
                                "avg_net": None, "oos_net": None, "summary": ""})
                _flush_time(rid, i, cand_d.get("name", "?"), kind, "DUPLICATE", ts)
                i -= 1  # Q7: revisits don't consume budget
                if len(results) >= 10 and sum(
                        1 for r in results[-10:] if r.get("verdict") == "DUPLICATE") / 10 > 0.3:
                    status = "SPACE_EXHAUSTED"
                    break
                continue
            if _sigfp:
                seen_signals.add(_sigfp)
            _reason = _sealbind(cand_d, data_hash, code_ver)
            if _reason:
                _record(rid, h, cand_d, fam_now, kind, "REJECT",
                        None, None, 0.0, db_path, data_hash, code_ver, *_prov, _sigfp,
                        eval_regime=_reg)
                results.append({"strategy": cand_d.get("name"), "mutation": kind,
                                "verdict": "REJECT", "reason": _reason, "alloc": mode,
                                "avg_net": None, "oos_net": None, "summary": ""})
                _flush_time(rid, i, cand_d.get("name", "?"), kind, "REJECT", ts)
                continue
            ts["gated"] = time.perf_counter()
            ag = alpha_gate(cand_d, bars, cap)
            ts["alpha"] = time.perf_counter()
            if not ag["pass"]:
                _record(rid, h, cand_d, fam_now, kind, "SCREENED",
                        None, None, 0.0, db_path, data_hash, code_ver, *_prov, _sigfp,
                        eval_regime=_reg)
                results.append({"strategy": cand_d.get("name"), "mutation": kind,
                                "verdict": "SCREENED", "avg_net": None, "alloc": mode,
                                "oos_net": None, "summary": f"alpha_gate {ag['metrics']}"[:150]})
                _flush_time(rid, i, cand_d.get("name", "?"), kind, "SCREENED", ts)
                continue
            from .stage1 import ic_screen as _ics  # stage 1: signal-level IC,
            _st1 = _ics(cand_d, bars, is_ml, cap)  # no exits/costs; sim only on survivors
            ts["stage1"] = time.perf_counter()
            if not _st1["pass"]:
                _record(rid, h, cand_d, fam_now, kind, "SCREENED",
                        None, None, 0.0, db_path, data_hash, code_ver, *_prov, _sigfp,
                        eval_regime=_reg)
                results.append({"strategy": cand_d.get("name"), "mutation": kind,
                                "verdict": "SCREENED", "avg_net": None, "alloc": mode,
                                "oos_net": None,
                                "summary": f"stage1_ic { {k: _st1.get(k) for k in ('mean_ic', 't_nw', 'n_dates', 'spread_bps')} }"[:150]})
                _flush_time(rid, i, cand_d.get("name", "?"), kind, "SCREENED", ts)
                continue
            from ..ml.strategies import quick_screen, validate_ml
            scr = quick_screen(cand_d, bars, start_cash,
                               min_trades=int(cap.get("screen_min_trades", 3)),
                               min_avg_net=float(cap.get("screen_min_avg_net", -30.0)))
            ts["screen"] = time.perf_counter()
            if not scr["pass"]:
                _record(rid, h, cand_d, fam_now, kind, "SCREENED",
                        scr["avg_net"], None, 0.0, db_path, data_hash, code_ver, *_prov, _sigfp,
                        eval_regime=_reg)
                results.append({"strategy": cand_d.get("name"), "mutation": kind,
                                "verdict": "SCREENED", "avg_net": scr["avg_net"], "alloc": mode,
                                "oos_net": None, "summary": ""})
                _flush_time(rid, i, cand_d.get("name", "?"), kind, "SCREENED", ts)
                continue
            if is_ml:
                v = _pilot_or_full(cand_d, bars, start_cash, True, pilot_symbols,
                                   pilot_enable, dataset_id, db_path)
            else:
                v = _pilot_or_full(cand_d, bars, start_cash, False, pilot_symbols,
                                   pilot_enable, dataset_id, db_path)
            ts["validated"] = time.perf_counter()
            if v.get("verdict") == "REJECT" and v.get("reason"):
                cand_d = dict(cand_d)  # surface gate in ledger strategy_json
                cand_d["meta"] = {**(cand_d.get("meta") or {}),
                                  "reject_reason": str(v["reason"])[:24]}
            if v.get("verdict") == "REJECT" and v.get("reason") in ("NEG_IS", "NEG_OOS") and not v.get("pilot_kill"):
                from ..research.capital_ladder import suggest_and_confirm as _ladder
                _sug = _ladder(cand_d, v, bars, is_ml, start_cash, cap)
                if _sug.get("suggested_min_capital"):
                    cand_d["meta"] = {**(cand_d.get("meta") or {}), **_sug}
            ts["ladder"] = time.perf_counter()
            if v.get("verdict") == "PAPER_READY" and v.get("seal"):
                cand_d = dict(cand_d)
                _seal = dict(v["seal"])
                _seal.update({"data_hash": data_hash, "code_version": code_ver,
                              "dataset_id": dataset_id})  # P13: seal binds data+code
                cand_d["meta"] = {**(cand_d.get("meta") or {}), "oos_seal": _seal}
            oos = v.get("locked_oos") or {}
            try:  # score_is/n_is feed the resume rank (defect: raw avg_net couldn't)
                from .scoring import score_is as _score_is0
                _isr0 = _score_is0(cand_d, v, cap) or {}
                _is0, _in0 = _isr0.get("score"), ((_isr0.get("breakdown") or {}).get("n")) or 0
            except Exception:
                _is0, _in0 = None, 0
            _record(rid, h, cand_d, fam_now, kind, v.get("verdict"),
                    (v.get("backtest") or {}).get("avg_net_per_trade"),
                    oos.get("avg_net_per_trade"), v.get("robustness"), db_path,
                    data_hash, code_ver, *_prov,
                    score_is=_is0, n_is=_in0, eval_regime=_reg)
            exp_id = f"run_policy_mut{seed + step}" if step > 1 else "run_basic"
            params = {"strategy": cand_d, "dataset": dataset, "symbols": syms,
                      "timeframe": timeframe, "start_cash": start_cash}
            try:
                if is_ml:
                    from ..ml.strategies import ml_signals, ml_exits
                    sigs = ml_signals(cand_d, bars,
                                      live_from=(v.get("locked_oos") or {}).get("from", ""))
                    from ..backtest.engine import run_backtest
                    r = run_backtest(ml_exits(cand_d), bars, start_cash=start_cash, signals=sigs)
                    summary = json.dumps({"ml": True, "metrics": {k: r.get(k) for k in
                                          ("n", "avg_net_per_trade", "net_profit")}})[:200]
                else:
                    summary = conn.run_and_extract(params, exp_id)
            except Exception as e:
                summary = f"error: {e}"
            ts["backtest"] = time.perf_counter()
            results.append({"strategy": cand_d.get("name"), "mutation": kind,
                            "verdict": v.get("verdict"), "alloc": mode,
                            "avg_net": (v.get("backtest") or {}).get("avg_net_per_trade"),
                            "oos_net": oos.get("avg_net_per_trade"),
                            "score": ((v.get("research_score") or {}).get("score")),
                            "summary": summary[:150]})
            ts["recorded"] = time.perf_counter()
            _flush_time(rid, i, cand_d.get("name", "?"), kind,
                        v.get("verdict") or "?", ts)
            score = ((v.get("research_score") or {}).get("score")
                     if (v.get("research_score") or {}).get("score") is not None
                     else (oos.get("avg_net_per_trade") or -1e18))
            try:  # elites rank pre-OOS only (OOS-ranked elites fit the seal)
                from .scoring import score_is as _score_is
                _isr = _score_is(cand_d, v, cap) or {}
                is_score = _isr.get("score")
                _in = ((_isr.get("breakdown") or {}).get("n")) or 0
                # shrunk toward the run median (round-2 defect: shrinking raw
                # toward zero ranked low-n losers above measured losers)
                _hist.append(float(is_score) if is_score is not None else 0.0)
                _med = sorted(_hist)[len(_hist) // 2]
                elite_key = (_med + (is_score - _med) * _in / (_in + 25)
                             if is_score is not None else -1e18)
            except Exception:
                elite_key = -1e18
            cur = elites.get(fam_now)
            if cur is None or elite_key > (cur.get("_score") or -1e18):
                elites[fam_now] = {"strategy_json": json.dumps(cand_d),
                                   "_score": elite_key, "_tries": 0}
    except KeyboardInterrupt:
        status = "PAUSED_USER"
    con = _con(db_path)
    try:
        con.execute("UPDATE research_runs SET status=? WHERE id=?", (status, rid))
        con.commit()
        done = con.execute("SELECT done FROM research_runs WHERE id=?", (rid,)).fetchone()[0]
    finally:
        con.close()
    ready = [r for r in results if r["verdict"] == "PAPER_READY"]
    try:  # every batch lands in-kernel for future retrieval (best-effort)
        from ..kernel_bridge import register_episode_finding
        register_episode_finding(episode_summary(rid, db_path))
    except Exception:
        pass
    return {"run_id": rid, "status": status, "tested_this_session": len(results),
            "tested_total": done, "paper_ready": len(ready), "capital": start_cash,
            "quality": quality, "seed": seed, "data_hash": data_hash,
            "code_version": code_ver, "dataset_id": dataset_id,
            "epoch_override": _override,
            "universe_snapshot_hash": _snaphash(syms),            "retired": [family_of(fam_bases[f]) for f in range(len(fam_bases)) if f not in live_fams],
            "best": sorted(results, key=lambda r: (r.get("score") if r.get("score") is not None else (r.get("oos_net") or -1e18)))[-3:],
            "results": results}


def _record(run_id: str, h: str, d: Dict, fam: str, kind: str, verdict: str | None,
            avg_net: Any, oos_net: Any, robustness: Any, db_path: str | None,
            data_hash: str = "", code_version: str = "",
            feature_set_hash: str = "", model_config_hash: str = "",
            random_seed: str = "", dataset_id: str = "", signal_hash: str = "",
            score_is: Any = None, n_is: Any = None, eval_regime: str = "") -> None:
    con = _con(db_path)
    try:
        con.execute("INSERT OR IGNORE INTO research_candidates(run_id,strategy_hash,"
                    "strategy_json,parent,mutation,verdict,avg_net,oos_net,robustness,family,"
                    "created_at,data_hash,code_version,feature_set_hash,model_config_hash,"
                    "random_seed,dataset_id,signal_hash,score_is,n_is,eval_regime)"
                    " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (run_id, h, json.dumps(d), (d.get("meta", {}) or {}).get("parent", d.get("name")),
                     kind, verdict, avg_net, oos_net, robustness, fam, _now(),
                     data_hash, code_version, feature_set_hash, model_config_hash,
                     random_seed, dataset_id, signal_hash, score_is, n_is, eval_regime))
        con.execute("UPDATE research_runs SET done=done+1 WHERE id=?", (run_id,))
        con.commit()
    finally:
        con.close()


def episode_summary(run_id: str, db_path: str | None = None) -> Dict[str, Any]:
    """P17: one compact aggregate per research episode (<1KB) for the kernel.

    The PIE loop orchestrates episodes; the domain engine burns thousands of
    cheap deterministic evals internally and returns only this summary, so
    1,000 candidates never become 1,000 LLM workflow cycles.
    """
    from collections import Counter
    con = _con(db_path)
    try:
        r = con.execute("SELECT objective,universe,mode,budget,done,status FROM research_runs"
                        " WHERE id=?", (run_id,)).fetchone()
        if not r:
            return {"error": "unknown run"}
        rows = con.execute("SELECT verdict,family,strategy_json FROM research_candidates"
                           " WHERE run_id=?", (run_id,)).fetchall()
    finally:
        con.close()
    import json as _j
    ready = []
    for v, f, sj in rows:
        if v == "PAPER_READY":
            try:
                ready.append(_j.loads(sj).get("name", "?"))
            except Exception:
                ready.append("?")
    return {"episode": run_id, "objective": r[0], "universe": r[1], "mode": r[2],
            "budget": r[3], "tested": r[4], "status": r[5],
            "verdicts": dict(Counter(v for v, _, _ in rows)),
            "families": dict(Counter((f or "?") for _, f, _ in rows)),
            "paper_ready": ready[:10], "n_paper_ready": len(ready)}


def run_status(run_id: str, db_path: str | None = None) -> Dict[str, Any]:
    con = _con(db_path)
    try:
        r = con.execute("SELECT objective,universe,mode,budget,done,status FROM research_runs"
                        " WHERE id=?", (run_id,)).fetchone()
        if not r:
            return {"error": "unknown run"}
        ready = con.execute("SELECT COUNT(*) FROM research_candidates WHERE run_id=? AND verdict='PAPER_READY'",
                            (run_id,)).fetchone()[0]
        return {"run_id": run_id, "objective": r[0], "universe": r[1], "mode": r[2],
                "budget": r[3], "tested": r[4], "status": r[5], "paper_ready": ready}
    finally:
        con.close()
