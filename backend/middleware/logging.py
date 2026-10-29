"""
ImmunoGrid — Request Logging Middleware
Logs all API requests with timing, user info, and security metadata.
"""

import time
import uuid
from fastapi import Request
import structlog

logger = structlog.get_logger("immunogrid.api")


async def request_logging_middleware(request: Request, call_next):
    """Log every request with timing and context."""
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()

    # Extract user from Authorization header (if present)
    auth_header = request.headers.get("Authorization", "")
    user_hint = "anonymous"
    if auth_header.startswith("Bearer "):
        # Just log first 8 chars of token — not the full token
        user_hint = f"token:{auth_header[7:15]}..."

    logger.info(
        "api_request",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        client=request.client.host if request.client else "unknown",
        user=user_hint,
    )

    response = await call_next(request)

    duration_ms = round((time.time() - start_time) * 1000, 2)

    logger.info(
        "api_response",
        request_id=request_id,
        status_code=response.status_code,
        duration_ms=duration_ms,
        path=request.url.path,
    )

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{duration_ms}ms"
    return response
