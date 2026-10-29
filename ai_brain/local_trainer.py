"""
ImmunoGrid — Federated Adversarial Consciousness (FAC)
Local Device AI Trainer

Each IoT device runs this locally.
It has TWO personalities:
1. Defender AI  → learns to detect attacks
2. Attacker AI  → imagines how it might be attacked

The attacker imaginations are shared across all devices
(not raw data — just the threat ideas).
"""

import json
import random
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import structlog
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.preprocessing import StandardScaler

logger = structlog.get_logger(__name__)


# ─── Neural Network Architectures ─────────────────────────────────────────────

class DefenderNet(nn.Module):
    """
    The Defender personality.
    A lightweight neural network that classifies network traffic
    as NORMAL or one of the attack types.
    
    Designed to run on resource-constrained IoT edge devices.
    """

    def __init__(self, input_dim: int = 12, num_classes: int = 5):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, num_classes),
        )
        self.num_classes = num_classes

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x)


class AttackerNet(nn.Module):
    """
    The Attacker personality (Generator in GAN terms).
    Generates synthetic attack scenarios — "imagines" attacks.
    These imagined attacks are shared with other devices
    to train everyone's Defender.
    """

    def __init__(self, noise_dim: int = 8, output_dim: int = 12):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(noise_dim, 16),
            nn.LeakyReLU(0.2),
            nn.Linear(16, 32),
            nn.LeakyReLU(0.2),
            nn.Linear(32, output_dim),
            nn.Tanh(),
        )

    def forward(self, noise: torch.Tensor) -> torch.Tensor:
        return self.network(noise)


# ─── Attack Classes ────────────────────────────────────────────────────────────

ATTACK_CLASSES = {
    0: "normal",
    1: "spoofing",
    2: "ddos",
    3: "data_poisoning",
    4: "replay_attack",
}

FEATURE_NAMES = [
    "send_interval", "packet_size", "timing_jitter", "size_variance",
    "cpu_usage", "message_rate", "subnet_score", "hour_of_day",
    "bytes_per_second", "unique_topics", "error_rate", "entropy",
]


# ─── Local Device Trainer ─────────────────────────────────────────────────────

@dataclass
class AdversarialImagination:
    """
    An imagined attack scenario from the Attacker personality.
    These are shared across devices in federated learning rounds.
    """
    device_id: str
    attack_type: str
    feature_vector: List[float]
    confidence: float
    generated_at: str
    description: str


class LocalDeviceTrainer:
    """
    The AI brain of a single IoT device.
    
    Implements Federated Adversarial Consciousness:
    1. Defender trains on local normal traffic + received attack imaginations
    2. Attacker generates new attack imaginations
    3. Imaginations are shared with the FL aggregator
    4. No raw sensor data ever leaves the device
    """

    def __init__(self, device_id: str, device_type: str):
        self.device_id = device_id
        self.device_type = device_type

        # Two personalities
        self.defender = DefenderNet(input_dim=len(FEATURE_NAMES), num_classes=5)
        self.attacker = AttackerNet(noise_dim=8, output_dim=len(FEATURE_NAMES))

        self.defender_optimizer = optim.Adam(self.defender.parameters(), lr=0.001)
        self.attacker_optimizer = optim.Adam(self.attacker.parameters(), lr=0.001)

        self.scaler = StandardScaler()
        self.training_rounds = 0
        self.local_data_buffer: List[Dict] = []
        self.imaginations: List[AdversarialImagination] = []

        logger.info(
            "local_trainer_initialized",
            device_id=device_id,
            device_type=device_type,
        )

    def extract_features(self, message: Dict[str, Any]) -> np.ndarray:
        """
        Extract a feature vector from a device message.
        These features are what the Defender learns from.
        """
        behavior = message.get("behavior", {})
        hour = datetime.utcnow().hour

        features = [
            behavior.get("send_interval", 2.0),
            behavior.get("packet_size", 48.0),
            behavior.get("timing_jitter", 1.0),   # Estimated
            behavior.get("size_variance", 2.0),    # Estimated
            behavior.get("cpu_usage", 0.15),
            1.0 / max(behavior.get("send_interval", 1.0), 0.1),  # message rate
            float(sum(ord(c) for c in behavior.get("subnet", "0")) % 100) / 100,
            hour / 23.0,  # normalized hour
            behavior.get("packet_size", 48.0) / max(behavior.get("send_interval", 1.0), 0.1),
            1.0,   # unique topics (simplified)
            0.0,   # error rate
            0.5,   # entropy (simplified)
        ]

        return np.array(features, dtype=np.float32)

    def add_to_buffer(self, message: Dict[str, Any], label: int = 0):
        """Add a message to the local training buffer."""
        features = self.extract_features(message)
        self.local_data_buffer.append({
            "features": features.tolist(),
            "label": label,
        })

        # Keep buffer manageable
        if len(self.local_data_buffer) > 500:
            self.local_data_buffer = self.local_data_buffer[-500:]

    def train_defender(self, epochs: int = 5) -> Dict[str, float]:
        """
        Train the Defender on local data + received attack imaginations.
        Returns training metrics.
        """
        if len(self.local_data_buffer) < 10:
            return {"loss": 0.0, "accuracy": 0.0, "samples": 0}

        # Prepare training data
        X = np.array([d["features"] for d in self.local_data_buffer])
        y = np.array([d["label"] for d in self.local_data_buffer])

        # Normalize
        X = self.scaler.fit_transform(X)

        X_tensor = torch.FloatTensor(X)
        y_tensor = torch.LongTensor(y)

        criterion = nn.CrossEntropyLoss()
        total_loss = 0.0
        correct = 0

        self.defender.train()
        for epoch in range(epochs):
            self.defender_optimizer.zero_grad()
            outputs = self.defender(X_tensor)
            loss = criterion(outputs, y_tensor)
            loss.backward()
            self.defender_optimizer.step()
            total_loss += loss.item()

            # Calculate accuracy
            _, predicted = torch.max(outputs, 1)
            correct = (predicted == y_tensor).sum().item()

        accuracy = correct / len(y)
        avg_loss = total_loss / epochs

        self.training_rounds += 1

        logger.debug(
            "defender_trained",
            device_id=self.device_id,
            loss=round(avg_loss, 4),
            accuracy=round(accuracy, 4),
            samples=len(X),
        )

        return {
            "loss": round(avg_loss, 4),
            "accuracy": round(accuracy, 4),
            "samples": len(X),
            "rounds": self.training_rounds,
        }

    def generate_attack_imaginations(self, count: int = 3) -> List[AdversarialImagination]:
        """
        The Attacker personality generates imagined attack scenarios.
        
        These are NOT real attacks — they are synthetic samples
        that represent how the device COULD be attacked.
        
        Shared with other devices in federated learning rounds.
        """
        imaginations = []
        attack_types = list(ATTACK_CLASSES.values())[1:]  # Exclude 'normal'

        self.attacker.eval()
        with torch.no_grad():
            for i in range(count):
                # Generate random noise
                noise = torch.randn(1, 8)

                # Attacker generates a synthetic attack feature vector
                synthetic_features = self.attacker(noise).squeeze().numpy()

                # Pick a random attack type for this imagination
                attack_type = random.choice(attack_types)

                # Generate a human-readable description
                description = self._describe_attack(attack_type, synthetic_features)

                imagination = AdversarialImagination(
                    device_id=self.device_id,
                    attack_type=attack_type,
                    feature_vector=synthetic_features.tolist(),
                    confidence=round(random.uniform(0.6, 0.95), 3),
                    generated_at=datetime.utcnow().isoformat(),
                    description=description,
                )
                imaginations.append(imagination)

        self.imaginations.extend(imaginations)

        logger.debug(
            "imaginations_generated",
            device_id=self.device_id,
            count=len(imaginations),
        )

        return imaginations

    def receive_imaginations(self, imaginations: List[AdversarialImagination]):
        """
        Receive attack imaginations from other devices.
        Add them to the local training buffer as labeled attack samples.
        """
        for imagination in imaginations:
            if imagination.device_id == self.device_id:
                continue  # Skip our own imaginations

            # Get the label for this attack type
            label = next(
                (k for k, v in ATTACK_CLASSES.items() if v == imagination.attack_type),
                0,
            )

            # Add to training buffer as a synthetic attack sample
            self.local_data_buffer.append({
                "features": imagination.feature_vector,
                "label": label,
            })

        logger.debug(
            "imaginations_received",
            device_id=self.device_id,
            received_count=len(imaginations),
        )

    def classify_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify an incoming message as normal or an attack type.
        Returns the classification with confidence scores.
        """
        features = self.extract_features(message)

        try:
            features_scaled = self.scaler.transform(features.reshape(1, -1))
        except Exception:
            features_scaled = features.reshape(1, -1)

        self.defender.eval()
        with torch.no_grad():
            x_tensor = torch.FloatTensor(features_scaled)
            logits = self.defender(x_tensor)
            probs = torch.softmax(logits, dim=1).squeeze().numpy()

        predicted_class = int(np.argmax(probs))
        confidence = float(np.max(probs))

        return {
            "device_id": message.get("device_id", "unknown"),
            "predicted_class": predicted_class,
            "predicted_label": ATTACK_CLASSES[predicted_class],
            "confidence": round(confidence, 4),
            "is_attack": predicted_class != 0,
            "probabilities": {
                ATTACK_CLASSES[i]: round(float(p), 4)
                for i, p in enumerate(probs)
            },
        }

    def get_model_weights(self) -> Dict[str, Any]:
        """Extract model weights for federated aggregation."""
        return {
            "defender": {k: v.tolist() for k, v in self.defender.state_dict().items()},
            "attacker": {k: v.tolist() for k, v in self.attacker.state_dict().items()},
        }

    def load_global_weights(self, global_weights: Dict[str, Any]):
        """Load aggregated global model weights from the FL server."""
        if "defender" in global_weights:
            state_dict = {
                k: torch.tensor(v)
                for k, v in global_weights["defender"].items()
            }
            self.defender.load_state_dict(state_dict)

        logger.debug("global_weights_loaded", device_id=self.device_id)

    def _describe_attack(self, attack_type: str, features: np.ndarray) -> str:
        descriptions = {
            "spoofing": f"Device {self.device_id} imagines: Attacker might clone identity with send_interval≈{abs(features[0]):.2f}s",
            "ddos": f"Device {self.device_id} imagines: Flood attack with {1/max(abs(features[0]),0.1):.0f} msgs/sec",
            "data_poisoning": f"Device {self.device_id} imagines: Data injection with unusual packet_size≈{abs(features[1])*100:.0f}bytes",
            "replay_attack": f"Device {self.device_id} imagines: Replay of captured packets with entropy≈{abs(features[-1]):.2f}",
        }
        return descriptions.get(attack_type, f"Unknown attack imagination from {self.device_id}")
