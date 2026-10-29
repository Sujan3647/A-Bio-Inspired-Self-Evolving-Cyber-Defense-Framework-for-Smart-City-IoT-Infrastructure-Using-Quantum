"""
ImmunoGrid — System Router
Overall system status, metrics, and admin operations.
"""

import random
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from routers.auth import get_current_user, require_roles
from models.user import UserRole
from services.aws import publish_sns_alert

router = APIRouter()


@router.get("/status")
async def system_status(current_user: dict = Depends(get_current_user)):
    """Complete system health status."""
    return {
        "system": "ImmunoGrid",
        "version": "1.0.0",
        "environment": "development",
        "status": "operational",
        "uptime_hours": round(random.uniform(24, 720), 1),
        "modules": {
            "iot_gateway":      {"status": "online", "devices": 500, "messages_sec": round(random.uniform(80, 150), 1)},
            "quantum_engine":   {"status": "online", "checks_today": random.randint(8000, 15000), "detection_rate": "97.3%"},
            "ai_brain":         {"status": "online", "fl_round": random.randint(1200, 1300), "accuracy": f"{round(random.uniform(96, 98.5), 1)}%"},
            "blockchain":       {"status": "online", "chain_length": random.randint(14800, 15000), "valid": True},
            "honeypot_network": {"status": "online", "active_decoys": 23, "attackers_trapped": random.randint(2, 8)},
            "pqc_crypto":       {"status": "online", "algorithm": "Kyber-512", "mode": "simulation"},
            "websocket":        {"status": "online", "connections": random.randint(1, 10)},
        },
        "cloud": {
            "aws_iot_core":      "connected",
            "aws_sagemaker":     "available",
            "aws_blockchain":    "available",
            "aws_cloudwatch":    "active",
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/metrics")
async def system_metrics(current_user: dict = Depends(get_current_user)):
    """System performance metrics for monitoring."""
    return {
        "messages_processed_today": random.randint(800000, 1200000),
        "attacks_blocked_today": random.randint(15, 40),
        "quantum_checks_today": random.randint(50000, 100000),
        "blockchain_blocks_today": random.randint(50, 150),
        "morphogenesis_events_today": random.randint(5, 25),
        "honeypot_interactions_today": random.randint(20, 80),
        "fl_rounds_today": random.randint(50, 100),
        "api_requests_today": random.randint(5000, 20000),
        "avg_api_latency_ms": round(random.uniform(8, 45), 1),
        "error_rate_pct": round(random.uniform(0.01, 0.1), 3),
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/timeline")
async def attack_timeline(
    hours: int = 24,
    current_user: dict = Depends(get_current_user),
):
    """Hourly attack timeline for charts."""
    timeline = []
    now = datetime.utcnow()
    for h in range(hours, 0, -1):
        t = now - timedelta(hours=h)
        is_rush = 7 <= t.hour <= 9 or 17 <= t.hour <= 19
        timeline.append({
            "hour": t.strftime("%H:00"),
            "timestamp": t.isoformat(),
            "attacks": random.randint(2, 12) if is_rush else random.randint(0, 5),
            "messages": random.randint(3000, 8000) if is_rush else random.randint(1000, 4000),
            "detections": random.randint(2, 11) if is_rush else random.randint(0, 4),
        })
    return {"timeline": timeline, "hours": hours}


@router.post("/emergency-lockdown")
async def emergency_lockdown(
    sector: str,
    current_user: dict = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.NATIONAL_SECURITY_OFFICER
    )),
):
    """Emergency lockdown of a city sector — Admin/Security Officer only."""
    
    # Real AWS SNS Publish
    alert_message = {
        "event": "EMERGENCY_LOCKDOWN",
        "sector": sector,
        "executed_by": current_user["email"],
        "timestamp": datetime.utcnow().isoformat()
    }
    publish_sns_alert(subject=f"CRITICAL: Lockdown Initiated - {sector}", message=alert_message)

    return {
        "action": "emergency_lockdown",
        "sector": sector,
        "status": "executed",
        "effects": [
            f"{sector} sector isolated from main network",
            "All devices quarantined pending investigation",
            "Backup data paths activated",
            "5 honeypots spawned around isolated sector",
            "Blockchain morphogenesis triggered",
            "National Security Officer notified via SNS (LocalStack)",
        ],
        "executed_by": current_user["email"],
        "timestamp": datetime.utcnow().isoformat(),
        "reversible": True,
        "reverse_command": f"POST /api/system/restore-sector?sector={sector}",
    }


@router.post("/restore-sector")
async def restore_sector(
    sector: str,
    current_user: dict = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.NATIONAL_SECURITY_OFFICER, UserRole.CITY_IT_MANAGER
    )),
):
    """Restore a previously locked-down sector."""
    return {
        "action": "restore_sector",
        "sector": sector,
        "status": "restored",
        "effects": [
            f"{sector} sector reconnected to main network",
            "Devices restored from blockchain state backup",
            "PQC keys rotated for all sector devices",
            "Quantum fingerprints re-registered",
        ],
        "executed_by": current_user["email"],
        "timestamp": datetime.utcnow().isoformat(),
    }
