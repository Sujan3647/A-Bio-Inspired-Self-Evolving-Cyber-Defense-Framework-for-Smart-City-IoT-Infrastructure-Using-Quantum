"""
ImmunoGrid — Street Camera Device
Simulates a smart city surveillance camera.
"""

import random
from typing import Any, Dict

from .base_device import BaseDevice, DeviceType


class StreetCamera(BaseDevice):
    """
    Simulates a smart street camera.
    Sends: motion alerts, crowd density, anomaly flags, stream metadata.
    """

    @property
    def device_type(self) -> DeviceType:
        return DeviceType.STREET_CAMERA

    @property
    def _base_send_interval(self) -> float:
        return 1.5  # sends every 1.5 seconds

    @property
    def _base_packet_size(self) -> int:
        return 96  # larger — includes metadata

    @property
    def _active_hours(self) -> tuple:
        return (0, 23)  # 24/7

    def generate_data(self) -> Dict[str, Any]:
        """Generate realistic camera metadata."""
        return {
            "motion_detected": random.random() < 0.3,
            "crowd_density": random.choice(["empty", "sparse", "moderate", "dense"]),
            "anomaly_flag": random.random() < 0.01,  # 1% anomaly
            "persons_detected": random.randint(0, 15),
            "vehicles_detected": random.randint(0, 8),
            "resolution": "1080p",
            "fps": 30,
            "night_mode": __import__("datetime").datetime.utcnow().hour < 6
                          or __import__("datetime").datetime.utcnow().hour > 20,
            "storage_used_gb": round(random.uniform(10, 500), 1),
            "signal_strength_dbm": random.randint(-90, -40),
        }
