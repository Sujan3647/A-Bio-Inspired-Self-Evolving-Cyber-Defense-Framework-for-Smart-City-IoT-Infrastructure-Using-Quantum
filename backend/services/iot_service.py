"""
ImmunoGrid — IoT Service
Business logic for IoT device management and simulation control.
"""

import random
from datetime import datetime
from typing import Any, Dict, List, Optional
import structlog

logger = structlog.get_logger(__name__)

_city = None   # SmartCity instance

DEVICE_TYPES = [
    {"type": "traffic_sensor",   "count": 100, "sector": "traffic"},
    {"type": "street_camera",    "count": 80,  "sector": "surveillance"},
    {"type": "water_monitor",    "count": 60,  "sector": "water"},
    {"type": "hospital_device",  "count": 80,  "sector": "hospital"},
    {"type": "power_sensor",     "count": 80,  "sector": "power"},
    {"type": "metro_sensor",     "count": 50,  "sector": "metro"},
    {"type": "airport_device",   "count": 30,  "sector": "airport"},
    {"type": "govt_office_node", "count": 20,  "sector": "government"},
]

ATTACK_TYPES = [
    {"type": "spoofing",          "detection_rate": 95.2, "mechanism": "Quantum Fingerprint"},
    {"type": "man_in_the_middle", "detection_rate": 94.1, "mechanism": "PQC Signature"},
    {"type": "ddos",              "detection_rate": 88.3, "mechanism": "AI Brain (FAC)"},
    {"type": "data_poisoning",    "detection_rate": 91.7, "mechanism": "AI Brain (FAC)"},
    {"type": "replay_attack",     "detection_rate": 89.4, "mechanism": "Blockchain Nonce"},
    {"type": "ransomware",        "detection_rate": 93.0, "mechanism": "AI + Blockchain"},
]

SECTORS = ["traffic", "hospital", "water", "power", "surveillance", "metro", "airport", "government"]


def get_device_types() -> Dict:
    return {
        "device_types": DEVICE_TYPES,
        "total_devices": sum(d["count"] for d in DEVICE_TYPES),
        "total_sectors":  len(set(d["sector"] for d in DEVICE_TYPES)),
    }


def get_attack_types() -> Dict:
    overall = sum(a["detection_rate"] for a in ATTACK_TYPES) / len(ATTACK_TYPES)
    return {
        "attack_types": ATTACK_TYPES,
        "overall_detection_rate": round(overall, 1),
    }


def get_simulation_status() -> Dict:
    return {
        "running":             False,
        "devices_active":      0,
        "messages_per_second": 0,
        "attacks_per_minute":  0,
        "uptime_seconds":      0,
        "timestamp":           datetime.utcnow().isoformat(),
    }


def inject_attack(attack_type: str, target_sector: str, user_email: str) -> Dict:
    """Inject a test attack into the simulation."""
    detection_rate = next(
        (a["detection_rate"] for a in ATTACK_TYPES if a["type"] == attack_type),
        90.0,
    )
    detected = random.random() < (detection_rate / 100)
    return {
        "attack_id":          f"MANUAL-ATK-{datetime.utcnow().strftime('%H%M%S')}",
        "attack_type":        attack_type,
        "target_sector":      target_sector,
        "target_device":      f"{target_sector}-device-{random.randint(1,100):04d}",
        "injected_by":        user_email,
        "detected":           detected,
        "response_time_ms":   round(random.uniform(50, 400), 1),
        "morphogenesis_triggered": True,
        "timestamp":          datetime.utcnow().isoformat(),
    }


def generate_devices(count: int = 50, sector: Optional[str] = None) -> List[Dict]:
    """Generate mock device list."""
    devices = []
    for i in range(count):
        dev_sector = sector or random.choice(SECTORS)
        dev_type   = next((d["type"] for d in DEVICE_TYPES if d["sector"] == dev_sector),
                         "traffic_sensor")
        devices.append({
            "device_id":        f"{dev_sector}-device-{i+1:04d}",
            "device_type":      dev_type,
            "sector":           dev_sector,
            "status":           random.choice(["online","online","online","compromised","quarantined"]),
            "location":         f"zone-{random.randint(1,10)}",
            "last_seen":        datetime.utcnow().isoformat(),
            "fingerprint_match": round(random.uniform(0.88, 1.0), 4),
            "messages_sent":    random.randint(100, 10000),
            "attack_attempts":  random.randint(0, 5),
        })
    return devices
