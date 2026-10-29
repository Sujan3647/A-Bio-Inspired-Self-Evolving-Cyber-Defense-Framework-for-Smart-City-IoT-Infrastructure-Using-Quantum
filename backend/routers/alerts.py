"""ImmunoGrid — Alerts Router"""
import random
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from routers.auth import get_current_user

router = APIRouter()


@router.get("/")
async def get_alerts(current_user: dict = Depends(get_current_user)):
    alerts = []
    types = [
        ("🚨 CRITICAL: Spoofing attack on hospital sector — device quarantined", "critical"),
        ("⚠️  HIGH: DDoS flood detected on traffic network — rerouting", "high"),
        ("⚠️  HIGH: Data poisoning attempt on water pipeline — blocked", "high"),
        ("ℹ️  MEDIUM: Fingerprint mismatch on power sensor #042", "medium"),
        ("ℹ️  MEDIUM: Replay attack attempt detected and blocked", "medium"),
        ("✅ LOW: Honeypot trap triggered — attacker being studied", "low"),
    ]
    for i, (msg, severity) in enumerate(types):
        alerts.append({
            "alert_id": f"ALT-{i+1:06d}",
            "message": msg,
            "severity": severity,
            "acknowledged": i > 2,
            "timestamp": (datetime.utcnow() - timedelta(minutes=i * 12)).isoformat(),
            "sector": random.choice(["hospital", "traffic", "water", "power"]),
        })
    return {"alerts": alerts, "unread": 3}


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, current_user: dict = Depends(get_current_user)):
    return {"alert_id": alert_id, "acknowledged": True, "by": current_user["email"]}
