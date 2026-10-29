"""
ImmunoGrid — Honeypot Decoy Spawner
Creates fake IoT devices that trap and study attackers.

When an attack is detected:
1. Spawn 3-5 fake devices that look identical to real ones
2. Attacker attacks the fake device (thinks it's real)
3. System captures attacker's exact technique + behavior
4. That technique is added to the quantum fingerprint DB
5. Real devices re-harden silently
"""

import asyncio
import json
import random
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List

import structlog

logger = structlog.get_logger(__name__)


class HoneypotDevice:
    """
    A fake decoy device designed to attract and trap attackers.
    Looks identical to a real device but everything is fake.
    """

    def __init__(self, mimics_device_id: str, mimics_sector: str):
        self.honeypot_id = f"honeypot-{uuid.uuid4().hex[:8]}"
        self.mimics_device_id = mimics_device_id
        self.mimics_sector = mimics_sector
        self.created_at = datetime.utcnow()
        self.interactions: List[Dict] = []
        self.active = True

        logger.info(
            "honeypot_spawned",
            honeypot_id=self.honeypot_id,
            mimics=mimics_device_id,
            sector=mimics_sector,
        )

    def record_interaction(self, attacker_payload: Dict[str, Any]):
        """Record an attacker interaction — capture their technique."""
        interaction = {
            "timestamp": datetime.utcnow().isoformat(),
            "attacker_payload": attacker_payload,
            "attacker_behavior": self._extract_attacker_behavior(attacker_payload),
        }
        self.interactions.append(interaction)
        logger.warning(
            "honeypot_interaction_captured",
            honeypot_id=self.honeypot_id,
            attack_type=attacker_payload.get("_attack_meta", {}).get("attack_type", "unknown"),
        )
        return interaction

    def _extract_attacker_behavior(self, payload: Dict) -> Dict[str, Any]:
        """Extract behavioral signature of the attacker from the payload."""
        behavior = payload.get("behavior", {})
        return {
            "send_interval": behavior.get("send_interval", 0),
            "packet_size": behavior.get("packet_size", 0),
            "subnet": behavior.get("subnet", "unknown"),
            "cpu_usage": behavior.get("cpu_usage", 0),
            "timestamp_pattern": payload.get("timestamp", ""),
            "attack_type": payload.get("_attack_meta", {}).get("attack_type", "unknown"),
            "attacker_id": payload.get("_attack_meta", {}).get("attacker_id", "unknown"),
        }

    def generate_fake_response(self) -> Dict[str, Any]:
        """Generate a fake response to lure the attacker deeper."""
        return {
            "device_id": self.mimics_device_id,
            "status": "online",
            "data": {"value": random.uniform(0, 100)},
            "message": "ACK",
            "_honeypot": True,  # Internal flag — not sent to attacker
        }

    def get_intelligence_report(self) -> Dict[str, Any]:
        """Generate an intelligence report on the captured attacker."""
        if not self.interactions:
            return {"interactions": 0}

        return {
            "honeypot_id": self.honeypot_id,
            "mimicked_device": self.mimics_device_id,
            "total_interactions": len(self.interactions),
            "attacker_techniques": list({
                i["attacker_behavior"]["attack_type"]
                for i in self.interactions
            }),
            "attacker_ids": list({
                i["attacker_behavior"]["attacker_id"]
                for i in self.interactions
            }),
            "first_interaction": self.interactions[0]["timestamp"] if self.interactions else None,
            "last_interaction": self.interactions[-1]["timestamp"] if self.interactions else None,
            "captured_behaviors": [i["attacker_behavior"] for i in self.interactions],
        }


class HoneypotNetwork:
    """
    Manages the complete honeypot trap network.
    Spawns, monitors, and deactivates honeypots.
    """

    def __init__(self):
        self.active_honeypots: Dict[str, HoneypotDevice] = {}
        self.total_spawned = 0
        self.total_interactions_captured = 0

    def spawn_honeypots(
        self,
        target_device_id: str,
        target_sector: str,
        count: int = 3,
    ) -> List[HoneypotDevice]:
        """Spawn decoy devices near the attacked real device."""
        honeypots = []
        for _ in range(count):
            hp = HoneypotDevice(
                mimics_device_id=target_device_id,
                mimics_sector=target_sector,
            )
            self.active_honeypots[hp.honeypot_id] = hp
            honeypots.append(hp)
            self.total_spawned += 1

        logger.info(
            "honeypot_network_expanded",
            new_honeypots=count,
            total_active=len(self.active_honeypots),
        )
        return honeypots

    def process_incoming_message(self, topic: str, payload: str) -> bool:
        """
        Check if an incoming message is targeting a honeypot.
        Returns True if it's a honeypot hit.
        """
        try:
            data = json.loads(payload)
            if "_attack_meta" not in data and "_attack_meta" not in data.get("data", {}):
                return False

            # Check if target matches any honeypot
            target_id = data.get("device_id", "")
            for hp in self.active_honeypots.values():
                if hp.mimics_device_id == target_id and hp.active:
                    interaction = hp.record_interaction(data)
                    self.total_interactions_captured += 1
                    return True

        except (json.JSONDecodeError, Exception):
            pass

        return False

    def get_all_intelligence(self) -> List[Dict]:
        """Collect intelligence from all honeypots."""
        return [
            hp.get_intelligence_report()
            for hp in self.active_honeypots.values()
            if hp.interactions
        ]

    def get_stats(self) -> Dict[str, Any]:
        return {
            "active_honeypots": len(self.active_honeypots),
            "total_spawned": self.total_spawned,
            "total_interactions_captured": self.total_interactions_captured,
            "attackers_trapped": len({
                behavior
                for hp in self.active_honeypots.values()
                for interaction in hp.interactions
                for behavior in [interaction["attacker_behavior"]["attacker_id"]]
            }),
        }
