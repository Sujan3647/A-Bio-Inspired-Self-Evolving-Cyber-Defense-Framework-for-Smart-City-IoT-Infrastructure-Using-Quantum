"""
ImmunoGrid — Replay Attacker
Captures a legitimate message and replays it later.
Detected by: sequence number check + timestamp validation + blockchain nonce.
"""

import json
import random
import uuid
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List

import structlog
from .base_attacker import AttackEvent, AttackType, BaseAttacker

logger = structlog.get_logger(__name__)


class ReplayAttacker(BaseAttacker):
    """
    Replay Attack:
    Records a legitimate message and re-sends it at a later time.
    The goal is to fool the system into thinking an old valid
    message is a new one — bypassing authentication.

    Detected by:
    - Timestamp is old (stale message)
    - Sequence number is repeated
    - Blockchain nonce already used
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._captured_messages: List[Dict] = []

    def capture_message(self, message: Dict):
        """Store a message for later replay."""
        self._captured_messages.append({
            "captured_at": datetime.utcnow().isoformat(),
            "message": message,
        })

    @property
    def attack_type(self) -> AttackType:
        return AttackType.REPLAY

    async def execute_attack(
        self,
        target_device_id: str,
        target_sector: str,
        publish_callback: Callable,
    ) -> AttackEvent:
        attack_id = f"replay-{uuid.uuid4().hex[:8]}"

        # Simulate a captured message from the past
        past_time = datetime.utcnow() - timedelta(minutes=random.randint(5, 60))
        replayed_message = {
            "device_id": target_device_id,
            "device_type": "traffic_sensor",
            "sector": target_sector,
            "status": "online",
            # Old timestamp — this is what gets detected
            "timestamp": past_time.isoformat(),
            # Repeated old sequence number — detected by blockchain
            "sequence": random.randint(1, 100),
            "behavior": {
                "send_interval": 2.347,
                "packet_size": 48,
                "subnet": "192.168.1.5",
                "cpu_usage": 0.142,
            },
            "data": {
                "vehicle_count_per_minute": random.randint(10, 50),
                "avg_speed_kmh": random.uniform(30, 70),
                "congestion_level": "low",
                "incident_detected": False,
            },
            "_attack_meta": {
                "attack_id": attack_id,
                "attack_type": "replay_attack",
                "attacker_id": self.attacker_id,
                "original_capture_time": past_time.isoformat(),
                "replay_delay_minutes": (datetime.utcnow() - past_time).seconds // 60,
            },
        }

        topic = f"immunogrid/{target_sector}/replay/{target_device_id}"
        try:
            await publish_callback(topic=topic, payload=json.dumps(replayed_message))
            success = True
        except Exception:
            success = False

        # Timestamp + sequence check catches replay ~89% of the time
        detected = random.random() < 0.89

        event = AttackEvent(
            attack_id=attack_id,
            attack_type=self.attack_type,
            target_device_id=target_device_id,
            target_sector=target_sector,
            timestamp=datetime.utcnow().isoformat(),
            success=success and not detected,
            detected=detected,
            payload=replayed_message,
        )
        self.log_attack(event)
        logger.warning("replay_attack", attack_id=attack_id, target=target_device_id, detected=detected)
        return event
