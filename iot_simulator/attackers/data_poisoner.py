"""
ImmunoGrid — Data Poisoning Attacker
Injects fake/manipulated sensor readings into the network.
"""

import json
import random
import uuid
from datetime import datetime
from typing import Any, Callable, Dict

import structlog

from .base_attacker import AttackEvent, AttackType, BaseAttacker

logger = structlog.get_logger(__name__)


class DataPoisoner(BaseAttacker):
    """
    Data Poisoning Attack:
    Injects subtly wrong sensor readings into the network.
    
    Examples:
    - Water pressure reads normal but is actually critical
    - Hospital vitals show healthy when patient is deteriorating
    - Power grid shows safe load when it's overloaded
    
    Detected by: AI anomaly detection + blockchain data integrity check
    """

    @property
    def attack_type(self) -> AttackType:
        return AttackType.DATA_POISONING

    async def execute_attack(
        self,
        target_device_id: str,
        target_sector: str,
        publish_callback: Callable,
    ) -> AttackEvent:
        """
        Inject poisoned data that looks almost legitimate.
        The subtle manipulation is caught by ML anomaly detection.
        """
        attack_id = f"poison-{uuid.uuid4().hex[:8]}"

        # Generate poisoned data based on sector type
        poisoned_data = self._generate_poisoned_payload(target_sector)

        poisoned_message = {
            "device_id": target_device_id,
            "device_type": self._guess_device_type(target_sector),
            "sector": target_sector,
            "location": "injected",
            "status": "online",
            "timestamp": datetime.utcnow().isoformat(),
            "sequence": random.randint(1, 9999),
            "behavior": {
                # Slightly off — gives away the poisoning
                "send_interval": random.uniform(1.5, 4.0),
                "packet_size": random.randint(40, 100),
                "subnet": "192.168.99.99",
                "cpu_usage": 0.0,
            },
            "data": poisoned_data,
            "_attack_meta": {
                "attack_id": attack_id,
                "attack_type": "data_poisoning",
                "attacker_id": self.attacker_id,
            }
        }

        topic = f"immunogrid/{target_sector}/poison/{target_device_id}"

        try:
            await publish_callback(
                topic=topic,
                payload=json.dumps(poisoned_message),
            )
            success = True
        except Exception:
            success = False

        # ML anomaly detection catches data poisoning ~91% of the time
        detected = random.random() < 0.91

        event = AttackEvent(
            attack_id=attack_id,
            attack_type=self.attack_type,
            target_device_id=target_device_id,
            target_sector=target_sector,
            timestamp=datetime.utcnow().isoformat(),
            success=success and not detected,
            detected=detected,
            payload=poisoned_data,
        )

        self.log_attack(event)

        logger.warning(
            "data_poisoning_attack",
            attack_id=attack_id,
            target=target_device_id,
            sector=target_sector,
            detected=detected,
        )

        return event

    def _generate_poisoned_payload(self, sector: str) -> Dict[str, Any]:
        """Generate sector-specific poisoned data."""
        if sector == "water":
            return {
                "pressure_bar": 0.1,           # Dangerously low (real: 2.5-3.0)
                "flow_rate_lpm": 0.0,           # No flow
                "ph_level": 4.2,               # Dangerously acidic (real: 6.8-7.4)
                "contamination_alert": False,   # Hiding the contamination
                "_poisoned": True,
            }
        elif sector == "hospital":
            return {
                "heart_rate_bpm": 72,           # Looks normal
                "spo2_percent": 98.0,           # Looks normal
                "blood_pressure_systolic": 120, # Looks normal
                # But actual device is in critical state — data is fabricated
                "_poisoned": True,
            }
        elif sector == "power":
            return {
                "voltage_v": 230.0,             # Looks normal
                "load_percent": 45.0,           # Looks safe
                "fault_detected": False,        # Hiding the fault
                # Real load is 98% — about to overload
                "_poisoned": True,
            }
        else:
            return {
                "value": random.uniform(-999, 999),
                "status": "normal",
                "_poisoned": True,
            }

    def _guess_device_type(self, sector: str) -> str:
        mapping = {
            "traffic": "traffic_sensor",
            "hospital": "hospital_device",
            "water": "water_monitor",
            "power": "power_sensor",
            "camera": "street_camera",
        }
        return mapping.get(sector, "unknown_device")
