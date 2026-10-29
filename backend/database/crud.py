"""
ImmunoGrid — Database CRUD Operations
Repository layer for all database interactions.
Supports PostgreSQL (SQLAlchemy) + MongoDB + Redis.
"""

import json
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import structlog

logger = structlog.get_logger(__name__)


# ── PostgreSQL CRUD via SQLAlchemy ────────────────────────────────────────────

class UserCRUD:
    """User management database operations."""

    def __init__(self, db_session=None):
        self.db = db_session

    def get_by_email(self, email: str) -> Optional[Dict]:
        if not self.db:
            return None
        try:
            from database.models import UserDB
            user = self.db.query(UserDB).filter(UserDB.email == email).first()
            if user:
                return {
                    "id": user.id, "email": user.email,
                    "full_name": user.full_name, "role": user.role,
                    "hashed_password": user.hashed_password,
                    "ministry": user.ministry, "is_active": user.is_active,
                }
        except Exception as e:
            logger.error("db_user_get_error", error=str(e))
        return None

    def create(self, user_data: Dict) -> Optional[str]:
        if not self.db:
            return None
        try:
            import uuid
            from database.models import UserDB
            user = UserDB(
                id=str(uuid.uuid4()),
                email=user_data["email"],
                full_name=user_data["full_name"],
                role=user_data["role"],
                hashed_password=user_data["hashed_password"],
                ministry=user_data.get("ministry", ""),
                is_active=True,
                created_at=datetime.utcnow(),
            )
            self.db.add(user)
            self.db.commit()
            return user.id
        except Exception as e:
            self.db.rollback()
            logger.error("db_user_create_error", error=str(e))
        return None

    def update_last_login(self, user_id: str):
        if not self.db:
            return
        try:
            from database.models import UserDB
            self.db.query(UserDB).filter(UserDB.id == user_id).update(
                {"last_login": datetime.utcnow()}
            )
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error("db_last_login_error", error=str(e))


class DeviceCRUD:
    """IoT device database operations."""

    def __init__(self, db_session=None):
        self.db = db_session

    def upsert(self, device_data: Dict) -> bool:
        if not self.db:
            return False
        try:
            from database.models import DeviceDB
            existing = self.db.query(DeviceDB).filter(
                DeviceDB.device_id == device_data["device_id"]
            ).first()
            if existing:
                for k, v in device_data.items():
                    if hasattr(existing, k):
                        setattr(existing, k, v)
                existing.last_seen = datetime.utcnow()
            else:
                device = DeviceDB(**{
                    k: v for k, v in device_data.items()
                    if hasattr(DeviceDB, k)
                })
                device.registered_at = datetime.utcnow()
                self.db.add(device)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error("db_device_upsert_error", error=str(e))
        return False

    def get_by_sector(self, sector: str) -> List[Dict]:
        if not self.db:
            return []
        try:
            from database.models import DeviceDB
            devices = self.db.query(DeviceDB).filter(DeviceDB.sector == sector).all()
            return [{"device_id": d.device_id, "status": d.status, "sector": d.sector}
                    for d in devices]
        except Exception as e:
            logger.error("db_device_sector_error", error=str(e))
        return []

    def count_by_status(self) -> Dict[str, int]:
        if not self.db:
            return {}
        try:
            from database.models import DeviceDB
            from sqlalchemy import func
            results = self.db.query(
                DeviceDB.status, func.count(DeviceDB.device_id)
            ).group_by(DeviceDB.status).all()
            return {status: count for status, count in results}
        except Exception as e:
            logger.error("db_device_count_error", error=str(e))
        return {}


class ThreatCRUD:
    """Threat event database operations."""

    def __init__(self, db_session=None):
        self.db = db_session

    def create(self, threat_data: Dict) -> Optional[str]:
        if not self.db:
            return None
        try:
            import uuid
            from database.models import ThreatEventDB
            threat = ThreatEventDB(
                id=str(uuid.uuid4()),
                **{k: v for k, v in threat_data.items() if hasattr(ThreatEventDB, k)}
            )
            self.db.add(threat)
            self.db.commit()
            return threat.id
        except Exception as e:
            self.db.rollback()
            logger.error("db_threat_create_error", error=str(e))
        return None

    def get_recent(self, limit: int = 50, sector: Optional[str] = None) -> List[Dict]:
        if not self.db:
            return []
        try:
            from database.models import ThreatEventDB
            q = self.db.query(ThreatEventDB).order_by(
                ThreatEventDB.timestamp.desc()
            )
            if sector:
                q = q.filter(ThreatEventDB.target_sector == sector)
            threats = q.limit(limit).all()
            return [
                {"id": t.id, "attack_type": t.attack_type, "severity": t.severity,
                 "sector": t.target_sector, "timestamp": str(t.timestamp)}
                for t in threats
            ]
        except Exception as e:
            logger.error("db_threat_get_error", error=str(e))
        return []

    def count_today(self) -> int:
        if not self.db:
            return 0
        try:
            from database.models import ThreatEventDB
            today = datetime.utcnow().replace(hour=0, minute=0, second=0)
            return self.db.query(ThreatEventDB).filter(
                ThreatEventDB.timestamp >= today
            ).count()
        except Exception as e:
            logger.error("db_threat_count_error", error=str(e))
        return 0


# ── MongoDB CRUD ──────────────────────────────────────────────────────────────

class EventLogMongo:
    """
    MongoDB operations for high-volume event logs.
    PostgreSQL handles structured data; MongoDB handles raw event streams.
    """

    def __init__(self, mongo_db=None):
        self.db = mongo_db

    def insert_event(self, event: Dict) -> bool:
        if not self.db:
            return False
        try:
            event["_inserted_at"] = datetime.utcnow()
            self.db["events"].insert_one(event)
            return True
        except Exception as e:
            logger.error("mongo_insert_error", error=str(e))
        return False

    def get_events(
        self,
        collection: str = "events",
        filter_dict: Optional[Dict] = None,
        limit: int = 100,
    ) -> List[Dict]:
        if not self.db:
            return []
        try:
            cursor = self.db[collection].find(
                filter_dict or {},
                {"_id": 0}
            ).sort("_inserted_at", -1).limit(limit)
            return list(cursor)
        except Exception as e:
            logger.error("mongo_get_error", error=str(e))
        return []

    def insert_attack_record(self, record: Dict) -> bool:
        return self.insert_event({**record, "_collection": "attacks"})

    def insert_device_message(self, message: Dict) -> bool:
        return self.insert_event({**message, "_collection": "messages"})

    def get_attack_timeline(self, hours: int = 24) -> List[Dict]:
        if not self.db:
            return []
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return self.get_events(
            filter_dict={"_collection": "attacks",
                         "_inserted_at": {"$gte": cutoff}},
            limit=500,
        )


# ── Redis Cache ───────────────────────────────────────────────────────────────

class RedisCache:
    """
    Redis caching for frequently accessed data.
    - Device status cache (5 min TTL)
    - Threat summary cache (30 sec TTL)
    - Session tokens
    - Rate limiting counters
    """

    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.default_ttl = 300  # 5 minutes

    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        if not self.redis:
            return False
        try:
            serialized = json.dumps(value)
            self.redis.setex(key, ttl or self.default_ttl, serialized)
            return True
        except Exception as e:
            logger.error("redis_set_error", key=key, error=str(e))
        return False

    def get(self, key: str) -> Optional[Any]:
        if not self.redis:
            return None
        try:
            value = self.redis.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.error("redis_get_error", key=key, error=str(e))
        return None

    def delete(self, key: str) -> bool:
        if not self.redis:
            return False
        try:
            self.redis.delete(key)
            return True
        except Exception:
            return False

    def cache_device_stats(self, stats: Dict):
        self.set("device_stats", stats, ttl=300)

    def get_device_stats(self) -> Optional[Dict]:
        return self.get("device_stats")

    def cache_threat_summary(self, summary: Dict):
        self.set("threat_summary", summary, ttl=30)

    def get_threat_summary(self) -> Optional[Dict]:
        return self.get("threat_summary")

    def cache_user_session(self, user_id: str, token_hash: str, ttl: int = 1800):
        self.set(f"session:{token_hash}", {"user_id": user_id}, ttl=ttl)

    def get_user_session(self, token_hash: str) -> Optional[Dict]:
        return self.get(f"session:{token_hash}")

    def invalidate_user_sessions(self, user_id: str):
        """Invalidate all sessions for a user (on password change/revocation)."""
        if not self.redis:
            return
        try:
            keys = self.redis.keys("session:*")
            for key in keys:
                val = self.get(key.decode() if isinstance(key, bytes) else key)
                if val and val.get("user_id") == user_id:
                    self.redis.delete(key)
        except Exception as e:
            logger.error("redis_invalidate_error", error=str(e))
