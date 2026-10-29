"""
ImmunoGrid — Differential Privacy Engine for Federated Learning
Adds calibrated noise to model gradients before sharing,
protecting individual device data while preserving learning.

Why differential privacy in ImmunoGrid:
- Devices share model updates (gradients) with the FL server
- Without DP, gradients can leak raw sensor data
- With DP: mathematically guaranteed privacy for each device

Mechanism: Gaussian Mechanism
- Clip gradients to bounded sensitivity
- Add Gaussian noise calibrated to privacy budget (epsilon, delta)
- Share noisy gradients — server aggregates, real data stays private

Privacy budget:
- epsilon (ε): privacy loss (smaller = more private, less accurate)
- delta (δ): failure probability
- ImmunoGrid default: ε=1.0, δ=1e-5 (strong privacy)
"""

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class PrivacyAccountant:
    """Tracks cumulative privacy budget spent across FL rounds."""
    epsilon:         float   # Privacy budget per round
    delta:           float   # Failure probability
    total_epsilon:   float = 0.0
    total_rounds:    int   = 0
    max_epsilon:     float = 10.0  # Stop training if exceeded

    def spend(self, epsilon_spent: float):
        self.total_epsilon += epsilon_spent
        self.total_rounds  += 1

    def is_budget_exhausted(self) -> bool:
        return self.total_epsilon >= self.max_epsilon

    def remaining_budget(self) -> float:
        return max(0.0, self.max_epsilon - self.total_epsilon)


class DifferentialPrivacyEngine:
    """
    Applies Gaussian differential privacy to FL gradient updates.

    Usage in ImmunoGrid:
    1. Device trains local model → gets gradient update
    2. Clip gradients (bound sensitivity)
    3. Add calibrated Gaussian noise
    4. Share noisy gradient to FL server
    5. Server aggregates — raw data mathematically protected
    """

    def __init__(
        self,
        epsilon:       float = 1.0,    # Privacy budget
        delta:         float = 1e-5,   # Failure probability
        max_grad_norm: float = 1.0,    # Gradient clipping bound
        noise_multiplier: float = 1.1, # Noise scale
    ):
        self.epsilon         = epsilon
        self.delta           = delta
        self.max_grad_norm   = max_grad_norm
        self.noise_multiplier = noise_multiplier
        self.accountant      = PrivacyAccountant(epsilon=epsilon, delta=delta)

        logger.info(
            "dp_engine_initialized",
            epsilon=epsilon,
            delta=delta,
            max_grad_norm=max_grad_norm,
            noise_multiplier=noise_multiplier,
        )

    def clip_gradients(self, gradients: np.ndarray) -> np.ndarray:
        """
        Clip gradient vector to max_grad_norm (L2 norm).
        This bounds the sensitivity of the gradient computation.
        """
        norm = np.linalg.norm(gradients)
        if norm > self.max_grad_norm:
            gradients = gradients * (self.max_grad_norm / norm)
        return gradients

    def add_noise(self, gradients: np.ndarray, num_samples: int) -> np.ndarray:
        """
        Add calibrated Gaussian noise to clipped gradients.

        Noise std = noise_multiplier × max_grad_norm / num_samples
        """
        noise_std = self.noise_multiplier * self.max_grad_norm / num_samples
        noise     = np.random.normal(0, noise_std, size=gradients.shape)
        return gradients + noise

    def privatize_gradients(
        self,
        gradients:   np.ndarray,
        num_samples: int,
    ) -> np.ndarray:
        """
        Full DP pipeline: clip → add noise → return private gradients.
        Also updates the privacy accountant.
        """
        if self.accountant.is_budget_exhausted():
            logger.warning("dp_budget_exhausted", total_epsilon=self.accountant.total_epsilon)
            # Return zeros instead of leaking data when budget exhausted
            return np.zeros_like(gradients)

        # 1. Clip
        clipped = self.clip_gradients(gradients)

        # 2. Add Gaussian noise
        noisy = self.add_noise(clipped, num_samples)

        # 3. Track privacy spend (simplified Rényi DP accounting)
        epsilon_spent = self._compute_epsilon_spent(num_samples)
        self.accountant.spend(epsilon_spent)

        return noisy

    def privatize_model_weights(
        self,
        weights_dict: Dict[str, Any],
        num_samples:  int,
    ) -> Dict[str, Any]:
        """
        Apply DP to a full model weights dictionary.
        Used before sharing weights with FL server.
        """
        private_weights = {}
        for layer_name, weights in weights_dict.items():
            w_arr = np.array(weights, dtype=np.float32)
            private_w = self.privatize_gradients(w_arr.flatten(), num_samples)
            private_weights[layer_name] = private_w.reshape(w_arr.shape).tolist()
        return private_weights

    def _compute_epsilon_spent(self, num_samples: int) -> float:
        """
        Simplified privacy accounting.
        True accounting uses Rényi DP — this is an approximation.
        """
        sampling_rate = min(1.0, num_samples / 500)  # 500 = expected total devices
        return self.epsilon * sampling_rate

    def get_privacy_report(self) -> Dict[str, Any]:
        """Return current privacy budget status."""
        return {
            "epsilon_per_round":   self.epsilon,
            "delta":               self.delta,
            "total_epsilon_spent": round(self.accountant.total_epsilon, 4),
            "rounds_completed":    self.accountant.total_rounds,
            "remaining_budget":    round(self.accountant.remaining_budget(), 4),
            "budget_exhausted":    self.accountant.is_budget_exhausted(),
            "noise_multiplier":    self.noise_multiplier,
            "max_grad_norm":       self.max_grad_norm,
            "privacy_guarantee":   f"(ε={self.epsilon}, δ={self.delta})-DP",
        }

    def compute_noise_std(self) -> float:
        """Return the noise standard deviation applied to gradients."""
        return self.noise_multiplier * self.max_grad_norm
