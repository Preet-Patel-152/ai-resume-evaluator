
from fastapi import HTTPException, Request
from collections import defaultdict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class RateLimiter:

    def __init__(self, max_requests: int = 10, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
        logger.info(
            f"Rate limiter initialized: {max_requests} requests per {window_seconds}s")

    async def check_rate_limit(self, request: Request):
        client_ip = request.client.host if request.client else "unknown"
        now = datetime.utcnow()

        # Clean up old requests outside the time window
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if now - req_time < timedelta(seconds=self.window_seconds)
        ]

        # Check if limit exceeded
        current_count = len(self.requests[client_ip])

        if current_count >= self.max_requests:
            logger.warning(
                f"Rate limit exceeded for {client_ip}: "
                f"{current_count}/{self.max_requests} requests"
            )
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {self.max_requests} requests allowed per hour",
                    "retry_after": self.window_seconds
                }
            )

        # Add current request to tracking
        self.requests[client_ip].append(now)
        logger.debug(
            f"Request tracked for {client_ip}: {current_count + 1}/{self.max_requests}")

    def get_remaining_requests(self, client_ip: str) -> int:
        now = datetime.utcnow()

        # Clean old requests
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if now - req_time < timedelta(seconds=self.window_seconds)
        ]

        current_count = len(self.requests[client_ip])
        return max(0, self.max_requests - current_count)
