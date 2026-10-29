"""
ImmunoGrid — Attack Scenario Generator
Generates realistic labeled attack scenarios for AI model training.

Used in:
1. Initial FL model training (before real data available)
2. Augmenting sparse real attack data
3. Testing the Federated Adversarial Consciousness (FAC)
4. Benchmarking detection accuracy across attack types

Scenarios generated:
- Normal traffic (diurnal patterns, rush hour, maintenance)
- Spoofing attacks (subtle behavioral deviations)
- DDoS floods (high message rate, CPU spike)
- Data poisoning (entropy anomalies)
- Replay attacks (stale timestamps, repeated sequences)
- MITM attacks (timing delays, entropy drops)
- Ransomware (command injection patterns)
"""

import random
from dataclasses import dataclass
from datetime import datetime, timedelta
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

FEATURE_NAMES = [
    "send_interval_s",
    "packet_size_bytes",
    "cpu_usage_pct",
    "message_rate_per_min",
    "hour_of_day",
    "bytes_per_second",
    "error_rate",
    "entropy",
    "inter_arrival_jitter_ms",
    "subnet_class",
    "day_of_week",
    "is_active_hours",
]

DEVICE_PROFILES = {
    "traffic_sensor":   {"interval": 2.3, "size": 48,  "active": (6, 22)},
    "hospital_device":  {"interval": 3.0, "size": 72,  "active": (0, 23)},
    "water_monitor":    {"interval": 5.0, "size": 52,  "active": (0, 23)},
    "power_sensor":     {"interval": 1.0, "size": 56,  "active": (0, 23)},
    "street_camera":    {"interval": 1.5, "size": 96,  "active": (0, 23)},
    "metro_sensor":     {"interval": 3.0, "size": 60,  "active": (5, 23)},
    "airport_device":   {"interval": 4.0, "size": 80,  "active": (0, 23)},
    "govt_office_node": {"interval": 6.0, "size": 72,  "active": (8, 18)},
}


@dataclass
class Scenario:
    """A single labeled traffic scenario."""
    features:    List[float]
    label:       int
    attack_type: str
    device_type: str
    hour:        int
    description: str


class AttackScenarioGenerator:
    """
    Generates synthetic labeled scenarios for training the FAC AI model.
    """

    def __init__(self, seed: int = 42):
        np.random.seed(seed)
        random.seed(seed)
        self.generated_count = 0

    def _hour_factor(self, hour: int) -> float:
        if 7 <= hour <= 9 or 17 <= hour <= 19: return 1.8
        if 2 <= hour <= 4:  return 0.3
        if 10 <= hour <= 16: return 1.2
        return 1.0

    def generate_normal(self, device_type: str, hour: int) -> Scenario:
        prof   = DEVICE_PROFILES.get(device_type, DEVICE_PROFILES["traffic_sensor"])
        factor = self._hour_factor(hour)
        interval    = max(0.5, np.random.normal(prof["interval"], 0.2) / factor)
        packet_size = max(20, int(np.random.normal(prof["size"], 3)))

        features = [
            round(interval, 4),
            float(packet_size),
            round(np.random.uniform(0.08, 0.25) * 100, 2),
            round(60 / interval, 2),
            float(hour),
            round(packet_size / interval, 2),
            round(np.random.exponential(0.005), 5),
            round(np.random.uniform(0.45, 0.65), 4),
            round(abs(np.random.normal(0, 50)), 2),
            float(np.random.choice([1, 2, 3])),
            float(datetime.utcnow().weekday()),
            1.0 if prof["active"][0] <= hour <= prof["active"][1] else 0.0,
        ]
        self.generated_count += 1
        return Scenario(features, 0, "normal", device_type, hour,
                        f"{device_type} normal traffic at hour {hour}")

    def generate_spoofing(self, device_type: str, hour: int) -> Scenario:
        """Spoofing: copies timing but wrong subnet, slightly off packet size."""
        prof     = DEVICE_PROFILES.get(device_type, DEVICE_PROFILES["traffic_sensor"])
        interval = max(0.5, np.random.normal(prof["interval"], 0.8))  # Larger variance
        size     = max(20, int(np.random.normal(prof["size"] + 12, 8)))  # Wrong size

        features = [
            round(interval, 4),
            float(size),
            round(np.random.uniform(0.0, 0.5) * 100, 2),
            round(60 / interval, 2),
            float(hour),
            round(size / interval, 2),
            round(np.random.uniform(0, 0.1), 5),
            round(np.random.uniform(0.3, 0.8), 4),
            round(abs(np.random.normal(200, 100)), 2),  # High jitter
            99.0,   # Wrong subnet class
            float(datetime.utcnow().weekday()),
            1.0,
        ]
        self.generated_count += 1
        return Scenario(features, 1, "spoofing", device_type, hour,
                        f"Spoofing {device_type}: copied timing, wrong subnet+size")

    def generate_ddos(self, device_type: str, hour: int) -> Scenario:
        """DDoS: very high message rate, maxed CPU, large bytes/sec."""
        interval = round(np.random.uniform(0.01, 0.1), 4)
        size     = max(20, int(np.random.normal(50, 5)))

        features = [
            interval,
            float(size),
            round(np.random.uniform(85, 100), 2),   # Maxed CPU
            round(60 / interval, 2),                 # Very high rate
            float(hour),
            round(size / interval, 2),               # High bytes/sec
            round(np.random.uniform(0.2, 0.5), 5),  # High error rate
            round(np.random.uniform(0.1, 0.4), 4),
            round(abs(np.random.normal(10, 5)), 2),
            float(np.random.choice([1, 2, 3])),
            float(datetime.utcnow().weekday()),
            1.0,
        ]
        self.generated_count += 1
        return Scenario(features, 2, "ddos", device_type, hour,
                        f"DDoS on {device_type}: {round(60/interval)} msgs/min, CPU={features[2]}%")

    def generate_data_poisoning(self, device_type: str, hour: int) -> Scenario:
        """Data poisoning: normal timing but extreme entropy (wrong data content)."""
        prof     = DEVICE_PROFILES.get(device_type, DEVICE_PROFILES["traffic_sensor"])
        interval = max(0.5, np.random.normal(prof["interval"], 0.15))
        size     = max(20, int(np.random.normal(prof["size"], 2)))

        features = [
            round(interval, 4),
            float(size),
            round(np.random.uniform(0.1, 0.2) * 100, 2),
            round(60 / interval, 2),
            float(hour),
            round(size / interval, 2),
            round(np.random.uniform(0.1, 0.4), 5),  # High error rate
            round(np.random.uniform(0.85, 1.0), 4), # High entropy (unusual data)
            round(abs(np.random.normal(0, 60)), 2),
            float(np.random.choice([1, 2, 3])),
            float(datetime.utcnow().weekday()),
            1.0,
        ]
        self.generated_count += 1
        return Scenario(features, 3, "data_poisoning", device_type, hour,
                        f"Data poisoning on {device_type}: entropy={features[7]}")

    def generate_replay(self, device_type: str, hour: int) -> Scenario:
        """Replay: normal timing but off-hours, low entropy, high error rate."""
        prof     = DEVICE_PROFILES.get(device_type, DEVICE_PROFILES["traffic_sensor"])
        interval = max(0.5, np.random.normal(prof["interval"], 0.05))
        size     = max(20, int(np.random.normal(prof["size"], 1)))
        off_hour = random.randint(1, 5)  # Replay at unusual hour

        features = [
            round(interval, 4),
            float(size),
            round(np.random.uniform(0.08, 0.15) * 100, 2),
            round(60 / interval, 2),
            float(off_hour),        # Off-hours timestamp
            round(size / interval, 2),
            round(np.random.uniform(0.4, 0.9), 5),  # Very high error (repeated seq)
            round(np.random.uniform(0.0, 0.15), 4), # Very low entropy
            round(abs(np.random.normal(0, 30)), 2),
            float(np.random.choice([1, 2, 3])),
            float(datetime.utcnow().weekday()),
            0.0,  # Not active hours
        ]
        self.generated_count += 1
        return Scenario(features, 4, "replay_attack", device_type, hour,
                        f"Replay on {device_type}: hour={off_hour}, entropy={features[7]}")

    def generate_mitm(self, device_type: str, hour: int) -> Scenario:
        """MITM: high jitter (interception delay), entropy drop."""
        prof     = DEVICE_PROFILES.get(device_type, DEVICE_PROFILES["traffic_sensor"])
        interval = max(0.5, np.random.normal(prof["interval"] + 0.3, 0.2))  # Slightly slower
        size     = max(20, int(np.random.normal(prof["size"], 5)))

        features = [
            round(interval, 4),
            float(size),
            round(np.random.uniform(0.1, 0.25) * 100, 2),
            round(60 / interval, 2),
            float(hour),
            round(size / interval, 2),
            round(np.random.uniform(0.05, 0.2), 5),
            round(np.random.uniform(0.2, 0.4), 4),  # Low entropy (intercepted)
            round(abs(np.random.normal(500, 200)), 2),  # Very high jitter
            float(np.random.choice([1, 2, 3])),
            float(datetime.utcnow().weekday()),
            1.0,
        ]
        self.generated_count += 1
        return Scenario(features, 5, "mitm", device_type, hour,
                        f"MITM on {device_type}: jitter={features[8]}ms, entropy={features[7]}")

    def generate_ransomware(self, device_type: str, hour: int) -> Scenario:
        """Ransomware: command injection — very fast, large packets, maxed CPU."""
        interval = round(np.random.uniform(0.01, 0.05), 4)
        size     = random.randint(200, 1024)

        features = [
            interval,
            float(size),
            round(np.random.uniform(95, 100), 2),  # Maxed CPU
            round(60 / interval, 2),
            float(hour),
            round(size / interval, 2),             # Very high bytes/sec
            round(np.random.uniform(0.0, 0.05), 5),
            round(np.random.uniform(0.6, 0.9), 4),
            round(abs(np.random.normal(20, 10)), 2),
            99.0,  # Foreign subnet
            float(datetime.utcnow().weekday()),
            1.0,
        ]
        self.generated_count += 1
        return Scenario(features, 6, "ransomware", device_type, hour,
                        f"Ransomware on {device_type}: CPU={features[2]}%, size={size}B")

    def generate_dataset(
        self,
        n_samples:      int   = 5000,
        attack_ratio:   float = 0.25,
        device_types:   Optional[List[str]] = None,
        include_mitm:   bool = True,
        include_ransom: bool = True,
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Generate a complete labeled dataset.

        Returns:
            X: (n_samples, n_features) feature matrix
            y: (n_samples,) label vector
            descriptions: list of scenario descriptions
        """
        if device_types is None:
            device_types = list(DEVICE_PROFILES.keys())

        n_attacks = int(n_samples * attack_ratio)
        n_normal  = n_samples - n_attacks

        generators = [
            self.generate_spoofing,
            self.generate_ddos,
            self.generate_data_poisoning,
            self.generate_replay,
        ]
        if include_mitm:   generators.append(self.generate_mitm)
        if include_ransom: generators.append(self.generate_ransomware)

        scenarios: List[Scenario] = []

        # Normal samples
        for _ in range(n_normal):
            dtype = random.choice(device_types)
            hour  = random.randint(0, 23)
            scenarios.append(self.generate_normal(dtype, hour))

        # Attack samples — balanced
        per_type = n_attacks // len(generators)
        for gen_fn in generators:
            for _ in range(per_type):
                dtype = random.choice(device_types)
                hour  = random.randint(0, 23)
                scenarios.append(gen_fn(dtype, hour))

        # Shuffle
        random.shuffle(scenarios)

        X = np.array([s.features for s in scenarios], dtype=np.float32)
        y = np.array([s.label   for s in scenarios], dtype=np.int64)
        descriptions = [s.description for s in scenarios]

        label_counts = {ATTACK_LABELS[i]: int((y == i).sum()) for i in range(7) if (y == i).sum() > 0}
        logger.info(
            "scenario_dataset_generated",
            total=len(scenarios),
            normal=int((y == 0).sum()),
            attacks=int((y != 0).sum()),
            distribution=label_counts,
        )

        return X, y, descriptions

    def generate_adversarial_imagination(
        self,
        device_id:   str,
        device_type: str,
        attack_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a single adversarial imagination for FAC sharing.
        Used by the Attacker personality to imagine attack scenarios.
        """
        hour = datetime.utcnow().hour

        if attack_type is None:
            attack_type = random.choice(list(ATTACK_LABELS.values())[1:])

        generators = {
            "spoofing":       self.generate_spoofing,
            "ddos":           self.generate_ddos,
            "data_poisoning": self.generate_data_poisoning,
            "replay_attack":  self.generate_replay,
            "mitm":           self.generate_mitm,
            "ransomware":     self.generate_ransomware,
        }

        gen_fn   = generators.get(attack_type, self.generate_spoofing)
        scenario = gen_fn(device_type, hour)

        return {
            "device_id":      device_id,
            "attack_type":    attack_type,
            "feature_vector": scenario.features,
            "confidence":     round(random.uniform(0.65, 0.95), 3),
            "description":    scenario.description,
            "generated_at":   datetime.utcnow().isoformat(),
            "source":         "scenario_generator",
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_generated": self.generated_count,
            "attack_types":    list(ATTACK_LABELS.values()),
            "device_types":    list(DEVICE_PROFILES.keys()),
            "feature_names":   FEATURE_NAMES,
            "n_features":      len(FEATURE_NAMES),
        }
