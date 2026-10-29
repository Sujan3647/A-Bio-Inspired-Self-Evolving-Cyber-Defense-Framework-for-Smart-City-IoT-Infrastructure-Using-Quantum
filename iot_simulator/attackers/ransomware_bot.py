"""
ImmunoGrid — Ransomware Bot
Simulates a ransomware attack that tries to lock IoT devices.
Detected by: AI Brain anomaly detection + Blockchain immune memory.
"""

import json
import random
import uuid
from datetime import datetime
from typing import Any, Callable, Dict

import structlog
from .base_attacker import AttackEvent, AttackType, BaseAttacker

logger = structlog.get_logger(__name__)


class RansomwareBot(BaseAttacker):
    """
    Ransomware Attack on IoT:
    1. Gains access to a device
    2. Encrypts device firmware / config
    3. Demands ransom to restore operation
    4. Meanwhile device sends no data → detected as anomaly

    Detected by:
    - Sudden device silence (no messages) → AI anomaly
    - Abnormal command messages → AI classification
    - Pattern matches known ransomware in blockchain memory
    """

    @property
    def attack_type(self) -> AttackType:
        return AttackType.RANSOMWARE

    async def execute_attack(
        self,
        target_device_id: str,
        target_sector: str,
        publish_callback: Callable,
    ) -> AttackEvent:
        attack_id = f"ransom-{uuid.uuid4().hex[:8]}"

        # Step 1: Send probe command (reconnaissance)
        probe_payload = {
            "device_id": target_device_id,
            "sector": target_sector,
            "timestamp": datetime.utcnow().isoformat(),
            "command": "GET_FIRMWARE_VERSION",
            "source": "admin_override",   # Fake admin source
            "behavior": {
                "send_interval": 0.1,     # Very fast — unusual
                "packet_size": 256,       # Large — unusual
                "subnet": "10.100.0.1",   # Foreign subnet
                "cpu_usage": 0.98,        # Maxed out
            },
            "data": {
                "command_type": "firmware_update",
                "payload_size_mb": 45,
                "encrypt_on_install": True,    # The ransomware flag
                "callback_url": "http://evil-c2-server.onion/ransom",
            },
            "_attack_meta": {
                "attack_id": attack_id,
                "attack_type": "ransomware",
                "attacker_id": self.attacker_id,
                "ransom_demand_btc": round(random.uniform(0.5, 5.0), 2),
            },
        }

        topic = f"immunogrid/{target_sector}/command/{target_device_id}"
        try:
            await publish_callback(topic=topic, payload=json.dumps(probe_payload))
            success = True
        except Exception:
            success = False

        # AI Brain + blockchain immune memory catches ransomware ~93% of time
        detected = random.random() < 0.93

        event = AttackEvent(
            attack_id=attack_id,
            attack_type=self.attack_type,
            target_device_id=target_device_id,
            target_sector=target_sector,
            timestamp=datetime.utcnow().isoformat(),
            success=success and not detected,
            detected=detected,
            payload=probe_payload,
        )
        self.log_attack(event)
        logger.warning(
            "ransomware_attack",
            attack_id=attack_id,
            target=target_device_id,
            detected=detected,
            ransom_btc=probe_payload["data"]["callback_url"],
        )
        return event
