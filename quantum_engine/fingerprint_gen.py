"""
ImmunoGrid — Quantum Behavioral Fingerprint Generator

This is Piece 2 of ImmunoGrid — the "DNA of every device".

How it works:
1. Take a device's behavioral profile (timing, packet size, CPU, etc.)
2. Encode it as angles in a quantum circuit (amplitude encoding)
3. The quantum circuit state IS the fingerprint
4. Compare incoming device behavior against stored fingerprint
5. If quantum states don't match → IMPOSTOR DETECTED

Uses Qiskit with AerSimulator for simulation.
"""

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
import structlog
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.quantum_info import Statevector, state_fidelity
from qiskit_aer import AerSimulator

logger = structlog.get_logger(__name__)


@dataclass
class QuantumFingerprint:
    """
    Stores the quantum fingerprint of a registered device.
    """
    device_id: str
    statevector: List[complex]        # The quantum state as fingerprint
    behavior_hash: str                # Classical hash for quick pre-check
    registered_at: str
    fidelity_threshold: float = 0.92  # Below this = impostor
    num_qubits: int = 4


@dataclass
class FingerprintMatchResult:
    """
    Result of comparing a device's current behavior
    against its registered quantum fingerprint.
    """
    device_id: str
    is_authentic: bool
    fidelity_score: float             # 0.0 (no match) to 1.0 (perfect match)
    threshold: float
    verdict: str                      # "AUTHENTIC" | "IMPOSTOR" | "SUSPICIOUS"
    checked_at: str


class QuantumFingerprintEngine:
    """
    The Quantum Behavioral Fingerprint Engine.
    
    This is the core of ImmunoGrid's device authentication.
    Instead of just checking a password (which can be stolen),
    we check HOW a device behaves — encoded as a quantum state.
    
    A hacker can copy a device's ID and credentials.
    They cannot replicate its exact quantum behavioral state.
    """

    def __init__(self, num_qubits: int = 4):
        self.num_qubits = num_qubits
        self.simulator = AerSimulator(method="statevector")
        self.fingerprint_db: Dict[str, QuantumFingerprint] = {}
        self.total_checks = 0
        self.impostors_detected = 0

        logger.info(
            "quantum_engine_initialized",
            num_qubits=num_qubits,
            backend="AerSimulator",
        )

    def _behavior_to_angles(self, behavior_vector: Dict[str, float]) -> List[float]:
        """
        Convert behavioral metrics into rotation angles for the quantum circuit.
        
        We normalize each metric to [0, π] so it can be used as
        a rotation angle in the quantum circuit.
        """
        # Define normalization ranges for each behavior metric
        normalizers = {
            "send_interval":  (0.5, 10.0),    # seconds
            "packet_size":    (20.0, 200.0),  # bytes
            "timing_jitter":  (0.0, 5.0),     # ms
            "size_variance":  (0.0, 20.0),    # bytes
            "cpu_usage":      (0.0, 1.0),     # fraction
            "active_start":   (0.0, 23.0),    # hour
            "active_end":     (0.0, 23.0),    # hour
        }

        angles = []
        keys = list(normalizers.keys())

        # Use only the first num_qubits metrics (we have 4 qubits → 4 angles)
        for key in keys[:self.num_qubits]:
            val = behavior_vector.get(key, 0.0)
            min_val, max_val = normalizers[key]
            # Normalize to [0, π]
            normalized = (val - min_val) / (max_val - min_val + 1e-9)
            angle = normalized * math.pi
            angles.append(angle)

        return angles

    def _build_fingerprint_circuit(self, angles: List[float]) -> QuantumCircuit:
        """
        Build a quantum circuit that encodes behavioral angles.
        
        Circuit structure:
        1. Apply Hadamard to create superposition
        2. Apply Ry rotations with behavioral angles
        3. Apply CNOT entanglement gates
        4. Final Hadamard layer
        
        This creates a unique quantum state that represents
        the device's behavioral fingerprint.
        """
        qr = QuantumRegister(self.num_qubits, name='behavior')
        circuit = QuantumCircuit(qr)

        # Step 1: Create superposition
        circuit.h(qr)

        # Step 2: Encode behavior as rotations
        for i, angle in enumerate(angles[:self.num_qubits]):
            circuit.ry(angle, qr[i])

        # Step 3: Entangle qubits (makes the fingerprint holistic)
        for i in range(self.num_qubits - 1):
            circuit.cx(qr[i], qr[i + 1])

        # Step 4: Add phase encoding for extra uniqueness
        for i, angle in enumerate(angles[:self.num_qubits]):
            circuit.rz(angle * 0.5, qr[i])

        return circuit

    def _get_statevector(self, circuit: QuantumCircuit) -> List[complex]:
        """Extract the statevector from a quantum circuit."""
        sv = Statevector.from_instruction(circuit)
        return sv.data.tolist()

    def register_device(self, device_id: str, behavior_vector: Dict[str, float]) -> QuantumFingerprint:
        """
        Register a device's quantum behavioral fingerprint.
        Called when a new device joins the network.
        """
        # Convert behavior to quantum angles
        angles = self._behavior_to_angles(behavior_vector)

        # Build and run the fingerprint circuit
        circuit = self._build_fingerprint_circuit(angles)
        statevector = self._get_statevector(circuit)

        # Create classical hash for quick lookup
        behavior_hash = hashlib.sha256(
            json.dumps(behavior_vector, sort_keys=True).encode()
        ).hexdigest()

        fingerprint = QuantumFingerprint(
            device_id=device_id,
            statevector=statevector,
            behavior_hash=behavior_hash,
            registered_at=datetime.utcnow().isoformat(),
            num_qubits=self.num_qubits,
        )

        self.fingerprint_db[device_id] = fingerprint

        logger.info(
            "device_fingerprint_registered",
            device_id=device_id,
            qubits=self.num_qubits,
        )

        return fingerprint

    def verify_device(
        self,
        device_id: str,
        current_behavior: Dict[str, float],
    ) -> FingerprintMatchResult:
        """
        Verify if a device's current behavior matches its registered fingerprint.
        
        This is called every time a device sends a message.
        If fidelity < threshold → the device is flagged as an IMPOSTOR.
        """
        self.total_checks += 1

        # Check if device is registered
        if device_id not in self.fingerprint_db:
            return FingerprintMatchResult(
                device_id=device_id,
                is_authentic=False,
                fidelity_score=0.0,
                threshold=0.92,
                verdict="UNKNOWN_DEVICE",
                checked_at=datetime.utcnow().isoformat(),
            )

        registered_fp = self.fingerprint_db[device_id]

        # Build quantum circuit for current behavior
        current_angles = self._behavior_to_angles(current_behavior)
        current_circuit = self._build_fingerprint_circuit(current_angles)
        current_sv = self._get_statevector(current_circuit)

        # Calculate quantum state fidelity
        # Fidelity = |<ψ_registered | ψ_current>|²
        # 1.0 = perfect match, 0.0 = completely different
        registered_sv = Statevector(registered_fp.statevector)
        current_sv_obj = Statevector(current_sv)
        fidelity = abs(state_fidelity(registered_sv, current_sv_obj))

        # Determine verdict
        threshold = registered_fp.fidelity_threshold
        if fidelity >= threshold:
            verdict = "AUTHENTIC"
            is_authentic = True
        elif fidelity >= threshold * 0.85:
            verdict = "SUSPICIOUS"
            is_authentic = False
            self.impostors_detected += 1
        else:
            verdict = "IMPOSTOR"
            is_authentic = False
            self.impostors_detected += 1

        result = FingerprintMatchResult(
            device_id=device_id,
            is_authentic=is_authentic,
            fidelity_score=round(fidelity, 6),
            threshold=threshold,
            verdict=verdict,
            checked_at=datetime.utcnow().isoformat(),
        )

        if not is_authentic:
            logger.warning(
                "impostor_detected",
                device_id=device_id,
                fidelity=round(fidelity, 4),
                verdict=verdict,
            )

        return result

    def get_stats(self) -> Dict:
        """Return engine statistics."""
        detection_rate = (
            self.impostors_detected / self.total_checks * 100
            if self.total_checks > 0 else 0
        )
        return {
            "registered_devices": len(self.fingerprint_db),
            "total_checks": self.total_checks,
            "impostors_detected": self.impostors_detected,
            "detection_rate_pct": round(detection_rate, 2),
            "num_qubits": self.num_qubits,
            "backend": "AerSimulator",
        }
