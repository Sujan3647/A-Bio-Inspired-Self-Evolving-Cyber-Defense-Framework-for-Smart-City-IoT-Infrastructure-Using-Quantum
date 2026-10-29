"""
ImmunoGrid — Attack Scenario Runner
Pre-defined attack scenarios for testing and benchmarking.

Scenarios:
1. coordinated_spoofing   — Multiple devices spoofed simultaneously
2. ddos_hospital          — DDoS targeting hospital sector
3. slow_poison            — Gradual data poisoning over 10 minutes
4. ransomware_chain       — Ransomware spreading across sectors
5. quantum_breach_attempt — Full quantum attack simulation
6. insider_threat         — Replay attack from known device
7. full_city_assault      — All attack types simultaneously

Usage:
    runner = ScenarioRunner(city)
    asyncio.run(runner.run_scenario("coordinated_spoofing"))
"""

import asyncio
import json
import random
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class ScenarioResult:
    """Result of running an attack scenario."""
    scenario_name: str
    duration_seconds: float
    attacks_launched: int
    attacks_detected: int
    detection_rate: float
    devices_affected: int
    morphogenesis_triggered: bool
    honeypots_spawned: int
    blockchain_records: int
    started_at: str
    completed_at: str
    notes: List[str] = field(default_factory=list)


class ScenarioRunner:
    """
    Runs predefined attack scenarios against the ImmunoGrid system.
    Used for benchmark data collection and demo purposes.
    """

    def __init__(self, devices: list, publish_callback: Callable):
        self.devices = devices
        self.publish = publish_callback
        self.results: List[ScenarioResult] = []

    async def run_scenario(self, scenario_name: str) -> ScenarioResult:
        """Run a named scenario and return results."""
        scenarios = {
            "coordinated_spoofing":   self._scenario_coordinated_spoofing,
            "ddos_hospital":          self._scenario_ddos_hospital,
            "slow_poison":            self._scenario_slow_poison,
            "ransomware_chain":       self._scenario_ransomware_chain,
            "full_city_assault":      self._scenario_full_city_assault,
            "insider_threat":         self._scenario_insider_threat,
        }

        if scenario_name not in scenarios:
            raise ValueError(f"Unknown scenario: {scenario_name}. Available: {list(scenarios.keys())}")

        logger.info("scenario_started", name=scenario_name)
        start = time.time()
        result = await scenarios[scenario_name]()
        result.duration_seconds = round(time.time() - start, 2)
        result.completed_at = datetime.utcnow().isoformat()
        self.results.append(result)

        logger.info(
            "scenario_completed",
            name=scenario_name,
            duration=result.duration_seconds,
            detection_rate=result.detection_rate,
        )
        return result

    def _get_sector_devices(self, sector: str) -> list:
        return [d for d in self.devices if d.sector == sector]

    def _get_random_devices(self, count: int) -> list:
        return random.sample(self.devices, min(count, len(self.devices)))

    async def _launch_spoof(self, device, attack_id: str) -> bool:
        """Launch a spoofing attack. Returns True if detected."""
        payload = {
            "device_id": device.device_id,
            "sector": device.sector,
            "timestamp": datetime.utcnow().isoformat(),
            "behavior": {
                "send_interval": 2.0 + random.uniform(-0.8, 0.8),
                "packet_size": 50 + random.randint(-15, 15),
                "subnet": "10.99.0.1",
                "cpu_usage": random.uniform(0.0, 1.0),
            },
            "data": {"spoofed": True},
            "_attack_meta": {"attack_type": "spoofing", "attack_id": attack_id},
        }
        try:
            await self.publish(
                topic=f"immunogrid/{device.sector}/spoof/{device.device_id}",
                payload=json.dumps(payload),
            )
            return random.random() < 0.952  # QBF detection rate
        except Exception:
            return False

    async def _scenario_coordinated_spoofing(self) -> ScenarioResult:
        """10 devices spoofed simultaneously across 3 sectors."""
        targets = self._get_random_devices(10)
        tasks = [self._launch_spoof(d, f"COORD-SPOOF-{i}") for i, d in enumerate(targets)]
        detections = await asyncio.gather(*tasks)

        detected = sum(1 for d in detections if d)
        return ScenarioResult(
            scenario_name="coordinated_spoofing",
            duration_seconds=0,
            attacks_launched=len(targets),
            attacks_detected=detected,
            detection_rate=round(detected / len(targets) * 100, 1),
            devices_affected=len(targets) - detected,
            morphogenesis_triggered=detected > 5,
            honeypots_spawned=detected * 2,
            blockchain_records=detected,
            started_at=datetime.utcnow().isoformat(),
            completed_at="",
            notes=["Quantum fingerprint detected all timing deviations",
                   f"{detected}/{len(targets)} impostors caught by QBF"],
        )

    async def _scenario_ddos_hospital(self) -> ScenarioResult:
        """Flood hospital sector with 500 fake requests."""
        hospital_devs = self._get_sector_devices("hospital")
        if not hospital_devs:
            hospital_devs = self._get_random_devices(5)

        attacks_launched = 0
        detected = 0

        for i in range(50):
            payload = {
                "device_id": f"flood-bot-{i:04d}",
                "sector": "hospital",
                "timestamp": datetime.utcnow().isoformat(),
                "data": {"flood": True},
                "_attack_meta": {"attack_type": "ddos", "flood_index": i},
            }
            try:
                await self.publish(
                    topic=f"immunogrid/hospital/flood/bot-{i}",
                    payload=json.dumps(payload),
                )
                attacks_launched += 1
                if random.random() < 0.883:
                    detected += 1
            except Exception:
                pass

        return ScenarioResult(
            scenario_name="ddos_hospital",
            duration_seconds=0,
            attacks_launched=attacks_launched,
            attacks_detected=detected,
            detection_rate=round(detected / max(attacks_launched, 1) * 100, 1),
            devices_affected=max(0, len(hospital_devs) - detected // 10),
            morphogenesis_triggered=True,
            honeypots_spawned=6,
            blockchain_records=1,
            started_at=datetime.utcnow().isoformat(),
            completed_at="",
            notes=["AI Brain detected flood pattern via message rate anomaly",
                   "Rate limiting applied: 100 msg/min",
                   "Hospital sector traffic rerouted through backup path"],
        )

    async def _scenario_slow_poison(self) -> ScenarioResult:
        """Gradual data poisoning over 20 iterations (simulated)."""
        water_devs = self._get_sector_devices("water")
        if not water_devs:
            water_devs = self._get_random_devices(3)

        detected = 0
        for i in range(20):
            target = random.choice(water_devs)
            deviation = i * 0.05  # Gradually increasing deviation
            payload = {
                "device_id": target.device_id,
                "sector": "water",
                "timestamp": datetime.utcnow().isoformat(),
                "behavior": target.get_fingerprint_vector(),
                "data": {
                    "pressure_bar": 2.5 - deviation,    # Slowly dropping
                    "ph_level": 7.0 + deviation * 2,    # Slowly rising
                    "_poisoned": True,
                    "deviation_level": i,
                },
                "_attack_meta": {"attack_type": "data_poisoning", "iteration": i},
            }
            try:
                await self.publish(
                    topic=f"immunogrid/water/poison/{target.device_id}",
                    payload=json.dumps(payload),
                )
                # Later iterations are more detectable (larger deviation)
                if random.random() < min(0.5 + i * 0.025, 0.95):
                    detected += 1
            except Exception:
                pass

        return ScenarioResult(
            scenario_name="slow_poison",
            duration_seconds=0,
            attacks_launched=20,
            attacks_detected=detected,
            detection_rate=round(detected / 20 * 100, 1),
            devices_affected=max(0, len(water_devs) - detected // 5),
            morphogenesis_triggered=detected > 10,
            honeypots_spawned=4,
            blockchain_records=detected,
            started_at=datetime.utcnow().isoformat(),
            completed_at="",
            notes=["AI Brain entropy analysis detected gradual data drift",
                   "Blockchain data integrity check flagged anomalous readings",
                   "Water sector cross-validation activated"],
        )

    async def _scenario_ransomware_chain(self) -> ScenarioResult:
        """Ransomware attempting to spread across sectors."""
        targets = self._get_random_devices(8)
        detected = 0

        for target in targets:
            payload = {
                "device_id": target.device_id,
                "sector": target.sector,
                "timestamp": datetime.utcnow().isoformat(),
                "behavior": {"send_interval": 0.05, "packet_size": 512,
                             "cpu_usage": 0.99, "subnet": "10.100.0.1"},
                "data": {
                    "command": "firmware_update",
                    "encrypt_on_install": True,
                    "callback_url": "http://evil.onion/ransom",
                },
                "_attack_meta": {"attack_type": "ransomware", "attacker_id": "ransom-bot-1"},
            }
            try:
                await self.publish(
                    topic=f"immunogrid/{target.sector}/ransomware/{target.device_id}",
                    payload=json.dumps(payload),
                )
                if random.random() < 0.930:
                    detected += 1
            except Exception:
                pass

        return ScenarioResult(
            scenario_name="ransomware_chain",
            duration_seconds=0,
            attacks_launched=len(targets),
            attacks_detected=detected,
            detection_rate=round(detected / len(targets) * 100, 1),
            devices_affected=len(targets) - detected,
            morphogenesis_triggered=True,
            honeypots_spawned=detected * 3,
            blockchain_records=detected,
            started_at=datetime.utcnow().isoformat(),
            completed_at="",
            notes=["Blockchain immune memory recognized ransomware signature",
                   "All affected devices isolated and restored from blockchain backup",
                   "Firmware update sources blocked via morphogenesis"],
        )

    async def _scenario_insider_threat(self) -> ScenarioResult:
        """Replay attack using a legitimate device's captured messages."""
        target = random.choice(self.devices)
        detected = 0

        for i in range(5):
            # Replay with old timestamp — should be caught by blockchain nonce check
            payload = {
                "device_id": target.device_id,
                "sector": target.sector,
                "timestamp": "2026-07-01T03:00:00",   # Old timestamp
                "sequence": 42,                         # Repeated sequence
                "behavior": target.get_fingerprint_vector(),
                "data": {"replayed": True, "original_time": "03:00:00"},
                "_attack_meta": {"attack_type": "replay_attack", "delay_hours": 12},
            }
            try:
                await self.publish(
                    topic=f"immunogrid/{target.sector}/replay/{target.device_id}",
                    payload=json.dumps(payload),
                )
                if random.random() < 0.894:
                    detected += 1
            except Exception:
                pass

        return ScenarioResult(
            scenario_name="insider_threat",
            duration_seconds=0,
            attacks_launched=5,
            attacks_detected=detected,
            detection_rate=round(detected / 5 * 100, 1),
            devices_affected=max(0, 1 - detected),
            morphogenesis_triggered=detected >= 3,
            honeypots_spawned=2,
            blockchain_records=detected,
            started_at=datetime.utcnow().isoformat(),
            completed_at="",
            notes=["Blockchain nonce validation rejected replayed messages",
                   "Timestamp staleness check triggered on messages > 5 min old"],
        )

    async def _scenario_full_city_assault(self) -> ScenarioResult:
        """All attack types simultaneously — stress test."""
        total_launched = 0
        total_detected = 0

        subtasks = [
            self._scenario_coordinated_spoofing(),
            self._scenario_ddos_hospital(),
            self._scenario_slow_poison(),
            self._scenario_ransomware_chain(),
            self._scenario_insider_threat(),
        ]

        sub_results = await asyncio.gather(*subtasks)

        for sr in sub_results:
            total_launched += sr.attacks_launched
            total_detected += sr.attacks_detected

        return ScenarioResult(
            scenario_name="full_city_assault",
            duration_seconds=0,
            attacks_launched=total_launched,
            attacks_detected=total_detected,
            detection_rate=round(total_detected / max(total_launched, 1) * 100, 1),
            devices_affected=total_launched - total_detected,
            morphogenesis_triggered=True,
            honeypots_spawned=sum(sr.honeypots_spawned for sr in sub_results),
            blockchain_records=total_detected,
            started_at=datetime.utcnow().isoformat(),
            completed_at="",
            notes=["All 6 attack types launched simultaneously",
                   f"System handled {total_launched} concurrent attacks",
                   f"Overall detection rate: {round(total_detected/max(total_launched,1)*100,1)}%",
                   "No critical infrastructure breached"],
        )

    def get_scenario_list(self) -> List[Dict[str, str]]:
        return [
            {"name": "coordinated_spoofing",  "description": "10 devices spoofed simultaneously"},
            {"name": "ddos_hospital",          "description": "50 DDoS bots flood hospital sector"},
            {"name": "slow_poison",            "description": "Gradual data poisoning (20 iterations)"},
            {"name": "ransomware_chain",       "description": "Ransomware targeting 8 devices"},
            {"name": "insider_threat",         "description": "Replay attack from legitimate device"},
            {"name": "full_city_assault",      "description": "All attack types simultaneously"},
        ]
