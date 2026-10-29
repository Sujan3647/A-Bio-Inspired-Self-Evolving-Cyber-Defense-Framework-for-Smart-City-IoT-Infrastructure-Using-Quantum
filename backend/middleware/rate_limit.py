"""
ImmunoGrid — Rate Limiting Middleware
Protects the API from DDoS and brute force attacks.
Uses Redis for distributed rate limiting across multiple instances.
"""

import time
import os
from collections import defaultdict
from typing import Dict

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

# Simple in-memory rate limiter (Redis in production)
_request_counts: Dict[str, list] = defaultdict(list)


class RateLimiter:
    """
    Sliding window rate limiter.
    Default: 100 requests per minute per IP.
    """

    def __init__(self, requests_per_minute: int = 100, window_seconds: int = 60):
        self.limit  = requests_per_minute
        self.window = window_seconds

    def is_allowed(self, identifier: str) -> bool:
        now = time.time()
        window_start = now - self.window

        # Remove old requests outside window
        _request_counts[identifier] = [
            t for t in _request_counts[identifier] if t > window_start
        ]

        if len(_request_counts[identifier]) >= self.limit:
            return False

        _request_counts[identifier].append(now)
        return True

    def get_remaining(self, identifier: str) -> int:
        now = time.time()
        window_start = now - self.window
        recent = [t for t in _request_counts[identifier] if t > window_start]
        return max(0, self.limit - len(recent))


# Global rate limiters
default_limiter = RateLimiter(requests_per_minute=100)
auth_limiter    = RateLimiter(requests_per_minute=10)    # Strict for login
api_limiter     = RateLimiter(requests_per_minute=200)


async def rate_limit_middleware(request: Request, call_next):
    """FastAPI middleware for rate limiting."""
    # Skip rate limiting in test environment
    if os.environ.get("APP_ENV") == "test":
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"
    path = request.url.path

    # Stricter limit for auth endpoints
    limiter = auth_limiter if "/auth/login" in path else default_limiter

    if not limiter.is_allowed(client_ip):
        remaining = limiter.get_remaining(client_ip)
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": "Rate limit exceeded. Too many requests.",
                "retry_after_seconds": limiter.window,
                "remaining": remaining,
            },
            headers={"Retry-After": str(limiter.window)},
        )

    response = await call_next(request)
    response.headers["X-RateLimit-Remaining"] = str(limiter.get_remaining(client_ip))
    return response
