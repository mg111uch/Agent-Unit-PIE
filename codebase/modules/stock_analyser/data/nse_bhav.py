"""NSE end-of-day archives -> SQLite.  Stdlib-only network code (urllib); no new dependency.

One file per day (sec_bhavdata_full_DDMMYYYY.csv) carries OHLC + volume + trades + DELIVERABLE qty/% for the
whole NSE equity universe, so ingesting it also gives you (a) delivery features and (b) the Nifty-500-wide
panel you currently lack.  Participant-wise F&O OI (fao_participant_oi_DDMMYYYY.csv) gives FII/DII/Pro/Client
positioning.  Both are public NSE archive files; NSE rate-limits bulk pulls and has changed URL layouts before
(circulars in 2024 and mid-2026), so: raw files are archived to disk, fetch is resumable, and parsing is
tolerant to column renames.  NOT validated against a live NSE response from the authoring sandbox (NSE hosts
are outside its network allow-list) -- run `python -m data.nse_bhav probe` first.
"""
from __future__ import annotations

import io
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

BHAV_URLS = [
    "https://nsearchives.nseindia.com/products/content/sec_bhavdata_full_{d}.csv",
    "https://archives.nseindia.com/products/content/sec_bhavdata_full_{d}.csv",
]
PART_OI_URLS = [
    "https://nsearchives.nseindia.com/content/nsccl/fao_participant_oi_{d}.csv",
    "https://archives.nseindia.com/content/nsccl/fao_participant_oi_{d}.csv",
]
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36", "Accept": "*/*"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS bhav_eq(
  symbol TEXT, series TEXT, date TEXT, prev_close REAL, open REAL, high REAL, low REAL, close REAL,
  avg_price REAL, qty REAL, turnover_lacs REAL, trades REAL, deliv_qty REAL, deliv_per REAL,
  PRIMARY KEY(symbol, series, date));
CREATE INDEX IF NOT EXISTS ix_bhav_date ON bhav_eq(date);
CREATE TABLE IF NOT EXISTS part_oi(date TEXT, client TEXT, field TEXT, value REAL, PRIMARY KEY(date,client,field));
CREATE TABLE IF NOT EXISTS ingest_days(kind TEXT, date TEXT, status TEXT, PRIMARY KEY(kind,date));
"""
_COLMAP = {
    "SYMBOL": "symbol", "SERIES": "series", "DATE1": "date", "PREV_CLOSE": "prev_close", "OPEN_PRICE": "open",
    "HIGH_PRICE": "high", "LOW_PRICE": "low", "CLOSE_PRICE": "close", "AVG_PRICE": "avg_price",
    "TTL_TRD_QNTY": "qty", "TURNOVER_LACS": "turnover_lacs", "NO_OF_TRADES": "trades",
    "DELIV_QTY": "deliv_qty", "DELIV_PER": "deliv_per",
}


def parse_bhav(text: str) -> pd.DataFrame:
    df = pd.read_csv(io.StringIO(text), skipinitialspace=True)
    df.columns = [c.strip().upper() for c in df.columns]
    df = df.rename(columns=_COLMAP)
    keep = [v for v in _COLMAP.values() if v in df.columns]
    df = df[keep].copy()
    for c in keep:
        if c not in ("symbol", "series", "date"):
            df[c] = pd.to_numeric(df[c].astype(str).str.strip().replace({"-": None, "": None}), errors="coerce")
    df["symbol"] = df["symbol"].str.strip()
    df["series"] = df["series"].str.strip()
    df["date"] = pd.to_datetime(df["date"].astype(str).str.strip(), format="%d-%b-%Y", errors="coerce").dt.strftime("%Y-%m-%d")
    return df[(df["series"] == "EQ") & df["date"].notna()].reset_index(drop=True)


def parse_part_oi(text: str, day: str) -> pd.DataFrame:
    lines = text.strip().splitlines()
    df = pd.read_csv(io.StringIO("\n".join(lines[1:])), skipinitialspace=True)  # line 0 is a title row
    df.columns = [c.strip() for c in df.columns]
    ctype = df.columns[0]
    long = df.melt(id_vars=[ctype], var_name="field", value_name="value").rename(columns={ctype: "client"})
    long["client"] = long["client"].astype(str).str.strip()
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    long["date"] = day
    return long.dropna(subset=["value"])[["date", "client", "field", "value"]]


def _get(urls, d: str, timeout=30):
    """Return (text|None, status) with status in {'ok','404','blocked'}.
    Only an all-404 outcome means "holiday / not published"; 403/429/network errors are 'blocked' and must be
    retried on a later run (never recorded as MISSING, or a throttle would silently punch holes in history)."""
    blocked = False
    for u in urls:
        req = urllib.request.Request(u.format(d=d), headers=UA)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "replace"), "ok"
        except urllib.error.HTTPError as e:
            if e.code == 404:
                continue
            blocked = True
            time.sleep(5)
        except (urllib.error.URLError, TimeoutError):
            blocked = True
            time.sleep(2)
    return None, ("blocked" if blocked else "404")


def ingest_text(con, kind: str, iso: str, txt: str) -> int:
    """Parse one day's raw file and upsert.  Separated from network code so it is unit-testable."""
    if kind == "bhav":
        df = parse_bhav(txt)
        cols = ["symbol", "series", "date", "prev_close", "open", "high", "low", "close", "avg_price", "qty", "turnover_lacs", "trades", "deliv_qty", "deliv_per"]
        for c in cols:
            if c not in df:
                df[c] = None
        con.executemany(
            "INSERT OR REPLACE INTO bhav_eq VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            df[cols].astype(object).where(df[cols].notna(), None).itertuples(index=False, name=None),
        )
    else:
        df = parse_part_oi(txt, iso)
        con.executemany("INSERT OR REPLACE INTO part_oi VALUES(?,?,?,?)", df.itertuples(index=False, name=None))
    con.execute("INSERT OR REPLACE INTO ingest_days VALUES(?,?,?)", (kind, iso, "OK"))
    return len(df)


def backfill(db: str, start: date, end: date, raw_dir="data/raw_nse", sleep=0.5, kinds=("bhav", "part_oi")):
    con = sqlite3.connect(db)
    con.executescript(SCHEMA)
    raw = Path(raw_dir)
    raw.mkdir(parents=True, exist_ok=True)
    done = {(k, d) for k, d in con.execute("SELECT kind,date FROM ingest_days")}
    d = start
    while d <= end:
        if d.weekday() < 5:
            iso, stamp = d.isoformat(), d.strftime("%d%m%Y")
            for kind, urls in (("bhav", BHAV_URLS), ("part_oi", PART_OI_URLS)):
                if kind not in kinds or (kind, iso) in done:
                    continue
                txt, status = _get(urls, stamp)
                if status == "blocked":
                    time.sleep(30)  # throttled: leave undone, next run retries
                    continue
                if txt is None:
                    con.execute("INSERT OR REPLACE INTO ingest_days VALUES(?,?,?)", (kind, iso, "MISSING"))  # holiday / not published
                else:
                    p = raw / f"{kind}_{stamp}.csv"
                    p.write_text(txt)
                    try:
                        if txt[:2] == "PK":  # zip payload (NSE format change) — quarantine, don't crash loop
                            raise ValueError("zip-payload")
                        ingest_text(con, kind, iso, txt)
                    except Exception:
                        p.rename(p.with_suffix(".bad"))
                        con.execute("INSERT OR REPLACE INTO ingest_days VALUES(?,?,?)", (kind, iso, "BAD"))
                con.commit()
                time.sleep(sleep)
        d += timedelta(days=1)
    con.close()


def load_bhav(db: str, symbols=None) -> pd.DataFrame:
    con = sqlite3.connect(db)
    q = "SELECT * FROM bhav_eq WHERE series='EQ'"
    df = pd.read_sql_query(q, con, parse_dates=["date"])
    con.close()
    return df if symbols is None else df[df["symbol"].isin(symbols)]


if __name__ == "__main__":  # python -m data.nse_bhav probe | backfill DB YYYY-MM-DD YYYY-MM-DD
    if sys.argv[1] == "probe":
        d = date.today() - timedelta(days=1)
        while d.weekday() >= 5:
            d -= timedelta(days=1)
        txt, status = _get(BHAV_URLS, d.strftime("%d%m%Y"))
        print("bhav status:", status, "| cols:", (txt or "").splitlines()[:1])
    elif sys.argv[1] == "backfill":
        backfill(sys.argv[2], datetime.fromisoformat(sys.argv[3]).date(), datetime.fromisoformat(sys.argv[4]).date())
