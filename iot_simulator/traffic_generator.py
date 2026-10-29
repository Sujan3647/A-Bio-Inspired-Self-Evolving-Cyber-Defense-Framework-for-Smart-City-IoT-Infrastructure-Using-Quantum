"""
ImmunoGrid — Realistic Network Traffic Generator
Generates synthetic network traffic data that mimics real smart city
IoT communication patterns. Used for AI model training datasets.

Patterns generated:
- Normal diurnal traffic (day/night cycles)
- Rush hour peaks (07:00-09:00, 17:00-19:00)
- Maintenance windows (02:00-04:00 — low traffic)
- Random anomalies (1-3% of traffic)
- Attack-injected traffic (labeled for supervised learning)

Output: pandas DataFrame with features + labels for ML training
"""

import random
from datetime import datetime, timedelta
from typing import Optional, Tuple

import numpy as np
import pandas as pd
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

FEATURE_COLUMNS = [
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


class TrafficGenerator:
    """
    Generates realistic labeled network traffic for ML training.
    Simulates a 24-hour period of smart city IoT communication.
    """

    def __init__(self, seed: int = 42):
        np.random.seed(seed)
        random.seed(seed)

    def _hour_factor(self, hour: int) -> float:
        """Traffic intensity factor based on hour of day."""
        if 7 <= hour <= 9 or 17 <= hour <= 19:
            return 1.8    # Rush hour
        if 2 <= hour <= 4:
            return 0.3    # Maintenance window
        if 10 <= hour <= 16:
            return 1.2    # Business hours
        if 22 <= hour or hour <= 1:
            return 0.5    # Night
        return 1.0

    def generate_normal_sample(self, hour: int, device_type: str = "traffic_sensor") -> dict:
        """Generate a single normal traffic sample."""
        factor = self._hour_factor(hour)
        base_interval = {"traffic_sensor": 2.3, "hospital_device": 3.0,
                         "water_monitor": 5.0, "power_sensor": 1.0}.get(device_type, 2.5)

        send_interval = max(0.5, np.random.normal(base_interval, 0.2) / factor)
        packet_size   = int(np.random.normal(48, 3))
        cpu_usage     = np.random.uniform(0.08, 0.25)

        return {
            "send_interval_s":        round(send_interval, 4),
            "packet_size_bytes":      max(20, packet_size),
            "cpu_usage_pct":          round(cpu_usage * 100, 2),
            "message_rate_per_min":   round(60 / send_interval, 2),
            "hour_of_day":            hour,
            "bytes_per_second":       round(packet_size / send_interval, 2),
            "error_rate":             round(np.random.exponential(0.005), 4),
            "entropy":                round(np.random.uniform(0.45, 0.65), 4),
            "inter_arrival_jitter_ms": round(abs(np.random.normal(0, 50)), 2),
            "subnet_class":           random.choice([1, 2, 3]),  # 192.168.x.x classes
            "day_of_week":            datetime.utcnow().weekday(),
            "is_active_hours":        1 if 6 <= hour <= 22 else 0,
            "label":                  0,
            "attack_type":            "normal",
            "device_type":            device_type,
        }

    def generate_attack_sample(self, attack_type: int, hour: int) -> dict:
        """Generate a labeled attack traffic sample."""
        sample = self.generate_normal_sample(hour)

        if attack_type == 1:   # Spoofing
            sample["send_interval_s"]        = round(np.random.normal(2.0, 0.8), 4)
            sample["packet_size_bytes"]       = int(np.random.normal(58, 10))
            sample["subnet_class"]            = 99   # Wrong subnet
            sample["inter_arrival_jitter_ms"] = round(abs(np.random.normal(200, 100)), 2)

        elif attack_type == 2:  # DDoS
            sample["send_interval_s"]    = round(np.random.uniform(0.01, 0.1), 4)
            sample["cpu_usage_pct"]      = round(np.random.uniform(85, 100), 2)
            sample["message_rate_per_min"] = round(np.random.uniform(600, 6000), 2)
            sample["bytes_per_second"]   = round(np.random.uniform(500, 10000), 2)
            sample["error_rate"]         = round(np.random.uniform(0.3, 0.8), 4)

        elif attack_type == 3:  # Data Poisoning
            sample["entropy"]            = round(np.random.uniform(0.85, 1.0), 4)
            sample["error_rate"]         = round(np.random.uniform(0.1, 0.4), 4)
            # Timing looks normal but data is wrong (entropy spike)

        elif attack_type == 4:  # Replay
            sample["send_interval_s"]    = round(np.random.normal(2.3, 0.05), 4)
            sample["entropy"]            = round(np.random.uniform(0.0, 0.15), 4)  # Low entropy
            sample["error_rate"]         = round(np.random.uniform(0.4, 0.9), 4)   # High error
            sample["hour_of_day"]        = random.randint(1, 5)   # Off-hours replay
            sample["is_active_hours"]    = 0

        elif attack_type == 5:  # MITM
            sample["inter_arrival_jitter_ms"] = round(abs(np.random.normal(500, 200)), 2)
            sample["entropy"]            = round(np.random.uniform(0.2, 0.4), 4)
            sample["error_rate"]         = round(np.random.uniform(0.05, 0.2), 4)

        elif attack_type == 6:  # Ransomware
            sample["send_interval_s"]    = round(np.random.uniform(0.01, 0.05), 4)
            sample["packet_size_bytes"]  = random.randint(200, 1024)
            sample["cpu_usage_pct"]      = round(np.random.uniform(95, 100), 2)
            sample["bytes_per_second"]   = round(np.random.uniform(2000, 50000), 2)
            sample["subnet_class"]       = 99

        sample["label"]       = attack_type
        sample["attack_type"] = ATTACK_LABELS[attack_type]
        return sample

    def generate_dataset(
        self,
        n_samples: int = 5000,
        attack_ratio: float = 0.25,
        device_types: Optional[list] = None,
    ) -> pd.DataFrame:
        """
        Generate a complete labeled training dataset.

        Args:
            n_samples: Total number of samples
            attack_ratio: Fraction of samples that are attacks (0.0-1.0)
            device_types: List of device types to include

        Returns:
            pd.DataFrame with features, label, and attack_type columns
        """
        if device_types is None:
            device_types = ["traffic_sensor", "hospital_device", "water_monitor",
                           "power_sensor", "metro_sensor"]

        n_attacks = int(n_samples * attack_ratio)
        n_normal  = n_samples - n_attacks

        samples = []

        # Normal samples
        for _ in range(n_normal):
            hour   = random.randint(0, 23)
            dtype  = random.choice(device_types)
            sample = self.generate_normal_sample(hour, dtype)
            samples.append(sample)

        # Attack samples — balanced across 6 attack types
        attacks_per_type = n_attacks // 6
        for attack_type in range(1, 7):
            for _ in range(attacks_per_type):
                hour   = random.randint(0, 23)
                sample = self.generate_attack_sample(attack_type, hour)
                samples.append(sample)

        # Shuffle
        random.shuffle(samples)

        df = pd.DataFrame(samples)
        logger.info(
            "dataset_generated",
            total=len(df),
            normal=len(df[df['label'] == 0]),
            attacks=len(df[df['label'] != 0]),
            attack_types=df['attack_type'].value_counts().to_dict(),
        )
        return df

    def get_feature_columns(self) -> list:
        return FEATURE_COLUMNS

    def save_dataset(self, df: pd.DataFrame, path: str = "immunogrid_dataset.csv"):
        """Save dataset to CSV for ML training."""
        df.to_csv(path, index=False)
        logger.info("dataset_saved", path=path, rows=len(df))

    def generate_streaming_sample(self, device_type: str = "traffic_sensor") -> dict:
        """Generate a single sample for real-time streaming simulation."""
        hour = datetime.utcnow().hour
        is_attack = random.random() < 0.05   # 5% attack rate
        if is_attack:
            attack_type = random.randint(1, 6)
            return self.generate_attack_sample(attack_type, hour)
        return self.generate_normal_sample(hour, device_type)


if __name__ == "__main__":
    gen = TrafficGenerator(seed=42)
    df = gen.generate_dataset(n_samples=10000, attack_ratio=0.20)
    print(f"\nDataset shape: {df.shape}")
    print(f"\nLabel distribution:\n{df['attack_type'].value_counts()}")
    print(f"\nFeature columns: {gen.get_feature_columns()}")
    gen.save_dataset(df, "immunogrid_training_dataset.csv")
    print("\n✅ Dataset saved to immunogrid_training_dataset.csv")
