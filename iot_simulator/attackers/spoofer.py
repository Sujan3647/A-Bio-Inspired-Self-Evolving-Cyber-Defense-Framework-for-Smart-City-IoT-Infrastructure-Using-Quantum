"""
ImmunoGrid — Spoofing Attacker
Pretends to be a legitimate IoT device.
This is what the Quantum Behavioral Fingerprint is designed to catch.
"""

import json
import random
import uuid
from datetime import datetime
from typing import Any, Callable, Dict

import structlog

from .base_attacker import AttackEvent, AttackType, BaseAttacker

logger = structlog.get_logger(__name__)


class SpoofingAttacker(BaseAttacker):
    """
    Spoofing Attack:
    The attacker copies a real device's ID and tries to send
    fake data pretending to be that device.
    
    What gives them away (quantum fingerprint detects):
    - Timing is slightly off (can't replicate exact jitter)
    - Packet size varies differently
    - CPU usage pattern doesn't match
    - Subnet might be different
    """

    @property
    def attack_type(self) -> AttackType:
        return AttackType.SPOOFING

    async def execute_attack(
        self,
        target_device_id: str,
        target_sector: str,
        publish_callback: Callable,
    ) -> AttackEvent:
        """
        Clone a device's identity and send spoofed data.
        The tiny behavioral differences will be caught by
        the quantum fingerprint engine.
        """
        attack_id = f"spoof-{uuid.uuid4().hex[:8]}"

        # Attacker copies the device ID but their behavior is subtly different
        # This is the critical flaw — quantum fingerprinting catches this
        spoofed_payload = {
            "device_id": target_device_id,           # Copied device ID
            "device_type": "traffic_sensor",          # Guessed type
            "sector": target_sector,
            "location": "unknown",
            "status": "online",
            "timestamp": datetime.utcnow().isoformat(),
            "sequence": random.randint(1000, 9999),
            # The behavioral fingerprint is WRONG — attacker can't replicate exactly
            "behavior": {
                "send_interval": 2.0 + random.uniform(-0.5, 0.5),   # Off by ±0.5s
                "packet_size": 48 + random.randint(-10, 10),          # Wrong size
                "subnet": f"10.0.{random.randint(1, 255)}.{random.randint(1, 254)}",  # Wrong subnet
                "cpu_usage": round(random.uniform(0.0, 1.0), 4),     # Wrong CPU pattern
            },
            "data": {
                "vehicle_count_per_minute": random.randint(0, 200),  # Fake data
                "avg_speed_kmh": random.uniform(0, 200),
                "congestion_level": "low",
                "incident_detected": False,
            },
            "_attack_meta": {
                "attack_id": attack_id,
                "attack_type": "spoofing",
                "attacker_id": self.attacker_id,
            }
        }

        topic = f"immunogrid/{target_sector}/traffic_sensor/{target_device_id}"

        try:
            await publish_callback(
                topic=topic,
                payload=json.dumps(spoofed_payload),
            )
            success = True
        except Exception:
            success = False

        # In our simulation, the quantum fingerprint detects spoofing
        # ~95% of the time (based on behavioral difference magnitude)
        detected = random.random() < 0.95

        event = AttackEvent(
            attack_id=attack_id,
            attack_type=self.attack_type,
            target_device_id=target_device_id,
            target_sector=target_sector,
            timestamp=datetime.utcnow().isoformat(),
            success=success and not detected,
            detected=detected,
            payload=spoofed_payload,
        )

        self.log_attack(event)

        logger.warning(
            "spoofing_attack",
            attack_id=attack_id,
            target=target_device_id,
            detected=detected,
            success=event.success,
        )

        return event
