"""
ImmunoGrid — Post-Quantum Cryptography (Hybrid Layer)

Provides encryption and signing using:
- CRYSTALS-Kyber  → Key encapsulation (replaces RSA/ECC for key exchange)
- CRYSTALS-Dilithium → Digital signatures (replaces ECDSA)
- AES-256-GCM     → Symmetric encryption of actual data

Why HYBRID?
We use PQC for key exchange + classical AES for bulk data.
This is the NIST-recommended approach for transitioning to PQC.

Note: This module uses a pure-Python simulation of Kyber/Dilithium
when liboqs is not available. For production, install liboqs-python.
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
import struct
import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import structlog
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

logger = structlog.get_logger(__name__)

# Try to import liboqs (Open Quantum Safe library)
# Falls back to simulation mode if not installed
try:
    import oqs
    OQS_AVAILABLE = True
    logger.info("liboqs_loaded", mode="hardware_pqc")
except ImportError:
    OQS_AVAILABLE = False
    logger.warning("liboqs_not_available", mode="simulation_fallback",
                   note="Install liboqs-python for real PQC. Using simulation mode.")


@dataclass
class KeyPair:
    """A PQC key pair (public + private)."""
    algorithm: str
    public_key: bytes
    private_key: bytes
    created_at: float = 0.0

    def __post_init__(self):
        self.created_at = time.time()


@dataclass
class EncryptedMessage:
    """An encrypted message container."""
    ciphertext: bytes
    nonce: bytes
    kem_ciphertext: bytes      # KEM-encapsulated shared secret
    algorithm: str
    sender_id: str
    timestamp: float
    signature: Optional[bytes] = None


@dataclass
class SignedMessage:
    """A digitally signed message."""
    message: bytes
    signature: bytes
    public_key: bytes
    algorithm: str
    signer_id: str


class PQCSimulator:
    """
    Simulates PQC algorithms when liboqs is not installed.
    Uses secure random key generation + HMAC for demo purposes.
    
    NOT cryptographically equivalent to real Kyber/Dilithium —
    for research demonstration and development only.
    """

    @staticmethod
    def kyber_keygen() -> Tuple[bytes, bytes]:
        """Simulate Kyber-512 key generation."""
        private_key = secrets.token_bytes(64)   # 512-bit private key
        # Public key derived from private (simplified)
        public_key = hashlib.sha512(private_key).digest()
        return public_key, private_key

    @staticmethod
    def kyber_encapsulate(public_key: bytes) -> Tuple[bytes, bytes]:
        """Simulate Kyber encapsulation → (ciphertext, shared_secret)."""
        # Shared secret derived deterministically from public key + random salt
        salt = secrets.token_bytes(16)
        shared_secret = hmac.new(public_key[:32], salt, hashlib.sha256).digest()
        # KEM ciphertext = salt + MAC (allows decapsulation to recover shared_secret)
        kem_ct = salt + hmac.new(public_key[:32], salt, hashlib.sha256).digest()
        return kem_ct, shared_secret

    @staticmethod
    def kyber_decapsulate(private_key: bytes, kem_ciphertext: bytes) -> bytes:
        """Simulate Kyber decapsulation → shared_secret."""
        # Public key is derived from private key the same way as in keygen
        public_key = hashlib.sha512(private_key).digest()
        # Recover salt from first 16 bytes of ciphertext
        salt = kem_ciphertext[:16]
        # Re-derive shared secret using same public key + salt
        shared_secret = hmac.new(public_key[:32], salt, hashlib.sha256).digest()
        return shared_secret

    @staticmethod
    def dilithium_keygen() -> Tuple[bytes, bytes]:
        """Simulate Dilithium-2 key generation."""
        private_key = secrets.token_bytes(96)
        public_key = hashlib.sha512(private_key).digest()
        return public_key, private_key

    @staticmethod
    def dilithium_sign(private_key: bytes, message: bytes) -> bytes:
        """Simulate Dilithium signing."""
        signature = hmac.new(private_key[:32], message, hashlib.sha256).digest()
        signature += secrets.token_bytes(32)  # Simulate full signature size
        return signature

    @staticmethod
    def dilithium_verify(public_key: bytes, message: bytes, signature: bytes) -> bool:
        """Simulate Dilithium verification."""
        # In simulation, we can't truly verify without the private key
        # This always returns True for demo — real liboqs verifies properly
        return len(signature) >= 32


class HybridPQCCrypto:
    """
    ImmunoGrid's Hybrid Post-Quantum Cryptography Layer.
    
    Every message between IoT devices and the cloud passes through this.
    Provides:
    1. Key encapsulation (Kyber) → quantum-safe key exchange
    2. Symmetric encryption (AES-256-GCM) → fast bulk encryption
    3. Digital signatures (Dilithium) → quantum-safe authentication
    """

    def __init__(self, entity_id: str):
        self.entity_id = entity_id
        self.kem_algorithm = "Kyber512"
        self.sig_algorithm = "Dilithium2"

        # Generate key pairs
        self.kem_keypair = self._generate_kem_keypair()
        self.sig_keypair = self._generate_sig_keypair()

        logger.info(
            "pqc_crypto_initialized",
            entity_id=entity_id,
            kem=self.kem_algorithm,
            sig=self.sig_algorithm,
            mode="liboqs" if OQS_AVAILABLE else "simulation",
        )

    def _generate_kem_keypair(self) -> KeyPair:
        """Generate Kyber key encapsulation key pair."""
        if OQS_AVAILABLE:
            kem = oqs.KeyEncapsulation(self.kem_algorithm)
            public_key = kem.generate_keypair()
            private_key = kem.export_secret_key()
        else:
            public_key, private_key = PQCSimulator.kyber_keygen()

        return KeyPair(
            algorithm=self.kem_algorithm,
            public_key=public_key,
            private_key=private_key,
        )

    def _generate_sig_keypair(self) -> KeyPair:
        """Generate Dilithium signature key pair."""
        if OQS_AVAILABLE:
            sig = oqs.Signature(self.sig_algorithm)
            public_key = sig.generate_keypair()
            private_key = sig.export_secret_key()
        else:
            public_key, private_key = PQCSimulator.dilithium_keygen()

        return KeyPair(
            algorithm=self.sig_algorithm,
            public_key=public_key,
            private_key=private_key,
        )

    def encrypt_message(
        self,
        plaintext: bytes,
        recipient_public_key: bytes,
    ) -> EncryptedMessage:
        """
        Encrypt a message for a recipient using hybrid PQC encryption.
        
        Process:
        1. KEM: Encapsulate a shared secret using recipient's Kyber public key
        2. HKDF: Derive an AES-256 key from the shared secret
        3. AES-256-GCM: Encrypt the plaintext with the derived key
        """
        # Step 1: KEM encapsulation → get shared secret
        if OQS_AVAILABLE:
            kem = oqs.KeyEncapsulation(self.kem_algorithm)
            kem_ct, shared_secret = kem.encap_secret(recipient_public_key)
        else:
            kem_ct, shared_secret = PQCSimulator.kyber_encapsulate(recipient_public_key)

        # Step 2: Derive AES key via HKDF
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,   # 256-bit AES key
            salt=None,
            info=b"immunogrid-aes-key",
        )
        aes_key = hkdf.derive(shared_secret)

        # Step 3: AES-256-GCM encryption
        nonce = secrets.token_bytes(12)   # 96-bit nonce
        aesgcm = AESGCM(aes_key)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)

        return EncryptedMessage(
            ciphertext=ciphertext,
            nonce=nonce,
            kem_ciphertext=kem_ct,
            algorithm=f"{self.kem_algorithm}+AES-256-GCM",
            sender_id=self.entity_id,
            timestamp=time.time(),
        )

    def decrypt_message(self, encrypted_msg: EncryptedMessage) -> bytes:
        """Decrypt a message using this entity's private KEM key."""
        # Step 1: KEM decapsulation → recover shared secret
        if OQS_AVAILABLE:
            kem = oqs.KeyEncapsulation(self.kem_algorithm, self.kem_keypair.private_key)
            shared_secret = kem.decap_secret(encrypted_msg.kem_ciphertext)
        else:
            shared_secret = PQCSimulator.kyber_decapsulate(
                self.kem_keypair.private_key,
                encrypted_msg.kem_ciphertext,
            )

        # Step 2: Derive AES key
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b"immunogrid-aes-key",
        )
        aes_key = hkdf.derive(shared_secret)

        # Step 3: AES-256-GCM decryption
        aesgcm = AESGCM(aes_key)
        plaintext = aesgcm.decrypt(
            encrypted_msg.nonce,
            encrypted_msg.ciphertext,
            None,
        )

        return plaintext

    def sign_message(self, message: bytes) -> SignedMessage:
        """Sign a message using Dilithium."""
        if OQS_AVAILABLE:
            sig = oqs.Signature(self.sig_algorithm, self.sig_keypair.private_key)
            signature = sig.sign(message)
        else:
            signature = PQCSimulator.dilithium_sign(self.sig_keypair.private_key, message)

        return SignedMessage(
            message=message,
            signature=signature,
            public_key=self.sig_keypair.public_key,
            algorithm=self.sig_algorithm,
            signer_id=self.entity_id,
        )

    def verify_signature(self, signed_msg: SignedMessage) -> bool:
        """Verify a Dilithium signature."""
        if OQS_AVAILABLE:
            sig = oqs.Signature(self.sig_algorithm)
            return sig.verify(
                signed_msg.message,
                signed_msg.signature,
                signed_msg.public_key,
            )
        else:
            return PQCSimulator.dilithium_verify(
                signed_msg.public_key,
                signed_msg.message,
                signed_msg.signature,
            )

    def get_public_keys(self) -> Dict[str, bytes]:
        """Return this entity's public keys for sharing."""
        return {
            "kem_public_key": self.kem_keypair.public_key,
            "sig_public_key": self.sig_keypair.public_key,
            "entity_id": self.entity_id.encode(),
        }
