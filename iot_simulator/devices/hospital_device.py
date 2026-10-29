"""
ImmunoGrid — Hospital Medical Device
Simulates smart hospital equipment.
"""

import random
from typing import Any, Dict

from .base_device import BaseDevice, DeviceType


class HospitalDevice(BaseDevice):
    """
    Simulates critical hospital medical equipment.
    Sends: patient vitals, device status, alert flags.
    """

    EQUIPMENT_TYPES = [
        "patient_monitor", "ventilator", "infusion_pump",
        "mri_scanner", "icu_monitor", "ecg_machine",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.equipment_type = random.choice(self.EQUIPMENT_TYPES)
        self.patient_id = f"PT-{random.randint(1000, 9999)}"

    @property
    def device_type(self) -> DeviceType:
        return DeviceType.HOSPITAL_DEVICE

    @property
    def _base_send_interval(self) -> float:
        return 3.0  # sends every 3 seconds

    @property
    def _base_packet_size(self) -> int:
        return 72

    @property
    def _active_hours(self) -> tuple:
        return (0, 23)  # 24/7 — critical care never stops

    def generate_data(self) -> Dict[str, Any]:
        """Generate realistic medical device readings."""
        return {
            "equipment_type": self.equipment_type,
            "patient_id": self.patient_id,
            "heart_rate_bpm": random.randint(55, 105),
            "blood_pressure_systolic": random.randint(110, 140),
            "blood_pressure_diastolic": random.randint(70, 90),
            "spo2_percent": round(random.uniform(95.0, 100.0), 1),
            "temperature_c": round(random.uniform(36.1, 37.5), 1),
            "respiratory_rate": random.randint(12, 20),
            "battery_level_pct": random.randint(20, 100),
            "alarm_active": random.random() < 0.02,
            "device_functional": True,
            "last_calibrated": "2026-01-15",
        }
