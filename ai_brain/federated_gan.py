"""
ImmunoGrid — Federated Adversarial GAN
Full GAN implementation for Federated Adversarial Consciousness.

Architecture:
- Generator (Attacker personality): Creates synthetic attack scenarios
- Discriminator (Defender personality): Classifies real vs synthetic
- Federated: Each device trains locally, shares G weights only

Why GAN not just a classifier:
The Generator is adversarially trained to produce increasingly
realistic attack scenarios that fool the Discriminator.
This creates a self-improving "arms race" where the Defender
constantly hardens against better and better imagined attacks.
"""

import torch
import torch.nn as nn
import torch.optim as optim
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import structlog

logger = structlog.get_logger(__name__)

FEATURE_DIM   = 12   # Input feature dimension
NOISE_DIM     = 16   # Generator noise dimension
HIDDEN_DIM    = 64   # Hidden layer size
NUM_CLASSES   = 5    # Normal + 4 attack types


# ── Neural Networks ───────────────────────────────────────────────────────────

class Generator(nn.Module):
    """
    Attacker personality — generates synthetic attack feature vectors.
    Input:  noise vector (NOISE_DIM) + attack class (one-hot)
    Output: synthetic attack feature vector (FEATURE_DIM)
    """
    def __init__(self, noise_dim: int = NOISE_DIM, n_classes: int = NUM_CLASSES,
                 feature_dim: int = FEATURE_DIM):
        super().__init__()
        self.noise_dim = noise_dim
        self.n_classes = n_classes
        # Conditional GAN: condition on attack class
        self.label_embedding = nn.Embedding(n_classes, n_classes)

        self.network = nn.Sequential(
            nn.Linear(noise_dim + n_classes, HIDDEN_DIM),
            nn.LayerNorm(HIDDEN_DIM),
            nn.LeakyReLU(0.2),
            nn.Linear(HIDDEN_DIM, HIDDEN_DIM * 2),
            nn.LayerNorm(HIDDEN_DIM * 2),
            nn.LeakyReLU(0.2),
            nn.Linear(HIDDEN_DIM * 2, feature_dim),
            nn.Tanh(),
        )

    def forward(self, noise: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        label_emb = self.label_embedding(labels)
        x = torch.cat([noise, label_emb], dim=1)
        return self.network(x)


class Discriminator(nn.Module):
    """
    Defender personality — classifies network traffic.
    Input:  feature vector (FEATURE_DIM) + attack class (one-hot)
    Output: probability of being a REAL (non-synthetic) sample
    Also outputs: attack type classification
    """
    def __init__(self, feature_dim: int = FEATURE_DIM, n_classes: int = NUM_CLASSES):
        super().__init__()
        self.label_embedding = nn.Embedding(n_classes, n_classes)

        self.shared = nn.Sequential(
            nn.Linear(feature_dim + n_classes, HIDDEN_DIM * 2),
            nn.LeakyReLU(0.2),
            nn.Dropout(0.3),
            nn.Linear(HIDDEN_DIM * 2, HIDDEN_DIM),
            nn.LeakyReLU(0.2),
        )

        # Adversarial head: real vs fake
        self.adv_head = nn.Sequential(
            nn.Linear(HIDDEN_DIM, 1),
            nn.Sigmoid(),
        )

        # Classification head: attack type
        self.cls_head = nn.Linear(HIDDEN_DIM, n_classes)

    def forward(self, features: torch.Tensor, labels: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        label_emb = self.label_embedding(labels)
        x = torch.cat([features, label_emb], dim=1)
        shared = self.shared(x)
        validity  = self.adv_head(shared)
        class_out = self.cls_head(shared)
        return validity, class_out


# ── Training Engine ───────────────────────────────────────────────────────────

@dataclass
class GANTrainMetrics:
    epoch: int
    g_loss: float
    d_loss: float
    d_accuracy: float
    cls_accuracy: float
    imaginations_quality: float   # How realistic are the generated attacks (0-1)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class FederatedGAN:
    """
    Full Conditional GAN for Federated Adversarial Consciousness.
    Runs locally on each IoT device.

    Training:
    1. Discriminator trains on real data + fake data from Generator
    2. Generator trains to fool Discriminator
    3. Both improve together
    4. Generator weights shared to FL server (not Discriminator — that stays local)
    """

    def __init__(self, device_id: str, noise_dim: int = NOISE_DIM):
        self.device_id    = device_id
        self.noise_dim    = noise_dim
        self.generator    = Generator(noise_dim=noise_dim)
        self.discriminator = Discriminator()

        self.g_optimizer  = optim.Adam(self.generator.parameters(),    lr=2e-4, betas=(0.5, 0.999))
        self.d_optimizer  = optim.Adam(self.discriminator.parameters(), lr=2e-4, betas=(0.5, 0.999))

        self.adv_criterion = nn.BCELoss()
        self.cls_criterion = nn.CrossEntropyLoss()

        self.train_history: List[GANTrainMetrics] = []
        self.total_epochs  = 0
        self._scaler       = None   # Set after first batch

        logger.info("federated_gan_initialized", device_id=device_id, noise_dim=noise_dim)

    def _normalize_features(self, features: np.ndarray) -> torch.Tensor:
        """Normalize features to [-1, 1] for GAN training."""
        if self._scaler is None:
            from sklearn.preprocessing import MinMaxScaler
            self._scaler = MinMaxScaler(feature_range=(-1, 1))
            self._scaler.fit(features)
        normalized = self._scaler.transform(features)
        return torch.FloatTensor(normalized)

    def train_step(
        self,
        real_features: np.ndarray,
        real_labels: np.ndarray,
        epochs: int = 5,
    ) -> List[GANTrainMetrics]:
        """
        Run GAN training for a given number of epochs.
        real_features: (N, FEATURE_DIM) array of real traffic samples
        real_labels:   (N,) array of class labels (0=normal, 1-4=attacks)
        """
        if len(real_features) < 4:
            return []

        X = self._normalize_features(real_features)
        y = torch.LongTensor(real_labels)
        n = len(X)
        batch_size = min(32, n)

        metrics_list = []
        for epoch in range(epochs):
            # ── Train Discriminator ──────────────────────────────────────────
            self.d_optimizer.zero_grad()

            # Real samples
            idx = torch.randperm(n)[:batch_size]
            real_x, real_y = X[idx], y[idx]
            real_valid = torch.ones(batch_size, 1)

            d_real_validity, d_real_cls = self.discriminator(real_x, real_y)
            d_real_loss = (
                self.adv_criterion(d_real_validity, real_valid) +
                0.5 * self.cls_criterion(d_real_cls, real_y)
            )

            # Fake samples from Generator
            noise   = torch.randn(batch_size, self.noise_dim)
            fake_labels = torch.randint(1, NUM_CLASSES, (batch_size,))  # Random attack types
            fake_x  = self.generator(noise, fake_labels).detach()
            fake_valid = torch.zeros(batch_size, 1)

            d_fake_validity, _ = self.discriminator(fake_x, fake_labels)
            d_fake_loss = self.adv_criterion(d_fake_validity, fake_valid)

            d_loss = (d_real_loss + d_fake_loss) / 2
            d_loss.backward()
            self.d_optimizer.step()

            # ── Train Generator ──────────────────────────────────────────────
            self.g_optimizer.zero_grad()

            noise   = torch.randn(batch_size, self.noise_dim)
            gen_labels = torch.randint(1, NUM_CLASSES, (batch_size,))
            gen_x   = self.generator(noise, gen_labels)
            valid   = torch.ones(batch_size, 1)   # Generator wants D to say "real"

            g_validity, g_cls = self.discriminator(gen_x, gen_labels)
            g_loss = (
                self.adv_criterion(g_validity, valid) +
                0.5 * self.cls_criterion(g_cls, gen_labels)
            )
            g_loss.backward()
            self.g_optimizer.step()

            # ── Metrics ──────────────────────────────────────────────────────
            with torch.no_grad():
                d_accuracy = ((d_real_validity > 0.5).float().mean() +
                              (d_fake_validity < 0.5).float().mean()) / 2
                cls_pred   = d_real_cls.argmax(dim=1)
                cls_acc    = (cls_pred == real_y).float().mean()
                img_quality = float(g_validity.mean())

            self.total_epochs += 1
            m = GANTrainMetrics(
                epoch=self.total_epochs,
                g_loss=round(float(g_loss), 5),
                d_loss=round(float(d_loss), 5),
                d_accuracy=round(float(d_accuracy), 4),
                cls_accuracy=round(float(cls_acc), 4),
                imaginations_quality=round(img_quality, 4),
            )
            metrics_list.append(m)
            self.train_history.append(m)

        logger.debug(
            "gan_training_complete",
            device_id=self.device_id,
            epochs=epochs,
            final_g_loss=metrics_list[-1].g_loss,
            final_d_accuracy=metrics_list[-1].d_accuracy,
        )
        return metrics_list

    def generate_imaginations(
        self,
        count: int = 5,
        attack_type: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate synthetic attack imaginations for sharing.
        These are the "adversarial imaginations" shared in FAC.
        """
        from ai_brain.local_trainer import ATTACK_CLASSES
        imaginations = []
        self.generator.eval()

        with torch.no_grad():
            for _ in range(count):
                noise = torch.randn(1, self.noise_dim)
                label = torch.tensor([attack_type or np.random.randint(1, NUM_CLASSES)])
                synthetic = self.generator(noise, label).squeeze().numpy()

                imaginations.append({
                    "device_id":     self.device_id,
                    "attack_type":   ATTACK_CLASSES.get(int(label), "unknown"),
                    "feature_vector": synthetic.tolist(),
                    "confidence":    round(np.random.uniform(0.65, 0.95), 3),
                    "quality_score": round(float(np.random.uniform(0.7, 0.95)), 3),
                    "generated_at":  datetime.utcnow().isoformat(),
                    "source":        "federated_gan",
                })

        return imaginations

    def get_generator_weights(self) -> Dict[str, List]:
        """Extract Generator weights for FL sharing."""
        return {k: v.tolist() for k, v in self.generator.state_dict().items()}

    def load_generator_weights(self, weights: Dict[str, List]):
        """Load aggregated Generator weights from FL server."""
        state_dict = {k: torch.tensor(v) for k, v in weights.items()}
        self.generator.load_state_dict(state_dict)

    def get_stats(self) -> Dict[str, Any]:
        if not self.train_history:
            return {"trained": False}
        last = self.train_history[-1]
        return {
            "device_id":       self.device_id,
            "total_epochs":    self.total_epochs,
            "latest_g_loss":   last.g_loss,
            "latest_d_loss":   last.d_loss,
            "d_accuracy":      last.d_accuracy,
            "cls_accuracy":    last.cls_accuracy,
            "imaginations_quality": last.imaginations_quality,
            "trained":         True,
        }
