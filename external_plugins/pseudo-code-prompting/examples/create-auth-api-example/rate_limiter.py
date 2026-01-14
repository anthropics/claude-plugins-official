from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
import redis
from config import settings
from typing import Optional

limiter = Limiter(key_func=get_remote_address)

class RateLimitManager:
    def __init__(self):
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                socket_connect_timeout=settings.REDIS_CONNECTION_TIMEOUT,
                decode_responses=True
            )
            self.redis_client.ping()
            self.use_redis = True
        except:
            self.use_redis = False
            self.in_memory_cache = {}

    def is_rate_limited(self, key: str, limit: str) -> bool:
        """
        Check if a request exceeds rate limit
        Format: "5/minute", "3/hour", etc.
        """
        if not self.use_redis:
            return self._check_in_memory(key, limit)
        return self._check_redis(key, limit)

    def _check_redis(self, key: str, limit: str) -> bool:
        try:
            parts = limit.split('/')
            count = int(parts[0])
            period = parts[1]

            ttl_seconds = self._parse_period(period)
            redis_key = f"rate_limit:{key}"

            current = self.redis_client.incr(redis_key)
            if current == 1:
                self.redis_client.expire(redis_key, ttl_seconds)

            return current > count
        except:
            return False

    def _check_in_memory(self, key: str, limit: str) -> bool:
        """Fallback in-memory rate limiting"""
        try:
            parts = limit.split('/')
            count = int(parts[0])
            period = parts[1]

            ttl_seconds = self._parse_period(period)
            redis_key = f"rate_limit:{key}"

            if redis_key not in self.in_memory_cache:
                self.in_memory_cache[redis_key] = {"count": 0, "reset_time": 0}

            import time
            current_time = time.time()
            cache_entry = self.in_memory_cache[redis_key]

            if current_time >= cache_entry["reset_time"]:
                cache_entry["count"] = 1
                cache_entry["reset_time"] = current_time + ttl_seconds
                return False

            cache_entry["count"] += 1
            return cache_entry["count"] > count
        except:
            return False

    @staticmethod
    def _parse_period(period: str) -> int:
        if period == "minute":
            return 60
        elif period == "hour":
            return 3600
        elif period == "day":
            return 86400
        else:
            return 60

rate_limit_manager = RateLimitManager()
