"""
ImmunoGrid — Quantum Key Distribution (QKD) Simulation
Simulates BB84 protocol for quantum-secure key distribution
between IoT devices and the central server.

BB84 Protocol Steps:
1. Alice (device) prepares qubits in random bases
2. Bob (server) measures in random bases
3. Alice and Bob compare bases (over classical channel)
4. Keep only bits where bases matched → raw key
5. Error checking → final secret key

In production: QKD hardware (ID Quantique, Toshiba QKD systems)
In simulation: Qiskit circuit simulation
"""

import random
import secrets
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple

import numpy as np
import structlog
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

logger = structlog.get_logger(__name__)

BASIS_RECTILINEAR = 0   # { |0⟩, |1⟩ }
BASIS_DIAGONAL    = 1   # { |+⟩, |−⟩ }


@dataclass
class QKDSession:
    """Result of a QKD key exchange session."""
    session_id: str
    device_id: str
    server_id: str
    raw_key_bits: int       # Bits before sifting
    sifted_key_bits: int    # Bits after base comparison
    final_key_bits: int     # Bits after error correction
    qber: float             # Quantum Bit Error Rate (eavesdrop indicator)
    secure: bool            # False if QBER > threshold (eavesdrop detected)
    key_hex: str            # The final shared secret key (hex)
    timestamp: str


class BB84Simulator:
    """
    Simulates the BB84 Quantum Key Distribution protocol.

    Used in ImmunoGrid as an additional layer of quantum-secure
    key exchange between critical IoT devices (hospital, power grid)
    and the central server.

    Note: This is a software simulation. Real QKD requires
    quantum hardware (fiber optic quantum channels).
    """

    QBER_THRESHOLD = 0.11   # Above 11% QBER → eavesdropper present

    def __init__(self):
        self.simulator = AerSimulator()
        self.sessions: List[QKDSession] = []
        logger.info("bb84_simulator_initialized")

    def _prepare_qubit(self, bit: int, basis: int) -> QuantumCircuit:
        """
        Alice prepares a single qubit.
        bit=0, basis=0 → |0⟩ (rectilinear)
        bit=1, basis=0 → |1⟩ (rectilinear)
        bit=0, basis=1 → |+⟩ (diagonal)
        bit=1, basis=1 → |−⟩ (diagonal)
        """
        qc = QuantumCircuit(1, 1)
        if bit == 1:
            qc.x(0)       # Flip to |1⟩
        if basis == BASIS_DIAGONAL:
            qc.h(0)       # Apply Hadamard for diagonal basis
        return qc

    def _measure_qubit(self, qc: QuantumCircuit, basis: int) -> int:
        """Bob measures a qubit in his chosen basis."""
        if basis == BASIS_DIAGONAL:
            qc.h(0)       # Rotate back from diagonal
        qc.measure(0, 0)

        job    = self.simulator.run(qc, shots=1)
        result = job.result()
        counts = result.get_counts()
        return int(max(counts, key=counts.get))

    def run_protocol(
        self,
        device_id: str,
        server_id: str = "immunogrid-server",
        n_qubits: int = 256,
        eavesdrop_probability: float = 0.0,
    ) -> QKDSession:
        """
        Run the full BB84 protocol between a device and server.

        Args:
            device_id: ID of the IoT device (Alice)
            server_id: ID of the server (Bob)
            n_qubits:  Number of qubits to exchange
            eavesdrop_probability: Simulate eavesdropper (0.0 = none)

        Returns:
            QKDSession with the final shared key
        """
        import uuid
        session_id = f"QKD-{uuid.uuid4().hex[:12].upper()}"

        # Step 1: Alice prepares random bits and bases
        alice_bits  = [random.randint(0, 1) for _ in range(n_qubits)]
        alice_bases = [random.randint(0, 1) for _ in range(n_qubits)]

        # Step 2: Bob chooses random measurement bases
        bob_bases = [random.randint(0, 1) for _ in range(n_qubits)]

        # Step 3: Simulate quantum channel + optional eavesdropper
        bob_results = []
        for i in range(n_qubits):
            qc = self._prepare_qubit(alice_bits[i], alice_bases[i])

            # Eavesdropper intercepts (introduces errors)
            if random.random() < eavesdrop_probability:
                eve_basis  = random.randint(0, 1)
                eve_result = self._measure_qubit(QuantumCircuit(1, 1), eve_basis)
                # Eve re-prepares qubit (50% chance of introducing error)
                qc = self._prepare_qubit(eve_result, eve_basis)

            result = self._measure_qubit(qc, bob_bases[i])
            bob_results.append(result)

        # Step 4: Sifting — keep bits where bases matched
        sifted_alice = []
        sifted_bob   = []
        for i in range(n_qubits):
            if alice_bases[i] == bob_bases[i]:
                sifted_alice.append(alice_bits[i])
                sifted_bob.append(bob_results[i])

        # Step 5: Error checking (QBER)
        check_size = max(1, len(sifted_alice) // 4)
        check_indices = random.sample(range(len(sifted_alice)), check_size)
        errors = sum(1 for i in check_indices if sifted_alice[i] != sifted_bob[i])
        qber   = errors / check_size

        # Remove check bits from key
        key_indices = [i for i in range(len(sifted_alice)) if i not in check_indices]
        final_key_bits_list = [sifted_alice[i] for i in key_indices]

        # Convert to bytes
        key_bytes = bytearray()
        for i in range(0, len(final_key_bits_list) - 7, 8):
            byte_val = 0
            for j in range(8):
                byte_val = (byte_val << 1) | final_key_bits_list[i + j]
            key_bytes.append(byte_val)

        is_secure = qber <= self.QBER_THRESHOLD
        key_hex   = key_bytes.hex() if is_secure else ""

        session = QKDSession(
            session_id=session_id,
            device_id=device_id,
            server_id=server_id,
            raw_key_bits=n_qubits,
            sifted_key_bits=len(sifted_alice),
            final_key_bits=len(final_key_bits_list),
            qber=round(qber, 4),
            secure=is_secure,
            key_hex=key_hex[:32],   # First 128 bits
            timestamp=datetime.utcnow().isoformat(),
        )

        self.sessions.append(session)

        if is_secure:
            logger.info(
                "qkd_session_secure",
                session_id=session_id,
                device=device_id,
                qber=round(qber, 4),
                key_bits=len(final_key_bits_list),
            )
        else:
            logger.warning(
                "qkd_eavesdrop_detected",
                session_id=session_id,
                device=device_id,
                qber=round(qber, 4),
                threshold=self.QBER_THRESHOLD,
            )

        return session

    def get_stats(self) -> dict:
        secure   = [s for s in self.sessions if s.secure]
        insecure = [s for s in self.sessions if not s.secure]
        avg_qber = sum(s.qber for s in self.sessions) / max(len(self.sessions), 1)

        return {
            "total_sessions": len(self.sessions),
            "secure_sessions": len(secure),
            "eavesdrop_detected": len(insecure),
            "avg_qber": round(avg_qber, 4),
            "avg_key_bits": int(sum(s.final_key_bits for s in self.sessions) / max(len(self.sessions), 1)),
            "security_rate": f"{len(secure)/max(len(self.sessions),1)*100:.1f}%",
        }
