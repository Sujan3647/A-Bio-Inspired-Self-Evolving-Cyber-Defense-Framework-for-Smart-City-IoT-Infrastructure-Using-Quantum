"""
ImmunoGrid — Byzantine Fault Defense for Federated Learning
Detects and mitigates Byzantine gradient poisoning attacks
where malicious devices submit corrupted model updates.

Methods:
1. FedMedian    — robust aggregation using coordinate-wise median
2. Krum         — select most consistent client update
3. Trimmed Mean — discard top/bottom fraction of gradient values
4. Norm Clipping — clip gradient norms to bound attacker influence
5. FLAME        — clustering-based Byzantine detection

Used together with the PBFT consensus to ensure only
honest gradient updates reach the global model.
"""

import numpy as np
from typing import Any, Dict, List, Optional, Tuple
import structlog

logger = structlog.get_logger(__name__)


class ByzantineDefenseEngine:
    """
    Robust aggregation methods for Byzantine fault-tolerant
    Federated Learning in ImmunoGrid.

    Protects the Federated Adversarial Consciousness (FAC)
    from adversarial gradient injection attacks.
    """

    def __init__(self, n_clients: int, n_byzantine: int = 1):
        self.n_clients   = n_clients
        self.n_byzantine = n_byzantine    # Max Byzantine clients assumed
        self.aggregations_performed = 0
        self.byzantine_detected = 0

    # ── Robust Aggregation Methods ────────────────────────────────────────────

    def fedmedian(self, gradients: List[np.ndarray]) -> np.ndarray:
        """
        FedMedian: coordinate-wise median aggregation.
        Tolerates up to (n-1)/2 Byzantine clients.
        More robust than FedAvg but slower convergence.
        """
        stacked = np.stack(gradients, axis=0)   # (n_clients, param_dim)
        result  = np.median(stacked, axis=0)
        self.aggregations_performed += 1
        logger.debug("fedmedian_applied", n_clients=len(gradients))
        return result

    def trimmed_mean(
        self,
        gradients: List[np.ndarray],
        trim_fraction: float = 0.1,
    ) -> np.ndarray:
        """
        Trimmed Mean: remove top and bottom trim_fraction of values
        before averaging. Reduces influence of extreme outlier gradients.
        """
        n      = len(gradients)
        trim_k = max(1, int(n * trim_fraction))
        stacked = np.stack(gradients, axis=0)

        # Sort along client axis, trim both ends
        sorted_grads = np.sort(stacked, axis=0)
        trimmed = sorted_grads[trim_k : n - trim_k]
        result  = np.mean(trimmed, axis=0)

        self.aggregations_performed += 1
        logger.debug("trimmed_mean_applied",
                     n_clients=n, trimmed=2*trim_k, remaining=len(trimmed))
        return result

    def krum(
        self,
        gradients: List[np.ndarray],
        n_to_select: int = 1,
    ) -> np.ndarray:
        """
        Krum: select the gradient update closest to its (n - f - 2) neighbors.
        Tolerates up to f = n_byzantine Byzantine clients.

        Returns the average of the n_to_select most Krum-consistent updates.
        """
        n = len(gradients)
        f = self.n_byzantine
        neighbors_to_use = n - f - 2

        if neighbors_to_use <= 0:
            logger.warning("krum_fallback_to_median",
                           reason=f"n={n} too small for f={f}")
            return self.fedmedian(gradients)

        # Compute pairwise L2 distances
        distances = np.zeros((n, n))
        for i in range(n):
            for j in range(i+1, n):
                d = np.linalg.norm(gradients[i] - gradients[j])**2
                distances[i, j] = distances[j, i] = d

        # Krum score: sum of distances to nearest neighbors_to_use neighbors
        scores = []
        for i in range(n):
            sorted_dists = np.sort(distances[i])
            score = sorted_dists[1 : neighbors_to_use + 1].sum()
            scores.append(score)

        # Select n_to_select updates with lowest score
        selected_idx = np.argsort(scores)[:n_to_select]
        result = np.mean([gradients[i] for i in selected_idx], axis=0)

        self.aggregations_performed += 1
        logger.debug("krum_applied", selected=selected_idx.tolist(),
                     n_clients=n, n_select=n_to_select)
        return result

    def norm_clipping(
        self,
        gradients: List[np.ndarray],
        clip_threshold: float = 2.0,
    ) -> np.ndarray:
        """
        Norm Clipping: clip each gradient to bounded L2 norm,
        then average. Limits how much any single client can deviate.
        """
        clipped = []
        for g in gradients:
            norm = np.linalg.norm(g)
            if norm > clip_threshold:
                g = g * (clip_threshold / norm)
                self.byzantine_detected += 1
            clipped.append(g)

        result = np.mean(clipped, axis=0)
        self.aggregations_performed += 1
        return result

    def flame(
        self,
        gradients: List[np.ndarray],
        noise_sigma: float = 0.001,
    ) -> np.ndarray:
        """
        FLAME (Filtering + Aggregation for Malicious Elimination):
        Simplified version — cluster gradients, keep majority cluster,
        then apply norm clipping + noise to the retained updates.

        Full FLAME uses HDBSCAN clustering. We use a simplified
        cosine similarity threshold approach.
        """
        n = len(gradients)
        if n < 3:
            return np.mean(gradients, axis=0)

        # Normalize to unit vectors for cosine similarity
        norms = [np.linalg.norm(g) for g in gradients]
        normed = [g / (norm + 1e-9) for g, norm in zip(gradients, norms)]

        # Compute cosine similarity matrix
        sim_matrix = np.array([[np.dot(normed[i], normed[j])
                                for j in range(n)] for i in range(n)])

        # Keep gradients with average similarity above threshold
        avg_sim = sim_matrix.mean(axis=1)
        threshold = np.median(avg_sim) * 0.8
        retained_idx = [i for i, s in enumerate(avg_sim) if s >= threshold]

        if not retained_idx:
            retained_idx = list(range(n))

        retained = [gradients[i] for i in retained_idx]
        excluded = n - len(retained)

        if excluded > 0:
            self.byzantine_detected += excluded
            logger.warning("flame_excluded_clients",
                           excluded=excluded, retained=len(retained))

        # Apply norm clipping to retained
        clip_threshold = np.median([np.linalg.norm(g) for g in retained]) * 1.5
        clipped = []
        for g in retained:
            norm = np.linalg.norm(g)
            if norm > clip_threshold:
                g = g * (clip_threshold / norm)
            clipped.append(g)

        result = np.mean(clipped, axis=0)

        # Add small noise for differential privacy
        noise  = np.random.normal(0, noise_sigma, size=result.shape)
        result = result + noise

        self.aggregations_performed += 1
        return result

    def aggregate_robust(
        self,
        gradients:  List[np.ndarray],
        method:     str = "fedmedian",
        weights:    Optional[List[float]] = None,
    ) -> Tuple[np.ndarray, str]:
        """
        Main entry point: apply selected robust aggregation method.

        Args:
            gradients: List of gradient arrays from FL clients
            method:    "fedmedian" | "trimmed_mean" | "krum" |
                       "norm_clipping" | "flame" | "fedavg"
            weights:   Optional sample counts for weighted FedAvg

        Returns:
            (aggregated_gradient, method_used)
        """
        if not gradients:
            raise ValueError("No gradients to aggregate")

        methods = {
            "fedmedian":    lambda: self.fedmedian(gradients),
            "trimmed_mean": lambda: self.trimmed_mean(gradients),
            "krum":         lambda: self.krum(gradients),
            "norm_clipping":lambda: self.norm_clipping(gradients),
            "flame":        lambda: self.flame(gradients),
            "fedavg":       lambda: (
                np.average(gradients, axis=0, weights=weights)
                if weights else np.mean(gradients, axis=0)
            ),
        }

        if method not in methods:
            logger.warning("unknown_method_fallback",
                           method=method, using="fedmedian")
            method = "fedmedian"

        result = methods[method]()
        logger.info("robust_aggregation_complete",
                    method=method, n_clients=len(gradients),
                    byzantine_detected=self.byzantine_detected)
        return result, method

    # ── Attack Detection ─────────────────────────────────────────────────────

    def detect_gradient_poisoning(
        self,
        gradients:  List[np.ndarray],
        threshold:  float = 3.0,
    ) -> List[int]:
        """
        Detect likely Byzantine gradient poisoning via statistical outlier detection.
        Returns list of client indices flagged as potentially Byzantine.

        Method: flag clients whose gradient norm deviates > threshold × IQR
        from the median norm.
        """
        norms = np.array([np.linalg.norm(g) for g in gradients])
        q1, q3 = np.percentile(norms, [25, 75])
        iqr    = q3 - q1
        lower  = q1 - threshold * iqr
        upper  = q3 + threshold * iqr

        suspects = [i for i, n in enumerate(norms)
                    if n < lower or n > upper]

        if suspects:
            self.byzantine_detected += len(suspects)
            logger.warning("gradient_poisoning_suspected",
                           suspects=suspects,
                           norms=norms[suspects].tolist(),
                           median_norm=float(np.median(norms)),
                           threshold_range=[float(lower), float(upper)])

        return suspects

    def get_stats(self) -> Dict[str, Any]:
        return {
            "n_clients":              self.n_clients,
            "max_byzantine_assumed":  self.n_byzantine,
            "aggregations_performed": self.aggregations_performed,
            "byzantine_detected":     self.byzantine_detected,
        }
