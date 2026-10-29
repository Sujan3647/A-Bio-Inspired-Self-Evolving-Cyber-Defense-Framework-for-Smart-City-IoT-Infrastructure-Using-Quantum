"""ImmunoGrid — Dashboard Data Router"""
import random
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from routers.auth import get_current_user
from models.user import UserRole, ROLE_PERMISSIONS

router = APIRouter()


@router.get("/command-center")
async def command_center(current_user: dict = Depends(get_current_user)):
    """National Command Center — Super Admin / Security Officer dashboard data."""
    return {
        "system_health": round(random.uniform(97.0, 100.0), 1),
        "devices_online": random.randint(485, 500),
        "devices_total": 500,
        "attacks_today": random.randint(8, 25),
        "critical_alerts": random.randint(0, 3),
        "detection_rate": "97.3%",
        "blockchain_blocks": 14823,
        "ai_accuracy": "97.2%",
        "quantum_checks": random.randint(8000, 15000),
        "city_sectors": [
            {"sector": "traffic", "status": "normal", "devices": 120, "threats": 2},
            {"sector": "hospital", "status": "alert", "devices": 100, "threats": 1},
            {"sector": "water", "status": "normal", "devices": 80, "threats": 0},
            {"sector": "power", "status": "normal", "devices": 100, "threats": 1},
            {"sector": "surveillance", "status": "normal", "devices": 100, "threats": 0},
        ],
        "recent_attacks": [
            {"type": "spoofing", "sector": "hospital", "time": "2 min ago", "status": "mitigated"},
            {"type": "ddos", "sector": "traffic", "time": "15 min ago", "status": "mitigated"},
            {"type": "data_poisoning", "sector": "water", "time": "1 hr ago", "status": "mitigated"},
        ],
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/traffic")
async def traffic_dashboard(current_user: dict = Depends(get_current_user)):
    return {
        "sector": "traffic",
        "total_sensors": 120,
        "online": 118,
        "offline": 1,
        "compromised": 1,
        "fingerprint_match_rate": "99.2%",
        "data_integrity_score": "98.7%",
        "anomalies_today": 2,
        "avg_vehicle_count": random.randint(35, 75),
        "congestion_zones": random.randint(0, 5),
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/hospital")
async def hospital_dashboard(current_user: dict = Depends(get_current_user)):
    return {
        "sector": "hospital",
        "total_devices": 100,
        "online": 98,
        "device_types": {"icu_monitor": 20, "ventilator": 15, "infusion_pump": 30, "other": 35},
        "security_alerts": 1,
        "encryption_status": "all_encrypted",
        "hipaa_compliance": "compliant",
        "last_audit": datetime.utcnow().isoformat(),
        "critical_devices_secure": True,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/water")
async def water_dashboard(current_user: dict = Depends(get_current_user)):
    return {
        "sector": "water",
        "total_monitors": 80,
        "online": 79,
        "avg_pressure_bar": round(random.uniform(2.4, 3.0), 2),
        "avg_ph": round(random.uniform(6.9, 7.3), 2),
        "contamination_alerts": 0,
        "anomalies_today": 1,
        "data_integrity": "verified",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/power")
async def power_dashboard(current_user: dict = Depends(get_current_user)):
    return {
        "sector": "power",
        "total_sensors": 100,
        "online": 96,
        "avg_voltage": round(random.uniform(228, 232), 1),
        "avg_load_pct": round(random.uniform(55, 75), 1),
        "fault_alerts": random.randint(0, 2),
        "grid_stability": "stable",
        "anomalies_today": random.randint(0, 3),
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/compliance")
async def compliance_dashboard(current_user: dict = Depends(get_current_user)):
    return {
        "iso_27001": "compliant",
        "nist_csf": "compliant",
        "gdpr": "compliant",
        "total_incidents": 3847,
        "incidents_resolved": 3844,
        "incidents_open": 3,
        "audit_trail_complete": True,
        "last_audit_date": "2026-07-01",
        "next_audit_date": "2026-10-01",
        "blockchain_integrity": "verified",
        "report_generated": datetime.utcnow().isoformat(),
    }
