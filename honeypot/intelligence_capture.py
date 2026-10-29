"""
ImmunoGrid — Honeypot Intelligence Capture & Analysis

After a honeypot traps an attacker, this module:
1. Analyzes the attacker's behavioral signature
2. Generates a new quantum fingerprint entry for the attacker
3. Writes an intelligence report for the blockchain
4. Updates the AI Brain with new adversarial training samples
"""

import json
import hashlib
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class AttackerProfile:
    """Behavioral profile of a captured attacker."""
    attacker_id: str
    first_seen: str
    last_seen: str
    attack_types: List[str]
    behavioral_signature: Dict[str, Any]
    target_sectors: List[str]
    total_attempts: int
    success_rate: float
    profile_hash: str


@dataclass
class IntelligenceReport:
    """Full intelligence report from honeypot capture."""
    report_id: str
    honeypot_id: str
    attacker_profile: AttackerProfile
    recommended_defenses: List[str]
    blockchain_entry: Dict[str, Any]
    ai_training_samples: List[Dict]
    generated_at: str


class IntelligenceCaptureEngine:
    """
    Analyzes captured honeypot interactions and produces
    actionable intelligence for all ImmunoGrid modules.
    """

    def __init__(self):
        self.attacker_profiles: Dict[str, AttackerProfile] = {}
        self.reports: List[IntelligenceReport] = []
        self.total_attackers_profiled = 0

    def analyze_honeypot(
        self,
        honeypot_id: str,
        interactions: List[Dict],
    ) -> Optional[IntelligenceReport]:
        """
        Analyze all interactions captured by a honeypot.
        Returns a full intelligence report.
        """
        if not interactions:
            return None

        report_id = f"RPT-{hashlib.md5(honeypot_id.encode()).hexdigest()[:12].upper()}"

        # Aggregate attacker behavior
        attack_types = list({
            i.get("attacker_behavior", {}).get("attack_type", "unknown")
            for i in interactions
        })
        attacker_ids = list({
            i.get("attacker_behavior", {}).get("attacker_id", "unknown")
            for i in interactions
        })
        target_sectors = list({
            i.get("attacker_payload", {}).get("sector", "unknown")
            for i in interactions
        })

        # Build behavioral signature from captured data
        behavioral_sig = self._aggregate_behavior(interactions)

        # Create attacker profile
        primary_attacker = attacker_ids[0] if attacker_ids else "unknown"
        profile_hash = hashlib.sha256(json.dumps(behavioral_sig, sort_keys=True).encode()).hexdigest()

        profile = AttackerProfile(
            attacker_id=primary_attacker,
            first_seen=interactions[0].get("timestamp", datetime.utcnow().isoformat()),
            last_seen=interactions[-1].get("timestamp", datetime.utcnow().isoformat()),
            attack_types=attack_types,
            behavioral_signature=behavioral_sig,
            target_sectors=target_sectors,
            total_attempts=len(interactions),
            success_rate=0.0,  # Honeypot = 0% real success
            profile_hash=profile_hash,
        )

        self.attacker_profiles[primary_attacker] = profile
        self.total_attackers_profiled += 1

        # Recommend defenses based on attack type
        defenses = self._recommend_defenses(attack_types)

        # Prepare blockchain entry
        blockchain_entry = {
            "report_id": report_id,
            "attacker_profile_hash": profile_hash,
            "attack_types": attack_types,
            "target_sectors": target_sectors,
            "honeypot_id": honeypot_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Generate AI training samples from captured behavior
        ai_samples = self._generate_ai_samples(interactions)

        report = IntelligenceReport(
            report_id=report_id,
            honeypot_id=honeypot_id,
            attacker_profile=profile,
            recommended_defenses=defenses,
            blockchain_entry=blockchain_entry,
            ai_training_samples=ai_samples,
            generated_at=datetime.utcnow().isoformat(),
        )

        self.reports.append(report)

        logger.info(
            "intelligence_report_generated",
            report_id=report_id,
            attack_types=attack_types,
            interactions=len(interactions),
            defenses_recommended=len(defenses),
        )

        return report

    def _aggregate_behavior(self, interactions: List[Dict]) -> Dict[str, Any]:
        """Extract statistical behavioral signature from interactions."""
        send_intervals = [
            i.get("attacker_behavior", {}).get("send_interval", 2.0)
            for i in interactions
        ]
        packet_sizes = [
            i.get("attacker_behavior", {}).get("packet_size", 48)
            for i in interactions
        ]

        if not send_intervals:
            return {}

        return {
            "avg_send_interval": round(sum(send_intervals) / len(send_intervals), 4),
            "avg_packet_size": round(sum(packet_sizes) / len(packet_sizes), 2),
            "unique_subnets": list({
                i.get("attacker_behavior", {}).get("subnet", "")
                for i in interactions
            }),
            "interaction_count": len(interactions),
        }

    def _recommend_defenses(self, attack_types: List[str]) -> List[str]:
        """Map captured attack types to recommended defense actions."""
        defense_map = {
            "spoofing": [
                "Increase quantum fingerprint sensitivity to 0.95",
                "Spawn 5 additional honeypots in affected sector",
                "Add attacker subnet to firewall blocklist",
            ],
            "man_in_the_middle": [
                "Force certificate rotation on all sector devices",
                "Enable mutual TLS with Dilithium signatures",
                "Add route pinning for critical devices",
            ],
            "ddos": [
                "Activate rate limiting: 50 msgs/min per device",
                "Enable DDoS scrubbing on AWS WAF",
                "Deploy traffic shaping on sector gateway",
            ],
            "data_poisoning": [
                "Enable cross-validation with neighbor device readings",
                "Increase anomaly detection sensitivity in AI Brain",
                "Add sensor data hash verification on blockchain",
            ],
            "replay_attack": [
                "Reduce message nonce TTL to 30 seconds",
                "Enable strict sequence number enforcement",
                "Add blockchain-based message deduplication",
            ],
            "ransomware": [
                "Block all external firmware update sources",
                "Enable immutable device config on blockchain",
                "Isolate device from network, restore from blockchain backup",
            ],
        }

        defenses = []
        for attack_type in attack_types:
            defenses.extend(defense_map.get(attack_type, ["Monitor and log"]))

        return list(set(defenses))

    def _generate_ai_samples(self, interactions: List[Dict]) -> List[Dict]:
        """Convert captured interactions into AI training samples."""
        samples = []
        attack_label_map = {
            "spoofing": 1,
            "ddos": 2,
            "data_poisoning": 3,
            "replay_attack": 4,
            "man_in_the_middle": 4,
            "ransomware": 3,
        }

        for interaction in interactions:
            behavior = interaction.get("attacker_behavior", {})
            attack_type = behavior.get("attack_type", "unknown")
            label = attack_label_map.get(attack_type, 0)

            samples.append({
                "features": [
                    behavior.get("send_interval", 2.0),
                    behavior.get("packet_size", 48),
                    1.0,   # timing jitter (high for attacker)
                    5.0,   # size variance (high for attacker)
                    0.95,  # cpu usage (high during attack)
                    12.0,  # active_start
                    12.0,  # active_end
                    1.0 / max(behavior.get("send_interval", 1.0), 0.1),
                    0.5,
                    1.0,
                    0.8,
                    0.9,
                ],
                "label": label,
                "attack_type": attack_type,
                "source": "honeypot_capture",
            })

        return samples

    def get_all_profiles(self) -> List[Dict]:
        """Return all captured attacker profiles."""
        return [asdict(p) for p in self.attacker_profiles.values()]

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_attackers_profiled": self.total_attackers_profiled,
            "total_reports": len(self.reports),
            "unique_attack_types": list({
                at
                for p in self.attacker_profiles.values()
                for at in p.attack_types
            }),
        }
