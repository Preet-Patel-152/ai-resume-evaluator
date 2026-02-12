import os
from redis.asyncio import Redis

_redis = None


def get_redis() -> Redis:
    global _redis
    if _redis is None:
        _redis = Redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            decode_responses=True
        )
    return _redis


# this file is for any direct redis interactions we want to do outside of the rate limiter,
# like caching llm responses, or storing analytics data, etc.
