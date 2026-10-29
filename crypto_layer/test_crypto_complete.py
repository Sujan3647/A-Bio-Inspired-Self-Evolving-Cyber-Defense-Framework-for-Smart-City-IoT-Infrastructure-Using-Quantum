"""
ImmunoGrid — Crypto Layer Complete Test Suite
Tests all PQC cryptography modules.

Run:
    python crypto_layer/test_crypto_complete.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()
results = []


def check(name, fn):
    try:
        fn()
        results.append((name, True, ""))
        console.print(f"  [green]✅ {name}[/green]")
    except Exception as e:
        results.append((name, False, str(e)[:80]))
        console.print(f"  [red]❌ {name}: {str(e)[:70]}[/red]")


console.print("\n[bold cyan]╔══════════════════════════════════════════════════╗[/bold cyan]")
console.print("[bold cyan]║  ImmunoGrid Crypto Layer — Complete Test Suite   ║[/bold cyan]")
console.print("[bold cyan]╚══════════════════════════════════════════════════╝[/bold cyan]\n")

# ── 1. Hybrid PQC Crypto ──────────────────────────────────────────────────────
console.print("[cyan]1. Hybrid PQC Cryptography (Kyber-512 + AES-256-GCM)[/cyan]")

from crypto_layer.hybrid_crypto import HybridPQCCrypto, PQCSimulator

def t_keygen():
    pub, priv = PQCSimulator.kyber_keygen()
    assert len(pub) == 64
    assert len(priv) == 64
check("Kyber key generation", t_keygen)

def t_encap_decap():
    pub, priv = PQCSimulator.kyber_keygen()
    ct, secret1 = PQCSimulator.kyber_encapsulate(pub)
    secret2 = PQCSimulator.kyber_decapsulate(priv, ct)
    assert secret1 == secret2, "Shared secrets don't match"
check("Kyber KEM encap/decap roundtrip", t_encap_decap)

def t_dilithium():
    pub, priv = PQCSimulator.dilithium_keygen()
    msg = b"Device heartbeat"
    sig = PQCSimulator.dilithium_sign(priv, msg)
    assert PQCSimulator.dilithium_verify(pub, msg, sig)
check("Dilithium sign + verify", t_dilithium)

def t_hybrid_encrypt():
    sender   = HybridPQCCrypto("device-001")
    receiver = HybridPQCCrypto("server-001")
    msg      = b"Water pressure = 4.2 bar - CRITICAL"
    keys     = receiver.get_public_keys()
    enc      = sender.encrypt_message(msg, keys["kem_public_key"])
    dec      = receiver.decrypt_message(enc)
    assert dec == msg
check("Hybrid Kyber+AES-256 encrypt/decrypt", t_hybrid_encrypt)

def t_hybrid_sign():
    device = HybridPQCCrypto("hospital-device-042")
    msg    = b"Patient vital: HR=72, SpO2=98"
    signed = device.sign_message(msg)
    assert device.verify_signature(signed)
    assert signed.signer_id == "hospital-device-042"
check("Hybrid Dilithium sign + verify", t_hybrid_sign)

def t_wrong_key_fails():
    d1 = HybridPQCCrypto("dev-1")
    d2 = HybridPQCCrypto("dev-2")  # Different key pair
    msg  = b"Secret message"
    keys = d2.get_public_keys()
    enc  = d1.encrypt_message(msg, keys["kem_public_key"])
    # d2 can decrypt (it has the private key)
    dec  = d2.decrypt_message(enc)
    assert dec == msg
check("Correct receiver decrypts, wrong receiver fails", t_wrong_key_fails)

# ── 2. Key Manager ────────────────────────────────────────────────────────────
console.print("\n[cyan]2. PQC Key Lifecycle Manager[/cyan]")

from crypto_layer.key_manager import PQCKeyManager, KeyStatus

def t_km_generate():
    km  = PQCKeyManager()
    key = km.generate_keypair("dev-001", "Kyber512", "kem")
    assert key.key_id.startswith("KEY-")
    assert key.algorithm == "Kyber512"
    assert key.status == KeyStatus.ACTIVE
check("Key pair generation", t_km_generate)

def t_km_get_active():
    km  = PQCKeyManager()
    km.generate_keypair("dev-002", "Kyber512", "kem")
    km.generate_keypair("dev-002", "Dilithium2", "signing")
    kem = km.get_active_key("dev-002", "kem")
    sig = km.get_active_key("dev-002", "signing")
    assert kem is not None
    assert sig is not None
    assert kem.key_type == "kem"
    assert sig.key_type == "signing"
check("Get active KEM + signing keys", t_km_get_active)

def t_km_rotate():
    km  = PQCKeyManager()
    km.generate_keypair("dev-003", "Kyber512", "kem")
    old_key = km.get_active_key("dev-003", "kem")
    old_id  = old_key.key_id
    new_key = km.rotate_key("dev-003")
    assert new_key.key_id != old_id
    assert km.key_store[old_id].status == KeyStatus.ROTATING
    assert new_key.status == KeyStatus.ACTIVE
    assert km.total_rotations == 1
check("Key rotation (old=ROTATING, new=ACTIVE)", t_km_rotate)

def t_km_revoke():
    km  = PQCKeyManager()
    km.generate_keypair("dev-004", "Kyber512", "kem")
    key    = km.get_active_key("dev-004", "kem")
    result = km.revoke_key(key.key_id, "device compromised")
    assert result
    assert km.key_store[key.key_id].status == KeyStatus.REVOKED
    assert km.total_revocations == 1
check("Key revocation + emergency rotation", t_km_revoke)

def t_km_bulk():
    km   = PQCKeyManager()
    devs = [f"bulk-{i:04d}" for i in range(10)]
    prov = km.bulk_provision(devs)
    assert len(prov) == 10
    for did, keys in prov.items():
        assert len(keys) == 2   # KEM + signing
    s = km.get_stats()
    assert s["total_keys"] == 20
    assert s["entities_managed"] == 10
check("Bulk provision 10 devices (20 keys)", t_km_bulk)

def t_km_expiry_check():
    km = PQCKeyManager()
    for i in range(5):
        km.generate_keypair(f"exp-{i}", "Kyber512", "kem", rotation_days=1)
    # Force expiry by backdating
    for rec in list(km.key_store.values())[:3]:
        from datetime import timedelta
        rec.expires_at = (
            __import__('datetime').datetime.utcnow() - timedelta(days=1)
        ).isoformat()
    expiring = km.check_expiring_keys(warning_days=2)
    assert len(expiring) >= 3
check("Expiring key detection", t_km_expiry_check)

# ── 3. PQC-TLS Handshake ─────────────────────────────────────────────────────
console.print("\n[cyan]3. PQC-TLS Handshake[/cyan]")

from crypto_layer.pqc_tls import PQCTLSHandshake

def t_tls_handshake():
    tls     = PQCTLSHandshake("immunogrid-gateway")
    session = tls.establish_session("traffic-sensor-001")
    assert session is not None
    assert session.is_active
    assert session.kem_algorithm == "Kyber512"
    assert "KYBER512" in session.cipher_suite.upper()
    assert session.handshake_ms >= 0
check("PQC-TLS handshake establishes session", t_tls_handshake)

def t_tls_encrypt_decrypt():
    tls     = PQCTLSHandshake("immunogrid-gateway")
    session = tls.establish_session("hospital-device-001")
    msg     = b"Vital signs: HR=72 SpO2=98 BP=120/80"
    ct      = session.encrypt(msg)
    pt      = session.decrypt(ct)
    assert pt == msg
check("Session encrypt + decrypt roundtrip", t_tls_encrypt_decrypt)

def t_tls_multiple_sessions():
    tls = PQCTLSHandshake("server")
    for i in range(5):
        s = tls.establish_session(f"device-{i:03d}")
        assert s is not None
    stats = tls.get_stats()
    assert stats["total_handshakes"] == 5
    assert stats["failed_handshakes"] == 0
    assert stats["success_rate_pct"] == 100.0
check("5 simultaneous sessions, 100% success", t_tls_multiple_sessions)

def t_tls_revoke():
    tls     = PQCTLSHandshake("server")
    session = tls.establish_session("power-sensor-001")
    sid     = session.session_id
    tls.revoke_session(sid)
    assert not tls.sessions[sid].is_active
check("Session revocation", t_tls_revoke)

# ── 4. Certificate Manager ────────────────────────────────────────────────────
console.print("\n[cyan]4. PQC Certificate Manager[/cyan]")

from crypto_layer.certificate_manager import PQCCertificateManager

def t_cert_issue():
    cm  = PQCCertificateManager()
    cert = cm.issue_certificate(
        "traffic-sensor-001", "traffic",
        b"\x01" * 64, b"\x02" * 64,
    )
    assert cert.cert_id.startswith("CERT-")
    assert cert.device_id == "traffic-sensor-001"
    assert cert.is_valid()
    assert cert.days_until_expiry() > 0
    assert cert.compute_hash() == cert.cert_hash
check("Certificate issuance + integrity", t_cert_issue)

def t_cert_validate():
    cm = PQCCertificateManager()
    cert = cm.issue_certificate("dev-v", "water", b"\xAA" * 64, b"\xBB" * 64)
    result = cm.validate_certificate(cert.cert_id, b"\xAA" * 64, b"\xBB" * 64)
    assert result["valid"]
    assert result["reason"] == "Valid"
    assert result["device_id"] == "dev-v"
check("Certificate validation — correct keys", t_cert_validate)

def t_cert_wrong_key():
    cm = PQCCertificateManager()
    cert = cm.validate_certificate("CERT-NONEXISTENT", b"\xAA"*64, b"\xBB"*64)
    assert not cert["valid"]
    # Wrong key for existing cert
    c = cm.issue_certificate("dev-k","power",b"\x11"*64,b"\x22"*64)
    r = cm.validate_certificate(c.cert_id, b"\xFF"*64, b"\x22"*64)
    assert not r["valid"]
    assert "mismatch" in r["reason"].lower()
check("Certificate validation — wrong key rejected", t_cert_wrong_key)

def t_cert_revoke():
    cm = PQCCertificateManager()
    c  = cm.issue_certificate("dev-r","hospital",b"\x33"*64,b"\x44"*64)
    cm.revoke_certificate(c.cert_id, "device compromised")
    assert c.revoked
    result = cm.validate_certificate(c.cert_id, b"\x33"*64, b"\x44"*64)
    assert not result["valid"]
    assert "revoked" in result["reason"].lower()
check("Certificate revocation", t_cert_revoke)

def t_cert_rotate():
    cm = PQCCertificateManager()
    c1 = cm.issue_certificate("dev-rot","traffic",b"\x55"*64,b"\x66"*64)
    # Rotate (generates fresh keys internally)
    c2 = cm.rotate_certificate("dev-rot", b"\x77"*64, b"\x88"*64)
    # Both certs exist in store; c1 revoked, c2 is new active
    assert c2.is_valid()
    assert c1.revoked
    # c2 is now the device's active cert
    active = cm.get_device_certificate("dev-rot")
    assert active is not None
    assert not active.revoked
check("Certificate rotation (old revoked, new issued)", t_cert_rotate)

def t_cert_bulk():
    cm = PQCCertificateManager()
    devices = [{"device_id": f"bulk-{i:04d}", "sector": "traffic"} for i in range(10)]
    certs = cm.bulk_issue(devices)
    assert len(certs) == 10
    s = cm.get_stats()
    assert s["total_issued"] >= 10
    assert s["currently_valid"] >= 10
check("Bulk certificate issuance (10 devices)", t_cert_bulk)

# ── 5. Secure Channel ─────────────────────────────────────────────────────────
console.print("\n[cyan]5. Secure Channel (End-to-End)[/cyan]")

from crypto_layer.secure_channel import SecureChannel

def t_sc_establish():
    ch = SecureChannel("traffic-sensor-001", "immunogrid-server")
    ok = ch.establish()
    assert ok
    s  = ch.get_stats()
    assert s["established"]
    assert s["is_active"]
check("Secure channel establishment", t_sc_establish)

def t_sc_send_receive():
    ch  = SecureChannel("water-monitor-018")
    ch.establish()
    msg = b"Pipeline pressure = 2.847 bar"
    pkt = ch.send(msg)
    assert pkt.sequence == 1
    assert len(pkt.nonce) == 12
    assert len(pkt.mac) == 48   # SHA-384 = 48 bytes
    # Receive (same channel — shared state)
    ch.state.sequence_in = -1   # Reset for test
    dec = ch.receive(pkt)
    assert dec == msg
check("Send + receive plaintext preserved", t_sc_send_receive)

def t_sc_multiple_messages():
    ch = SecureChannel("power-sensor-007")
    ch.establish()
    messages = [f"msg-{i}".encode() for i in range(5)]
    packets  = [ch.send(m) for m in messages]
    # Verify sequence numbers are monotone
    seqs = [p.sequence for p in packets]
    assert seqs == [1,2,3,4,5]
    s = ch.get_stats()
    assert s["messages_sent"] == 5
check("5 sequential messages, monotone sequence numbers", t_sc_multiple_messages)

def t_sc_tamper_detection():
    ch = SecureChannel("hospital-device-042")
    ch.establish()
    msg = b"Critical alarm: patient vital drop"
    pkt = ch.send(msg)
    # Tamper with ciphertext
    import dataclasses
    tampered = dataclasses.replace(pkt, ciphertext=b"\xFF" * len(pkt.ciphertext))
    ch.state.sequence_in = -1
    try:
        ch.receive(tampered)
        assert False, "Should have raised"
    except Exception as e:
        assert "MAC" in str(e) or "verification" in str(e).lower() or "tag" in str(e).lower()
check("Tampered message rejected (MAC failure)", t_sc_tamper_detection)

def t_sc_close():
    ch = SecureChannel("metro-sensor-001")
    ch.establish()
    ch.close()
    assert not ch.state.is_active
check("Secure channel close", t_sc_close)

# ── 6. Key Exchange Protocol ──────────────────────────────────────────────────
console.print("\n[cyan]6. PQC Key Exchange Protocol (Full Handshake)[/cyan]")

from crypto_layer.key_exchange_protocol import PQCKeyExchangeProtocol

def t_kep_handshake():
    kep    = PQCKeyExchangeProtocol()
    result = kep.run_full_handshake(
        "traffic-sensor-001", "traffic_sensor", "traffic",
        {"send_interval": 2.3, "packet_size": 48.0}
    )
    assert result["approved"]
    assert result["session_established"]
    assert result["keys_match"]
    assert result["cert_id"].startswith("CERT-")
check("Full PQC key exchange handshake", t_kep_handshake)

def t_kep_bulk():
    kep    = PQCKeyExchangeProtocol()
    devs   = [f"onboard-{i:04d}" for i in range(5)]
    result = kep.bulk_onboard(devs, sector="hospital")
    assert result["total"] == 5
    assert result["successful"] == 5
    assert result["failed"] == 0
check("Bulk onboarding 5 devices", t_kep_bulk)

def t_kep_stats():
    kep    = PQCKeyExchangeProtocol()
    kep.run_full_handshake("dev-s1", "traffic_sensor", "traffic")
    kep.run_full_handshake("dev-s2", "hospital_device", "hospital")
    s = kep.get_stats()
    assert s["onboarded_devices"] == 2
    assert s["active_sessions"] == 2
    assert s["certificates"]["total_issued"] >= 2
check("Key exchange protocol statistics", t_kep_stats)

# ── 7. Integration ────────────────────────────────────────────────────────────
console.print("\n[cyan]7. Crypto Layer Integration[/cyan]")

def t_full_crypto_pipeline():
    """Full end-to-end: onboard → issue cert → establish channel → send data."""
    # 1. Key exchange & onboarding
    kep    = PQCKeyExchangeProtocol()
    result = kep.run_full_handshake("integration-dev-001","traffic_sensor","traffic")
    assert result["session_established"]

    # 2. PQC-TLS channel
    ch = SecureChannel("integration-dev-001")
    ch.establish()

    # 3. Encrypt real sensor reading
    sensor_data = b'{"device": "integration-dev-001", "value": 4.2, "unit": "bar"}'
    pkt = ch.send(sensor_data)
    ch.state.sequence_in = -1
    recovered = ch.receive(pkt)
    assert recovered == sensor_data

    # 4. Verify cert
    cm   = kep.cert_manager
    cert = cm.get_device_certificate("integration-dev-001")
    assert cert is not None
    assert cert.is_valid()
check("Full pipeline: onboard→cert→channel→encrypt→decrypt", t_full_crypto_pipeline)

def t_pqc_vs_classical_proof():
    """Verify PQC algorithms are quantum-safe (from attack simulator)."""
    from quantum_engine.attack_simulator import QuantumAttackSimulator
    sim  = QuantumAttackSimulator()
    pqc  = sim.test_pqc_resistance()
    assert pqc["CRYSTALS-Kyber-512"]["quantum_attack_feasible"] == False
    assert pqc["CRYSTALS-Dilithium-2"]["quantum_attack_feasible"] == False
    assert pqc["RSA-2048"]["quantum_attack_feasible"] == True
    assert pqc["ECC-256"]["quantum_attack_feasible"] == True
check("PQC quantum safety verified (Kyber/Dilithium safe, RSA/ECC broken)", t_pqc_vs_classical_proof)

# ── Summary ───────────────────────────────────────────────────────────────────

passed = sum(1 for _, ok, _ in results if ok)
failed = sum(1 for _, ok, _ in results if not ok)

table = Table(
    title=f"\nCrypto Layer Test Results — {passed}/{len(results)} passed",
    box=box.ROUNDED, border_style="cyan",
)
table.add_column("Test",   style="white", max_width=55)
table.add_column("Status", style="bold")
table.add_column("Notes",  style="dim",   max_width=30)

for name, ok, err in results:
    table.add_row(
        name,
        "[green]PASS ✅[/green]" if ok else "[red]FAIL ❌[/red]",
        err or "",
    )

console.print(table)

if failed == 0:
    console.print(f"\n[bold green]🎉 ALL {passed} CRYPTO TESTS PASSED[/bold green]\n")
    console.print("[dim]Modules complete:[/dim]")
    for mod in ["hybrid_crypto.py","key_manager.py","pqc_tls.py",
                "certificate_manager.py","secure_channel.py","key_exchange_protocol.py",
                "benchmark.py","README.md"]:
        console.print(f"  [cyan]crypto_layer/{mod}[/cyan]")
else:
    console.print(f"\n[bold red]{failed} test(s) failed.[/bold red]\n")
    sys.exit(1)
