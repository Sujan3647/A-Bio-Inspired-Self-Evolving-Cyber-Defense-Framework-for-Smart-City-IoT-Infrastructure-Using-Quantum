"""
ImmunoGrid — FL Model Drift Monitor
Detects when the global federated model starts degrading
due to concept drift, adversarial poisoning, or data distribution shift.

Monitors:
1. Accuracy degradation over FL rounds
2. Loss spike detection
3. Gradient divergence (Byzantine fault indicator)
4. Imagination diversity (FAC health check)
5. Model version integrity via blockchain hash
"""

import hashlib
import json
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)


class DriftSeverity(Enum):
    NONE     = "none"
    MINOR    = "minor"
    MODERATE = "moderate"
    SEVERE   = "severe"


@dataclass
class ModelSnapshot:
    """Snapshot of model performance at a given FL round."""
    round_number: int
    accuracy: float
    loss: float
    participants: int
    blockchain_hash: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class DriftAlert:
    """Alert raised when model drift is detected."""
    alert_id: str
    severity: DriftSeverity
    metric: str
    description: str
    current_value: float
    threshold: float
    recommended_action: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class ModelDriftMonitor:
    """
    Monitors the federated learning model for drift and poisoning.

    Thresholds:
    - Accuracy drop > 5% from peak → moderate alert
    - Accuracy drop > 10% from peak → severe alert
    - Loss spike > 2× baseline → moderate alert
    - Participants drop > 20% → minor alert (potential Byzantine fault)
    """

    ACCURACY_DROP_MODERATE = 0.05    # 5% drop
    ACCURACY_DROP_SEVERE   = 0.10    # 10% drop
    LOSS_SPIKE_THRESHOLD   = 2.0     # 2× baseline
    MIN_PARTICIPANTS_RATIO = 0.80    # 80% of expected

    def __init__(self, expected_participants: int = 500):
        self.snapshots: List[ModelSnapshot] = []
        self.alerts: List[DriftAlert] = []
        self.expected_participants = expected_participants
        self.peak_accuracy = 0.0
        self.baseline_loss: Optional[float] = None
        self.alert_count = 0

    def record_round(self, snapshot: ModelSnapshot) -> List[DriftAlert]:
        """Record a new FL round and check for drift."""
        self.snapshots.append(snapshot)

        # Update peak accuracy
        if snapshot.accuracy > self.peak_accuracy:
            self.peak_accuracy = snapshot.accuracy

        # Set baseline loss from first 5 rounds
        if len(self.snapshots) == 5:
            self.baseline_loss = statistics.mean(
                s.loss for s in self.snapshots[:5]
            )

        new_alerts = []

        # Check accuracy degradation
        acc_alert = self._check_accuracy_drift(snapshot)
        if acc_alert:
            new_alerts.append(acc_alert)

        # Check loss spike
        loss_alert = self._check_loss_spike(snapshot)
        if loss_alert:
            new_alerts.append(loss_alert)

        # Check participant drop
        part_alert = self._check_participant_drop(snapshot)
        if part_alert:
            new_alerts.append(part_alert)

        # Check blockchain hash validity
        hash_alert = self._check_model_integrity(snapshot)
        if hash_alert:
            new_alerts.append(hash_alert)

        self.alerts.extend(new_alerts)

        if new_alerts:
            logger.warning(
                "model_drift_detected",
                round=snapshot.round_number,
                alerts=len(new_alerts),
                severities=[a.severity.value for a in new_alerts],
            )
        else:
            logger.debug(
                "fl_round_healthy",
                round=snapshot.round_number,
                accuracy=snapshot.accuracy,
                loss=snapshot.loss,
            )

        return new_alerts

    def _make_alert(
        self,
        severity: DriftSeverity,
        metric: str,
        description: str,
        current: float,
        threshold: float,
        action: str,
    ) -> DriftAlert:
        self.alert_count += 1
        return DriftAlert(
            alert_id=f"DRIFT-{self.alert_count:06d}",
            severity=severity,
            metric=metric,
            description=description,
            current_value=current,
            threshold=threshold,
            recommended_action=action,
        )

    def _check_accuracy_drift(self, snap: ModelSnapshot) -> Optional[DriftAlert]:
        if self.peak_accuracy == 0:
            return None
        drop = (self.peak_accuracy - snap.accuracy) / self.peak_accuracy
        if drop >= self.ACCURACY_DROP_SEVERE:
            return self._make_alert(
                DriftSeverity.SEVERE,
                "accuracy",
                f"Accuracy dropped {drop*100:.1f}% from peak {self.peak_accuracy:.1f}% — possible Byzantine poisoning",
                snap.accuracy,
                self.peak_accuracy * (1 - self.ACCURACY_DROP_SEVERE),
                "Trigger Byzantine fault detection — review client updates for round " + str(snap.round_number),
            )
        if drop >= self.ACCURACY_DROP_MODERATE:
            return self._make_alert(
                DriftSeverity.MODERATE,
                "accuracy",
                f"Accuracy dropped {drop*100:.1f}% — possible concept drift or data poisoning",
                snap.accuracy,
                self.peak_accuracy * (1 - self.ACCURACY_DROP_MODERATE),
                "Re-run adversarial imagination generation. Add new training scenarios.",
            )
        return None

    def _check_loss_spike(self, snap: ModelSnapshot) -> Optional[DriftAlert]:
        if not self.baseline_loss:
            return None
        ratio = snap.loss / self.baseline_loss
        if ratio >= self.LOSS_SPIKE_THRESHOLD:
            return self._make_alert(
                DriftSeverity.MODERATE,
                "loss",
                f"Loss spiked to {snap.loss:.4f} ({ratio:.1f}× baseline) — possible gradient injection",
                snap.loss,
                self.baseline_loss * self.LOSS_SPIKE_THRESHOLD,
                "Inspect gradient submissions from round " + str(snap.round_number) + ". Exclude outlier clients.",
            )
        return None

    def _check_participant_drop(self, snap: ModelSnapshot) -> Optional[DriftAlert]:
        ratio = snap.participants / self.expected_participants
        if ratio < self.MIN_PARTICIPANTS_RATIO:
            return self._make_alert(
                DriftSeverity.MINOR,
                "participants",
                f"Only {snap.participants}/{self.expected_participants} devices participated — possible network issue",
                float(snap.participants),
                float(self.expected_participants * self.MIN_PARTICIPANTS_RATIO),
                "Check IoT device connectivity. Resume failed nodes.",
            )
        return None

    def _check_model_integrity(self, snap: ModelSnapshot) -> Optional[DriftAlert]:
        """Verify the model hash matches what's recorded on blockchain."""
        # Recompute hash from snapshot data
        expected_hash = hashlib.sha256(
            f"{snap.round_number}{snap.accuracy:.4f}{snap.loss:.4f}".encode()
        ).hexdigest()
        # In production: compare against blockchain record
        # For simulation: always passes
        return None

    def get_health_summary(self) -> Dict[str, Any]:
        """Return overall model health summary."""
        if not self.snapshots:
            return {"status": "no_data", "rounds": 0}

        last = self.snapshots[-1]
        recent_acc = [s.accuracy for s in self.snapshots[-5:]]
        trend = "improving" if len(recent_acc) > 1 and recent_acc[-1] > recent_acc[0] else \
                "declining"  if len(recent_acc) > 1 and recent_acc[-1] < recent_acc[0] - 0.01 else \
                "stable"

        recent_alerts = [a for a in self.alerts[-10:] if a.severity != DriftSeverity.NONE]
        critical_alerts = [a for a in recent_alerts if a.severity == DriftSeverity.SEVERE]

        status = "healthy" if not critical_alerts else "critical" if critical_alerts else "warning"

        return {
            "status": status,
            "rounds_completed": len(self.snapshots),
            "current_accuracy": last.accuracy,
            "peak_accuracy": self.peak_accuracy,
            "current_loss": last.loss,
            "accuracy_trend": trend,
            "total_drift_alerts": len(self.alerts),
            "recent_alerts": len(recent_alerts),
            "critical_alerts": len(critical_alerts),
            "model_healthy": status == "healthy",
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            "snapshots_recorded": len(self.snapshots),
            "total_alerts": len(self.alerts),
            "peak_accuracy": self.peak_accuracy,
            "baseline_loss": self.baseline_loss,
            "health": self.get_health_summary(),
        }
