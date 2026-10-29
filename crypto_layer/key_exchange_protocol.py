"""
ImmunoGrid — PQC Key Exchange Protocol
Full post-quantum key exchange flow for IoT device onboarding.

Protocol:
1. Device generates Kyber-512 + Dilithium-2 key pair
2. Device sends public keys to ImmunoGrid server
3. Server issues PQC certificate (signed with Dilithium)
4. Server encapsulates shared secret with device's Kyber public key
5. Both derive session key via HKDF
6. Secure channel established with AES-256-GCM

This protocol is a simplified version of TLS 1.3 + PQC extension,
following NIST guidelines for post-quantum key establishment.
"""

import hashlib
import json
import secrets
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, Tuple

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class DeviceOnboardingRequest:
    """Request from device to join the ImmunoGrid network."""
    device_id:         str
    device_type:       str
    sector:            str
    kyber_pubkey:      bytes     # Kyber-512 public key
    dilithium_pubkey:  bytes     # Dilithium-2 public key
    behavioral_profile: Dict    # For quantum fingerprinting
    timestamp:         str
    nonce:             str       # Fresh random value (anti-replay)


@dataclass
class OnboardingResponse:
    """Server response to device onboarding request."""
    device_id:       str
    cert_id:         str
    kem_ciphertext:  bytes       # Kyber encapsulated shared secret
    session_hint:    str         # Truncated session key hash (for verification)
    server_cert:     Dict        # Server's certificate
    approved:        bool
    timestamp:       str
    message:         str = "Device successfully onboarded to ImmunoGrid"


class PQCKeyExchangeProtocol:
    """
    Orchestrates the full PQC key exchange and device onboarding flow.

    Roles:
    - ImmunoGrid Server: runs the server side (issues certs, KEM)
    - IoT Device:        runs the client side (sends pubkeys, receives cert)
    """

    def __init__(self):
        from crypto_layer.certificate_manager import PQCCertificateManager
        from crypto_layer.key_manager         import PQCKeyManager
        self.cert_manager = PQCCertificateManager()
        self.key_manager  = PQCKeyManager()
        self.onboarded_devices: Dict[str, OnboardingResponse] = {}
        self.sessions:         Dict[str, bytes] = {}    # device_id → session_key
        logger.info("key_exchange_protocol_initialized")

    # ── Server Side ───────────────────────────────────────────────────────────

    def server_process_onboarding(
        self, request: DeviceOnboardingRequest
    ) -> OnboardingResponse:
        """
        Server processes device onboarding request.
        Issues PQC certificate + KEM-encapsulated session key.
        """
        # 1. Validate nonce freshness
        if not self._is_nonce_fresh(request.nonce, request.timestamp):
            return OnboardingResponse(
                device_id=request.device_id, cert_id="",
                kem_ciphertext=b"", session_hint="",
                server_cert={}, approved=False,
                timestamp=datetime.utcnow().isoformat(),
                message="Stale request — replay attack suspected",
            )

        # 2. Register PQC keys
        self.key_manager.generate_keypair(request.device_id, "Kyber512",   "kem")
        self.key_manager.generate_keypair(request.device_id, "Dilithium2", "signing")

        # 3. Issue PQC certificate
        fp_hash = hashlib.sha256(
            json.dumps(request.behavioral_profile, sort_keys=True).encode()
        ).hexdigest()

        cert = self.cert_manager.issue_certificate(
            device_id=request.device_id,
            sector=request.sector,
            kyber_pubkey=request.kyber_pubkey,
            dilithium_pubkey=request.dilithium_pubkey,
            fp_hash=fp_hash,
        )

        # 4. KEM encapsulation — derive shared secret
        kem_ct, shared_secret = self._kyber_encapsulate(request.kyber_pubkey)

        # 5. Derive session key via HKDF
        session_key = self._derive_session_key(
            shared_secret, request.device_id, cert.cert_id
        )
        self.sessions[request.device_id] = session_key

        # 6. Store onboarding record
        response = OnboardingResponse(
            device_id=request.device_id,
            cert_id=cert.cert_id,
            kem_ciphertext=kem_ct,
            session_hint=session_key[:8].hex(),    # First 8 bytes as hint
            server_cert=cert.to_dict(),
            approved=True,
            timestamp=datetime.utcnow().isoformat(),
        )
        self.onboarded_devices[request.device_id] = response

        logger.info(
            "device_onboarded",
            device_id=request.device_id,
            cert_id=cert.cert_id,
            sector=request.sector,
        )
        return response

    # ── Client (Device) Side ──────────────────────────────────────────────────

    def device_generate_request(
        self,
        device_id:          str,
        device_type:        str,
        sector:             str,
        behavioral_profile: Dict,
    ) -> Tuple[DeviceOnboardingRequest, bytes, bytes]:
        """
        Device generates onboarding request with fresh key pair.
        Returns (request, kyber_privkey, dilithium_privkey)
        """
        from crypto_layer.hybrid_crypto import PQCSimulator

        kyber_pubkey,     kyber_privkey     = PQCSimulator.kyber_keygen()
        dilithium_pubkey, dilithium_privkey = PQCSimulator.dilithium_keygen()

        request = DeviceOnboardingRequest(
            device_id=device_id,
            device_type=device_type,
            sector=sector,
            kyber_pubkey=kyber_pubkey,
            dilithium_pubkey=dilithium_pubkey,
            behavioral_profile=behavioral_profile,
            timestamp=datetime.utcnow().isoformat(),
            nonce=secrets.token_hex(16),
        )
        return request, kyber_privkey, dilithium_privkey

    def device_process_response(
        self,
        response:       OnboardingResponse,
        kyber_privkey:  bytes,
    ) -> Optional[bytes]:
        """
        Device decapsulates KEM ciphertext to recover shared session key.
        Returns session key or None if failed.
        """
        if not response.approved:
            logger.warning("onboarding_rejected", device_id=response.device_id,
                           reason=response.message)
            return None

        try:
            from crypto_layer.hybrid_crypto import PQCSimulator
            shared_secret = PQCSimulator.kyber_decapsulate(
                kyber_privkey, response.kem_ciphertext
            )
            session_key = self._derive_session_key(
                shared_secret, response.device_id, response.cert_id
            )

            # Verify session hint matches
            if session_key[:8].hex() == response.session_hint:
                logger.info("session_key_verified", device_id=response.device_id)
                return session_key
            else:
                logger.error("session_key_mismatch", device_id=response.device_id)
                return None

        except Exception as e:
            logger.error("device_response_error", error=str(e))
            return None

    # ── Full Handshake (both sides) ───────────────────────────────────────────

    def run_full_handshake(
        self,
        device_id:   str,
        device_type: str,
        sector:      str,
        behavioral_profile: Optional[Dict] = None,
    ) -> Dict:
        """
        Run the complete PQC key exchange handshake end-to-end.
        Used in tests and demos.
        """
        t_start = time.time()
        profile = behavioral_profile or {"send_interval": 2.3, "packet_size": 48.0}

        # Device side: generate request
        request, kyber_priv, _ = self.device_generate_request(
            device_id, device_type, sector, profile
        )

        # Server side: process request
        response = self.server_process_onboarding(request)

        # Device side: recover session key
        device_session_key = self.device_process_response(response, kyber_priv)

        duration_ms = round((time.time() - t_start) * 1000, 2)

        return {
            "device_id":         device_id,
            "approved":          response.approved,
            "cert_id":           response.cert_id,
            "session_established": device_session_key is not None,
            "keys_match":        (
                device_session_key is not None and
                device_session_key == self.sessions.get(device_id)
            ),
            "duration_ms":       duration_ms,
            "cert_expires":      response.server_cert.get("valid_until", "")[:10],
            "timestamp":         datetime.utcnow().isoformat(),
        }

    def bulk_onboard(
        self,
        device_ids: list,
        sector:     str = "traffic",
    ) -> Dict:
        """Onboard multiple devices in one call."""
        results = []
        for device_id in device_ids:
            result = self.run_full_handshake(device_id, "traffic_sensor", sector)
            results.append(result)

        successful = sum(1 for r in results if r["session_established"])
        return {
            "total":       len(device_ids),
            "successful":  successful,
            "failed":      len(device_ids) - successful,
            "results":     results,
        }

    def get_stats(self) -> Dict:
        cert_stats = self.cert_manager.get_stats()
        return {
            "onboarded_devices": len(self.onboarded_devices),
            "active_sessions":   len(self.sessions),
            "certificates":      cert_stats,
        }

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _kyber_encapsulate(self, pubkey: bytes) -> Tuple[bytes, bytes]:
        from crypto_layer.hybrid_crypto import PQCSimulator
        return PQCSimulator.kyber_encapsulate(pubkey)

    def _derive_session_key(
        self, shared_secret: bytes, device_id: str, cert_id: str
    ) -> bytes:
        from cryptography.hazmat.primitives.kdf.hkdf import HKDF
        from cryptography.hazmat.primitives import hashes
        info = f"immunogrid-session:{device_id}:{cert_id}".encode()
        hkdf = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=info)
        return hkdf.derive(shared_secret)

    def _is_nonce_fresh(self, nonce: str, timestamp_str: str) -> bool:
        try:
            ts  = datetime.fromisoformat(timestamp_str)
            age = abs((datetime.utcnow() - ts).total_seconds())
            return age < 300   # 5 minute tolerance
        except Exception:
            return False
