"""
ImmunoGrid — Smart Contract Simulation
Simulates Hyperledger Fabric chaincode logic in Python.

In production this runs as Go chaincode on Hyperledger Fabric.
This Python version is used for:
1. Local development and testing
2. Research paper algorithm description
3. Integration testing without a full Fabric network

Contract functions:
- RecordAttack        → write attack to ledger
- GetAttackHistory    → query past attacks
- TriggerMorphogenesis → execute defense restructuring
- VerifyChainIntegrity → validate blockchain
- GetNetworkTopology  → current defense topology state
"""

import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import structlog

logger = structlog.get_logger(__name__)


class ContractError(Exception):
    """Raised when a smart contract invocation fails."""
    pass


class MorphogenesisType(Enum):
    ISOLATE_SECTOR             = "isolate_sector"
    SPAWN_HONEYPOTS            = "spawn_honeypots"
    UPDATE_FIREWALL            = "update_firewall"
    QUARANTINE_DEVICE          = "quarantine_device"
    INCREASE_FP_SENSITIVITY    = "increase_fp_sensitivity"
    REROUTE_TRAFFIC            = "reroute_traffic"
    BROADCAST_ALERT            = "broadcast_alert"


@dataclass
class LedgerEntry:
    """A single immutable entry on the ledger."""
    entry_id: str
    transaction_type: str
    data: Dict[str, Any]
    submitter: str
    timestamp: str
    prev_hash: str
    entry_hash: str = ""

    def compute_hash(self) -> str:
        content = json.dumps({
            "entry_id": self.entry_id,
            "transaction_type": self.transaction_type,
            "data": self.data,
            "submitter": self.submitter,
            "timestamp": self.timestamp,
            "prev_hash": self.prev_hash,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()


class ImmunoGridChaincode:
    """
    ImmunoGrid Smart Contract (Chaincode) — Python simulation.

    In production: compiled as Go, deployed on Hyperledger Fabric peers.
    Channel: immunogrid-channel
    Chaincode ID: immunogrid-chaincode
    """

    def __init__(self):
        self.ledger: List[LedgerEntry] = []
        self.world_state: Dict[str, Any] = {
            "network_topology": {
                "active_sectors": ["traffic", "hospital", "water", "power",
                                   "surveillance", "metro", "airport", "government"],
                "isolated_sectors": [],
                "quarantined_devices": [],
                "honeypot_count": 5,
                "fp_sensitivity": 0.92,
                "firewall_rules": {},
            },
            "attack_count": 0,
            "morphogenesis_count": 0,
        }
        self.attack_pattern_db: Dict[str, int] = {}
        # Create genesis entry
        self._genesis()
        logger.info("chaincode_initialized", ledger_size=1)

    def _genesis(self):
        entry = LedgerEntry(
            entry_id="GENESIS-0000",
            transaction_type="GENESIS",
            data={"message": "ImmunoGrid chaincode initialized"},
            submitter="system",
            timestamp=datetime.utcnow().isoformat(),
            prev_hash="0" * 64,
        )
        entry.entry_hash = entry.compute_hash()
        self.ledger.append(entry)

    def _append_entry(
        self,
        transaction_type: str,
        data: Dict[str, Any],
        submitter: str = "system",
    ) -> LedgerEntry:
        """Append a new immutable entry to the ledger."""
        prev_hash = self.ledger[-1].entry_hash if self.ledger else "0" * 64
        entry = LedgerEntry(
            entry_id=f"TX-{len(self.ledger):08d}",
            transaction_type=transaction_type,
            data=data,
            submitter=submitter,
            timestamp=datetime.utcnow().isoformat(),
            prev_hash=prev_hash,
        )
        entry.entry_hash = entry.compute_hash()
        self.ledger.append(entry)
        return entry

    # ── Contract Functions ────────────────────────────────────────────────────

    def record_attack(
        self,
        attack_type: str,
        device_id: str,
        sector: str,
        severity: str,
        attacker_signature: Dict,
        detected_by: str,
        submitter: str = "system",
    ) -> Dict[str, Any]:
        """
        RecordAttack — write an attack event to the immutable ledger.
        Automatically triggers morphogenesis based on attack type and severity.
        """
        self.world_state["attack_count"] += 1
        attack_id = f"ATK-{self.world_state['attack_count']:08d}"

        # Track attack patterns (immune memory)
        pattern_key = f"{attack_type}:{sector}"
        self.attack_pattern_db[pattern_key] = self.attack_pattern_db.get(pattern_key, 0) + 1

        # Determine morphogenesis actions
        morphogenesis_actions = self._get_morphogenesis_actions(attack_type, severity, sector)

        entry_data = {
            "attack_id": attack_id,
            "attack_type": attack_type,
            "device_id": device_id,
            "sector": sector,
            "severity": severity,
            "attacker_signature": attacker_signature,
            "detected_by": detected_by,
            "morphogenesis_triggered": len(morphogenesis_actions) > 0,
            "morphogenesis_actions": morphogenesis_actions,
        }

        entry = self._append_entry("ATTACK_RECORD", entry_data, submitter)

        # Execute morphogenesis
        if morphogenesis_actions:
            self._execute_morphogenesis(morphogenesis_actions, sector, device_id)

        logger.warning(
            "attack_recorded",
            attack_id=attack_id,
            type=attack_type,
            sector=sector,
            morphogenesis=len(morphogenesis_actions),
        )

        return {
            "attack_id": attack_id,
            "entry_id": entry.entry_id,
            "entry_hash": entry.entry_hash,
            "morphogenesis_actions": morphogenesis_actions,
            "timestamp": entry.timestamp,
        }

    def get_attack_history(
        self,
        sector: Optional[str] = None,
        attack_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict]:
        """GetAttackHistory — query past attacks from the ledger."""
        results = []
        for entry in reversed(self.ledger):
            if entry.transaction_type != "ATTACK_RECORD":
                continue
            data = entry.data
            if sector and data.get("sector") != sector:
                continue
            if attack_type and data.get("attack_type") != attack_type:
                continue
            results.append({**data, "entry_hash": entry.entry_hash, "timestamp": entry.timestamp})
            if len(results) >= limit:
                break
        return results

    def trigger_morphogenesis(
        self,
        actions: List[str],
        sector: str,
        device_id: str,
        submitter: str = "admin",
    ) -> Dict:
        """TriggerMorphogenesis — manually execute defense restructuring."""
        self._execute_morphogenesis(actions, sector, device_id)
        entry = self._append_entry(
            "MORPHOGENESIS",
            {"actions": actions, "sector": sector, "device_id": device_id, "manual": True},
            submitter,
        )
        return {
            "entry_id": entry.entry_id,
            "actions_executed": actions,
            "topology": self.world_state["network_topology"],
        }

    def is_attack_pattern_known(self, attack_type: str, sector: str) -> Tuple[bool, int]:
        """Check if an attack pattern has been seen before (immune memory)."""
        key = f"{attack_type}:{sector}"
        count = self.attack_pattern_db.get(key, 0)
        return count > 0, count

    def get_attack_history(self, sector: Optional[str] = None) -> List[Dict]:
        """Return recorded attacks, optionally filtered by sector."""
        records = []
        for entry in self.ledger:
            if entry.transaction_type != "ATTACK_RECORD":
                continue
            data = entry.data
            if sector and data.get("sector") != sector:
                continue
            records.append({**data, "entry_hash": entry.entry_hash, "timestamp": entry.timestamp})
        return records

    def get_network_topology(self) -> Dict:
        """GetNetworkTopology — return current defense topology."""
        return {
            **self.world_state["network_topology"],
            "attack_count": self.world_state["attack_count"],
            "morphogenesis_count": self.world_state["morphogenesis_count"],
            "ledger_size": len(self.ledger),
        }

    def verify_chain_integrity(self) -> Dict:
        """VerifyChainIntegrity — validate the full chain."""
        is_valid = True
        broken_at = None

        for i in range(1, len(self.ledger)):
            current = self.ledger[i]
            previous = self.ledger[i - 1]

            # Check entry hash
            recomputed = current.compute_hash()
            if current.entry_hash != recomputed:
                is_valid = False
                broken_at = i
                break

            # Check chain link
            if current.prev_hash != previous.entry_hash:
                is_valid = False
                broken_at = i
                break

        return {
            "is_valid": is_valid,
            "ledger_size": len(self.ledger),
            "broken_at_index": broken_at,
            "verified_at": datetime.utcnow().isoformat(),
        }

    # ── Internal Morphogenesis Logic ──────────────────────────────────────────

    def _get_morphogenesis_actions(
        self, attack_type: str, severity: str, sector: str,
    ) -> List[str]:
        """Map attack → morphogenesis response actions."""
        actions = [MorphogenesisType.BROADCAST_ALERT.value]

        if attack_type == "spoofing":
            actions += [MorphogenesisType.INCREASE_FP_SENSITIVITY.value,
                        MorphogenesisType.SPAWN_HONEYPOTS.value]
            if severity in ("high", "critical"):
                actions.append(MorphogenesisType.QUARANTINE_DEVICE.value)

        elif attack_type == "ddos":
            actions += [MorphogenesisType.UPDATE_FIREWALL.value,
                        MorphogenesisType.REROUTE_TRAFFIC.value]
            if severity == "critical":
                actions.append(MorphogenesisType.ISOLATE_SECTOR.value)

        elif attack_type in ("data_poisoning", "man_in_the_middle"):
            actions += [MorphogenesisType.QUARANTINE_DEVICE.value,
                        MorphogenesisType.UPDATE_FIREWALL.value]

        elif attack_type in ("replay_attack", "ransomware"):
            actions += [MorphogenesisType.QUARANTINE_DEVICE.value,
                        MorphogenesisType.SPAWN_HONEYPOTS.value]

        return list(set(actions))

    def _execute_morphogenesis(
        self, actions: List[str], sector: str, device_id: str,
    ):
        """Apply morphogenesis actions to the world state."""
        self.world_state["morphogenesis_count"] += 1
        topology = self.world_state["network_topology"]

        for action in actions:
            if action == MorphogenesisType.ISOLATE_SECTOR.value:
                if sector not in topology["isolated_sectors"]:
                    topology["isolated_sectors"].append(sector)
                    if sector in topology["active_sectors"]:
                        topology["active_sectors"].remove(sector)

            elif action == MorphogenesisType.QUARANTINE_DEVICE.value:
                if device_id not in topology["quarantined_devices"]:
                    topology["quarantined_devices"].append(device_id)

            elif action == MorphogenesisType.SPAWN_HONEYPOTS.value:
                topology["honeypot_count"] += 2

            elif action == MorphogenesisType.INCREASE_FP_SENSITIVITY.value:
                topology["fp_sensitivity"] = max(0.75, topology["fp_sensitivity"] - 0.02)

            elif action == MorphogenesisType.UPDATE_FIREWALL.value:
                topology["firewall_rules"][sector] = {
                    "rate_limit": "100/min",
                    "block_unknown": True,
                    "updated_at": datetime.utcnow().isoformat(),
                }

    def get_stats(self) -> Dict:
        """Return chaincode statistics."""
        return {
            "ledger_entries": len(self.ledger),
            "attack_records": self.world_state["attack_count"],
            "morphogenesis_events": self.world_state["morphogenesis_count"],
            "chain_valid": self.verify_chain_integrity()["is_valid"],
            "topology": self.get_network_topology(),
        }
