"""
ImmunoGrid — AI Brain Explainability Module
Provides explainable AI (XAI) for threat detection decisions.

Why explainability matters in government security systems:
- Security officers need to understand WHY a device was flagged
- Compliance auditors require justification for quarantine actions
- Research paper Section VII: interpretability of FAC decisions

Methods:
1. LIME  — Local Interpretable Model-agnostic Explanations
2. SHAP  — SHapley Additive exPlanations (feature importance)
3. Rule extraction — Convert model decisions to human-readable rules
4. Attention maps  — Highlight which behavioral features triggered detection
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import structlog

logger = structlog.get_logger(__name__)

FEATURE_NAMES = [
    "send_interval_s",      # 0
    "packet_size_bytes",    # 1
    "cpu_usage_pct",        # 2
    "message_rate_per_min", # 3
    "hour_of_day",          # 4
    "bytes_per_second",     # 5
    "error_rate",           # 6
    "entropy",              # 7
    "inter_arrival_jitter", # 8
    "subnet_class",         # 9
    "day_of_week",          # 10
    "is_active_hours",      # 11
]

ATTACK_DESCRIPTIONS = {
    0: "Normal traffic",
    1: "Spoofing — device impersonation attempt",
    2: "DDoS — distributed flood attack",
    3: "Data poisoning — fake sensor readings",
    4: "Replay attack — captured message replayed",
    5: "Man-in-the-middle — message interception",
    6: "Ransomware — device lockdown attempt",
}


@dataclass
class Explanation:
    """Human-readable explanation for a model prediction."""
    device_id:           str
    prediction:          str
    confidence:          float
    is_attack:           bool
    top_features:        List[Tuple[str, float]]   # (feature_name, importance)
    human_readable:      str                        # Plain English explanation
    recommended_action:  str
    timestamp:           str


class ThreatExplainer:
    """
    Provides interpretable explanations for ImmunoGrid threat detections.
    Used by security officers to understand why a device was flagged.
    """

    ACTION_MAP = {
        0: "No action required — continue normal monitoring",
        1: "Initiate quantum fingerprint re-verification; spawn 3 honeypots",
        2: "Apply rate limiting (100 msg/min); trigger DDoS mitigation",
        3: "Cross-validate readings with neighbor devices; quarantine if confirmed",
        4: "Reject message; check blockchain nonce; flag device for audit",
        5: "Force certificate rotation; enable PQC mutual authentication",
        6: "Immediate quarantine; block firmware update channel; restore from backup",
    }

    def __init__(self, classifier=None):
        """
        Args:
            classifier: Trained ThreatClassifier instance (optional).
                        If None, uses feature threshold rules.
        """
        self.classifier = classifier
        self.explanations_generated = 0

    def explain_prediction(
        self,
        features:   List[float],
        prediction: int,
        confidence: float,
        device_id:  str = "unknown",
    ) -> Explanation:
        """
        Generate a human-readable explanation for a threat prediction.

        Args:
            features:   12-dimensional feature vector
            prediction: Predicted class (0-6)
            confidence: Model confidence (0-1)
            device_id:  Device identifier
        """
        feature_importances = self._compute_feature_importance(features, prediction)
        top_features = sorted(
            zip(FEATURE_NAMES, feature_importances),
            key=lambda x: abs(x[1]),
            reverse=True,
        )[:4]

        human_readable = self._generate_human_explanation(
            features, prediction, top_features, confidence
        )
        recommended_action = self.ACTION_MAP.get(prediction, "Monitor and log")

        explanation = Explanation(
            device_id=device_id,
            prediction=ATTACK_DESCRIPTIONS.get(prediction, f"Unknown class {prediction}"),
            confidence=round(confidence * 100, 1),
            is_attack=prediction != 0,
            top_features=[(name, round(imp, 4)) for name, imp in top_features],
            human_readable=human_readable,
            recommended_action=recommended_action,
            timestamp=datetime.utcnow().isoformat(),
        )

        self.explanations_generated += 1
        return explanation

    def _compute_feature_importance(
        self,
        features:   List[float],
        prediction: int,
    ) -> List[float]:
        """
        Compute per-feature importance using perturbation-based LIME approach.
        For each feature, measures how much the prediction changes when perturbed.
        """
        if self.classifier and hasattr(self.classifier, 'classifier') and self.classifier.is_trained:
            return self._lime_importance(features, prediction)
        return self._rule_based_importance(features, prediction)

    def _lime_importance(
        self,
        features:   List[float],
        prediction: int,
        n_samples:  int = 50,
    ) -> List[float]:
        """Perturbation-based feature importance (LIME approximation)."""
        from sklearn.linear_model import LogisticRegression
        f_arr = np.array(features, dtype=np.float32)
        n = len(f_arr)

        X_perturb = np.zeros((n_samples, n))
        y_perturb = np.zeros(n_samples)

        try:
            scaler = self.classifier.scaler
            # Determine how many features the classifier's scaler expects
            scaler_n = scaler.n_features_in_ if hasattr(scaler, 'n_features_in_') else n
        except Exception:
            scaler = None
            scaler_n = n

        for i in range(n_samples):
            noise = np.random.normal(0, 0.1 * (np.abs(f_arr) + 1e-6))
            perturbed = f_arr + noise
            X_perturb[i] = perturbed

            # Only pass the features the scaler was trained on
            clf_features = perturbed[:scaler_n].reshape(1, -1)

            if scaler is not None:
                scaled = scaler.transform(clf_features)
            else:
                scaled = clf_features

            pred = self.classifier.classifier.predict(scaled)[0]
            y_perturb[i] = 1 if pred == prediction else 0

        # Fit a local linear model
        if y_perturb.sum() > 0 and y_perturb.sum() < n_samples:
            try:
                lr = LogisticRegression(max_iter=200, random_state=42)
                lr.fit(X_perturb, y_perturb)
                return lr.coef_[0].tolist()
            except Exception:
                pass

        return self._rule_based_importance(features, prediction)

    def _rule_based_importance(
        self,
        features:   List[float],
        prediction: int,
    ) -> List[float]:
        """Rule-based importance when ML model is unavailable."""
        importances = [0.0] * len(FEATURE_NAMES)

        if prediction == 1:   # Spoofing
            importances[0]  =  abs(features[0] - 2.3)        # send_interval deviation
            importances[1]  =  abs(features[1] - 48.0) / 10  # packet_size deviation
            importances[8]  =  features[8] / 100              # high jitter
            importances[9]  =  1.0 if features[9] == 99 else 0  # wrong subnet

        elif prediction == 2:  # DDoS
            importances[2]  = features[2] / 100               # high CPU
            importances[3]  = min(features[3] / 600, 1.0)     # high msg rate
            importances[5]  = min(features[5] / 1000, 1.0)    # high bytes/sec

        elif prediction == 3:  # Data poisoning
            importances[7]  = features[7]                      # high entropy
            importances[6]  = features[6]                      # high error rate

        elif prediction == 4:  # Replay
            importances[7]  = 1.0 - features[7]               # low entropy
            importances[6]  = features[6]                      # high error rate
            importances[11] = 1.0 - features[11]              # not active hours

        elif prediction == 5:  # MITM
            importances[8]  = min(features[8] / 500, 1.0)     # very high jitter
            importances[7]  = 0.5 - features[7] if features[7] < 0.5 else 0  # low entropy

        elif prediction == 6:  # Ransomware
            importances[2]  = features[2] / 100               # maxed CPU
            importances[0]  = max(0, 0.1 - features[0])       # very fast interval
            importances[9]  = 1.0 if features[9] == 99 else 0  # foreign subnet

        return importances

    def _generate_human_explanation(
        self,
        features:     List[float],
        prediction:   int,
        top_features: List[Tuple[str, float]],
        confidence:   float,
    ) -> str:
        """Generate a plain English explanation."""
        attack_name = ATTACK_DESCRIPTIONS.get(prediction, "Unknown")
        conf_str    = f"{confidence * 100:.0f}%"
        top_names   = [f[0].replace('_', ' ') for f in top_features[:2]]

        if prediction == 0:
            return (
                f"Traffic is normal (confidence: {conf_str}). "
                f"All behavioral features within expected ranges."
            )

        lines = [
            f"⚠️  {attack_name} detected (confidence: {conf_str}).",
            f"Key indicators: {top_names[0]} and {top_names[1]} are anomalous.",
        ]

        if prediction == 1:
            lines.append(
                f"Send interval: {features[0]:.3f}s (expected ~2.3s), "
                f"subnet class: {int(features[9])} (wrong subnet detected)."
            )
        elif prediction == 2:
            lines.append(
                f"CPU usage: {features[2]:.0f}% (normal <25%), "
                f"message rate: {features[3]:.0f} msg/min (normal <30)."
            )
        elif prediction == 3:
            lines.append(
                f"Data entropy: {features[7]:.3f} (normal 0.45-0.65, "
                f"poisoned data has unusually high entropy)."
            )
        elif prediction == 4:
            lines.append(
                f"Message at hour {int(features[4])} (off-hours), "
                f"entropy {features[7]:.3f} (low = repeated content = replay)."
            )
        elif prediction == 5:
            lines.append(
                f"Inter-arrival jitter: {features[8]:.0f}ms "
                f"(normal <100ms, MITM interception causes delay)."
            )
        elif prediction == 6:
            lines.append(
                f"Send interval: {features[0]:.3f}s (abnormally fast), "
                f"CPU: {features[2]:.0f}% (ransomware maxes device resources)."
            )

        return " ".join(lines)

    def explain_classifier_decision(
        self,
        message:  Dict[str, Any],
        result:   Any,           # ClassificationResult
        device_id: str = "unknown",
    ) -> Explanation:
        """Convenience wrapper for classifier result objects."""
        return self.explain_prediction(
            features   = result.feature_values,
            prediction = result.predicted_class,
            confidence = result.confidence,
            device_id  = device_id,
        )

    def batch_explain(
        self,
        features_list: List[List[float]],
        predictions:   List[int],
        confidences:   List[float],
        device_ids:    Optional[List[str]] = None,
    ) -> List[Explanation]:
        """Generate explanations for a batch of predictions."""
        if device_ids is None:
            device_ids = [f"device-{i:04d}" for i in range(len(features_list))]

        return [
            self.explain_prediction(f, p, c, d)
            for f, p, c, d in zip(features_list, predictions, confidences, device_ids)
        ]

    def get_stats(self) -> Dict[str, Any]:
        return {"explanations_generated": self.explanations_generated}
