"""
ImmunoGrid — Standalone Threat Classifier
A lightweight scikit-learn classifier for threat detection.
Used when PyTorch is unavailable or for initial bootstrapping.

Classifies IoT messages into:
  0 = normal
  1 = spoofing
  2 = ddos
  3 = data_poisoning
  4 = replay_attack
"""

import json
import pickle
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import structlog
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

logger = structlog.get_logger(__name__)

ATTACK_LABELS = {
    0: "normal",
    1: "spoofing",
    2: "ddos",
    3: "data_poisoning",
    4: "replay_attack",
}

FEATURE_NAMES = [
    "send_interval", "packet_size", "cpu_usage",
    "message_rate", "hour_of_day", "bytes_per_second",
    "error_rate", "entropy",
]


@dataclass
class ClassificationResult:
    device_id: str
    predicted_label: str
    predicted_class: int
    confidence: float
    is_attack: bool
    feature_values: List[float]
    classified_at: str


class ThreatClassifier:
    """
    Lightweight RandomForest-based threat classifier.
    Works without PyTorch — uses scikit-learn only.
    Can be used standalone or as a fallback when the FAC AI is unavailable.
    """

    def __init__(self, n_estimators: int = 100):
        self.classifier = RandomForestClassifier(
            n_estimators=n_estimators,
            random_state=42,
            class_weight="balanced",
        )
        self.anomaly_detector = IsolationForest(
            contamination=0.1,
            random_state=42,
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        self.training_samples = 0
        self.accuracy = 0.0

    def extract_features(self, message: Dict[str, Any]) -> np.ndarray:
        """Extract numeric feature vector from a device message."""
        behavior = message.get("behavior", {})
        hour = datetime.utcnow().hour
        send_interval = behavior.get("send_interval", 2.0)

        features = [
            send_interval,
            float(behavior.get("packet_size", 48)),
            behavior.get("cpu_usage", 0.15),
            1.0 / max(send_interval, 0.1),
            hour / 23.0,
            float(behavior.get("packet_size", 48)) / max(send_interval, 0.1),
            0.0,
            0.5,
        ]
        return np.array(features, dtype=np.float32)

    def generate_synthetic_dataset(self, n_samples: int = 2000) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate a synthetic training dataset representing normal + attack behavior.
        Used for initial model training before real data is available.
        """
        np.random.seed(42)
        X, y = [], []

        samples_per_class = n_samples // 5

        # Normal traffic
        for _ in range(samples_per_class):
            X.append([
                np.random.normal(2.3, 0.2),    # send_interval
                np.random.normal(48, 3),        # packet_size
                np.random.uniform(0.08, 0.25),  # cpu_usage
                np.random.normal(0.43, 0.05),   # message_rate
                np.random.uniform(0, 1),        # hour_normalized
                np.random.normal(20, 3),        # bytes/sec
                np.random.uniform(0, 0.02),     # error_rate
                np.random.uniform(0.4, 0.6),    # entropy
            ])
            y.append(0)

        # Spoofing (wrong timing + subnet)
        for _ in range(samples_per_class):
            X.append([
                np.random.normal(2.0, 0.8),    # off timing
                np.random.normal(55, 8),        # wrong size
                np.random.uniform(0.0, 0.5),
                np.random.normal(0.50, 0.2),
                np.random.uniform(0, 1),
                np.random.normal(28, 8),
                np.random.uniform(0, 0.1),
                np.random.uniform(0.3, 0.8),
            ])
            y.append(1)

        # DDoS (very high message rate + high CPU)
        for _ in range(samples_per_class):
            X.append([
                np.random.uniform(0.01, 0.1),  # very fast
                np.random.normal(48, 2),
                np.random.uniform(0.8, 1.0),   # maxed CPU
                np.random.uniform(10, 100),    # high rate
                np.random.uniform(0, 1),
                np.random.uniform(400, 1000),
                np.random.uniform(0.2, 0.5),
                np.random.uniform(0.1, 0.4),
            ])
            y.append(2)

        # Data poisoning (normal timing but wrong values)
        for _ in range(samples_per_class):
            X.append([
                np.random.normal(2.3, 0.15),
                np.random.normal(48, 2),
                np.random.uniform(0.1, 0.2),
                np.random.normal(0.43, 0.03),
                np.random.uniform(0, 1),
                np.random.normal(20, 2),
                np.random.uniform(0, 0.05),
                np.random.uniform(0.8, 1.0),   # high entropy = unusual data
            ])
            y.append(3)

        # Replay attack (old timestamps, repeated sequence)
        for _ in range(samples_per_class):
            X.append([
                np.random.normal(2.3, 0.1),
                np.random.normal(48, 1),
                np.random.uniform(0.08, 0.15),
                np.random.normal(0.43, 0.02),
                np.random.uniform(0, 0.3),     # off-hours replay
                np.random.normal(20, 1),
                np.random.uniform(0.3, 0.8),   # high error (repeated seq)
                np.random.uniform(0.0, 0.2),   # low entropy
            ])
            y.append(4)

        return np.array(X, dtype=np.float32), np.array(y)

    def train(self, X: Optional[np.ndarray] = None, y: Optional[np.ndarray] = None):
        """Train the classifier. Uses synthetic data if none provided."""
        if X is None or y is None:
            logger.info("generating_synthetic_training_data")
            X, y = self.generate_synthetic_dataset(n_samples=2000)

        self.training_samples = len(X)

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42, stratify=y
        )

        # Train classifier
        self.classifier.fit(X_train, y_train)

        # Train anomaly detector
        normal_mask = y_train == 0
        self.anomaly_detector.fit(X_train[normal_mask])

        # Evaluate
        y_pred = self.classifier.predict(X_test)
        self.accuracy = accuracy_score(y_test, y_pred)
        self.is_trained = True

        # Build target names based on actual classes in test set
        test_classes = sorted(set(y_test.tolist()) | set(y_pred.tolist()))
        target_names = [ATTACK_LABELS.get(i, f"class_{i}") for i in test_classes]

        logger.info(
            "threat_classifier_trained",
            samples=self.training_samples,
            accuracy=round(self.accuracy, 4),
        )

        return {
            "accuracy": round(self.accuracy * 100, 2),
            "samples":  self.training_samples,
            "report":   classification_report(
                y_test, y_pred,
                labels=test_classes,
                target_names=target_names,
                output_dict=True,
            ),
        }

    def classify(self, message: Dict[str, Any]) -> ClassificationResult:
        """Classify a single message."""
        if not self.is_trained:
            self.train()

        features = self.extract_features(message)
        features_scaled = self.scaler.transform(features.reshape(1, -1))

        # Classification
        predicted_class = int(self.classifier.predict(features_scaled)[0])
        probas = self.classifier.predict_proba(features_scaled)[0]
        confidence = float(probas[predicted_class])

        # Anomaly detection (secondary check)
        anomaly_score = self.anomaly_detector.decision_function(features_scaled)[0]
        is_anomaly = anomaly_score < -0.1

        # If anomaly detected but classifier says normal, upgrade to suspicious
        if is_anomaly and predicted_class == 0:
            predicted_class = 1  # Flag as spoofing
            confidence = max(0.6, confidence)

        return ClassificationResult(
            device_id=message.get("device_id", "unknown"),
            predicted_label=ATTACK_LABELS.get(predicted_class, "unknown"),
            predicted_class=predicted_class,
            confidence=round(confidence, 4),
            is_attack=predicted_class != 0,
            feature_values=features.tolist(),
            classified_at=datetime.utcnow().isoformat(),
        )

    def save_model(self, path: str = "threat_classifier.pkl"):
        """Save trained model to disk."""
        with open(path, "wb") as f:
            pickle.dump({"classifier": self.classifier, "scaler": self.scaler,
                         "anomaly": self.anomaly_detector, "accuracy": self.accuracy}, f)
        logger.info("model_saved", path=path)

    def load_model(self, path: str = "threat_classifier.pkl"):
        """Load trained model from disk."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model file not found: {path}")
        with open(path, "rb") as f:
            data = pickle.load(f)
        self.classifier = data["classifier"]
        self.scaler = data["scaler"]
        self.anomaly_detector = data["anomaly"]
        self.accuracy = data["accuracy"]
        self.is_trained = True
        logger.info("model_loaded", path=path, accuracy=self.accuracy)

    def get_feature_importance(self) -> Dict[str, float]:
        """Return feature importance scores."""
        if not self.is_trained:
            return {}
        importances = self.classifier.feature_importances_
        return {
            name: round(float(imp), 4)
            for name, imp in sorted(
                zip(FEATURE_NAMES, importances),
                key=lambda x: -x[1],
            )
        }
