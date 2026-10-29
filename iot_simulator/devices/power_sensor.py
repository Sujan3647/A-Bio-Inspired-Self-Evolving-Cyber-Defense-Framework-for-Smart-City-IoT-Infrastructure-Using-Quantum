"""
ImmunoGrid — Power Grid Sensor
Simulates a smart power grid monitoring device.
"""

import random
from typing import Any, Dict

from .base_device import BaseDevice, DeviceType


class PowerSensor(BaseDevice):
    """
    Simulates a power grid sensor on a substation or transmission line.
    Sends: voltage, current, frequency, load, fault detection.
    """

    @property
    def device_type(self) -> DeviceType:
        return DeviceType.POWER_SENSOR

    @property
    def _base_send_interval(self) -> float:
        return 1.0  # power grid needs fast updates

    @property
    def _base_packet_size(self) -> int:
        return 56

    @property
    def _active_hours(self) -> tuple:
        return (0, 23)  # 24/7

    def generate_data(self) -> Dict[str, Any]:
        """Generate realistic power grid sensor readings."""
        fault = random.random() < 0.01  # 1% fault chance
        return {
            "voltage_v": round(random.uniform(218, 242) if not fault else random.uniform(150, 180), 2),
            "current_a": round(random.uniform(10, 100), 2),
            "frequency_hz": round(random.uniform(49.8, 50.2), 3),
            "power_factor": round(random.uniform(0.85, 1.0), 3),
            "load_percent": round(random.uniform(30, 95), 1),
            "active_power_kw": round(random.uniform(50, 500), 2),
            "reactive_power_kvar": round(random.uniform(5, 50), 2),
            "fault_detected": fault,
            "fault_type": random.choice(["overvoltage", "undervoltage", "overcurrent"]) if fault else None,
            "grid_zone": f"ZONE-{random.randint(1, 10)}",
            "transformer_temp_c": round(random.uniform(40, 85), 1),
        }
