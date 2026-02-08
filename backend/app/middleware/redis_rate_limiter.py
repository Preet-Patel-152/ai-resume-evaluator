from fastapi import HTTPException, Request
from redis.asyncio import Redis
import os

LUA_SCRIPT = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
end
local ttl = redis.call('TTL', KEYS[1])
return {current, ttl}
"""


class RedisRateLimiter:
    def __init__(self, redis: Redis, max_requests: int, window_seconds: int):
        self.redis = redis
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    def _get_ip(self, request: Request) -> str:
        xff = request.headers.get("x-forwarded-for")
        if xff:
            return xff.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def check_rate_limit(self, request: Request):
        ip = self._get_ip(request)
        key = f"rate_limit:{ip}:{request.url.path}"

        try:
            current, ttl = await self.redis.eval(
                LUA_SCRIPT,
                1,
                key,
                str(self.window_seconds)
            )

            if int(current) > self.max_requests:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "Rate limit exceeded",
                        "retry_after": max(int(ttl), 0)
                    }
                )

        except HTTPException:
            raise
        except Exception:
            # FAIL OPEN → Redis down should NOT crash API
            return
