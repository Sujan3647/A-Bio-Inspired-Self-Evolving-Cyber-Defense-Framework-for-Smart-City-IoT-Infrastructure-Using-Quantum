"""
ImmunoGrid — Byzantine Fault-Tolerant Consensus
Simulates Hyperledger Fabric's PBFT-based consensus mechanism.

Ensures attack records are written to the blockchain only when
a quorum of network nodes agree — preventing a compromised node
from injecting false records.

Consensus flow:
1. Client proposes transaction (attack record)
2. Primary node broadcasts PREPARE
3. ≥ 2f+1 nodes send PREPARE vote
4. Primary sends COMMIT
5. ≥ 2f+1 nodes COMMIT → transaction finalized
6. Block added to chain

Where f = max number of faulty nodes tolerated
For 4 nodes: f=1 → need 3/4 agreement
"""

import hashlib
import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)


class NodeStatus(Enum):
    HEALTHY   = "healthy"
    FAULTY    = "faulty"
    BYZANTINE = "byzantine"   # Actively malicious


class MessageType(Enum):
    PROPOSE  = "PROPOSE"
    PREPARE  = "PREPARE"
    COMMIT   = "COMMIT"
    REPLY    = "REPLY"


@dataclass
class ConsensusNode:
    """A peer node in the Hyperledger Fabric network."""
    node_id:    str
    org_name:   str
    status:     NodeStatus = NodeStatus.HEALTHY
    vote_count: int = 0
    committed:  int = 0

    def is_honest(self) -> bool:
        return self.status == NodeStatus.HEALTHY

    def vote(self, proposal_hash: str) -> Optional[str]:
        """Cast a vote. Faulty nodes may abstain or vote incorrectly."""
        if self.status == NodeStatus.FAULTY:
            return None   # Abstains
        if self.status == NodeStatus.BYZANTINE:
            # Sends a different hash to disrupt consensus
            return hashlib.sha256(b"corrupt").hexdigest()
        self.vote_count += 1
        return proposal_hash


@dataclass
class ConsensusResult:
    """Result of a consensus round."""
    proposal_id:    str
    transaction:    Dict[str, Any]
    reached:        bool
    votes_received: int
    votes_needed:   int
    faulty_nodes:   int
    duration_ms:    float
    block_hash:     str
    timestamp:      str


class PBFTConsensus:
    """
    Practical Byzantine Fault Tolerant (PBFT) Consensus Simulation.
    Used in Hyperledger Fabric for ImmunoGrid's Morphogenetic Blockchain.

    Network: 4 peers (Organizations) — tolerates 1 Byzantine node.
    In production: runs as Hyperledger Fabric orderer service.
    """

    def __init__(self, num_nodes: int = 4):
        self.nodes = self._create_network(num_nodes)
        self.total_consensus_rounds = 0
        self.failed_rounds          = 0
        self.byzantine_detected     = 0

        # f = floor((n-1)/3)
        self.f = (num_nodes - 1) // 3
        self.quorum = 2 * self.f + 1

        logger.info(
            "pbft_consensus_initialized",
            nodes=num_nodes,
            fault_tolerance=self.f,
            quorum_needed=self.quorum,
        )

    def _create_network(self, n: int) -> List[ConsensusNode]:
        orgs = ["ImmunoGridOrg1", "ImmunoGridOrg2", "SecurityOrg", "AuditOrg"]
        return [
            ConsensusNode(
                node_id=f"peer{i}-{orgs[i % len(orgs)].lower()}",
                org_name=orgs[i % len(orgs)],
            )
            for i in range(n)
        ]

    def propose_transaction(
        self, transaction: Dict[str, Any]
    ) -> ConsensusResult:
        """
        Propose a transaction for consensus.
        Returns ConsensusResult with reached=True if quorum achieved.
        """
        import time
        start_ms = time.time() * 1000

        proposal_id = f"PROP-{uuid.uuid4().hex[:12].upper()}"
        tx_bytes = str(sorted(transaction.items())).encode()
        proposal_hash = hashlib.sha256(tx_bytes).hexdigest()

        self.total_consensus_rounds += 1

        # Phase 1: PREPARE — each node votes
        votes: Dict[str, int] = {}
        faulty_count = 0

        for node in self.nodes:
            vote = node.vote(proposal_hash)
            if vote is None:
                faulty_count += 1
                continue
            if vote != proposal_hash:
                faulty_count += 1
                self.byzantine_detected += 1
                logger.warning("byzantine_vote_detected", node_id=node.node_id)
                continue
            votes[vote] = votes.get(vote, 0) + 1

        # Count maximum agreement
        max_agreement = max(votes.values()) if votes else 0
        consensus_reached = max_agreement >= self.quorum

        # Phase 2: COMMIT (if PREPARE succeeded)
        if consensus_reached:
            for node in self.nodes:
                if node.is_honest():
                    node.committed += 1

        duration_ms = round(time.time() * 1000 - start_ms, 2)

        block_hash = (
            hashlib.sha256(
                f"{proposal_hash}{datetime.utcnow().isoformat()}".encode()
            ).hexdigest()
            if consensus_reached else ""
        )

        if not consensus_reached:
            self.failed_rounds += 1
            logger.warning(
                "consensus_failed",
                proposal=proposal_id,
                votes=max_agreement,
                needed=self.quorum,
                faulty=faulty_count,
            )
        else:
            logger.info(
                "consensus_reached",
                proposal=proposal_id,
                votes=max_agreement,
                block_hash=block_hash[:16],
            )

        return ConsensusResult(
            proposal_id=proposal_id,
            transaction=transaction,
            reached=consensus_reached,
            votes_received=max_agreement,
            votes_needed=self.quorum,
            faulty_nodes=faulty_count,
            duration_ms=duration_ms,
            block_hash=block_hash,
            timestamp=datetime.utcnow().isoformat(),
        )

    def simulate_byzantine_attack(self, node_index: int):
        """Mark a node as Byzantine (for testing resilience)."""
        if 0 <= node_index < len(self.nodes):
            self.nodes[node_index].status = NodeStatus.BYZANTINE
            logger.warning("node_marked_byzantine", node_id=self.nodes[node_index].node_id)

    def heal_node(self, node_index: int):
        """Restore a node to healthy status."""
        if 0 <= node_index < len(self.nodes):
            self.nodes[node_index].status = NodeStatus.HEALTHY

    def get_network_health(self) -> Dict[str, Any]:
        healthy   = sum(1 for n in self.nodes if n.status == NodeStatus.HEALTHY)
        faulty    = sum(1 for n in self.nodes if n.status == NodeStatus.FAULTY)
        byzantine = sum(1 for n in self.nodes if n.status == NodeStatus.BYZANTINE)
        return {
            "total_nodes":   len(self.nodes),
            "healthy":       healthy,
            "faulty":        faulty,
            "byzantine":     byzantine,
            "fault_tolerance": self.f,
            "quorum_possible": healthy >= self.quorum,
            "nodes": [
                {"id": n.node_id, "org": n.org_name, "status": n.status.value,
                 "votes_cast": n.vote_count, "blocks_committed": n.committed}
                for n in self.nodes
            ],
        }

    def get_stats(self) -> Dict[str, Any]:
        success_rate = (
            (self.total_consensus_rounds - self.failed_rounds) /
            max(self.total_consensus_rounds, 1) * 100
        )
        return {
            "total_rounds":       self.total_consensus_rounds,
            "successful":         self.total_consensus_rounds - self.failed_rounds,
            "failed":             self.failed_rounds,
            "success_rate":       round(success_rate, 2),
            "byzantine_detected": self.byzantine_detected,
            "network":            self.get_network_health(),
        }
