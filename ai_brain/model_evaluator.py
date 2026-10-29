"""
ImmunoGrid — FL Model Evaluator
Evaluates, compares, and benchmarks federated learning models.

Produces:
- Per-class accuracy breakdown
- Confusion matrix
- F1-score, precision, recall per attack type
- Comparison between FL rounds (convergence analysis)
- Adversarial robustness evaluation (how well model resists poisoning)
- Paper-ready benchmark tables
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import structlog

logger = structlog.get_logger(__name__)

ATTACK_LABELS = {
    0: "normal",
    1: "spoofing",
    2: "ddos",
    3: "data_poisoning",
    4: "replay_attack",
    5: "mitm",
    6: "ransomware",
}


@dataclass
class ClassMetrics:
    """Per-class evaluation metrics."""
    class_name:  str
    precision:   float
    recall:      float
    f1_score:    float
    support:     int    # Number of test samples for this class


@dataclass
class EvaluationResult:
    """Complete evaluation result for one model version."""
    round_number:    int
    overall_accuracy: float
    macro_f1:        float
    weighted_f1:     float
    per_class:       List[ClassMetrics]
    confusion_matrix: List[List[int]]
    evaluated_at:    str = field(default_factory=lambda: datetime.utcnow().isoformat())
    notes:           str = ""


class ModelEvaluator:
    """
    Evaluates ImmunoGrid AI Brain model performance.
    Used for:
    1. Research paper Table III (detection rates per attack type)
    2. Monitoring model quality across FL rounds
    3. Detecting model degradation / poisoning
    4. Comparing FAC vs standard FedAvg
    """

    def __init__(self):
        self.evaluation_history: List[EvaluationResult] = []

    def evaluate(
        self,
        model,              # sklearn or torch model with predict method
        X_test:   np.ndarray,
        y_test:   np.ndarray,
        round_number: int = 0,
        notes:    str = "",
    ) -> EvaluationResult:
        """Evaluate a model on test data."""
        if hasattr(model, 'predict'):
            y_pred = model.predict(X_test)
        elif hasattr(model, 'classify'):
            y_pred = np.array([model.classify({'behavior': {}}).predicted_class
                               for _ in X_test])
        else:
            raise ValueError("Model must have predict() or classify() method")

        return self._compute_metrics(y_pred, y_test, round_number, notes)

    def evaluate_predictions(
        self,
        y_pred:       np.ndarray,
        y_test:       np.ndarray,
        round_number: int = 0,
        notes:        str = "",
    ) -> EvaluationResult:
        """Evaluate from already-computed predictions."""
        return self._compute_metrics(y_pred, y_test, round_number, notes)

    def _compute_metrics(
        self,
        y_pred:       np.ndarray,
        y_test:       np.ndarray,
        round_number: int,
        notes:        str,
    ) -> EvaluationResult:
        """Compute all metrics from predictions and ground truth."""
        # Use union of true labels and predicted labels, sorted
        classes = sorted(set(int(x) for x in y_test) | set(int(x) for x in y_pred))
        n = len(y_test)

        # Overall accuracy
        accuracy = float((y_pred == y_test).sum()) / n

        # Confusion matrix indexed by class position
        cls_to_idx = {c: i for i, c in enumerate(classes)}
        cm = [[0] * len(classes) for _ in range(len(classes))]
        for true, pred in zip(y_test, y_pred):
            ti = cls_to_idx.get(int(true))
            pi = cls_to_idx.get(int(pred))
            if ti is not None and pi is not None:
                cm[ti][pi] += 1

        # Per-class metrics
        per_class = []
        for cls in classes:
            tp = int(sum(1 for t, p in zip(y_test, y_pred) if t == cls and p == cls))
            fp = int(sum(1 for t, p in zip(y_test, y_pred) if t != cls and p == cls))
            fn = int(sum(1 for t, p in zip(y_test, y_pred) if t == cls and p != cls))
            support = int((y_test == cls).sum())

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1        = (2 * precision * recall / (precision + recall)
                         if (precision + recall) > 0 else 0.0)

            per_class.append(ClassMetrics(
                class_name = ATTACK_LABELS.get(cls, f"class_{cls}"),
                precision  = round(precision, 4),
                recall     = round(recall,    4),
                f1_score   = round(f1,        4),
                support    = support,
            ))

        macro_f1 = round(float(np.mean([m.f1_score for m in per_class])), 4)
        total_support = sum(m.support for m in per_class)
        weighted_f1   = round(
            sum(m.f1_score * m.support for m in per_class) / max(total_support, 1), 4,
        )

        result = EvaluationResult(
            round_number     = round_number,
            overall_accuracy = round(accuracy * 100, 2),
            macro_f1         = round(macro_f1 * 100, 2),
            weighted_f1      = round(weighted_f1 * 100, 2),
            per_class        = per_class,
            confusion_matrix = cm,
            notes            = notes,
        )

        self.evaluation_history.append(result)
        logger.info("model_evaluated", round=round_number,
                    accuracy=result.overall_accuracy, macro_f1=result.macro_f1)
        return result

    def compare_rounds(self) -> Dict[str, Any]:
        """Compare model performance across FL rounds."""
        if not self.evaluation_history:
            return {"error": "No evaluations recorded"}

        return {
            "rounds_evaluated": len(self.evaluation_history),
            "best_accuracy":    max(r.overall_accuracy for r in self.evaluation_history),
            "latest_accuracy":  self.evaluation_history[-1].overall_accuracy,
            "accuracy_trend":   [r.overall_accuracy for r in self.evaluation_history],
            "f1_trend":         [r.macro_f1         for r in self.evaluation_history],
            "converged":        (
                len(self.evaluation_history) >= 3 and
                self.evaluation_history[-1].overall_accuracy >= 95.0
            ),
        }

    def generate_paper_table(self) -> str:
        """Generate LaTeX table for research paper (Table III)."""
        if not self.evaluation_history:
            return "No evaluation data available"

        latest = self.evaluation_history[-1]
        lines  = [
            r"\begin{table}[h]",
            r"\caption{Attack Detection Rates by Attack Type}",
            r"\label{tab:detection}",
            r"\centering",
            r"\begin{tabular}{lccc}",
            r"\toprule",
            r"\textbf{Attack Type} & \textbf{Precision (\%)} & \textbf{Recall (\%)} & \textbf{F1-Score (\%)} \\",
            r"\midrule",
        ]
        for m in latest.per_class:
            if m.class_name != "normal":
                lines.append(
                    f"{m.class_name.replace('_',' ').title()} & "
                    f"{m.precision*100:.1f} & "
                    f"{m.recall*100:.1f} & "
                    f"{m.f1_score*100:.1f} \\\\"
                )
        lines.extend([
            r"\midrule",
            f"\\textbf{{Overall}} & & & \\textbf{{{latest.macro_f1:.1f}}} \\\\",
            r"\bottomrule",
            r"\end{tabular}",
            r"\end{table}",
        ])
        return "\n".join(lines)

    def detect_model_degradation(self, threshold_pct: float = 5.0) -> Optional[str]:
        """
        Detect if model is degrading across rounds.
        Returns warning message if degradation detected, None if healthy.
        """
        if len(self.evaluation_history) < 3:
            return None

        recent = self.evaluation_history[-3:]
        peak   = max(r.overall_accuracy for r in self.evaluation_history)
        latest = recent[-1].overall_accuracy

        drop = peak - latest
        if drop >= threshold_pct:
            return (
                f"⚠️  Model degradation detected: accuracy dropped {drop:.1f}% "
                f"from peak {peak:.1f}% to {latest:.1f}%. "
                f"Possible Byzantine poisoning or concept drift."
            )
        return None

    def get_detection_rates(self) -> Dict[str, float]:
        """
        Return detection rates per attack type.
        Used for paper Table III and dashboard display.
        """
        if not self.evaluation_history:
            return {}
        latest = self.evaluation_history[-1]
        return {
            m.class_name: round(m.recall * 100, 1)
            for m in latest.per_class
            if m.class_name != "normal"
        }
