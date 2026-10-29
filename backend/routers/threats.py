"""ImmunoGrid — Threat Intelligence Router"""
import random
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from routers.auth import get_current_user

router = APIRouter()

ATTACK_TYPES = ["spoofing", "ddos", "data_poisoning", "replay_attack", "man_in_the_middle"]
SEVERITIES = ["low", "medium", "high", "critical"]
SECTORS = ["traffic", "hospital", "water", "power", "surveillance"]


def _generate_mock_threats(count: int = 20):
    threats = []
    for i in range(count):
        ts = datetime.utcnow() - timedelta(minutes=random.randint(0, 1440))
        threats.append({
            "threat_id": f"THR-{i+1:06d}",
            "attack_type": random.choice(ATTACK_TYPES),
            "severity": random.choice(SEVERITIES),
            "target_sector": random.choice(SECTORS),
            "target_device": f"device-{random.randint(1, 500):04d}",
            "detected_by": random.choice(["quantum_fingerprint", "ai_brain", "honeypot"]),
            "status": random.choice(["detected", "mitigated", "investigating"]),
            "timestamp": ts.isoformat(),
            "morphogenesis_triggered": random.choice([True, False]),
            "confidence": round(random.uniform(0.75, 0.99), 3),
        })
    return sorted(threats, key=lambda x: x["timestamp"], reverse=True)


@router.get("/")
async def list_threats(current_user: dict = Depends(get_current_user)):
    """Return recent threat events."""
    return {"threats": _generate_mock_threats(50), "total": 50}


@router.get("/summary")
async def threat_summary(current_user: dict = Depends(get_current_user)):
    """Threat summary statistics."""
    return {
        "total_today": random.randint(8, 25),
        "critical": random.randint(0, 3),
        "high": random.randint(1, 5),
        "medium": random.randint(3, 10),
        "low": random.randint(2, 8),
        "detection_rate": "97.3%",
        "avg_response_time_ms": round(random.uniform(80, 350), 1),
        "by_type": {
            "spoofing": random.randint(2, 8),
            "ddos": random.randint(1, 5),
            "data_poisoning": random.randint(0, 4),
            "replay_attack": random.randint(0, 3),
        },
        "by_sector": {
            "traffic": random.randint(1, 5),
            "hospital": random.randint(0, 3),
            "water": random.randint(1, 4),
            "power": random.randint(0, 3),
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/live")
async def live_threats(current_user: dict = Depends(get_current_user)):
    """Real-time threat feed (last 5 minutes)."""
    return {"threats": _generate_mock_threats(5), "timestamp": datetime.utcnow().isoformat()}
