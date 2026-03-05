import hashlib
import os


def _hash_ip(ip: str) -> str:
    salt = os.getenv("IP_HASH_SALT", "")
    return hashlib.sha256(f"{salt}{ip}".encode()).hexdigest()[:16]


async def log_event(event: str, ip: str | None, redis) -> None:
    """
    Track usage stats in Redis. Never stores raw IPs.
    - stats:total_requests     → total grader uses (int)
    - stats:unique_ips         → approximate unique visitors (HyperLogLog)
    - stats:per_ip             → Hash of { ip_hash: count }
    """
    try:
        ip_hash = _hash_ip(ip) if ip else "unknown"

        await redis.incr("stats:total_requests")
        await redis.pfadd("stats:unique_ips", ip_hash)
        await redis.hincrby("stats:per_ip", ip_hash, 1)
    except Exception:
        # analytics must NEVER crash the app
        return
