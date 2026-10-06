import os, sqlite3, sys, tempfile, time
import numpy as np, pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from research.horizon_ic import horizon_scan, newey_west_t
from research.null_ic import perm_null, power_ic
from research.events import event_study
from research.event_prep import adj_price_wide, artifact_days, event_date_from_disclosure, net_bulk_deals
from data.nse_bhav import SCHEMA, ingest_text, parse_bhav
from features.flows import build_flow_features, FLOW_FEATS
from ml.freeze import freeze_ridge, load_ridge


def make_panel(n_sym=100, n_days=800, effect=0.0004, seed=0):
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2019-01-01", periods=n_days)
    z = np.zeros((n_days, n_sym)); z[0] = rng.standard_normal(n_sym)
    for t in range(1, n_days):
        z[t] = 0.97 * z[t - 1] + np.sqrt(1 - 0.97**2) * rng.standard_normal(n_sym)
    mkt = 0.01 * rng.standard_normal(n_days)[:, None]
    ret = np.zeros((n_days, n_sym))
    ret[1:] = effect * z[:-1] + mkt[1:] + 0.015 * rng.standard_normal((n_days - 1, n_sym))
    close = 100 * np.exp(np.cumsum(ret, axis=0))
    f1 = z + rng.standard_normal(z.shape)
    f2, f3 = rng.standard_normal(z.shape), rng.standard_normal(z.shape)
    syms = [f"S{i:03d}" for i in range(n_sym)]
    return pd.DataFrame({
        "date": np.repeat(dates, n_sym), "symbol": np.tile(syms, n_days), "close": close.ravel(),
        "f1": f1.ravel(), "f2": f2.ravel(), "f3": f3.ravel()})


def test_horizon_scan_signal_vs_null():
    sig = horizon_scan(make_panel(effect=0.0004), ["f1", "f2", "f3"], horizons=(5, 20, 60), refit_every=63)
    nul = horizon_scan(make_panel(effect=0.0, seed=1), ["f1", "f2", "f3"], horizons=(5, 20, 60), refit_every=63)
    print("\nSIGNAL\n", sig[["n_indep", "ic_mean", "t_nw_h", "t_naive_lag1", "t_nonoverlap", "long_top_n_bps", "be_ic"]].round(3))
    print("NULL\n", nul[["n_indep", "ic_mean", "t_nw_h", "t_naive_lag1", "t_nonoverlap"]].round(3))
    assert (sig["ic_mean"] > 0.02).all() and sig.loc[20, "t_nw_h"] > 2.0          # finds planted slow signal
    assert (nul["t_nw_h"].abs() < 3.0).all()                                      # honest t does not hallucinate on null
    # the HAC lag matters: naive lag-1 t is inflated vs horizon-matched lag at long horizons
    assert (sig.loc[60, "t_naive_lag1"] > sig.loc[60, "t_nw_h"] * 1.5)


def test_block_null_calibrates_long_horizon():
    """pure-noise panel at h=60: naive-iid permutation null is too narrow; block null restores calibration"""
    nul, sc = horizon_scan(make_panel(effect=0.0, seed=1), ["f1", "f2", "f3"], horizons=(60,), refit_every=63, return_scored=True)
    iid = perm_null(sc[60], lag=60, n_perm=300, block=1)
    blk = perm_null(sc[60], lag=60, n_perm=300, block=60)
    print("\nh=60 NULL panel: real t_nw", round(blk["real_t"], 2), "| iid-null t_q95", round(iid["null_t_q95"], 2), "| block-null t_q95", round(blk["null_t_q95"], 2))
    assert blk["null_t_q95"] > iid["null_t_q95"]            # block null is wider (honest)
    sig, ss = horizon_scan(make_panel(effect=0.0004), ["f1", "f2", "f3"], horizons=(20,), refit_every=63, return_scored=True)
    assert perm_null(ss[20], lag=20, n_perm=300, block=20)["p_mean"] < 0.05   # still detects real signal


def test_newey_west_inflation_on_overlap():
    rng = np.random.default_rng(0); e = rng.standard_normal(2000)
    ma = np.convolve(e, np.ones(20) / 20, "valid")                                # MA(20) like a 20d overlapping IC series
    assert abs(newey_west_t(ma, 19)) < abs(newey_west_t(ma, 1))


def test_perm_null_and_power():
    rng = np.random.default_rng(0); nd, ns = 300, 120
    dates = pd.bdate_range("2021-01-01", periods=nd); syms = [f"S{i}" for i in range(ns)]
    z = rng.standard_normal((nd, ns))
    def frame(ic):
        y = ic * z + np.sqrt(1 - ic**2) * rng.standard_normal((nd, ns))
        return pd.DataFrame({"date": np.repeat(dates, ns), "symbol": np.tile(syms, nd), "score": z.ravel(), "fwd": y.ravel()})
    real, nul = perm_null(frame(0.05), n_perm=300), perm_null(frame(0.0), n_perm=300)
    print("\nperm real", {k: round(v, 4) for k, v in real.items()}, "\nperm null", {k: round(v, 4) for k, v in nul.items()})
    assert real["p_mean"] < 0.01 and nul["p_mean"] > 0.02
    pw = power_ic(n_sym=200, n_indep=60, ics=(0.01, 0.02, 0.05), n_sim=200)
    print(pw.round(2)); assert pw[0.05] > pw[0.01] and pw[0.05] > 0.8


def test_event_study_planted_drift():
    rng = np.random.default_rng(3); n, ns = 700, 150
    dates = pd.bdate_range("2020-01-01", periods=n)
    r = 0.01 * rng.standard_normal((n, ns))
    ev = pd.DataFrame({"symbol": rng.integers(0, ns, 400), "i": rng.integers(20, n - 80, 400)}).drop_duplicates()
    for s_, i in zip(ev["symbol"], ev["i"]):
        r[i + 1: i + 41, s_] += 0.0005                                               # +2% over 40d after entry
    close = pd.DataFrame(100 * np.exp(np.cumsum(r, 0)), index=dates, columns=[f"S{i}" for i in range(ns)])
    events = pd.DataFrame({"symbol": [f"S{s}" for s in ev["symbol"]], "date": dates[ev["i"].values - 1]})
    out = event_study(events, close, horizons=(5, 40, 60), cost_bps=46)
    print("\n", out.round(3)); assert out.loc[40, "t_month_clustered"] > 3 and out.loc[40, "net_bps"] > 0
    null_ev = pd.DataFrame({"symbol": events["symbol"].values, "date": dates[rng.integers(20, n - 80, len(events))]})
    assert abs(event_study(null_ev, close, horizons=(40,)).loc[40, "t_month_clustered"]) < 3


def test_placebo_removes_selection_drift():
    """events picked from persistently-rising names (no true event effect): raw looks significant, placebo-adjusted does not"""
    rng = np.random.default_rng(11); n, ns = 900, 200
    dates = pd.bdate_range("2019-01-01", periods=n)
    drift = np.where(np.arange(ns) < 40, 0.0006, 0.0)                      # 20% of names trend up (small-cap-like)
    r = drift + 0.012 * rng.standard_normal((n, ns))
    close = pd.DataFrame(100 * np.exp(np.cumsum(r, 0)), index=dates, columns=[f"S{i}" for i in range(ns)])
    rows = [(f"S{rng.integers(0, 40)}", dates[rng.integers(30, n - 100)]) for _ in range(500)]   # only from drifting names
    ev = pd.DataFrame(rows, columns=["symbol", "date"]).drop_duplicates()
    out = event_study(ev, close, horizons=(40,), placebo_k=6, cost_bps=46)
    print("\n", out[["n", "mean_excess_bps", "t_month_clustered", "placebo_bps", "excess_vs_placebo_bps", "t_vs_placebo"]].round(2))
    assert out.loc[40, "t_month_clustered"] > 3 and abs(out.loc[40, "t_vs_placebo"]) < 2.5          # raw fooled, placebo not
    # and a TRUE effect survives the placebo adjustment
    r2 = r.copy()
    for s_, d_ in zip(ev["symbol"], ev["date"]):
        r2[dates.get_loc(d_) + 2: dates.get_loc(d_) + 42, int(s_[1:])] += 0.0006
    c2 = pd.DataFrame(100 * np.exp(np.cumsum(r2, 0)), index=dates, columns=close.columns)
    o2 = event_study(ev, c2, horizons=(40,), placebo_k=6)
    assert o2.loc[40, "t_vs_placebo"] > 3


def test_event_prep():
    rng = np.random.default_rng(0); n = 120; dates = pd.bdate_range("2024-01-01", periods=n)
    true_px = 100 * np.exp(np.cumsum(0.01 * rng.standard_normal(n)))
    raw = true_px.copy(); raw[60:] /= 2                                  # 2:1 split on day 60: raw closes halve
    prev = np.r_[raw[0], raw[:-1]]; prev[60] = raw[59] / 2                 # exchange re-bases PREV_CLOSE on the ex-date
    b = pd.DataFrame({"symbol": "AAA", "date": dates, "close": raw, "prev_close": prev})
    px = adj_price_wide(b)["AAA"]; assert abs(np.log(px.iloc[60] / px.iloc[59])) < 0.05           # continuous
    assert abs(np.log(b["close"].iloc[60] / b["close"].iloc[59])) > 0.6                           # naive close chain shows the fake -50%
    assert len(artifact_days(b.assign(close=b["close"].where(b.index != 30, b["close"] * 0.4)))) >= 1
    td = pd.bdate_range("2026-01-01", "2026-03-31")
    ts = pd.Series(pd.to_datetime(["2026-01-02 11:00", "2026-01-02 18:30", "2026-01-03 10:00"]))   # Fri am, Fri pm, Saturday
    got = event_date_from_disclosure(ts, td); assert list(got.dt.strftime("%Y-%m-%d")) == ["2026-01-02", "2026-01-05", "2026-01-05"]
    deals = pd.DataFrame({"symbol": ["X"] * 4, "date": ["2026-01-02"] * 4, "client": ["A", "A", "B", "B"],
                          "side": ["BUY", "SELL", "BUY", "BUY"], "qty": [100, 95, 50, 50]})
    nb = net_bulk_deals(deals); assert list(nb["client"]) == ["B"] and nb["side"].iloc[0] == 1


def test_ingest_parse_idempotent():
    txt = ("SYMBOL, SERIES, DATE1, PREV_CLOSE, OPEN_PRICE, HIGH_PRICE, LOW_PRICE, LAST_PRICE, CLOSE_PRICE, AVG_PRICE, "
           "TTL_TRD_QNTY, TURNOVER_LACS, NO_OF_TRADES, DELIV_QTY, DELIV_PER\n"
           "AAA, EQ, 02-Jan-2026, 100, 101, 103, 99, 102, 102.5, 101.8, 100000, 1018.0, 5000, 60000, 60.00\n"
           "BBB, BE, 02-Jan-2026, 50, 50, 51, 49, 50, 50, 50, 1000, 5.0, 40, -, -\n"
           "CCC, EQ, 02-Jan-2026, 10, 10, 11, 9, 10, 10, 10, 2000, 2.0, 80, -, -\n")
    df = parse_bhav(txt); assert list(df["symbol"]) == ["AAA", "CCC"] and df.loc[0, "deliv_per"] == 60.0 and np.isnan(df.loc[1, "deliv_per"])
    con = sqlite3.connect(":memory:"); con.executescript(SCHEMA)
    ingest_text(con, "bhav", "2026-01-02", txt); ingest_text(con, "bhav", "2026-01-02", txt)
    assert con.execute("SELECT COUNT(*) FROM bhav_eq").fetchone()[0] == 2
    oi = "Participant wise Open Interest\nClient Type, Future Index Long, Future Index Short\nFII, 100, 250\nDII, 50, 20\n"
    assert ingest_text(con, "part_oi", "2026-01-02", oi) == 4


def test_flow_features_shape_and_lookahead():
    rng = np.random.default_rng(0); n = 200
    d = pd.DataFrame({"symbol": "AAA", "date": pd.bdate_range("2025-01-01", periods=n), "close": 100 + np.cumsum(rng.standard_normal(n)),
                      "qty": rng.integers(1e5, 2e5, n), "trades": rng.integers(3e3, 6e3, n), "deliv_qty": rng.integers(3e4, 9e4, n),
                      "deliv_per": rng.uniform(30, 70, n), "turnover_lacs": rng.uniform(500, 900, n)})
    f = build_flow_features(d); assert list(f.columns) == ["date", "symbol", *FLOW_FEATS] and f[FLOW_FEATS].iloc[100:].notna().all().all()
    d2 = d.copy(); d2.loc[150:, "deliv_per"] += 40                                    # change the future...
    f2 = build_flow_features(d2)
    assert np.allclose(f.iloc[:150][FLOW_FEATS].fillna(0), f2.iloc[:150][FLOW_FEATS].fillna(0))  # ...past features unchanged


def test_freeze_roundtrip_and_tamper():
    db = tempfile.mktemp(suffix=".db")
    v = freeze_ridge(db, "ridge_rg", ["a", "b"], [0.5, -0.25], 0.1, {"trained_through": "2026-09-30"})
    assert freeze_ridge(db, "ridge_rg", ["a", "b"], [0.5, -0.25], 0.1, {"trained_through": "2026-09-30"}) == v
    v2, feats, f = load_ridge(db, "ridge_rg"); assert v2 == v and np.allclose(f([[2, 4]]), [0.5 * 2 - 0.25 * 4 + 0.1])
    con = sqlite3.connect(db); con.execute("UPDATE model_artifacts SET payload=replace(payload,'0.5','0.9')"); con.commit()
    try: load_ridge(db, "ridge_rg"); raise AssertionError("tamper not detected")
    except ValueError: pass


def test_mlp_beats_ridge_only_on_interaction():
    from ml.xs_net import mlp_scorer
    from research.horizon_ic import ridge_scorer
    rng = np.random.default_rng(5); n_d, n_s = 520, 80
    dates = pd.bdate_range("2020-01-01", periods=n_d)
    F = rng.standard_normal((n_d, n_s, 3))
    ret = np.zeros((n_d, n_s)); ret[1:] = 0.006 * F[:-1, :, 0] * F[:-1, :, 1] + 0.015 * rng.standard_normal((n_d - 1, n_s))
    close = 100 * np.exp(np.cumsum(ret, 0))
    panel = pd.DataFrame({"date": np.repeat(dates, n_s), "symbol": np.tile([f"S{i}" for i in range(n_s)], n_d), "close": close.ravel(),
                          **{f"f{k+1}": F[:, :, k].ravel() for k in range(3)}})
    kw = dict(horizons=(1,), refit_every=130, min_train_dates=260, entry_lag=0)
    t0 = time.time()
    r = horizon_scan(panel, ["f1", "f2", "f3"], scorer=ridge_scorer(), **kw)
    m = horizon_scan(panel, ["f1", "f2", "f3"], scorer=mlp_scorer(n_seeds=2, epochs=10), **kw)
    print(f"\nridge IC {r.loc[1,'ic_mean']:.4f} (t {r.loc[1,'t_nw_h']:.1f}) | mlp IC {m.loc[1,'ic_mean']:.4f} (t {m.loc[1,'t_nw_h']:.1f}) | {time.time()-t0:.0f}s")
    assert abs(r.loc[1, "ic_mean"]) < 0.02 and m.loc[1, "ic_mean"] > r.loc[1, "ic_mean"] + 0.015


if __name__ == "__main__":
    for k, v in list(globals().items()):
        if k.startswith("test_"):
            t = time.time(); v(); print(f"PASS {k} ({time.time()-t:.1f}s)")
