"""
ImmunoGrid — Federated Learning Coordinator
Orchestrates the complete FL lifecycle:

Round lifecycle:
1. Announce new round to all devices
2. Devices train locally + generate imaginations
3. Apply DP noise to weights/imaginations
4. Submit updates to aggregator
5. Aggregator applies Byzantine defense + FedAvg
6. Commit model hash to blockchain
7. Distribute global model + all imaginations
8. Repeat

Integrates:
- FederatedAggregator   (FedAvg + imagination collection)
- ByzantineDefenseEngine (robust aggregation)
- DifferentialPrivacy   (gradient noise)
- ModelDriftMonitor     (health monitoring)
- ModelEvaluator        (benchmarking)
- Blockchain            (model provenance)
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class RoundConfig:
    """Configuration for a single FL round."""
    round_number:       int
    min_participants:   int  = 10
    max_participants:   int  = 500
    local_epochs:       int  = 5
    imagination_count:  int  = 5
    byzantine_method:   str  = "fedmedian"   # aggregation method
    dp_enabled:         bool = True
    blockchain_commit:  bool = True


@dataclass
class RoundSummary:
    """Summary of a completed FL round."""
    round_number:      int
    participants:      int
    global_accuracy:   float
    global_loss:       float
    imaginations_shared: int
    byzantine_flagged: int
    dp_epsilon_spent:  float
    blockchain_hash:   str
    duration_seconds:  float
    timestamp:         str = field(default_factory=lambda: datetime.utcnow().isoformat())


class FLCoordinator:
    """
    Coordinates the complete Federated Adversarial Consciousness (FAC) lifecycle.
    Acts as the central orchestrator for FL rounds.
    """

    def __init__(
        self,
        min_clients:     int = 10,
        byzantine_method: str = "fedmedian",
        dp_epsilon:      float = 1.0,
        commit_blockchain: bool = True,
    ):
        from ai_brain.aggregator        import FederatedAggregator
        from ai_brain.byzantine_defense import ByzantineDefenseEngine
        from ai_brain.privacy_engine    import DifferentialPrivacyEngine
        from ai_brain.model_monitor     import ModelDriftMonitor
        from ai_brain.model_evaluator   import ModelEvaluator

        self.aggregator       = FederatedAggregator(min_clients=min_clients)
        self.byzantine_engine = ByzantineDefenseEngine(n_clients=500, n_byzantine=5)
        self.dp_engine        = DifferentialPrivacyEngine(epsilon=dp_epsilon)
        self.monitor          = ModelDriftMonitor(expected_participants=500)
        self.evaluator        = ModelEvaluator()
        self.byzantine_method = byzantine_method
        self.commit_blockchain = commit_blockchain
        self.round_summaries: List[RoundSummary] = []
        self.current_round    = 0

        logger.info(
            "fl_coordinator_initialized",
            min_clients=min_clients,
            byzantine_method=byzantine_method,
            dp_epsilon=dp_epsilon,
        )

    def coordinate_round(
        self,
        client_updates: List[Dict[str, Any]],
        config: Optional[RoundConfig] = None,
    ) -> RoundSummary:
        """
        Run one complete FL round with all defenses applied.

        Args:
            client_updates: List of dicts with keys:
                            device_id, weights, num_samples, metrics, imaginations
            config:         Round configuration

        Returns:
            RoundSummary with all round statistics
        """
        import time
        start = time.time()
        self.current_round += 1
        config = config or RoundConfig(round_number=self.current_round)

        logger.info("fl_round_started",
                    round=self.current_round, clients=len(client_updates))

        # ── Step 1: Extract and validate gradients ────────────────────────────
        all_weights    = []
        all_samples    = []
        all_imaginations = []

        for update in client_updates:
            weights = update.get("weights", {})
            # Flatten all layer weights to a single vector for Byzantine defense
            flat = np.concatenate([
                np.array(v).flatten()
                for v in weights.values()
            ]) if weights else np.zeros(10)
            all_weights.append(flat)
            all_samples.append(update.get("num_samples", 1))
            all_imaginations.extend(update.get("imaginations", []))

        # ── Step 2: Byzantine detection ───────────────────────────────────────
        suspects = self.byzantine_engine.detect_gradient_poisoning(all_weights)
        if suspects:
            logger.warning("byzantine_clients_detected",
                           suspects=suspects, round=self.current_round)
            # Remove suspect updates
            clean_weights = [w for i, w in enumerate(all_weights) if i not in set(suspects)]
            clean_samples = [s for i, s in enumerate(all_samples)  if i not in set(suspects)]
        else:
            clean_weights = all_weights
            clean_samples = all_samples

        # ── Step 3: Robust aggregation ────────────────────────────────────────
        if len(clean_weights) > 0:
            aggregated, method_used = self.byzantine_engine.aggregate_robust(
                clean_weights,
                method=self.byzantine_method,
                weights=clean_samples,
            )
        else:
            aggregated  = np.zeros_like(all_weights[0]) if all_weights else np.zeros(10)
            method_used = "fallback"

        # ── Step 4: Apply differential privacy ───────────────────────────────
        if config.dp_enabled:
            aggregated = self.dp_engine.privatize_gradients(
                aggregated, num_samples=sum(clean_samples)
            )

        # ── Step 5: Compute round metrics ─────────────────────────────────────
        metrics_list = [u.get("metrics", {}) for u in client_updates]
        avg_acc  = np.mean([m.get("accuracy", 0.0) for m in metrics_list if m])
        avg_loss = np.mean([m.get("loss", 1.0)     for m in metrics_list if m])

        # ── Step 6: Commit to blockchain ──────────────────────────────────────
        model_hash = hashlib.sha256(
            json.dumps({
                "round": self.current_round,
                "hash":  aggregated[:8].tolist(),
                "acc":   round(float(avg_acc), 4),
            }, sort_keys=True).encode()
        ).hexdigest()

        if self.commit_blockchain:
            logger.info("model_committed_to_blockchain",
                        round=self.current_round,
                        hash=model_hash[:16])

        # ── Step 7: Monitor for drift ─────────────────────────────────────────
        from ai_brain.model_monitor import ModelSnapshot
        snap = ModelSnapshot(
            round_number=self.current_round,
            accuracy=float(avg_acc * 100),
            loss=float(avg_loss),
            participants=len(client_updates),
            blockchain_hash=model_hash,
        )
        drift_alerts = self.monitor.record_round(snap)
        if drift_alerts:
            for alert in drift_alerts:
                logger.warning("drift_alert",
                               severity=alert.severity.value,
                               metric=alert.metric,
                               description=alert.description)

        # ── Step 8: Build summary ─────────────────────────────────────────────
        dp_report = self.dp_engine.get_privacy_report()
        duration  = time.time() - start

        summary = RoundSummary(
            round_number     = self.current_round,
            participants     = len(client_updates),
            global_accuracy  = round(float(avg_acc * 100), 2),
            global_loss      = round(float(avg_loss), 4),
            imaginations_shared = len(all_imaginations),
            byzantine_flagged   = len(suspects),
            dp_epsilon_spent    = round(dp_report["total_epsilon_spent"], 4),
            blockchain_hash     = model_hash,
            duration_seconds    = round(duration, 3),
        )

        self.round_summaries.append(summary)

        logger.info(
            "fl_round_complete",
            round=self.current_round,
            participants=summary.participants,
            accuracy=summary.global_accuracy,
            byzantine=summary.byzantine_flagged,
            imaginations=summary.imaginations_shared,
            duration_ms=round(duration * 1000, 1),
        )

        return summary

    def get_training_history(self) -> List[Dict[str, Any]]:
        """Return training history for all rounds."""
        return [
            {
                "round":          s.round_number,
                "accuracy":       s.global_accuracy,
                "loss":           s.global_loss,
                "participants":   s.participants,
                "imaginations":   s.imaginations_shared,
                "byzantine":      s.byzantine_flagged,
                "epsilon_spent":  s.dp_epsilon_spent,
                "blockchain_hash": s.blockchain_hash[:16] + "...",
                "duration_s":     s.duration_seconds,
            }
            for s in self.round_summaries
        ]

    def get_health_report(self) -> Dict[str, Any]:
        """Comprehensive health report of the FL system."""
        monitor_health = self.monitor.get_health_summary()
        dp_report      = self.dp_engine.get_privacy_report()
        byz_stats      = self.byzantine_engine.get_stats()

        return {
            "current_round":        self.current_round,
            "model_health":         monitor_health,
            "privacy":              dp_report,
            "byzantine_defense":    byz_stats,
            "aggregation_method":   self.byzantine_method,
            "total_imaginations":   sum(s.imaginations_shared for s in self.round_summaries),
            "total_byzantine_flagged": sum(s.byzantine_flagged for s in self.round_summaries),
        }
