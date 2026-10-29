"""
ImmunoGrid — Blockchain Service
Business logic for morphogenetic blockchain operations.
"""

import random
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import structlog

logger = structlog.get_logger(__name__)

_blockchain = None
_bridge     = None


def get_blockchain():
    """Lazy-load blockchain singleton."""
    global _blockchain
    if _blockchain is None:
        try:
            import sys, os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
            from blockchain.immune_ledger import MorphogeneticBlockchain
            _blockchain = MorphogeneticBlockchain(difficulty=1)
            logger.info("blockchain_service_loaded")
        except Exception as e:
            logger.warning("blockchain_load_failed", error=str(e))
    return _blockchain


def get_bridge():
    """Lazy-load Web3 bridge singleton."""
    global _bridge
    if _bridge is None:
        try:
            import sys, os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
            from blockchain.web3_bridge import ImmunoGridWeb3Bridge
            _bridge = ImmunoGridWeb3Bridge()
        except Exception as e:
            logger.warning("web3_bridge_load_failed", error=str(e))
    return _bridge


def record_attack(
    attack_type: str, device_id: str, sector: str,
    attacker_sig: Dict, detected_by: str, severity: str = "high"
) -> Dict:
    """Record an attack on the blockchain."""
    bc = get_blockchain()
    if bc:
        record = bc.record_attack(
            attack_type, device_id, sector, attacker_sig, detected_by, severity
        )
        return {
            "record_id":   record.record_id,
            "morphogenesis": record.morphogenesis_triggered,
            "actions":     record.response_actions,
            "chain_valid": bc.is_chain_valid(),
        }

    bridge = get_bridge()
    if bridge:
        return bridge.record_attack(attack_type, device_id, sector, severity, detected_by)

    # Simulation
    return {
        "record_id":   f"ATK-{hashlib.md5(f'{attack_type}{device_id}'.encode()).hexdigest()[:12].upper()}",
        "morphogenesis": True,
        "actions":     ["broadcast_alert", "spawn_honeypots"],
        "mode":        "simulation",
    }


def get_chain_stats() -> Dict:
    """Return blockchain statistics."""
    bc = get_blockchain()
    if bc:
        return bc.get_stats()

    bridge = get_bridge()
    if bridge:
        stats = bridge.get_contract_stats()
        return stats.get("immunogrid", {})

    return {
        "chain_length":            random.randint(14800, 15000),
        "total_attacks_recorded":  random.randint(3500, 4500),
        "known_attack_patterns":   47,
        "morphogenesis_events":    random.randint(120, 200),
        "isolated_sectors":        [],
        "quarantined_devices":     random.randint(0, 5),
        "honeypot_count":          random.randint(18, 30),
        "fingerprint_sensitivity": 0.92,
        "chain_valid":             True,
        "mode":                    "simulation",
    }


def get_topology() -> Dict:
    """Return current network topology."""
    bc = get_blockchain()
    if bc:
        topo = bc.topology
        return {
            "active_sectors":      topo.active_sectors,
            "isolated_sectors":    topo.isolated_sectors,
            "quarantined_devices": topo.quarantined_devices,
            "honeypot_count":      topo.honeypot_count,
            "fingerprint_sensitivity": topo.fingerprint_sensitivity,
            "firewall_rules":      topo.firewall_rules,
            "last_modified":       topo.last_modified,
            "morphogenesis_count": bc.total_morphogenesis_events,
        }

    return {
        "active_sectors":      ["traffic","hospital","water","power","surveillance","metro","airport","government"],
        "isolated_sectors":    [],
        "quarantined_devices": ["device-0043", "device-0187"],
        "honeypot_count":      23,
        "fingerprint_sensitivity": 0.92,
        "firewall_rules":      {"water": {"rate_limit": "100/min"}},
        "last_morphogenesis":  datetime.utcnow().isoformat(),
        "morphogenesis_count": random.randint(100, 200),
        "mode":                "simulation",
    }


def is_pattern_known(attack_type: str, sector: str) -> Dict:
    """Check if attack pattern is in immune memory."""
    bc = get_blockchain()
    if bc:
        known, count = bc.is_attack_pattern_known(attack_type, sector)
        return {"known": known, "count": count, "attack_type": attack_type, "sector": sector}

    bridge = get_bridge()
    if bridge:
        known, count = bridge.is_pattern_known(attack_type, sector)
        return {"known": known, "count": count}

    return {
        "known": random.choice([True, False]),
        "count": random.randint(0, 5),
        "mode":  "simulation",
    }
