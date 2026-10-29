"""
ImmunoGrid — Simulation Control Router
API endpoints to start/stop/monitor the IoT city simulation.
"""

import random
from datetime import datetime
from fastapi import APIRouter, Depends
from routers.auth import get_current_user, require_roles
from models.user import UserRole

router = APIRouter()

# Simulation state (in-memory for demo)
_sim_state = {
    "running": False,
    "devices_active": 0,
    "started_at": None,
    "messages_processed": 0,
    "attacks_simulated": 0,
}


@router.get("/status")
async def simulation_status(current_user: dict = Depends(get_current_user)):
    """Get current simulation status."""
    is_running = _sim_state["running"]
    return {
        "status": "running" if is_running else "stopped",
        "running": is_running,
        "devices_online": 500 if is_running else 0,
        "devices_active": 500 if is_running else 0,
        "messages_sent": _sim_state["messages_processed"] + (random.randint(80, 150) if is_running else 0),
        "attacks_launched": _sim_state["attacks_simulated"],
        "detection_rate": round(random.uniform(95.0, 99.0), 1) if is_running else 0,
        "messages_per_second": round(random.uniform(80, 150), 1) if is_running else 0,
        "attacks_per_minute": round(random.uniform(5, 15), 1) if is_running else 0,
        "uptime_seconds": (datetime.utcnow() - datetime.fromisoformat(_sim_state["started_at"])).seconds
                          if _sim_state["started_at"] else 0,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/start")
async def start_simulation(
    current_user: dict = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.DEVOPS_ENGINEER, UserRole.CITY_IT_MANAGER
    )),
):
    """Start the IoT city simulation."""
    _sim_state["running"] = True
    _sim_state["started_at"] = datetime.utcnow().isoformat()
    _sim_state["devices_active"] = 500
    return {
        "status": "started",
        "devices": 500,
        "sectors": 8,
        "attackers": 8,
        "message": "ImmunoGrid city simulation started with 500 devices across 8 sectors",
        "started_by": current_user["email"],
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/stop")
async def stop_simulation(
    current_user: dict = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.DEVOPS_ENGINEER
    )),
):
    """Stop the IoT city simulation."""
    _sim_state["running"] = False
    _sim_state["devices_active"] = 0
    return {
        "status": "stopped",
        "stopped_by": current_user["email"],
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/inject-attack")
async def inject_attack(
    attack_type: str = "spoofing",
    target_sector: str = "traffic",
    current_user: dict = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.DEVOPS_ENGINEER, UserRole.QUANTUM_ANALYST
    )),
):
    """Manually inject an attack into the simulation for testing."""
    attack_id = f"MANUAL-ATK-{datetime.utcnow().strftime('%H%M%S')}"
    detected = random.random() > 0.05  # 95% detection rate
    morpho_actions = random.sample(
        ["spawn_honeypots", "increase_fp_sensitivity", "update_firewall",
         "quarantine_device", "broadcast_alert", "reroute_traffic"],
        k=random.randint(1, 3)
    ) if detected else []
    detected_by_options = ["quantum_fingerprint", "ai_brain", "honeypot", "blockchain_nonce"]
    _sim_state["attacks_simulated"] += 1
    _sim_state["messages_processed"] += random.randint(5, 20)
    return {
        "attack_id": attack_id,
        "attack_type": attack_type,
        "sector": target_sector,
        "target_sector": target_sector,
        "target_device": f"{target_sector}-device-{random.randint(1,100):04d}",
        "injected_by": current_user["email"],
        "detected": detected,
        "detected_by": random.choice(detected_by_options) if detected else None,
        "response_time_ms": round(random.uniform(50, 400), 1),
        "morphogenesis": morpho_actions,
        "morphogenesis_triggered": bool(morpho_actions),
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/device-types")
async def device_types(current_user: dict = Depends(get_current_user)):
    """List all simulated device types."""
    return {
        "device_types": [
            {"type": "traffic_sensor",   "count": 100, "sector": "traffic"},
            {"type": "street_camera",    "count": 80,  "sector": "surveillance"},
            {"type": "water_monitor",    "count": 60,  "sector": "water"},
            {"type": "hospital_device",  "count": 80,  "sector": "hospital"},
            {"type": "power_sensor",     "count": 80,  "sector": "power"},
            {"type": "metro_sensor",     "count": 50,  "sector": "metro"},
            {"type": "airport_device",   "count": 30,  "sector": "airport"},
            {"type": "govt_office_node", "count": 20,  "sector": "government"},
        ],
        "total_devices": 500,
        "total_sectors": 8,
    }


@router.get("/attack-types")
async def attack_types(current_user: dict = Depends(get_current_user)):
    """List all simulated attack types with detection rates."""
    return {
        "attack_types": [
            {"type": "spoofing",          "detection_rate": 95.2, "mechanism": "Quantum Fingerprint"},
            {"type": "man_in_the_middle", "detection_rate": 94.1, "mechanism": "PQC Signature"},
            {"type": "ddos",              "detection_rate": 88.3, "mechanism": "AI Brain (FAC)"},
            {"type": "data_poisoning",    "detection_rate": 91.7, "mechanism": "AI Brain (FAC)"},
            {"type": "replay_attack",     "detection_rate": 89.4, "mechanism": "Blockchain Nonce"},
            {"type": "ransomware",        "detection_rate": 93.0, "mechanism": "AI + Blockchain"},
        ],
        "overall_detection_rate": 97.3,
    }
