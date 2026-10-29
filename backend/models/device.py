"""
ImmunoGrid — Device Models
Pydantic schemas for IoT device data.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class DeviceStatus(str, Enum):
    ONLINE      = "online"
    OFFLINE     = "offline"
    COMPROMISED = "compromised"
    QUARANTINED = "quarantined"
    HONEYPOT    = "honeypot"


class DeviceType(str, Enum):
    TRAFFIC_SENSOR   = "traffic_sensor"
    STREET_CAMERA    = "street_camera"
    WATER_MONITOR    = "water_monitor"
    HOSPITAL_DEVICE  = "hospital_device"
    POWER_SENSOR     = "power_sensor"
    METRO_SENSOR     = "metro_sensor"
    AIRPORT_DEVICE   = "airport_device"
    GOVT_OFFICE_NODE = "govt_office_node"


class BehaviorProfile(BaseModel):
    send_interval: float
    packet_size: int
    cpu_usage: float
    subnet: str
    active_hours: str


class DeviceBase(BaseModel):
    device_id: str
    device_type: DeviceType
    sector: str
    location: str
    status: DeviceStatus = DeviceStatus.ONLINE


class DeviceResponse(DeviceBase):
    message_count: int = 0
    attack_attempts: int = 0
    fingerprint_match: float = 1.0
    last_seen: datetime
    behavior_profile: Optional[BehaviorProfile] = None

    class Config:
        from_attributes = True


class DeviceMessage(BaseModel):
    device_id: str
    device_type: str
    sector: str
    location: str
    status: str
    timestamp: str
    sequence: int
    behavior: Dict[str, Any]
    data: Dict[str, Any]


class DeviceStats(BaseModel):
    total: int
    online: int
    compromised: int
    quarantined: int
    by_sector: Dict[str, Dict[str, int]]
    timestamp: str
