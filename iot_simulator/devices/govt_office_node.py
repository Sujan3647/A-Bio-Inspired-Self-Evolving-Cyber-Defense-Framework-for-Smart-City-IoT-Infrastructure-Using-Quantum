"""
ImmunoGrid — Government Office Network Node
Simulates smart government building network access devices.
"""

import random
from typing import Any, Dict
from .base_device import BaseDevice, DeviceType


class GovtOfficeNode(BaseDevice):
    """
    Simulates government office IoT network access nodes.
    Sends: network access logs, bandwidth usage, anomaly flags.
    """

    MINISTRIES = [
        "ministry-of-interior", "ministry-of-finance",
        "ministry-of-health", "national-security-office",
        "prime-minister-secretariat", "customs-authority",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ministry = random.choice(self.MINISTRIES)
        self.floor = random.randint(1, 10)

    @property
    def device_type(self) -> DeviceType:
        return DeviceType.GOVT_OFFICE_NODE

    @property
    def _base_send_interval(self) -> float:
        return 6.0

    @property
    def _base_packet_size(self) -> int:
        return 72

    @property
    def _active_hours(self) -> tuple:
        return (8, 18)  # Government office hours

    def generate_data(self) -> Dict[str, Any]:
        return {
            "ministry": self.ministry,
            "floor": self.floor,
            "active_users": random.randint(5, 80),
            "bandwidth_mbps": round(random.uniform(10, 1000), 2),
            "failed_logins": random.randint(0, 3),
            "unauthorized_access_attempt": random.random() < 0.01,
            "vpn_connections": random.randint(0, 20),
            "data_exfiltration_alert": random.random() < 0.003,
            "firewall_blocks_last_hour": random.randint(0, 50),
            "patch_status": random.choice(["up_to_date", "up_to_date", "pending"]),
            "encryption_active": True,
        }
