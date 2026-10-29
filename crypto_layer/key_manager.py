"""
ImmunoGrid — PQC Key Lifecycle Manager
Manages the full lifecycle of post-quantum cryptographic keys:
- Key generation for each device
- Key rotation scheduling
- Key distribution to devices
- Key revocation on compromise
- Key audit trail on blockchain
"""

import hashlib
import json
import secrets
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)


class KeyStatus(Enum):
    ACTIVE   = "active"
    ROTATING = "rotating"
    REVOKED  = "revoked"
    EXPIRED  = "expired"


@dataclass
class KeyRecord:
    """A single PQC key pair record."""
    key_id: str
    entity_id: str          # device or server ID
    algorithm: str          # Kyber512, Dilithium2, etc.
    key_type: str           # "kem" or "signing"
    public_key_hash: str    # SHA-256 of public key (not the key itself)
    created_at: str
    expires_at: str
    status: KeyStatus = KeyStatus.ACTIVE
    rotated_from: Optional[str] = None   # Previous key_id
    revoke_reason: Optional[str] = None


class PQCKeyManager:
    """
    Post-Quantum Cryptographic Key Lifecycle Manager.

    Manages KEM (Kyber) and Signing (Dilithium) keys for all
    IoT devices and backend services in ImmunoGrid.

    Key rotation policy:
    - IoT devices: rotate every 90 days
    - Backend services: rotate every 30 days
    - Emergency rotation on compromise: immediate
    """

    KEM_ROTATION_DAYS     = 90
    SIGNING_ROTATION_DAYS = 90
    SERVICE_ROTATION_DAYS = 30

    def __init__(self):
        self.key_store: Dict[str, KeyRecord] = {}          # key_id → KeyRecord
        self.entity_keys: Dict[str, List[str]] = {}        # entity_id → [key_ids]
        self.rotation_schedule: Dict[str, str] = {}        # entity_id → next_rotation_date
        self.total_keys_generated = 0
        self.total_rotations = 0
        self.total_revocations = 0

        logger.info("pqc_key_manager_initialized")

    def generate_keypair(
        self,
        entity_id: str,
        algorithm: str = "Kyber512",
        key_type: str = "kem",
        rotation_days: int = 90,
    ) -> KeyRecord:
        """Generate a new PQC key pair for an entity."""
        import uuid
        key_id = f"KEY-{hashlib.sha256(f'{entity_id}{algorithm}{uuid.uuid4()}'.encode()).hexdigest()[:16].upper()}"

        # Simulate key generation (real: use liboqs)
        fake_public_key = secrets.token_bytes(32)
        public_key_hash = hashlib.sha256(fake_public_key).hexdigest()

        now = datetime.utcnow()
        expires = now + timedelta(days=rotation_days)

        record = KeyRecord(
            key_id=key_id,
            entity_id=entity_id,
            algorithm=algorithm,
            key_type=key_type,
            public_key_hash=public_key_hash,
            created_at=now.isoformat(),
            expires_at=expires.isoformat(),
        )

        self.key_store[key_id] = record
        if entity_id not in self.entity_keys:
            self.entity_keys[entity_id] = []
        self.entity_keys[entity_id].append(key_id)

        # Set rotation schedule
        self.rotation_schedule[entity_id] = expires.isoformat()

        self.total_keys_generated += 1
        logger.info(
            "keypair_generated",
            key_id=key_id,
            entity_id=entity_id,
            algorithm=algorithm,
            expires=expires.date().isoformat(),
        )
        return record

    def rotate_key(self, entity_id: str, reason: str = "scheduled") -> KeyRecord:
        """Rotate keys for an entity — generate new, mark old as rotating."""
        # Find current active key
        old_key_id = None
        old_record = None
        for kid in reversed(self.entity_keys.get(entity_id, [])):
            r = self.key_store.get(kid)
            if r and r.status == KeyStatus.ACTIVE:
                old_key_id = kid
                old_record = r
                break

        # Generate new key
        algo = old_record.algorithm if old_record else "Kyber512"
        ktype = old_record.key_type if old_record else "kem"
        new_record = self.generate_keypair(entity_id, algo, ktype)
        new_record.rotated_from = old_key_id

        # Mark old key as rotating (grace period for in-flight messages)
        if old_record:
            old_record.status = KeyStatus.ROTATING

        self.total_rotations += 1

        logger.info(
            "key_rotated",
            entity_id=entity_id,
            old_key=old_key_id,
            new_key=new_record.key_id,
            reason=reason,
        )
        return new_record

    def revoke_key(self, key_id: str, reason: str) -> bool:
        """Immediately revoke a key (on device compromise)."""
        record = self.key_store.get(key_id)
        if not record:
            return False

        record.status = KeyStatus.REVOKED
        record.revoke_reason = reason
        self.total_revocations += 1

        # Immediately rotate the entity's keys
        self.rotate_key(record.entity_id, reason=f"emergency_after_revoke: {reason}")

        logger.warning(
            "key_revoked",
            key_id=key_id,
            entity_id=record.entity_id,
            reason=reason,
        )
        return True

    def get_active_key(self, entity_id: str, key_type: str = "kem") -> Optional[KeyRecord]:
        """Get the current active key for an entity."""
        for kid in reversed(self.entity_keys.get(entity_id, [])):
            r = self.key_store.get(kid)
            if r and r.status == KeyStatus.ACTIVE and r.key_type == key_type:
                return r
        return None

    def check_expiring_keys(self, warning_days: int = 14) -> List[KeyRecord]:
        """Return all keys expiring within warning_days."""
        cutoff = datetime.utcnow() + timedelta(days=warning_days)
        expiring = []
        for record in self.key_store.values():
            if record.status == KeyStatus.ACTIVE:
                exp = datetime.fromisoformat(record.expires_at)
                if exp <= cutoff:
                    expiring.append(record)
        return expiring

    def bulk_provision(self, device_ids: List[str]) -> Dict[str, List[KeyRecord]]:
        """
        Provision KEM + signing keys for a list of devices.
        Called during city bootstrap.
        """
        provisioned = {}
        for device_id in device_ids:
            kem_key  = self.generate_keypair(device_id, "Kyber512",    "kem",     self.KEM_ROTATION_DAYS)
            sign_key = self.generate_keypair(device_id, "Dilithium2",  "signing", self.SIGNING_ROTATION_DAYS)
            provisioned[device_id] = [kem_key, sign_key]

        logger.info("bulk_provisioned", count=len(device_ids))
        return provisioned

    def get_audit_log(self) -> List[Dict]:
        """Return full key audit log — for blockchain recording."""
        return [
            {
                "key_id":      r.key_id,
                "entity_id":   r.entity_id,
                "algorithm":   r.algorithm,
                "key_type":    r.key_type,
                "pk_hash":     r.public_key_hash[:16] + "...",
                "created_at":  r.created_at,
                "expires_at":  r.expires_at,
                "status":      r.status.value,
                "rotated_from": r.rotated_from,
            }
            for r in self.key_store.values()
        ]

    def get_stats(self) -> Dict:
        status_counts: Dict[str, int] = {}
        for r in self.key_store.values():
            s = r.status.value
            status_counts[s] = status_counts.get(s, 0) + 1

        expiring = len(self.check_expiring_keys(14))

        return {
            "total_keys": len(self.key_store),
            "entities_managed": len(self.entity_keys),
            "status_breakdown": status_counts,
            "total_generated": self.total_keys_generated,
            "total_rotations": self.total_rotations,
            "total_revocations": self.total_revocations,
            "keys_expiring_14d": expiring,
        }
