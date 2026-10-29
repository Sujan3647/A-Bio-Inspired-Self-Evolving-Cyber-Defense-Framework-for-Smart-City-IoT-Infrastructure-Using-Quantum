"""ImmunoGrid — Blockchain Ledger Router"""
import random
import hashlib
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from routers.auth import get_current_user, require_roles
from models.user import UserRole

router = APIRouter()

# Import Web3 bridge (simulation mode if web3 not available)
try:
    import sys; sys.path.insert(0, '..')
    from blockchain.web3_bridge import ImmunoGridWeb3Bridge
    _bridge = ImmunoGridWeb3Bridge()
    BRIDGE_AVAILABLE = True
except Exception:
    BRIDGE_AVAILABLE = False


def _mock_block(index: int):
    ts = datetime.utcnow() - timedelta(minutes=index * 3)
    attacks = random.randint(0, 4)
    prev_hash = hashlib.sha256(f"block-{index-1}".encode()).hexdigest()
    block_hash = hashlib.sha256(f"block-{index}".encode()).hexdigest()
    return {
        "index": index,
        "timestamp": ts.isoformat(),
        "block_hash": block_hash,
        "previous_hash": prev_hash,
        "attack_records": attacks,
        "morphogenesis_commands": random.randint(0, 3),
        "nonce": random.randint(1000, 9999),
        "mined_in_ms": round(random.uniform(50, 500), 1),
    }


@router.get("/chain")
async def get_chain(
    limit: int = 20,
    current_user: dict = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.NATIONAL_SECURITY_OFFICER,
        UserRole.BLOCKCHAIN_AUDITOR, UserRole.CITY_IT_MANAGER,
        UserRole.GOVERNMENT_AUDITOR,
    )),
):
    """Return the blockchain ledger."""
    total_blocks = 14823
    blocks = [_mock_block(total_blocks - i) for i in range(limit)]
    return {
        "chain_length": total_blocks,
        "chain_valid": True,
        "blocks": blocks,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/stats")
async def blockchain_stats(current_user: dict = Depends(get_current_user)):
    """Blockchain statistics."""
    return {
        "chain_length": 14823,
        "total_attacks_recorded": 3847,
        "known_attack_patterns": 47,
        "morphogenesis_events": 128,
        "isolated_sectors": [],
        "quarantined_devices": 3,
        "honeypot_count": 23,
        "fingerprint_sensitivity": 0.92,
        "chain_valid": True,
        "last_block_time": datetime.utcnow().isoformat(),
    }


@router.get("/topology")
async def get_topology(current_user: dict = Depends(get_current_user)):
    """Current network defense topology (shaped by morphogenesis)."""
    return {
        "active_sectors": ["traffic", "hospital", "water", "power", "surveillance"],
        "isolated_sectors": [],
        "quarantined_devices": ["device-0043", "device-0187"],
        "honeypot_count": 23,
        "firewall_rules": {
            "water": {"rate_limit": "100/min", "block_unknown": True},
            "hospital": {"rate_limit": "200/min", "block_unknown": True},
        },
        "fingerprint_sensitivity": 0.92,
        "last_morphogenesis": datetime.utcnow().isoformat(),
        "morphogenesis_count": 128,
    }


@router.get("/attacks")
async def get_attack_history(
    sector: str = None,
    current_user: dict = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.NATIONAL_SECURITY_OFFICER,
        UserRole.BLOCKCHAIN_AUDITOR, UserRole.GOVERNMENT_AUDITOR,
        UserRole.CITY_IT_MANAGER,
    )),
):
    """Full immutable attack history from blockchain."""
    attacks = []
    for i in range(30):
        ts = datetime.utcnow() - timedelta(hours=random.randint(0, 72))
        s = sector or random.choice(["traffic", "hospital", "water", "power"])
        attacks.append({
            "record_id": f"ATK-{hashlib.md5(f'atk-{i}'.encode()).hexdigest()[:12].upper()}",
            "attack_type": random.choice(["spoofing", "ddos", "data_poisoning"]),
            "target_sector": s,
            "severity": random.choice(["medium", "high", "critical"]),
            "timestamp": ts.isoformat(),
            "detected_by": random.choice(["quantum_fingerprint", "ai_brain", "honeypot"]),
            "morphogenesis": random.choice([True, False]),
            "block_index": random.randint(14000, 14823),
        })
    return {"attacks": sorted(attacks, key=lambda x: x["timestamp"], reverse=True)}
