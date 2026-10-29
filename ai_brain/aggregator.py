"""
ImmunoGrid — Federated Learning Aggregator (FL Server)

Runs on AWS SageMaker in production.
Collects model weights from all IoT edge devices,
aggregates them using FedAvg, and distributes the
global model back to all devices.

Also collects and redistributes adversarial imaginations
so every device learns from every other device's attack ideas.
"""

import copy
import json
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog
import torch
import torch.nn as nn

from .local_trainer import DefenderNet, FEATURE_NAMES

logger = structlog.get_logger(__name__)


@dataclass
class ClientUpdate:
    """Model update submitted by a single IoT device."""
    device_id: str
    round_number: int
    weights: Dict[str, List]          # Serialized model weights
    num_samples: int                  # How many samples it trained on
    metrics: Dict[str, float]         # loss, accuracy, etc.
    imaginations: List[Dict]          # Adversarial imaginations
    submitted_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class GlobalModelState:
    """The aggregated global model after each FL round."""
    round_number: int
    weights: Dict[str, List]
    num_participants: int
    avg_accuracy: float
    avg_loss: float
    total_imaginations_collected: int
    blockchain_hash: str              # Hash stored on blockchain for integrity
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class FederatedAggregator:
    """
    Federated Learning Aggregator — the central brain.

    Uses FedAvg (Federated Averaging) algorithm:
    - Each device sends: model weights (not raw data)
    - Server averages weights proportional to data size
    - Aggregated model sent back to all devices

    Also manages Adversarial Consciousness sharing:
    - Collects imaginations from all devices
    - Redistributes them so every device gets every other
      device's attack imaginations
    """

    def __init__(self, min_clients: int = 10, rounds: int = 0):
        self.min_clients = min_clients     # Minimum clients per round
        self.current_round = rounds
        self.global_model = DefenderNet(input_dim=len(FEATURE_NAMES), num_classes=5)
        self.pending_updates: List[ClientUpdate] = []
        self.global_model_history: List[GlobalModelState] = []
        self.all_imaginations: List[Dict] = []
        self.total_clients_seen: set = set()
        self._round_start_time: float = time.time()

        logger.info("fl_aggregator_initialized", min_clients=min_clients)

    def submit_update(self, update: ClientUpdate):
        """
        Receive a model update from a client device.
        Called when a device completes local training.
        """
        self.pending_updates.append(update)
        self.total_clients_seen.add(update.device_id)

        # Collect adversarial imaginations
        self.all_imaginations.extend(update.imaginations)

        logger.debug(
            "client_update_received",
            device_id=update.device_id,
            round=update.round_number,
            pending_count=len(self.pending_updates),
            imaginations_received=len(update.imaginations),
        )

        # Auto-aggregate when enough clients have submitted
        if len(self.pending_updates) >= self.min_clients:
            return self.aggregate()

        return None

    def aggregate(self) -> Optional[GlobalModelState]:
        """
        Run FedAvg aggregation on all pending client updates.

        FedAvg Algorithm:
        1. For each layer in the model
        2. Weighted average of all client weights
        3. Weight = client's num_samples / total_samples
        """
        if not self.pending_updates:
            return None

        self.current_round += 1
        updates = list(self.pending_updates)
        self.pending_updates.clear()

        total_samples = sum(u.num_samples for u in updates)

        logger.info(
            "fl_aggregation_started",
            round=self.current_round,
            clients=len(updates),
            total_samples=total_samples,
        )

        # FedAvg: weighted average of model weights
        aggregated_weights = {}
        for layer_name in updates[0].weights.keys():
            # Stack all client weights for this layer
            weighted_sum = None
            for update in updates:
                client_weight = torch.tensor(update.weights[layer_name])
                # Weight proportional to client's data size
                proportion = update.num_samples / max(total_samples, 1)
                weighted = client_weight * proportion

                if weighted_sum is None:
                    weighted_sum = weighted
                else:
                    weighted_sum = weighted_sum + weighted

            aggregated_weights[layer_name] = weighted_sum.tolist()

        # Update global model
        state_dict = {k: torch.tensor(v) for k, v in aggregated_weights.items()}
        self.global_model.load_state_dict(state_dict)

        # Calculate average metrics
        avg_accuracy = sum(u.metrics.get("accuracy", 0) for u in updates) / len(updates)
        avg_loss = sum(u.metrics.get("loss", 0) for u in updates) / len(updates)

        # Create blockchain hash for model integrity
        import hashlib
        model_str = json.dumps({k: str(v)[:50] for k, v in aggregated_weights.items()})
        blockchain_hash = hashlib.sha256(model_str.encode()).hexdigest()

        global_state = GlobalModelState(
            round_number=self.current_round,
            weights=aggregated_weights,
            num_participants=len(updates),
            avg_accuracy=round(avg_accuracy, 4),
            avg_loss=round(avg_loss, 4),
            total_imaginations_collected=len(self.all_imaginations),
            blockchain_hash=blockchain_hash,
        )

        self.global_model_history.append(global_state)

        logger.info(
            "fl_aggregation_complete",
            round=self.current_round,
            participants=len(updates),
            avg_accuracy=round(avg_accuracy, 4),
            avg_loss=round(avg_loss, 4),
            blockchain_hash=blockchain_hash[:16],
        )

        return global_state

    def get_global_weights(self) -> Optional[Dict[str, Any]]:
        """Return current global model weights for distribution to clients."""
        if not self.global_model_history:
            return None
        return {
            "round": self.current_round,
            "defender": {
                k: v.tolist()
                for k, v in self.global_model.state_dict().items()
            },
        }

    def get_imaginations_for_device(self, device_id: str) -> List[Dict]:
        """
        Return all imaginations EXCEPT those from this device.
        This is the Adversarial Consciousness sharing mechanism.
        """
        return [
            im for im in self.all_imaginations[-500:]  # Last 500
            if im.get("device_id") != device_id
        ]

    def is_round_ready(self) -> bool:
        """Check if enough clients have submitted for aggregation."""
        return len(self.pending_updates) >= self.min_clients

    def get_stats(self) -> Dict[str, Any]:
        """Return aggregator statistics."""
        latest = self.global_model_history[-1] if self.global_model_history else None
        return {
            "current_round": self.current_round,
            "total_clients_seen": len(self.total_clients_seen),
            "pending_updates": len(self.pending_updates),
            "total_imaginations_collected": len(self.all_imaginations),
            "min_clients_per_round": self.min_clients,
            "latest_accuracy": latest.avg_accuracy if latest else 0.0,
            "latest_loss": latest.avg_loss if latest else 0.0,
            "latest_blockchain_hash": latest.blockchain_hash[:16] if latest else None,
        }
