from __future__ import annotations

import time
import threading
from collections import defaultdict


class TokenBucket:
    def __init__(self, rate_per_minute: int):
        self.capacity = rate_per_minute
        self.tokens = rate_per_minute
        self.refill_rate = rate_per_minute / 60.0
        self.last_refill = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self) -> bool:
        with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
            self.last_refill = now
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False


class RateLimiter:
    def __init__(self):
        self._llm_buckets: dict[str, TokenBucket] = {}
        self._write_buckets: dict[str, TokenBucket] = {}
        self._lock = threading.Lock()

    def _get_bucket(self, buckets: dict, key: str, rate: int) -> TokenBucket:
        with self._lock:
            if key not in buckets:
                buckets[key] = TokenBucket(rate)
            return buckets[key]

    def check_llm(self, user_id: str, rate: int) -> bool:
        return self._get_bucket(self._llm_buckets, user_id, rate).acquire()

    def check_write(self, user_id: str, rate: int) -> bool:
        return self._get_bucket(self._write_buckets, user_id, rate).acquire()
