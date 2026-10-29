"""
ImmunoGrid — Standardized API Response Models
Consistent response format across all endpoints.
"""

from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel
from datetime import datetime

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""
    success: bool = True
    data:    Optional[T] = None
    message: str = "OK"
    timestamp: str = ""

    def __init__(self, **kwargs):
        if "timestamp" not in kwargs:
            kwargs["timestamp"] = datetime.utcnow().isoformat()
        super().__init__(**kwargs)


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated list response."""
    items:    List[T]
    total:    int
    page:     int = 1
    per_page: int = 20
    pages:    int = 1
    timestamp: str = ""

    def __init__(self, **kwargs):
        if "timestamp" not in kwargs:
            kwargs["timestamp"] = datetime.utcnow().isoformat()
        if "pages" not in kwargs and "total" in kwargs and "per_page" in kwargs:
            import math
            kwargs["pages"] = max(1, math.ceil(kwargs["total"] / kwargs["per_page"]))
        super().__init__(**kwargs)


class ErrorResponse(BaseModel):
    """Standard error response."""
    success: bool = False
    error:   str
    detail:  Optional[str] = None
    code:    int = 400
    timestamp: str = ""

    def __init__(self, **kwargs):
        if "timestamp" not in kwargs:
            kwargs["timestamp"] = datetime.utcnow().isoformat()
        super().__init__(**kwargs)


class HealthResponse(BaseModel):
    """System health check response."""
    status:    str
    version:   str
    timestamp: str
    services:  dict
    uptime_hours: Optional[float] = None
