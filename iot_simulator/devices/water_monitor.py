"""
ImmunoGrid — Water Pipeline Monitor
Simulates a smart water pipeline monitoring device.
"""

import random
from typing import Any, Dict

from .base_device import BaseDevice, DeviceType


class WaterMonitor(BaseDevice):
    """
    Simulates a water pipeline pressure and quality monitor.
    Sends: pressure, flow rate, pH, contamination alerts.
    """

    @property
    def device_type(self) -> DeviceType:
        return DeviceType.WATER_MONITOR

    @property
    def _base_send_interval(self) -> float:
        return 5.0  # sends every 5 seconds

    @property
    def _base_packet_size(self) -> int:
        return 52

    @property
    def _active_hours(self) -> tuple:
        return (0, 23)  # 24/7 monitoring

    def generate_data(self) -> Dict[str, Any]:
        """Generate realistic water pipeline readings."""
        # Occasional pressure anomaly (could indicate attack or pipe burst)
        pressure_anomaly = random.random() < 0.03
        base_pressure = random.uniform(2.0, 3.0)

        return {
            "pressure_bar": round(base_pressure * (2.5 if pressure_anomaly else 1.0), 3),
            "flow_rate_lpm": round(random.uniform(50, 200), 2),
            "ph_level": round(random.uniform(6.8, 7.4), 2),
            "turbidity_ntu": round(random.uniform(0.1, 2.0), 2),
            "chlorine_mg_l": round(random.uniform(0.2, 1.0), 3),
            "temperature_c": round(random.uniform(10, 25), 1),
            "contamination_alert": random.random() < 0.005,
            "valve_status": "open",
            "pipeline_id": f"PIPE-{random.randint(100, 999)}",
            "pressure_anomaly": pressure_anomaly,
        }
