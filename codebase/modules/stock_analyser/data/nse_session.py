"""NSE cookie-session: no API key, stdlib only (urllib + cookiejar).

NSE's WAF rejects bare API hits (403). Reproduce the browser order:
GET homepage -> keep cookies -> GET api with Referer. Re-handshake on 403.
Rate-limit: min interval between calls (NSE throttles past ~4 req/min).
"""
from __future__ import annotations
import gzip
import http.cookiejar
import json
import time
import urllib.request
from typing import Any, Dict

BASE = "https://www.nseindia.com"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
REFERER = BASE + "/option-chain"


class NseSession:
    def __init__(self, min_interval: float = 20.0, timeout: int = 15):
        self.min_interval = min_interval
        self.timeout = timeout
        self._last = 0.0
        jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
        self._handshook = False

    def _req(self, url: str, referer: str = BASE + "/") -> bytes:
        r = urllib.request.Request(url, headers={
            "User-Agent": UA, "Accept": "*/*", "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip", "Referer": referer, "Connection": "keep-alive"})
        with self.opener.open(r, timeout=self.timeout) as resp:
            raw = resp.read()
            return gzip.decompress(raw) if resp.headers.get("Content-Encoding") == "gzip" else raw

    def handshake(self) -> None:
        self._req(BASE + "/", referer=BASE + "/")
        self._handshook = True

    def get_json(self, path: str) -> Dict[str, Any]:
        """GET api path, handshake first; one re-handshake retry on failure."""
        wait = self.min_interval - (time.time() - self._last)
        if wait > 0:
            time.sleep(wait)
        if not self._handshook:
            self.handshake()
        url = BASE + path
        try:
            raw = self._req(url, referer=REFERER)
        except Exception:
            self._handshook = False
            self.handshake()
            raw = self._req(url, referer=REFERER)
        self._last = time.time()
        data = json.loads(raw.decode("utf-8", "replace"))
        if isinstance(data, dict) and "<html" in str(data.get("data", ""))[:20]:
            raise ValueError("NSE returned HTML (maintenance/block)")
        if not isinstance(data, dict) or "records" not in data:
            # retry once after fresh handshake (soft-403 can return 200 junk)
            self._handshook = False
            self.handshake()
            raw = self._req(url, referer=REFERER)
            self._last = time.time()
            data = json.loads(raw.decode("utf-8", "replace"))
        return data

    def chain_indices(self, symbol: str) -> Dict[str, Any]:
        return self.get_json(f"/api/option-chain-indices?symbol={symbol}")

    def chain_equities(self, symbol: str) -> Dict[str, Any]:
        return self.get_json(f"/api/option-chain-equities?symbol={symbol}")

    def quote_equity(self, symbol: str) -> Dict[str, Any]:
        return self.get_json(f"/api/quote-equity?symbol={symbol}")
