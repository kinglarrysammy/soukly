"""Rate limiting.

- development: in-memory (per process)
- production multi-instance: Redis when REDIS_URL is set
"""
from __future__ import annotations

import os
import time
from collections import defaultdict, deque

REDIS_URL = os.environ.get("REDIS_URL", "").strip()


class MemoryRateLimiter:
    def __init__(self):
        self._hits: dict[str, deque] = defaultdict(deque)

    def allow(self, key: str, limit: int, window_sec: int) -> bool:
        now = time.time()
        q = self._hits[key]
        while q and q[0] < now - window_sec:
            q.popleft()
        if len(q) >= limit:
            return False
        q.append(now)
        return True


class RedisRateLimiter:
    def __init__(self, url: str):
        try:
            import redis  # type: ignore
        except ImportError as e:
            raise RuntimeError("REDIS_URL set but redis package not installed") from e
        self._r = redis.Redis.from_url(url, decode_responses=True)

    def allow(self, key: str, limit: int, window_sec: int) -> bool:
        rk = f"rl:{key}"
        pipe = self._r.pipeline()
        now = time.time()
        pipe.zremrangebyscore(rk, 0, now - window_sec)
        pipe.zadd(rk, {str(now): now})
        pipe.zcard(rk)
        pipe.expire(rk, window_sec + 1)
        _, _, count, _ = pipe.execute()
        return int(count) <= limit


def build_limiter():
    if REDIS_URL:
        try:
            return RedisRateLimiter(REDIS_URL)
        except Exception as e:
            print(f"[rate_limit] Redis unavailable ({e}); using memory limiter")
    return MemoryRateLimiter()


limiter = build_limiter()
