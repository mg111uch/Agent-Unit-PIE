"""Resumable research: families compete via adaptive bandit, screen cheap, retire the dead.

- Seeds: base strategies (symbolic + ML). Allocator weights families by prior ×
  success-rate + exploration bonus (research/allocate.py); explore/exploit/validate split.
- Screen: alpha gate + 1 cheap backtest; only passers pay for full validation (locked OOS).
- Retirement: a family with `retire_after` consecutive REJECTs stops spawning.
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
                   LEDGER_ALTER5, LEDGER_ALTER6, LEDGER_ALTER7, LEDGER_ALTER8):
        try:
            con.execute(_alter)
        except Exception:
            pass
    return con


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


def best_candidates(run_id: str, limit: int = 5, db_path: str | None = None) -> List[Dict]:
    con = _con(db_path)
    try:
        cols = ["strategy_json", "parent", "mutation", "verdict", "avg_net", "oos_net"]
        rows = con.execute(f"SELECT {','.join(cols)} FROM research_candidates WHERE run_id=?"
                           " AND verdict NOT IN ('SCREENED','DUPLICATE') ORDER BY COALESCE(oos_net,-1e18) DESC LIMIT ?",
                           (run_id, limit,)).fetchall()
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


def _prepare_base(base_d: Dict[str, Any], cap: Dict[str, Any]) -> Dict[str, Any]:
    d = dict(base_d)
    d.setdefault("max_positions", cap.get("max_positions", 8))
    d.setdefault("flat_cost", cap.get("flat_cost_per_roundtrip", 60))
    return d


def run_job(objective: str, base_strategy: Dict[str, Any] | None = None,
            symbols: List[str] | None = None, universe: str = "MY_RESEARCH_UNIVERSE",
            budget: int = 20, seed: int = 1, timeframe: str = "1D", dataset: str = "csv",
            db_path: str | None = None, mode: str = "day", run_id: str | None = None,
            max_hours: float = 0, seeds: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    """budget<=0 + max_hours>0 = overnight open-ended until time cap or Ctrl-C."""
    cap = load_capital()
    syms = symbols or resolve_universe(universe) or ["RELIANCE"]
    fam_bases = [_prepare_base(s, cap) for s in (seeds or ([base_strategy] if base_strategy else []))]
    if not fam_bases:
        raise ValueError("seeds (or base_strategy) required")
    retire_after = int(cap.get("retire_after", 25))
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
    bars = conn._bars({"dataset": dataset, "symbols": syms, "n": 252, "timeframe": timeframe,
                       "seed": seed, "universe": universe})
    data_hash, code_ver = data_fingerprint(bars), code_version()
    dataset_id = f"{dataset}:{timeframe}:{data_hash}"
    quality = getattr(conn, "_quality", {})
    if dataset != "synthetic":
        from ..data.quality import gate as _qgate
        g = _qgate(bars, cap)
        bars, quality = g["bars"], {"excluded": g["excluded"], "mixed": g["mixed"],
                                    "dropped_forming": g["dropped_forming"]}
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
    results, i, status = [], 0, "COMPLETE"
    elites: Dict[str, Dict] = {}
    try:
        for b in best_candidates(rid, 20, db_path):
            try:
                d = json.loads(b["strategy_json"])
                fam = family_of(d)
                if fam not in elites:
                    elites[fam] = {"strategy_json": b["strategy_json"],
                                   "_score": b.get("oos_net") or -1e18}
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
                         if family_rejects(rid, family_of(fam_bases[f]), db_path) < retire_after]
            if not live_fams:
                status = "ALL_RETIRED"
                break
            from .allocate import choose as _choose, family_stats as _fstats
            from .allocate import novelty_kind as _nkind
            rng = random.Random(seed + i)
            live_names = [family_of(fam_bases[f]) for f in live_fams]
            stats = _fstats(rid, sorted(set(live_names)), db_path)
            fam_pick, mode, novelty = _choose(sorted(set(live_names)), stats, cap, rng)
            fi = rng.choice([f for f in live_fams if family_of(fam_bases[f]) == fam_pick])
            base_d = fam_bases[fi]
            fam = family_of(base_d)
            is_ml = (base_d.get("meta", {}) or {}).get("family") == "ml"
            kinds = ML_MUTATIONS if is_ml else MUTATIONS
            kind = _nkind(is_ml, rng) if novelty else rng.choice(kinds)
            if novelty:
                mode = "explore-novelty"
            elite = elites.get(fam)
            parent_d = base_d
            if mode == "exploit" and elite is not None:
                try:
                    parent_d = json.loads(elite["strategy_json"])
                except Exception:
                    pass
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
                cand_d = mutate_ml(parent_d, seed + i, kind) if is_ml else \
                    mutate(strategy_from_dict(parent_d), seed + i, kind).to_dict()
            h, fam_now = _hash(cand_d), family_of(cand_d)
            if h in seen and mode == "validate":
                # elite already tested: fall back to exploit-mutate, don't burn budget
                cand_d = mutate_ml(parent_d, seed + i + 999, kind if kind != "validate" else None) if is_ml else \
                    mutate(strategy_from_dict(parent_d), seed + i + 999, None).to_dict()
                h, fam_now, kind = _hash(cand_d), family_of(cand_d), "exploit-fallback"
            i += 1
            if h in seen:
                continue
            seen.add(h)
            from .firewall import fingerprints as _fps, check_seal_binding as _sealbind
            from .alpha_screen import screen as alpha_gate
            _fp = _fps(cand_d, seed + i, dataset_id, data_hash, code_ver)
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
                        None, None, 0.0, db_path, data_hash, code_ver, *_prov, _sigfp)
                results.append({"strategy": cand_d.get("name"), "mutation": kind,
                                "verdict": "DUPLICATE", "alloc": mode,
                                "avg_net": None, "oos_net": None, "summary": ""})
                continue
            if _sigfp:
                seen_signals.add(_sigfp)
            _reason = _sealbind(cand_d, data_hash, code_ver)
            if _reason:
                _record(rid, h, cand_d, fam_now, kind, "REJECT",
                        None, None, 0.0, db_path, data_hash, code_ver, *_prov, _sigfp)
                results.append({"strategy": cand_d.get("name"), "mutation": kind,
                                "verdict": "REJECT", "reason": _reason, "alloc": mode,
                                "avg_net": None, "oos_net": None, "summary": ""})
                continue
            ag = alpha_gate(cand_d, bars, cap)
            if not ag["pass"]:
                _record(rid, h, cand_d, fam_now, kind, "SCREENED",
                        None, None, 0.0, db_path, data_hash, code_ver, *_prov, _sigfp)
                results.append({"strategy": cand_d.get("name"), "mutation": kind,
                                "verdict": "SCREENED", "avg_net": None, "alloc": mode,
                                "oos_net": None, "summary": f"alpha_gate {ag['metrics']}"[:150]})
                continue
            from ..ml.strategies import quick_screen, validate_ml
            scr = quick_screen(cand_d, bars, start_cash,
                               min_trades=int(cap.get("screen_min_trades", 3)),
                               min_avg_net=float(cap.get("screen_min_avg_net", -30.0)))
            if not scr["pass"]:
                _record(rid, h, cand_d, fam_now, kind, "SCREENED",
                        scr["avg_net"], None, 0.0, db_path, data_hash, code_ver, *_prov, _sigfp)
                results.append({"strategy": cand_d.get("name"), "mutation": kind,
                                "verdict": "SCREENED", "avg_net": scr["avg_net"], "alloc": mode,
                                "oos_net": None, "summary": ""})
                continue
            if is_ml:
                v = validate_ml(cand_d, bars, start_cash)
            else:
                v = validate_strategy(strategy_from_dict(cand_d), bars, start_cash=start_cash)
            if v.get("verdict") == "PAPER_READY" and v.get("seal"):
                cand_d = dict(cand_d)
                _seal = dict(v["seal"])
                _seal.update({"data_hash": data_hash, "code_version": code_ver,
                              "dataset_id": dataset_id})  # P13: seal binds data+code
                cand_d["meta"] = {**(cand_d.get("meta") or {}), "oos_seal": _seal}
            oos = v.get("locked_oos") or {}
            _record(rid, h, cand_d, fam_now, kind, v.get("verdict"),
                    (v.get("backtest") or {}).get("avg_net_per_trade"),
                    oos.get("avg_net_per_trade"), v.get("robustness"), db_path,
                    data_hash, code_ver, *_prov)
            exp_id = f"run_policy_mut{seed + i}" if i > 1 else "run_basic"
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
            results.append({"strategy": cand_d.get("name"), "mutation": kind,
                            "verdict": v.get("verdict"), "alloc": mode,
                            "avg_net": (v.get("backtest") or {}).get("avg_net_per_trade"),
                            "oos_net": oos.get("avg_net_per_trade"),
                            "score": ((v.get("research_score") or {}).get("score")),
                            "summary": summary[:150]})
            score = ((v.get("research_score") or {}).get("score")
                     if (v.get("research_score") or {}).get("score") is not None
                     else (oos.get("avg_net_per_trade") or -1e18))
            cur = elites.get(fam_now)
            if cur is None or score > (cur.get("_score") or -1e18):
                elites[fam_now] = {"strategy_json": json.dumps(cand_d), "_score": score}
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
    return {"run_id": rid, "status": status, "tested_this_session": len(results),
            "tested_total": done, "paper_ready": len(ready), "capital": start_cash,
            "quality": quality, "seed": seed, "data_hash": data_hash,
            "code_version": code_ver, "dataset_id": dataset_id,
            "universe_snapshot_hash": _snaphash(syms),            "retired": [family_of(fam_bases[f]) for f in range(len(fam_bases)) if f not in live_fams],
            "best": sorted(results, key=lambda r: (r.get("score") if r.get("score") is not None else (r.get("oos_net") or -1e18)))[-3:],
            "results": results}


def _record(run_id: str, h: str, d: Dict, fam: str, kind: str, verdict: str | None,
            avg_net: Any, oos_net: Any, robustness: Any, db_path: str | None,
            data_hash: str = "", code_version: str = "",
            feature_set_hash: str = "", model_config_hash: str = "",
            random_seed: str = "", dataset_id: str = "", signal_hash: str = "") -> None:
    con = _con(db_path)
    try:
        con.execute("INSERT OR IGNORE INTO research_candidates(run_id,strategy_hash,"
                    "strategy_json,parent,mutation,verdict,avg_net,oos_net,robustness,family,"
                    "created_at,data_hash,code_version,feature_set_hash,model_config_hash,"
                    "random_seed,dataset_id,signal_hash) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (run_id, h, json.dumps(d), (d.get("meta", {}) or {}).get("parent", d.get("name")),
                     kind, verdict, avg_net, oos_net, robustness, fam, _now(),
                     data_hash, code_version, feature_set_hash, model_config_hash,
                     random_seed, dataset_id, signal_hash))
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
