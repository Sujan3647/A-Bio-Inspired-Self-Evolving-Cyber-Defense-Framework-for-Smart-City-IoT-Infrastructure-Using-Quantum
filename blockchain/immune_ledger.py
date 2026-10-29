"""
ImmunoGrid — Morphogenetic Blockchain (Immune Ledger)

The blockchain that:
1. Remembers EVERY attack permanently (immune memory)
2. AUTO-RESTRUCTURES the network after each attack (morphogenesis)
3. Executes smart contracts that change defense topology

This is the "scar tissue" of the system:
Every wound makes the network stronger at that exact spot.
"""

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import structlog

logger = structlog.get_logger(__name__)


class MorphogenesisAction(Enum):
    """Actions the blockchain can trigger to reshape the network."""
    ISOLATE_SECTOR = "isolate_sector"
    SPAWN_HONEYPOTS = "spawn_honeypots"
    REROUTE_TRAFFIC = "reroute_traffic"
    UPDATE_FIREWALL = "update_firewall_rules"
    QUARANTINE_DEVICE = "quarantine_device"
    PROMOTE_BACKUP = "promote_backup_node"
    BROADCAST_ALERT = "broadcast_alert"
    INCREASE_FINGERPRINT_SENSITIVITY = "increase_fp_sensitivity"


@dataclass
class AttackRecord:
    """An immutable record of an attack event."""
    record_id: str
    attack_type: str
    target_device_id: str
    target_sector: str
    attacker_signature: Dict[str, Any]   # Behavioral profile of attacker
    timestamp: str
    detected_by: str                      # Which mechanism detected it
    severity: str                         # "low" | "medium" | "high" | "critical"
    morphogenesis_triggered: bool
    response_actions: List[str]
    data_hash: str                        # Hash of the full attack data


@dataclass
class Block:
    """
    A single block in the Morphogenetic Blockchain.
    
    Each block contains:
    - Attack records (immune memory)
    - Morphogenesis commands (network restructuring)
    - Previous block hash (chain integrity)
    """
    index: int
    timestamp: str
    attack_records: List[AttackRecord]
    morphogenesis_commands: List[Dict[str, Any]]
    previous_hash: str
    nonce: int = 0
    block_hash: str = ""

    def calculate_hash(self) -> str:
        """Calculate the SHA-256 hash of this block."""
        block_data = {
            "index": self.index,
            "timestamp": self.timestamp,
            "attack_records": [r.record_id for r in self.attack_records],
            "morphogenesis_commands": self.morphogenesis_commands,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
        }
        block_string = json.dumps(block_data, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def mine(self, difficulty: int = 2):
        """
        Simple proof-of-work mining.
        Finds a nonce such that hash starts with 'difficulty' zeros.
        """
        target = "0" * difficulty
        while not self.block_hash.startswith(target):
            self.nonce += 1
            self.block_hash = self.calculate_hash()


@dataclass
class NetworkTopology:
    """
    Current state of the network defense topology.
    The blockchain modifies this after each attack (morphogenesis).
    """
    active_sectors: List[str] = field(default_factory=lambda: [
        "traffic", "hospital", "water", "power", "surveillance", "government"
    ])
    isolated_sectors: List[str] = field(default_factory=list)
    quarantined_devices: List[str] = field(default_factory=list)
    honeypot_count: int = 5
    firewall_rules: Dict[str, Any] = field(default_factory=dict)
    fingerprint_sensitivity: float = 0.92   # Threshold for quantum fingerprint
    backup_routes: Dict[str, str] = field(default_factory=dict)
    last_modified: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class MorphogeneticBlockchain:
    """
    The Morphogenetic Blockchain — ImmunoGrid's Immune Memory.
    
    In-memory implementation for simulation.
    In production: Hyperledger Fabric on AWS Managed Blockchain.
    
    Key capabilities:
    1. Record every attack permanently and immutably
    2. Execute morphogenesis smart contracts automatically
    3. Maintain full audit trail for government compliance
    4. Provide attack pattern recognition (same attack = instant block)
    """

    def __init__(self, difficulty: int = 2):
        self.difficulty = difficulty
        self.chain: List[Block] = []
        self.pending_records: List[AttackRecord] = []
        self.topology = NetworkTopology()
        self.attack_pattern_db: Dict[str, int] = {}  # attack_hash → count
        self.total_morphogenesis_events = 0

        # Create genesis block
        self._create_genesis_block()

        logger.info(
            "morphogenetic_blockchain_initialized",
            difficulty=difficulty,
            genesis_hash=self.chain[0].block_hash[:16],
        )

    def _create_genesis_block(self):
        """Create the first block in the chain."""
        genesis = Block(
            index=0,
            timestamp=datetime.utcnow().isoformat(),
            attack_records=[],
            morphogenesis_commands=[{
                "action": "GENESIS",
                "message": "ImmunoGrid Morphogenetic Blockchain initialized",
                "network_topology": "nominal",
            }],
            previous_hash="0" * 64,
        )
        genesis.mine(self.difficulty)
        self.chain.append(genesis)

    def record_attack(
        self,
        attack_type: str,
        target_device_id: str,
        target_sector: str,
        attacker_signature: Dict[str, Any],
        detected_by: str,
        severity: str = "medium",
    ) -> AttackRecord:
        """
        Record an attack event on the blockchain.
        Automatically triggers morphogenesis if needed.
        """
        record_id = f"ATK-{uuid.uuid4().hex[:12].upper()}"

        # Determine morphogenesis response
        response_actions = self._determine_response(attack_type, severity, target_sector)
        morphogenesis_needed = len(response_actions) > 0

        # Create data hash
        data = {
            "attack_type": attack_type,
            "target": target_device_id,
            "sector": target_sector,
            "attacker_sig": attacker_signature,
            "timestamp": datetime.utcnow().isoformat(),
        }
        data_hash = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

        record = AttackRecord(
            record_id=record_id,
            attack_type=attack_type,
            target_device_id=target_device_id,
            target_sector=target_sector,
            attacker_signature=attacker_signature,
            timestamp=datetime.utcnow().isoformat(),
            detected_by=detected_by,
            severity=severity,
            morphogenesis_triggered=morphogenesis_needed,
            response_actions=response_actions,
            data_hash=data_hash,
        )

        # Add to pending records
        self.pending_records.append(record)

        # Track attack patterns
        pattern_key = f"{attack_type}:{target_sector}"
        self.attack_pattern_db[pattern_key] = self.attack_pattern_db.get(pattern_key, 0) + 1

        # If severe enough, mine a block immediately
        if severity in ("high", "critical") or len(self.pending_records) >= 5:
            self.mine_block()

        # Execute morphogenesis
        if morphogenesis_needed:
            self._execute_morphogenesis(response_actions, target_sector, target_device_id)

        logger.warning(
            "attack_recorded_on_blockchain",
            record_id=record_id,
            attack_type=attack_type,
            severity=severity,
            morphogenesis=morphogenesis_needed,
            chain_length=len(self.chain),
        )

        return record

    def mine_block(self) -> Optional[Block]:
        """Mine a new block with all pending attack records."""
        if not self.pending_records:
            return None

        morphogenesis_commands = [
            {
                "action": action,
                "triggered_by": [r.record_id for r in self.pending_records],
                "timestamp": datetime.utcnow().isoformat(),
            }
            for action in set(
                action
                for record in self.pending_records
                for action in record.response_actions
            )
        ]

        new_block = Block(
            index=len(self.chain),
            timestamp=datetime.utcnow().isoformat(),
            attack_records=list(self.pending_records),
            morphogenesis_commands=morphogenesis_commands,
            previous_hash=self.chain[-1].block_hash,
        )
        new_block.mine(self.difficulty)
        self.chain.append(new_block)
        self.pending_records.clear()

        logger.info(
            "block_mined",
            block_index=new_block.index,
            block_hash=new_block.block_hash[:16],
            records_count=len(new_block.attack_records),
        )

        return new_block

    def _determine_response(
        self,
        attack_type: str,
        severity: str,
        target_sector: str,
    ) -> List[str]:
        """
        Smart contract logic: determine what morphogenesis actions to take.
        This is the "immune response" triggered by each attack.
        """
        actions = []

        # Always broadcast alert
        actions.append(MorphogenesisAction.BROADCAST_ALERT.value)

        if attack_type == "spoofing":
            actions.append(MorphogenesisAction.INCREASE_FINGERPRINT_SENSITIVITY.value)
            actions.append(MorphogenesisAction.SPAWN_HONEYPOTS.value)
            if severity in ("high", "critical"):
                actions.append(MorphogenesisAction.QUARANTINE_DEVICE.value)

        elif attack_type == "ddos":
            actions.append(MorphogenesisAction.REROUTE_TRAFFIC.value)
            actions.append(MorphogenesisAction.UPDATE_FIREWALL.value)
            if severity == "critical":
                actions.append(MorphogenesisAction.ISOLATE_SECTOR.value)

        elif attack_type == "data_poisoning":
            actions.append(MorphogenesisAction.QUARANTINE_DEVICE.value)
            actions.append(MorphogenesisAction.PROMOTE_BACKUP.value)
            actions.append(MorphogenesisAction.UPDATE_FIREWALL.value)

        elif attack_type in ("replay_attack", "man_in_the_middle"):
            actions.append(MorphogenesisAction.REROUTE_TRAFFIC.value)
            actions.append(MorphogenesisAction.SPAWN_HONEYPOTS.value)

        return actions

    def _execute_morphogenesis(
        self,
        actions: List[str],
        sector: str,
        device_id: str,
    ):
        """
        Execute the morphogenesis — physically reshape the network defenses.
        This modifies the NetworkTopology object.
        """
        self.total_morphogenesis_events += 1

        for action in actions:
            if action == MorphogenesisAction.ISOLATE_SECTOR.value:
                if sector not in self.topology.isolated_sectors:
                    self.topology.isolated_sectors.append(sector)
                    logger.warning("morphogenesis_sector_isolated", sector=sector)

            elif action == MorphogenesisAction.QUARANTINE_DEVICE.value:
                if device_id not in self.topology.quarantined_devices:
                    self.topology.quarantined_devices.append(device_id)
                    logger.warning("morphogenesis_device_quarantined", device_id=device_id)

            elif action == MorphogenesisAction.SPAWN_HONEYPOTS.value:
                self.topology.honeypot_count += 2
                logger.info("morphogenesis_honeypots_spawned",
                           new_count=self.topology.honeypot_count)

            elif action == MorphogenesisAction.INCREASE_FINGERPRINT_SENSITIVITY.value:
                # Lower threshold = more sensitive = catches more impostors
                self.topology.fingerprint_sensitivity = max(
                    0.75,
                    self.topology.fingerprint_sensitivity - 0.02,
                )
                logger.info("morphogenesis_fp_sensitivity_increased",
                           new_threshold=self.topology.fingerprint_sensitivity)

            elif action == MorphogenesisAction.UPDATE_FIREWALL.value:
                self.topology.firewall_rules[sector] = {
                    "rate_limit": "100/min",
                    "block_unknown_devices": True,
                    "updated_at": datetime.utcnow().isoformat(),
                }

        self.topology.last_modified = datetime.utcnow().isoformat()

    def is_attack_pattern_known(self, attack_type: str, sector: str) -> Tuple[bool, int]:
        """
        Check if this attack pattern has been seen before.
        Immune memory at work — same attack = instant recognition.
        """
        pattern_key = f"{attack_type}:{sector}"
        count = self.attack_pattern_db.get(pattern_key, 0)
        return count > 0, count

    def is_chain_valid(self) -> bool:
        """Verify blockchain integrity — ensures no tampering."""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            if current.block_hash != current.calculate_hash():
                return False
            if current.previous_hash != previous.block_hash:
                return False

        return True

    def get_attack_history(self, sector: Optional[str] = None) -> List[Dict]:
        """Return all attack records, optionally filtered by sector."""
        all_records = []
        for block in self.chain[1:]:  # Skip genesis
            for record in block.attack_records:
                if sector is None or record.target_sector == sector:
                    all_records.append({
                        "record_id":     record.record_id,
                        "attack_type":   record.attack_type,
                        "target":        record.target_device_id,
                        "sector":        record.target_sector,
                        "target_sector": record.target_sector,
                        "severity":      record.severity,
                        "timestamp":     record.timestamp,
                        "detected_by":   record.detected_by,
                        "morphogenesis": record.morphogenesis_triggered,
                        "responses":     record.response_actions,
                    })
        return all_records

    def get_stats(self) -> Dict:
        """Return blockchain statistics."""
        total_attacks = sum(
            len(block.attack_records) for block in self.chain[1:]
        )
        return {
            "chain_length": len(self.chain),
            "total_attacks_recorded": total_attacks,
            "known_attack_patterns": len(self.attack_pattern_db),
            "morphogenesis_events": self.total_morphogenesis_events,
            "isolated_sectors": self.topology.isolated_sectors,
            "quarantined_devices": len(self.topology.quarantined_devices),
            "honeypot_count": self.topology.honeypot_count,
            "fingerprint_sensitivity": self.topology.fingerprint_sensitivity,
            "chain_valid": self.is_chain_valid(),
        }
