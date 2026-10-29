"""
ImmunoGrid — Airport Security Device
Simulates smart airport security and operations monitoring.
"""

import random
from typing import Any, Dict
from .base_device import BaseDevice, DeviceType


class AirportDevice(BaseDevice):
    """
    Simulates airport security and operations IoT devices.
    Sends: scanner status, passenger flow, security alerts, gate info.
    """

    ZONES = ["terminal-1", "terminal-2", "runway-north", "cargo-bay", "immigration", "customs"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.zone = random.choice(self.ZONES)
        self.device_subtype = random.choice([
            "body_scanner", "baggage_xray", "passport_reader",
            "gate_sensor", "fuel_sensor", "runway_monitor",
        ])

    @property
    def device_type(self) -> DeviceType:
        return DeviceType.AIRPORT_DEVICE

    @property
    def _base_send_interval(self) -> float:
        return 4.0

    @property
    def _base_packet_size(self) -> int:
        return 80

    @property
    def _active_hours(self) -> tuple:
        return (0, 23)  # Airports never sleep

    def generate_data(self) -> Dict[str, Any]:
        return {
            "zone": self.zone,
            "device_subtype": self.device_subtype,
            "passengers_scanned": random.randint(0, 30),
            "security_alert": random.random() < 0.008,
            "queue_length": random.randint(0, 50),
            "processing_time_sec": round(random.uniform(5, 45), 1),
            "false_alarm_rate": round(random.uniform(0.001, 0.05), 4),
            "equipment_temperature_c": round(random.uniform(22, 40), 1),
            "network_latency_ms": round(random.uniform(5, 50), 2),
            "operational": random.random() > 0.01,
            "last_maintenance": "2026-07-01",
        }
