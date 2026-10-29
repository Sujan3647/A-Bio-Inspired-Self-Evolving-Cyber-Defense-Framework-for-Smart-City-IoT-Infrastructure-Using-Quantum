"""ImmunoGrid — Devices Router"""
import random
from datetime import datetime
from fastapi import APIRouter, Depends
from routers.auth import get_current_user, require_roles
from models.user import UserRole, ROLE_PERMISSIONS

router = APIRouter()

SECTORS = ["traffic", "hospital", "water", "power", "surveillance", "government"]
DEVICE_TYPES = ["traffic_sensor", "street_camera", "water_monitor", "hospital_device", "power_sensor"]


def _generate_mock_devices(count: int = 50):
    devices = []
    for i in range(count):
        sector = random.choice(SECTORS)
        devices.append({
            "device_id": f"{sector}-device-{i+1:04d}",
            "device_type": random.choice(DEVICE_TYPES),
            "sector": sector,
            "status": random.choice(["online", "online", "online", "online", "compromised", "quarantined"]),
            "location": f"zone-{random.randint(1,10)}",
            "last_seen": datetime.utcnow().isoformat(),
            "fingerprint_match": round(random.uniform(0.88, 1.0), 4),
            "messages_sent": random.randint(100, 10000),
            "attack_attempts": random.randint(0, 5),
        })
    return devices


@router.get("/")
async def list_devices(current_user: dict = Depends(get_current_user)):
    """List IoT devices filtered by user's authorized sectors."""
    permissions = ROLE_PERMISSIONS.get(current_user["role"], {})
    authorized_sectors = permissions.get("sectors", [])

    all_devices = _generate_mock_devices(500)

    if permissions.get("can_view_all"):
        return {"devices": all_devices, "total": len(all_devices)}

    filtered = [d for d in all_devices if d["sector"] in authorized_sectors]
    return {"devices": filtered, "total": len(filtered)}


@router.get("/stats")
async def device_stats(current_user: dict = Depends(get_current_user)):
    """Device statistics summary."""
    return {
        "total": 500,
        "online": 487,
        "compromised": 8,
        "quarantined": 5,
        "by_sector": {
            "traffic": {"total": 120, "online": 118},
            "hospital": {"total": 100, "online": 98},
            "water": {"total": 80, "online": 79},
            "power": {"total": 100, "online": 96},
            "surveillance": {"total": 100, "online": 96},
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/{device_id}")
async def get_device(device_id: str, current_user: dict = Depends(get_current_user)):
    """Get details of a specific device."""
    return {
        "device_id": device_id,
        "status": "online",
        "fingerprint_match": 0.9834,
        "last_seen": datetime.utcnow().isoformat(),
        "sector": "traffic",
        "location": "zone-3",
        "messages_sent": 4523,
        "attack_attempts": 1,
        "behavior_profile": {
            "send_interval": 2.347,
            "packet_size": 47,
            "cpu_usage": 0.142,
            "active_hours": "06:00-22:00",
        },
    }
