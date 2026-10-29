"""
ImmunoGrid — Base IoT Device
Every simulated device inherits from this class.
"""

import asyncio
import json
import random
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

import structlog

logger = structlog.get_logger(__name__)


class DeviceStatus(Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    COMPROMISED = "compromised"
    QUARANTINED = "quarantined"
    HONEYPOT = "honeypot"


class DeviceType(Enum):
    TRAFFIC_SENSOR  = "traffic_sensor"
    STREET_CAMERA   = "street_camera"
    WATER_MONITOR   = "water_monitor"
    HOSPITAL_DEVICE = "hospital_device"
    POWER_SENSOR    = "power_sensor"
    GOVT_OFFICE_NODE = "govt_office_node"
    METRO_SENSOR    = "metro_sensor"
    AIRPORT_DEVICE  = "airport_device"


@dataclass
class DeviceBehaviorProfile:
    """
    The behavioral fingerprint of a device.
    Used by the Quantum Engine to create quantum fingerprints.
    """
    device_id: str
    send_interval_seconds: float       # How often it sends data
    packet_size_bytes: int             # Average packet size
    active_hours_start: int            # Active from hour (0-23)
    active_hours_end: int              # Active until hour (0-23)
    avg_cpu_usage: float               # Average CPU % (0.0 - 1.0)
    subnet: str                        # Network subnet
    data_type_signature: str          # Type of data it sends
    # Tiny variations that make quantum fingerprinting possible
    timing_jitter_ms: float = field(default_factory=lambda: random.uniform(0.1, 2.0))
    size_variance_bytes: int = field(default_factory=lambda: random.randint(1, 5))


class BaseDevice(ABC):
    """
    Base class for all simulated IoT devices in ImmunoGrid.
    
    Each device:
    - Has a unique behavioral fingerprint (for quantum engine)
    - Sends encrypted data via MQTT
    - Can be attacked or compromised
    - Runs an internal mini AI (Federated Adversarial Consciousness)
    """

    def __init__(
        self,
        device_id: Optional[str] = None,
        location: str = "sector-unknown",
        sector: str = "general",
    ):
        self.device_id = device_id or f"{self.device_type.value}-{uuid.uuid4().hex[:8]}"
        self.location = location
        self.sector = sector
        self.status = DeviceStatus.ONLINE
        self.created_at = datetime.utcnow()
        self.last_seen = datetime.utcnow()
        self.message_count = 0
        self.attack_attempts = 0
        self.behavior_profile = self._generate_behavior_profile()
        self._running = False
        self._attack_log: list = []

        logger.info(
            "device_initialized",
            device_id=self.device_id,
            device_type=self.device_type.value,
            sector=self.sector,
            location=self.location,
        )

    @property
    @abstractmethod
    def device_type(self) -> DeviceType:
        """Every device must declare its type."""
        pass

    @abstractmethod
    def generate_data(self) -> Dict[str, Any]:
        """Generate the sensor reading / data payload."""
        pass

    def _generate_behavior_profile(self) -> DeviceBehaviorProfile:
        """
        Generate unique behavioral fingerprint for this device.
        Slightly different for every instance — this is what
        the quantum engine encodes as a quantum fingerprint.
        """
        return DeviceBehaviorProfile(
            device_id=self.device_id,
            send_interval_seconds=self._base_send_interval + random.uniform(-0.3, 0.3),
            packet_size_bytes=self._base_packet_size + random.randint(-3, 3),
            active_hours_start=self._active_hours[0],
            active_hours_end=self._active_hours[1],
            avg_cpu_usage=random.uniform(0.08, 0.25),
            subnet=f"192.168.{random.randint(1, 10)}.{random.randint(1, 254)}",
            data_type_signature=self.device_type.value,
        )

    @property
    def _base_send_interval(self) -> float:
        """Default send interval — overridden by subclasses."""
        return 2.0

    @property
    def _base_packet_size(self) -> int:
        """Default packet size — overridden by subclasses."""
        return 64

    @property
    def _active_hours(self) -> tuple:
        """Active hours (start, end) — overridden by subclasses."""
        return (0, 23)

    def _is_active_hour(self) -> bool:
        """Check if this device should be active right now."""
        current_hour = datetime.utcnow().hour
        return self._active_hours[0] <= current_hour <= self._active_hours[1]

    def build_message(self) -> Dict[str, Any]:
        """
        Build a complete MQTT message payload.
        Includes device metadata + sensor data.
        """
        sensor_data = self.generate_data()
        return {
            "device_id": self.device_id,
            "device_type": self.device_type.value,
            "sector": self.sector,
            "location": self.location,
            "status": self.status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "sequence": self.message_count,
            "behavior": {
                "send_interval": self.behavior_profile.send_interval_seconds,
                "packet_size": self.behavior_profile.packet_size_bytes,
                "subnet": self.behavior_profile.subnet,
                "cpu_usage": round(self.behavior_profile.avg_cpu_usage, 4),
            },
            "data": sensor_data,
        }

    def get_fingerprint_vector(self) -> Dict[str, float]:
        """
        Return the behavioral fingerprint as a numeric vector.
        This is fed into the Quantum Engine for fingerprint encoding.
        """
        return {
            "send_interval": self.behavior_profile.send_interval_seconds,
            "packet_size": float(self.behavior_profile.packet_size_bytes),
            "timing_jitter": self.behavior_profile.timing_jitter_ms,
            "size_variance": float(self.behavior_profile.size_variance_bytes),
            "cpu_usage": self.behavior_profile.avg_cpu_usage,
            "active_start": float(self.behavior_profile.active_hours_start),
            "active_end": float(self.behavior_profile.active_hours_end),
        }

    def mark_compromised(self, attack_type: str):
        """Mark this device as compromised."""
        self.status = DeviceStatus.COMPROMISED
        self.attack_attempts += 1
        self._attack_log.append({
            "attack_type": attack_type,
            "timestamp": datetime.utcnow().isoformat(),
        })
        logger.warning(
            "device_compromised",
            device_id=self.device_id,
            attack_type=attack_type,
        )

    def quarantine(self):
        """Quarantine this device — isolate from network."""
        self.status = DeviceStatus.QUARANTINED
        logger.warning("device_quarantined", device_id=self.device_id)

    def restore(self):
        """Restore device to normal operation."""
        self.status = DeviceStatus.ONLINE
        logger.info("device_restored", device_id=self.device_id)

    async def run(self, publish_callback=None):
        """
        Main device loop — continuously sends data.
        publish_callback: async function to call with each message.
        """
        self._running = True
        logger.info("device_started", device_id=self.device_id)

        while self._running:
            try:
                if self.status == DeviceStatus.ONLINE and self._is_active_hour():
                    message = self.build_message()
                    self.message_count += 1
                    self.last_seen = datetime.utcnow()

                    if publish_callback:
                        await publish_callback(
                            topic=f"immunogrid/{self.sector}/{self.device_type.value}/{self.device_id}",
                            payload=json.dumps(message),
                        )

                    logger.debug(
                        "device_message_sent",
                        device_id=self.device_id,
                        seq=self.message_count,
                    )

                await asyncio.sleep(self.behavior_profile.send_interval_seconds)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("device_error", device_id=self.device_id, error=str(e))
                await asyncio.sleep(1.0)

        logger.info("device_stopped", device_id=self.device_id)

    def stop(self):
        """Stop the device loop."""
        self._running = False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize device state."""
        return {
            "device_id": self.device_id,
            "device_type": self.device_type.value,
            "sector": self.sector,
            "location": self.location,
            "status": self.status.value,
            "message_count": self.message_count,
            "attack_attempts": self.attack_attempts,
            "created_at": self.created_at.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "fingerprint": self.get_fingerprint_vector(),
        }

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.device_id} status={self.status.value}>"
