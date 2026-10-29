"""
ImmunoGrid — Honeypot Service
Business logic for honeypot network operations.
"""

import random
from datetime import datetime
from typing import Dict, List, Optional
import structlog

logger = structlog.get_logger(__name__)

_honeypot_network = None


def get_network():
    global _honeypot_network
    if _honeypot_network is None:
        try:
            import sys, os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
            from honeypot.decoy_spawner import HoneypotNetwork
            _honeypot_network = HoneypotNetwork()
            logger.info("honeypot_service_loaded")
        except Exception as e:
            logger.warning("honeypot_load_failed", error=str(e))
    return _honeypot_network


def spawn_honeypots(target_device_id: str, sector: str, count: int = 3) -> Dict:
    """Spawn decoy honeypot devices."""
    net = get_network()
    if net:
        decoys = net.spawn_honeypots(target_device_id, sector, count)
        return {
            "spawned": len(decoys),
            "sector":  sector,
            "honeypot_ids": [d.honeypot_id for d in decoys],
        }
    # Simulation
    return {
        "spawned": count,
        "sector":  sector,
        "honeypot_ids": [f"honeypot-sim-{i:04d}" for i in range(count)],
        "mode": "simulation",
    }


def get_stats() -> Dict:
    """Return honeypot network statistics."""
    net = get_network()
    if net:
        return net.get_stats()
    return {
        "active_honeypots":           random.randint(18, 30),
        "total_spawned":              random.randint(40, 60),
        "attackers_trapped_today":    random.randint(2, 8),
        "total_interactions_captured": random.randint(80, 200),
        "intelligence_reports":       random.randint(8, 15),
        "ai_samples_fed_back":        random.randint(150, 400),
        "mode": "simulation",
    }


def analyze_honeypot_intelligence(honeypot_id: str, interactions: List[Dict]) -> Dict:
    """Analyze captured honeypot interactions."""
    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        from honeypot.intelligence_capture import IntelligenceCaptureEngine
        ice    = IntelligenceCaptureEngine()
        report = ice.analyze_honeypot(honeypot_id, interactions)
        if report:
            return {
                "report_id":          report.report_id,
                "attack_types":       report.attacker_profile.attack_types,
                "defenses_recommended": report.recommended_defenses,
                "ai_samples":         len(report.ai_training_samples),
            }
    except Exception as e:
        logger.warning("honeypot_analysis_fallback", error=str(e))
    return {"report_id": f"RPT-SIM-{honeypot_id[:8]}", "mode": "simulation"}
