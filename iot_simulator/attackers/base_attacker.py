"""
ImmunoGrid — Base Attacker
All hacker simulators inherit from this class.
"""

import asyncio
import json
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)


class AttackType(Enum):
    SPOOFING = "spoofing"
    MITM = "man_in_the_middle"
    DDOS = "ddos"
    DATA_POISONING = "data_poisoning"
    RANSOMWARE = "ransomware"
    REPLAY = "replay_attack"
    BYZANTINE = "byzantine_fault"


@dataclass
class AttackEvent:
    """Represents a single attack attempt."""
    attack_id: str
    attack_type: AttackType
    target_device_id: str
    target_sector: str
    timestamp: str
    success: bool
    detected: bool
    payload: Dict[str, Any]


class BaseAttacker(ABC):
    """
    Base class for all attack simulators.
    Simulates real-world hacking techniques against IoT devices.
    """

    def __init__(self, attacker_id: Optional[str] = None):
        self.attacker_id = attacker_id or f"attacker-{uuid.uuid4().hex[:8]}"
        self.attack_count = 0
        self.successful_attacks = 0
        self.detected_count = 0
        self.attack_log: List[AttackEvent] = []
        self._running = False

    @property
    @abstractmethod
    def attack_type(self) -> AttackType:
        pass

    @abstractmethod
    async def execute_attack(
        self,
        target_device_id: str,
        target_sector: str,
        publish_callback: Callable,
    ) -> AttackEvent:
        """Execute the attack against a target device."""
        pass

    def log_attack(self, event: AttackEvent):
        self.attack_log.append(event)
        self.attack_count += 1
        if event.success:
            self.successful_attacks += 1
        if event.detected:
            self.detected_count += 1

        logger.warning(
            "attack_executed",
            attacker_id=self.attacker_id,
            attack_type=self.attack_type.value,
            target=event.target_device_id,
            success=event.success,
            detected=event.detected,
        )

    def get_stats(self) -> Dict[str, Any]:
        detection_rate = (
            self.detected_count / self.attack_count * 100
            if self.attack_count > 0 else 0
        )
        return {
            "attacker_id": self.attacker_id,
            "attack_type": self.attack_type.value,
            "total_attacks": self.attack_count,
            "successful_attacks": self.successful_attacks,
            "detected_count": self.detected_count,
            "detection_rate_pct": round(detection_rate, 2),
        }
