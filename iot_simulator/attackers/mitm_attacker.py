"""
ImmunoGrid — Man-in-the-Middle (MITM) Attacker
Intercepts and modifies messages between IoT devices and the cloud.
Detected by: PQC signature verification + quantum fingerprinting.
"""

import json
import random
import uuid
from datetime import datetime
from typing import Any, Callable, Dict

import structlog
from .base_attacker import AttackEvent, AttackType, BaseAttacker

logger = structlog.get_logger(__name__)


class MITMAttacker(BaseAttacker):
    """
    MITM Attack:
    Intercepts a legitimate message, modifies it, and re-sends it.

    What gives it away:
    - Dilithium signature mismatch (modified payload ≠ original signature)
    - Timestamp anomaly (slight delay from interception)
    - Quantum fingerprint mismatch on re-sent message
    Detected by PQC layer ~94% of the time.
    """

    @property
    def attack_type(self) -> AttackType:
        return AttackType.MITM

    async def execute_attack(
        self,
        target_device_id: str,
        target_sector: str,
        publish_callback: Callable,
    ) -> AttackEvent:
        attack_id = f"mitm-{uuid.uuid4().hex[:8]}"

        # Simulate intercepting a legitimate message and modifying it
        intercepted_and_modified = {
            "device_id": target_device_id,
            "device_type": "traffic_sensor",
            "sector": target_sector,
            "status": "online",
            "timestamp": datetime.utcnow().isoformat(),
            "sequence": random.randint(1, 9999),
            # Behavior copied from real device but signature will be wrong
            "behavior": {
                "send_interval": 2.347 + random.uniform(-0.1, 0.1),
                "packet_size": 48 + random.randint(-2, 2),
                "subnet": "192.168.1.5",
                "cpu_usage": round(random.uniform(0.1, 0.3), 4),
            },
            # Modified data — this is what the attacker wants to inject
            "data": {
                "vehicle_count_per_minute": 0,        # Attacker says road is empty
                "avg_speed_kmh": 200.0,               # Fake dangerous speed
                "congestion_level": "critical",
                "incident_detected": True,             # Fake incident
                "_modified_by_mitm": True,
            },
            # PQC signature is missing / forged — this is detected
            "pqc_signature": "FORGED_SIGNATURE_" + uuid.uuid4().hex[:16],
            "_attack_meta": {
                "attack_id": attack_id,
                "attack_type": "man_in_the_middle",
                "attacker_id": self.attacker_id,
                "original_device": target_device_id,
            },
        }

        topic = f"immunogrid/{target_sector}/mitm/{target_device_id}"
        try:
            await publish_callback(topic=topic, payload=json.dumps(intercepted_and_modified))
            success = True
        except Exception:
            success = False

        # PQC signature verification catches MITM ~94% of the time
        detected = random.random() < 0.94

        event = AttackEvent(
            attack_id=attack_id,
            attack_type=self.attack_type,
            target_device_id=target_device_id,
            target_sector=target_sector,
            timestamp=datetime.utcnow().isoformat(),
            success=success and not detected,
            detected=detected,
            payload=intercepted_and_modified,
        )
        self.log_attack(event)
        logger.warning("mitm_attack", attack_id=attack_id, target=target_device_id, detected=detected)
        return event
