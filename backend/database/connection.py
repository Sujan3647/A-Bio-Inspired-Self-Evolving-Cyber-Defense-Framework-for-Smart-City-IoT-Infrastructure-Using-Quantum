"""
ImmunoGrid — Database Connection Manager
Manages PostgreSQL, MongoDB, and Redis connections.
"""

import os
from typing import Optional
import structlog

logger = structlog.get_logger(__name__)

# ── PostgreSQL (SQLAlchemy) ───────────────────────────────────────────────────

def get_postgres_url() -> str:
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db   = os.getenv("POSTGRES_DB",   "immunogrid")
    user = os.getenv("POSTGRES_USER", "immunogrid_user")
    pw   = os.getenv("POSTGRES_PASSWORD", "immunogrid_pass")
    return f"postgresql+psycopg2://{user}:{pw}@{host}:{port}/{db}"


def get_async_postgres_url() -> str:
    return get_postgres_url().replace("postgresql+psycopg2", "postgresql+asyncpg")


# ── MongoDB ───────────────────────────────────────────────────────────────────

def get_mongo_client():
    """Get MongoDB client (lazy import to avoid startup failure)."""
    try:
        from pymongo import MongoClient
        uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/immunogrid")
        client = MongoClient(uri, serverSelectionTimeoutMS=3000)
        client.server_info()   # Ping
        logger.info("mongodb_connected")
        return client
    except Exception as e:
        logger.warning("mongodb_unavailable", error=str(e))
        return None


def get_mongo_db(db_name: str = "immunogrid"):
    client = get_mongo_client()
    if client:
        return client[db_name]
    return None


# ── Redis ─────────────────────────────────────────────────────────────────────

def get_redis_client():
    """Get Redis client."""
    try:
        import redis
        url = os.getenv("REDIS_URL", "redis://localhost:6379")
        client = redis.from_url(url, decode_responses=True, socket_timeout=2)
        client.ping()
        logger.info("redis_connected")
        return client
    except Exception as e:
        logger.warning("redis_unavailable", error=str(e))
        return None


# ── Health check ──────────────────────────────────────────────────────────────

def check_db_health() -> dict:
    """Check connectivity to all databases."""
    results = {}

    # PostgreSQL
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(get_postgres_url(), connect_args={"connect_timeout": 3})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        results["postgres"] = "connected"
    except Exception as e:
        results["postgres"] = f"unavailable: {str(e)[:40]}"

    # MongoDB
    mongo = get_mongo_client()
    results["mongodb"] = "connected" if mongo else "unavailable"

    # Redis
    redis = get_redis_client()
    results["redis"] = "connected" if redis else "unavailable"

    return results
