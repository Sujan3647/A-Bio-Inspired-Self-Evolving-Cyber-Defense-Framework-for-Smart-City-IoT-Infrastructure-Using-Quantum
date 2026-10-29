"""
ImmunoGrid — Threat Models
Pydantic schemas for threat/attack events.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class AttackType(str, Enum):
    SPOOFING       = "spoofing"
    MITM           = "man_in_the_middle"
    DDOS           = "ddos"
    DATA_POISONING = "data_poisoning"
    REPLAY         = "replay_attack"
    RANSOMWARE     = "ransomware"
    BYZANTINE      = "byzantine_fault"
    UNKNOWN        = "unknown"


class Severity(str, Enum):
    LOW      = "low"
    MEDIUM   = "medium"
    HIGH     = "high"
    CRITICAL = "critical"


class ThreatStatus(str, Enum):
    DETECTED     = "detected"
    INVESTIGATING = "investigating"
    MITIGATED    = "mitigated"
    RESOLVED     = "resolved"


class DetectionMechanism(str, Enum):
    QUANTUM_FINGERPRINT = "quantum_fingerprint"
    AI_BRAIN            = "ai_brain"
    HONEYPOT            = "honeypot"
    BLOCKCHAIN_MEMORY   = "blockchain_memory"
    PQC_SIGNATURE       = "pqc_signature"
    COMBINED            = "combined"


class ThreatEvent(BaseModel):
    threat_id: str
    attack_type: AttackType
    severity: Severity
    target_sector: str
    target_device: str
    detected_by: DetectionMechanism
    status: ThreatStatus
    confidence: float
    timestamp: datetime
    morphogenesis_triggered: bool = False
    response_actions: List[str] = []
    attacker_signature: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class ThreatSummary(BaseModel):
    total_today: int
    critical: int
    high: int
    medium: int
    low: int
    detection_rate: str
    avg_response_time_ms: float
    by_type: Dict[str, int]
    by_sector: Dict[str, int]
    timestamp: str


class BlockchainAttackRecord(BaseModel):
    record_id: str
    attack_type: AttackType
    target_sector: str
    severity: Severity
    timestamp: str
    detected_by: str
    morphogenesis: bool
    block_index: int
    data_hash: str
