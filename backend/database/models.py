"""
ImmunoGrid — SQLAlchemy Database Models
ORM models for PostgreSQL storage.
"""

from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean,
    DateTime, Text, JSON, ForeignKey, Index,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class UserDB(Base):
    __tablename__ = "users"

    id             = Column(String(36), primary_key=True)
    email          = Column(String(255), unique=True, nullable=False, index=True)
    full_name      = Column(String(255), nullable=False)
    role           = Column(String(50),  nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    ministry       = Column(String(255), nullable=True)
    department     = Column(String(255), nullable=True)
    employee_id    = Column(String(50),  nullable=True)
    is_active      = Column(Boolean,     default=True, nullable=False)
    created_at     = Column(DateTime,    default=datetime.utcnow, nullable=False)
    last_login     = Column(DateTime,    nullable=True)

    __table_args__ = (
        Index("ix_users_role_active", "role", "is_active"),
    )


class DeviceDB(Base):
    __tablename__ = "devices"

    device_id      = Column(String(100), primary_key=True)
    device_type    = Column(String(50),  nullable=False, index=True)
    sector         = Column(String(50),  nullable=False, index=True)
    location       = Column(String(100), nullable=False)
    status         = Column(String(20),  default="online", nullable=False)
    message_count  = Column(Integer,     default=0)
    attack_attempts = Column(Integer,    default=0)
    fingerprint_hash = Column(String(64), nullable=True)
    behavior_profile = Column(JSON,      nullable=True)
    registered_at  = Column(DateTime,    default=datetime.utcnow)
    last_seen      = Column(DateTime,    nullable=True)

    __table_args__ = (
        Index("ix_devices_sector_status", "sector", "status"),
    )


class ThreatEventDB(Base):
    __tablename__ = "threat_events"

    id             = Column(String(36), primary_key=True)
    attack_type    = Column(String(50),  nullable=False, index=True)
    severity       = Column(String(20),  nullable=False, index=True)
    target_device  = Column(String(100), ForeignKey("devices.device_id"), nullable=True)
    target_sector  = Column(String(50),  nullable=False, index=True)
    detected_by    = Column(String(50),  nullable=False)
    status         = Column(String(30),  default="detected")
    confidence     = Column(Float,       nullable=True)
    morphogenesis  = Column(Boolean,     default=False)
    blockchain_hash = Column(String(64), nullable=True)
    attacker_sig   = Column(JSON,        nullable=True)
    response_actions = Column(JSON,      nullable=True)
    timestamp      = Column(DateTime,    default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index("ix_threats_sector_time", "target_sector", "timestamp"),
        Index("ix_threats_type_time",   "attack_type",   "timestamp"),
    )


class BlockchainRecordDB(Base):
    __tablename__ = "blockchain_records"

    record_id      = Column(String(30),  primary_key=True)
    block_index    = Column(Integer,     nullable=False, index=True)
    attack_type    = Column(String(50),  nullable=False)
    device_id      = Column(String(100), nullable=True)
    sector         = Column(String(50),  nullable=False)
    severity       = Column(String(20),  nullable=False)
    data_hash      = Column(String(64),  nullable=False)
    block_hash     = Column(String(64),  nullable=False)
    morphogenesis  = Column(Boolean,     default=False)
    timestamp      = Column(DateTime,    default=datetime.utcnow, nullable=False, index=True)


class FLRoundDB(Base):
    __tablename__ = "fl_rounds"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    round_number   = Column(Integer, unique=True, nullable=False, index=True)
    accuracy       = Column(Float,   nullable=False)
    loss           = Column(Float,   nullable=False)
    participants   = Column(Integer, nullable=False)
    blockchain_hash = Column(String(64), nullable=True)
    imaginations   = Column(Integer, default=0)
    timestamp      = Column(DateTime, default=datetime.utcnow)


class KeyRecordDB(Base):
    __tablename__ = "key_records"

    key_id         = Column(String(40),  primary_key=True)
    entity_id      = Column(String(100), nullable=False, index=True)
    algorithm      = Column(String(30),  nullable=False)
    key_type       = Column(String(20),  nullable=False)
    public_key_hash = Column(String(64), nullable=False)
    status         = Column(String(20),  default="active", nullable=False)
    rotated_from   = Column(String(40),  nullable=True)
    created_at     = Column(DateTime,    default=datetime.utcnow)
    expires_at     = Column(DateTime,    nullable=False)

    __table_args__ = (
        Index("ix_keys_entity_status", "entity_id", "status"),
    )


class AuditLogDB(Base):
    __tablename__ = "audit_logs"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    user_id        = Column(String(36), nullable=True, index=True)
    action         = Column(String(100), nullable=False)
    resource       = Column(String(100), nullable=True)
    ip_address     = Column(String(45),  nullable=True)
    user_agent     = Column(String(255), nullable=True)
    success        = Column(Boolean,     default=True)
    details        = Column(JSON,        nullable=True)
    timestamp      = Column(DateTime,    default=datetime.utcnow, nullable=False, index=True)
