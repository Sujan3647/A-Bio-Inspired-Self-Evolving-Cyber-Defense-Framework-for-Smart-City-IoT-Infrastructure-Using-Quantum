"""
ImmunoGrid — PQC Certificate Manager
Manages post-quantum digital certificates for IoT devices.

A PQC certificate is a self-describing credential that binds:
- Device identity (device_id + sector)
- Quantum fingerprint hash (behavioral DNA)
- Dilithium-2 public key (signing)
- Kyber-512 public key (encryption)
- Validity period + issuer

Replaces X.509 certificates with PQC-safe equivalents.
"""

import hashlib
import json
import secrets
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class PQCCertificate:
    """Post-Quantum Cryptographic certificate for an IoT device."""
    cert_id:           str
    device_id:         str
    sector:            str
    issuer:            str            # "ImmunoGrid-CA"
    subject:           str            # "CN=device_id, O=sector"
    kyber_pubkey_hash: str            # SHA-256 of Kyber-512 public key
    dilithium_pubkey_hash: str        # SHA-256 of Dilithium-2 public key
    fp_hash:           str            # Quantum behavioral fingerprint hash
    valid_from:        str
    valid_until:       str
    serial_number:     str
    cert_hash:         str = ""       # Hash of whole cert (integrity)
    revoked:           bool = False
    revoke_reason:     Optional[str] = None

    def compute_hash(self) -> str:
        data = json.dumps({
            "cert_id": self.cert_id,
            "device_id": self.device_id,
            "kyber": self.kyber_pubkey_hash,
            "dilithium": self.dilithium_pubkey_hash,
            "fp": self.fp_hash,
            "valid_from": self.valid_from,
            "valid_until": self.valid_until,
        }, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()

    def is_valid(self) -> bool:
        if self.revoked:
            return False
        now = datetime.utcnow()
        valid_from  = datetime.fromisoformat(self.valid_from)
        valid_until = datetime.fromisoformat(self.valid_until)
        return valid_from <= now <= valid_until

    def days_until_expiry(self) -> int:
        until = datetime.fromisoformat(self.valid_until)
        delta = until - datetime.utcnow()
        return max(0, delta.days)

    def to_dict(self) -> Dict:
        return asdict(self)


class PQCCertificateManager:
    """
    Issues, validates, and manages PQC certificates for IoT devices.

    Certificate lifecycle:
    1. Issue    — create cert with device keys + fingerprint
    2. Validate — check expiry, revocation, key match
    3. Rotate   — issue new cert when nearing expiry
    4. Revoke   — mark cert as invalid (on compromise)
    5. CRL      — Certificate Revocation List query
    """

    DEFAULT_VALIDITY_DAYS = 90
    WARNING_DAYS          = 14   # Warn when expiring within 14 days
    ISSUER                = "ImmunoGrid-CA"

    def __init__(self):
        self.cert_store:  Dict[str, PQCCertificate] = {}    # cert_id → cert
        self.device_certs: Dict[str, str] = {}              # device_id → cert_id
        self.crl:         List[str] = []                    # revoked cert_ids
        self.issued_count  = 0
        self.revoked_count = 0
        logger.info("pqc_cert_manager_initialized")

    def issue_certificate(
        self,
        device_id:           str,
        sector:              str,
        kyber_pubkey:        bytes,
        dilithium_pubkey:    bytes,
        fp_hash:             str = "",
        validity_days:       int = DEFAULT_VALIDITY_DAYS,
    ) -> PQCCertificate:
        """Issue a new PQC certificate for a device."""
        self.issued_count += 1
        cert_id = f"CERT-{hashlib.sha256(f'{device_id}{datetime.utcnow()}'.encode()).hexdigest()[:16].upper()}"
        serial  = secrets.token_hex(8).upper()
        now     = datetime.utcnow()
        until   = now + timedelta(days=validity_days)

        cert = PQCCertificate(
            cert_id=cert_id,
            device_id=device_id,
            sector=sector,
            issuer=self.ISSUER,
            subject=f"CN={device_id},O={sector},L=SmartCity",
            kyber_pubkey_hash=hashlib.sha256(kyber_pubkey).hexdigest(),
            dilithium_pubkey_hash=hashlib.sha256(dilithium_pubkey).hexdigest(),
            fp_hash=fp_hash or hashlib.sha256(device_id.encode()).hexdigest(),
            valid_from=now.isoformat(),
            valid_until=until.isoformat(),
            serial_number=serial,
        )
        cert.cert_hash = cert.compute_hash()

        self.cert_store[cert_id]      = cert
        self.device_certs[device_id]  = cert_id

        logger.info(
            "cert_issued",
            cert_id=cert_id,
            device_id=device_id,
            expires=until.date().isoformat(),
        )
        return cert

    def validate_certificate(
        self,
        cert_id:          str,
        kyber_pubkey:     bytes,
        dilithium_pubkey: bytes,
    ) -> Dict[str, Any]:
        """Validate a certificate — check expiry, revocation, key match."""
        if cert_id not in self.cert_store:
            return {"valid": False, "reason": "Certificate not found"}

        cert = self.cert_store[cert_id]

        # Check revocation
        if cert.revoked or cert_id in self.crl:
            return {"valid": False, "reason": f"Certificate revoked: {cert.revoke_reason}"}

        # Check expiry
        if not cert.is_valid():
            return {"valid": False, "reason": "Certificate expired"}

        # Check key match
        if hashlib.sha256(kyber_pubkey).hexdigest() != cert.kyber_pubkey_hash:
            return {"valid": False, "reason": "Kyber key mismatch — possible IMPOSTOR"}

        if hashlib.sha256(dilithium_pubkey).hexdigest() != cert.dilithium_pubkey_hash:
            return {"valid": False, "reason": "Dilithium key mismatch"}

        # Verify cert integrity
        if cert.compute_hash() != cert.cert_hash:
            return {"valid": False, "reason": "Certificate tampered"}

        return {
            "valid":          True,
            "reason":         "Valid",
            "cert_id":        cert_id,
            "device_id":      cert.device_id,
            "days_remaining": cert.days_until_expiry(),
            "expires":        cert.valid_until[:10],
        }

    def get_device_certificate(self, device_id: str) -> Optional[PQCCertificate]:
        """Get the current certificate for a device."""
        cert_id = self.device_certs.get(device_id)
        if cert_id:
            return self.cert_store.get(cert_id)
        return None

    def revoke_certificate(self, cert_id: str, reason: str) -> bool:
        """Revoke a certificate."""
        cert = self.cert_store.get(cert_id)
        if not cert:
            return False
        cert.revoked      = True
        cert.revoke_reason = reason
        self.crl.append(cert_id)
        self.revoked_count += 1
        logger.warning("cert_revoked", cert_id=cert_id, device=cert.device_id, reason=reason)
        return True

    def rotate_certificate(
        self,
        device_id:        str,
        new_kyber_pubkey: bytes,
        new_dilithium_pubkey: bytes,
        fp_hash:          str = "",
    ) -> Optional[PQCCertificate]:
        """Rotate a device's certificate — revoke old, issue new."""
        old_cert_id = self.device_certs.get(device_id)
        if old_cert_id:
            self.revoke_certificate(old_cert_id, "scheduled_rotation")

        old_cert = self.cert_store.get(old_cert_id) if old_cert_id else None
        sector   = old_cert.sector if old_cert else "unknown"

        new_cert = self.issue_certificate(
            device_id, sector, new_kyber_pubkey, new_dilithium_pubkey, fp_hash
        )
        logger.info("cert_rotated", device_id=device_id, new_cert=new_cert.cert_id)
        return new_cert

    def check_expiring_certificates(self, warning_days: int = 14) -> List[PQCCertificate]:
        """Return list of certificates expiring within warning_days."""
        return [
            cert for cert in self.cert_store.values()
            if not cert.revoked and 0 < cert.days_until_expiry() <= warning_days
        ]

    def bulk_issue(
        self,
        devices: List[Dict[str, Any]],
        validity_days: int = 90,
    ) -> List[PQCCertificate]:
        """Bulk issue certificates for many devices."""
        import os
        certs = []
        for device in devices:
            cert = self.issue_certificate(
                device_id=device["device_id"],
                sector=device.get("sector", "general"),
                kyber_pubkey=os.urandom(32),        # Simulated key
                dilithium_pubkey=os.urandom(64),    # Simulated key
                fp_hash=device.get("fp_hash", ""),
                validity_days=validity_days,
            )
            certs.append(cert)
        logger.info("bulk_certs_issued", count=len(certs))
        return certs

    def get_stats(self) -> Dict[str, Any]:
        valid    = sum(1 for c in self.cert_store.values() if c.is_valid())
        expiring = len(self.check_expiring_certificates(self.WARNING_DAYS))
        return {
            "total_issued":   self.issued_count,
            "currently_valid": valid,
            "revoked":        self.revoked_count,
            "expiring_soon":  expiring,
            "crl_size":       len(self.crl),
            "devices_with_certs": len(self.device_certs),
        }
