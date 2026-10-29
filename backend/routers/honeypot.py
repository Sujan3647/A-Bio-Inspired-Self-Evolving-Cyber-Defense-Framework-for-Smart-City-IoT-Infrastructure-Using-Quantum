"""
ImmunoGrid — Honeypot Network Router
API endpoints for honeypot management and intelligence reports.
"""

import random
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from routers.auth import get_current_user, require_roles
from models.user import UserRole

router = APIRouter()

SECTORS = ["traffic", "hospital", "water", "power", "surveillance"]
ATTACK_TYPES = ["spoofing", "ddos", "data_poisoning", "replay_attack", "mitm"]


def _mock_honeypots(count: int = 23):
    honeypots = []
    for i in range(count):
        sector = random.choice(SECTORS)
        ts = datetime.utcnow() - timedelta(minutes=random.randint(0, 1440))
        honeypots.append({
            "honeypot_id": f"honeypot-{i+1:04d}",
            "mimics_device": f"{sector}-device-{random.randint(1,100):04d}",
            "sector": sector,
            "active": True,
            "interactions_captured": random.randint(0, 8),
            "attackers_trapped": random.randint(0, 3),
            "created_at": ts.isoformat(),
            "last_interaction": (ts + timedelta(minutes=random.randint(0, 60))).isoformat()
                                if random.random() > 0.4 else None,
        })
    return honeypots


def _mock_intelligence_reports(count: int = 10):
    reports = []
    for i in range(count):
        ts = datetime.utcnow() - timedelta(hours=random.randint(1, 48))
        reports.append({
            "report_id": f"RPT-{i+1:06d}",
            "honeypot_id": f"honeypot-{random.randint(1,23):04d}",
            "attacker_id": f"atk-{random.randint(1000,9999)}",
            "attack_types": random.sample(ATTACK_TYPES, k=random.randint(1, 2)),
            "total_interactions": random.randint(1, 15),
            "target_sectors": random.sample(SECTORS, k=random.randint(1, 2)),
            "recommended_defenses": random.randint(2, 5),
            "ai_samples_generated": random.randint(5, 20),
            "generated_at": ts.isoformat(),
            "added_to_blockchain": True,
        })
    return sorted(reports, key=lambda x: x["generated_at"], reverse=True)


@router.get("/stats")
async def honeypot_stats(current_user: dict = Depends(get_current_user)):
    """Honeypot network statistics."""
    return {
        "active_honeypots": 23,
        "total_spawned": 47,
        "attackers_trapped_today": random.randint(2, 8),
        "total_interactions_captured": random.randint(80, 200),
        "intelligence_reports": 10,
        "ai_samples_fed_back": random.randint(150, 400),
        "top_attacked_sector": random.choice(SECTORS),
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/active")
async def list_active_honeypots(current_user: dict = Depends(get_current_user)):
    """List all active honeypot decoys."""
    honeypots = _mock_honeypots(23)
    return {"honeypots": honeypots, "total": len(honeypots)}


@router.get("/intelligence")
async def intelligence_reports(
    current_user: dict = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.NATIONAL_SECURITY_OFFICER,
        UserRole.CITY_IT_MANAGER, UserRole.QUANTUM_ANALYST,
    )),
):
    """Intelligence reports generated from honeypot captures."""
    reports = _mock_intelligence_reports(10)
    return {"reports": reports, "total": len(reports)}


@router.get("/intelligence/{report_id}")
async def get_intelligence_report(
    report_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get a specific intelligence report."""
    sector = random.choice(SECTORS)
    attack_type = random.choice(ATTACK_TYPES)
    return {
        "report_id": report_id,
        "honeypot_id": "honeypot-0007",
        "attacker_profile": {
            "attacker_id": "atk-4721",
            "attack_types": [attack_type],
            "behavioral_signature": {
                "avg_send_interval": round(random.uniform(0.1, 3.0), 3),
                "avg_packet_size": random.randint(30, 200),
                "unique_subnets": ["10.0.0.42", "10.0.0.43"],
                "interaction_count": random.randint(3, 15),
            },
            "target_sectors": [sector],
            "total_attempts": random.randint(3, 20),
            "success_rate": 0.0,
        },
        "recommended_defenses": [
            f"Increase quantum fingerprint sensitivity to 0.95 for {sector}",
            "Spawn 3 additional honeypots in attacked zone",
            "Add attacker subnet 10.0.0.42/43 to firewall blocklist",
            "Update AI model with 12 new adversarial training samples",
        ],
        "ai_samples_generated": 12,
        "added_to_blockchain": True,
        "blockchain_hash": "0x7a3f...d82c",
        "generated_at": datetime.utcnow().isoformat(),
    }


@router.post("/spawn")
async def spawn_honeypots(
    sector: str,
    count: int = 3,
    current_user: dict = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.NATIONAL_SECURITY_OFFICER, UserRole.CITY_IT_MANAGER
    )),
):
    """Manually spawn honeypot decoys in a sector."""
    new_honeypots = [
        {
            "honeypot_id": f"honeypot-manual-{i+1:04d}",
            "sector": sector,
            "active": True,
            "created_at": datetime.utcnow().isoformat(),
        }
        for i in range(count)
    ]
    return {
        "spawned": count,
        "sector": sector,
        "honeypots": new_honeypots,
        "spawned_by": current_user["email"],
        "timestamp": datetime.utcnow().isoformat(),
    }
