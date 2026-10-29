"""
ImmunoGrid — DDoS Attacker
Floods devices with fake traffic to overwhelm them.
"""

import asyncio
import json
import random
import uuid
from datetime import datetime
from typing import Any, Callable, Dict

import structlog

from .base_attacker import AttackEvent, AttackType, BaseAttacker

logger = structlog.get_logger(__name__)


class DDoSAttacker(BaseAttacker):
    """
    DDoS (Distributed Denial of Service) Attack:
    Floods a target device or sector with massive amounts of
    fake requests, overwhelming it and causing service outage.
    
    The AI Brain detects this via:
    - Abnormal message frequency
    - Multiple sources with similar patterns
    - Traffic volume anomaly
    """

    def __init__(self, *args, flood_rate: int = 100, **kwargs):
        super().__init__(*args, **kwargs)
        self.flood_rate = flood_rate  # messages per second

    @property
    def attack_type(self) -> AttackType:
        return AttackType.DDOS

    async def execute_attack(
        self,
        target_device_id: str,
        target_sector: str,
        publish_callback: Callable,
    ) -> AttackEvent:
        """
        Launch DDoS flood against a target sector.
        Sends hundreds of fake messages rapidly.
        """
        attack_id = f"ddos-{uuid.uuid4().hex[:8]}"
        messages_sent = 0

        logger.warning(
            "ddos_attack_started",
            attack_id=attack_id,
            target=target_device_id,
            flood_rate=self.flood_rate,
        )

        # Send a burst of flood messages
        burst_count = random.randint(50, 200)
        tasks = []

        for i in range(burst_count):
            # Each flood message pretends to come from a different device
            fake_device_id = f"flood-bot-{uuid.uuid4().hex[:6]}"
            flood_payload = {
                "device_id": fake_device_id,
                "device_type": "unknown",
                "sector": target_sector,
                "timestamp": datetime.utcnow().isoformat(),
                "sequence": i,
                "data": {"flood": True, "junk": random.randbytes(32).hex()},
                "_attack_meta": {
                    "attack_id": attack_id,
                    "attack_type": "ddos",
                    "flood_index": i,
                }
            }
            topic = f"immunogrid/{target_sector}/flood/{fake_device_id}"
            tasks.append(publish_callback(topic=topic, payload=json.dumps(flood_payload)))
            messages_sent += 1

        try:
            await asyncio.gather(*tasks, return_exceptions=True)
            success = True
        except Exception:
            success = False

        # AI anomaly detection catches DDoS ~88% of the time
        detected = random.random() < 0.88

        event = AttackEvent(
            attack_id=attack_id,
            attack_type=self.attack_type,
            target_device_id=target_device_id,
            target_sector=target_sector,
            timestamp=datetime.utcnow().isoformat(),
            success=success and not detected,
            detected=detected,
            payload={"messages_sent": messages_sent, "burst_count": burst_count},
        )

        self.log_attack(event)
        return event
