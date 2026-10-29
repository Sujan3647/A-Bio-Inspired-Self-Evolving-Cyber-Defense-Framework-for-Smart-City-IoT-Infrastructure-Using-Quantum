"""
ImmunoGrid — Metro / Transit Sensor
Simulates smart metro and public transport monitoring devices.
"""

import random
from typing import Any, Dict
from .base_device import BaseDevice, DeviceType


class MetroSensor(BaseDevice):
    """
    Simulates a metro/transit system sensor.
    Sends: passenger count, door status, speed, platform alerts.
    """

    STATION_NAMES = [
        "central-station", "airport-terminal", "city-mall",
        "government-district", "university", "hospital-junction",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.station = random.choice(self.STATION_NAMES)
        self.train_id = f"TRAIN-{random.randint(100, 999)}"

    @property
    def device_type(self) -> DeviceType:
        return DeviceType.METRO_SENSOR

    @property
    def _base_send_interval(self) -> float:
        return 3.0

    @property
    def _base_packet_size(self) -> int:
        return 60

    @property
    def _active_hours(self) -> tuple:
        return (5, 23)  # Metro runs 5am to 11pm

    def generate_data(self) -> Dict[str, Any]:
        hour = __import__("datetime").datetime.utcnow().hour
        rush_hour = (7 <= hour <= 9) or (17 <= hour <= 19)
        return {
            "station": self.station,
            "train_id": self.train_id,
            "passenger_count": random.randint(150, 500) if rush_hour else random.randint(20, 100),
            "platform_crowding": random.choice(["high", "medium"]) if rush_hour else "low",
            "train_speed_kmh": random.randint(0, 80),
            "door_status": random.choice(["open", "closed", "closed", "closed"]),
            "delay_minutes": random.randint(0, 5) if random.random() < 0.15 else 0,
            "emergency_alarm": random.random() < 0.005,
            "temperature_c": round(random.uniform(18, 30), 1),
            "ticket_gates_active": random.randint(3, 8),
            "cctv_operational": random.random() > 0.02,
        }
