"""
ImmunoGrid — Full Integration Test Suite
Tests all 8 modules working together.

Run (via pytest):
    pytest test_integration.py -v -m integration

Run (standalone):
    python test_integration.py
"""

import pytest

pytestmark = pytest.mark.integration


# ── 1. IoT Simulator ──────────────────────────────────────────────────────────

def test_device_types_build_and_fingerprint():
    from iot_simulator.devices import (
        TrafficSensor, StreetCamera, WaterMonitor,
        HospitalDevice, PowerSensor, MetroSensor,
        AirportDevice, GovtOfficeNode,
    )
    devices = [
        TrafficSensor(location="z1", sector="traffic"),
        StreetCamera(location="z2", sector="surveillance"),
        WaterMonitor(location="z3", sector="water"),
        HospitalDevice(location="z4", sector="hospital"),
        PowerSensor(location="z5", sector="power"),
        MetroSensor(location="z6", sector="metro"),
        AirportDevice(location="z7", sector="airport"),
        GovtOfficeNode(location="z8", sector="government"),
    ]
    for d in devices:
        msg = d.build_message()
        fp = d.get_fingerprint_vector()
        assert msg["device_id"] == d.device_id
        assert len(fp) == 7


def test_attacker_types():
    from iot_simulator.attackers import (
        SpoofingAttacker, DDoSAttacker, DataPoisoner,
        MITMAttacker, ReplayAttacker, RansomwareBot,
    )
    attackers = [
        SpoofingAttacker(), DDoSAttacker(), DataPoisoner(),
        MITMAttacker(), ReplayAttacker(), RansomwareBot(),
    ]
    assert len(attackers) == 6


# ── 2. Quantum Engine ─────────────────────────────────────────────────────────

def test_quantum_device_fingerprint_registration():
    from quantum_engine.fingerprint_gen import QuantumFingerprintEngine
    from iot_simulator.devices import TrafficSensor

    qe = QuantumFingerprintEngine(num_qubits=4)
    d = TrafficSensor(location="test", sector="traffic")
    fp = qe.register_device(d.device_id, d.get_fingerprint_vector())
    assert fp.device_id == d.device_id
    assert len(fp.statevector) == 16


def test_quantum_real_device_authenticated():
    from quantum_engine.fingerprint_gen import QuantumFingerprintEngine
    from iot_simulator.devices import TrafficSensor

    qe = QuantumFingerprintEngine(num_qubits=4)
    d = TrafficSensor(location="test", sector="traffic")
    qe.register_device(d.device_id, d.get_fingerprint_vector())
    result = qe.verify_device(d.device_id, d.get_fingerprint_vector())
    assert result.is_authentic, f"Real device should be authentic, got: {result.verdict}"


def test_quantum_unknown_device_rejected():
    from quantum_engine.fingerprint_gen import QuantumFingerprintEngine

    qe = QuantumFingerprintEngine(num_qubits=4)
    result = qe.verify_device(
        "unknown-device-xyz",
        {"send_interval": 2.0, "packet_size": 48.0, "timing_jitter": 1.0,
         "size_variance": 2.0, "cpu_usage": 0.15, "active_start": 6.0, "active_end": 22.0},
    )
    assert not result.is_authentic


# ── 3. Morphogenetic Blockchain ───────────────────────────────────────────────

def test_blockchain_genesis_block():
    from blockchain.immune_ledger import MorphogeneticBlockchain

    bc = MorphogeneticBlockchain(difficulty=1)
    assert len(bc.chain) == 1
    assert bc.is_chain_valid()


def test_blockchain_attack_record_and_morphogenesis():
    from blockchain.immune_ledger import MorphogeneticBlockchain

    bc = MorphogeneticBlockchain(difficulty=1)
    rec = bc.record_attack("spoofing", "dev-001", "traffic", {}, "quantum", "high")
    assert rec.record_id.startswith("ATK-")
    assert bc.is_chain_valid()
    assert bc.get_stats()["morphogenesis_events"] > 0


def test_blockchain_immune_memory():
    from blockchain.immune_ledger import MorphogeneticBlockchain

    bc = MorphogeneticBlockchain(difficulty=1)
    bc.record_attack("ddos", "dev-002", "hospital", {}, "ai_brain", "critical")
    known, count = bc.is_attack_pattern_known("ddos", "hospital")
    assert known and count >= 1


# ── 4. Post-Quantum Crypto ────────────────────────────────────────────────────

def test_pqc_encrypt_decrypt_roundtrip():
    from crypto_layer.hybrid_crypto import HybridPQCCrypto

    sender   = HybridPQCCrypto("sender")
    receiver = HybridPQCCrypto("receiver")
    message  = b"Sensor reading: 4.2 bar"
    keys     = receiver.get_public_keys()
    enc      = sender.encrypt_message(message, keys["kem_public_key"])
    dec      = receiver.decrypt_message(enc)
    assert dec == message


def test_pqc_sign_verify_roundtrip():
    from crypto_layer.hybrid_crypto import HybridPQCCrypto

    device = HybridPQCCrypto("device-001")
    signed = device.sign_message(b"Device heartbeat OK")
    assert device.verify_signature(signed)


# ── 5. AI Brain (FAC) ─────────────────────────────────────────────────────────

pytest_slow = pytest.mark.slow

@pytest.mark.slow
def test_ai_defender_training():
    torch = pytest.importorskip("torch")
    from ai_brain.local_trainer import LocalDeviceTrainer
    from iot_simulator.devices import TrafficSensor

    d       = TrafficSensor(location="test", sector="traffic")
    trainer = LocalDeviceTrainer(d.device_id, "traffic_sensor")
    msg     = d.build_message()
    for _ in range(20):
        trainer.add_to_buffer(msg, label=0)
    metrics = trainer.train_defender(epochs=3)
    assert "accuracy" in metrics


@pytest.mark.slow
def test_ai_adversarial_imaginations():
    pytest.importorskip("torch")
    from ai_brain.local_trainer import LocalDeviceTrainer

    trainer      = LocalDeviceTrainer("test-dev", "traffic_sensor")
    imaginations = trainer.generate_attack_imaginations(count=3)
    assert len(imaginations) == 3
    assert all(hasattr(im, "attack_type") for im in imaginations)


@pytest.mark.slow
def test_ai_federated_aggregation():
    pytest.importorskip("torch")
    from ai_brain.aggregator import FederatedAggregator, ClientUpdate
    from ai_brain.local_trainer import LocalDeviceTrainer
    from iot_simulator.devices import TrafficSensor

    agg = FederatedAggregator(min_clients=3)
    for i in range(3):
        d       = TrafficSensor(location=f"z{i}", sector="traffic")
        trainer = LocalDeviceTrainer(d.device_id, "traffic_sensor")
        msg     = d.build_message()
        for _ in range(15):
            trainer.add_to_buffer(msg, label=0)
        metrics = trainer.train_defender(epochs=2)
        update  = ClientUpdate(
            device_id=d.device_id,
            round_number=1,
            weights=trainer.get_model_weights()["defender"],
            num_samples=15,
            metrics=metrics,
            imaginations=[],
        )
        agg.submit_update(update)
    assert agg.current_round >= 1


# ── 6. Honeypot Network ───────────────────────────────────────────────────────

def test_honeypot_spawn_and_stats():
    from honeypot.decoy_spawner import HoneypotNetwork

    hp     = HoneypotNetwork()
    decoys = hp.spawn_honeypots("dev-001", "traffic", count=3)
    assert len(decoys) == 3
    assert hp.get_stats()["active_honeypots"] == 3


def test_honeypot_intelligence_capture():
    from honeypot.decoy_spawner import HoneypotNetwork
    from honeypot.intelligence_capture import IntelligenceCaptureEngine

    hp      = HoneypotNetwork()
    decoys  = hp.spawn_honeypots("dev-002", "hospital", count=1)
    hp_dev  = decoys[0]
    payload = {
        "_attack_meta": {"attack_type": "spoofing", "attacker_id": "atk-001"},
        "behavior":     {"send_interval": 2.9, "packet_size": 60},
        "sector":       "hospital",
    }
    hp_dev.record_interaction(payload)

    ice    = IntelligenceCaptureEngine()
    report = ice.analyze_honeypot(hp_dev.honeypot_id, hp_dev.interactions)
    assert report is not None
    assert len(report.recommended_defenses) > 0


# ── 7. Backend RBAC ───────────────────────────────────────────────────────────

def test_rbac_13_roles_with_permissions():
    from models.user import UserRole, ROLE_PERMISSIONS

    assert len(list(UserRole)) == 13
    for role in UserRole:
        assert role in ROLE_PERMISSIONS


def test_rbac_bcrypt_auth_and_demo_users():
    from routers.auth import _hash_password, _verify_password, DEMO_USERS

    assert _verify_password("Admin@123", _hash_password("Admin@123"))
    assert not _verify_password("wrong", _hash_password("Admin@123"))
    assert "admin@immunogrid.gov" in DEMO_USERS
    assert len(DEMO_USERS) == 9


# ── 8. Full Pipeline Integration ──────────────────────────────────────────────

def test_full_pipeline_iot_quantum_blockchain_honeypot():
    """IoT device → quantum verify → blockchain record → honeypot spawn."""
    from quantum_engine.fingerprint_gen import QuantumFingerprintEngine
    from blockchain.immune_ledger import MorphogeneticBlockchain
    from honeypot.decoy_spawner import HoneypotNetwork
    from iot_simulator.devices import TrafficSensor

    qe = QuantumFingerprintEngine(num_qubits=4)
    bc = MorphogeneticBlockchain(difficulty=1)
    hp = HoneypotNetwork()

    devices = [TrafficSensor(location=f"t{i}", sector="traffic") for i in range(5)]
    for d in devices:
        qe.register_device(d.device_id, d.get_fingerprint_vector())

    # Verify → Record → Honeypot
    result = qe.verify_device(devices[0].device_id, devices[0].get_fingerprint_vector())
    assert result.is_authentic

    rec = bc.record_attack("spoofing", devices[0].device_id, "traffic", {}, "quantum", "high")
    assert bc.is_chain_valid()

    decoys = hp.spawn_honeypots(devices[0].device_id, "traffic", count=2)
    assert len(decoys) == 2


# ── Standalone runner (kept for backward compat) ─────────────────────────────

if __name__ == "__main__":
    import sys
    import subprocess
    sys.exit(subprocess.call(["python", "-m", "pytest", __file__, "-v"]))
