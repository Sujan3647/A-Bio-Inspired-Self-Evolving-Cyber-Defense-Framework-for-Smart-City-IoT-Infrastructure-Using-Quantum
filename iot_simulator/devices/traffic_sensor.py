"""
ImmunoGrid — Traffic Sensor Device
Simulates a smart city traffic monitoring sensor.
"""

import random
from typing import Any, Dict

from .base_device import BaseDevice, DeviceType


class TrafficSensor(BaseDevice):
    """
    Simulates a traffic sensor at a road intersection.
    Sends: vehicle count, speed, congestion level, incident flags.
    """

    @property
    def device_type(self) -> DeviceType:
        return DeviceType.TRAFFIC_SENSOR

    @property
    def _base_send_interval(self) -> float:
        return 2.0  # sends every 2 seconds

    @property
    def _base_packet_size(self) -> int:
        return 48

    @property
    def _active_hours(self) -> tuple:
        return (5, 23)  # active 5am to 11pm

    def generate_data(self) -> Dict[str, Any]:
        """Generate realistic traffic sensor readings."""
        hour = __import__("datetime").datetime.utcnow().hour
        # More traffic during rush hours
        is_rush_hour = 7 <= hour <= 9 or 17 <= hour <= 19
        base_count = random.randint(30, 80) if is_rush_hour else random.randint(5, 25)

        return {
            "vehicle_count_per_minute": base_count + random.randint(-3, 3),
            "avg_speed_kmh": round(random.uniform(15, 60) if is_rush_hour else random.uniform(40, 90), 1),
            "congestion_level": random.choice(["low", "medium", "high"]) if is_rush_hour else "low",
            "incident_detected": random.random() < 0.02,  # 2% chance
            "pedestrian_count": random.randint(0, 20),
            "signal_phase": random.choice(["red", "green", "yellow"]),
            "weather_condition": random.choice(["clear", "rain", "fog"]),
            "sensor_temperature_c": round(random.uniform(20, 45), 1),
        }
