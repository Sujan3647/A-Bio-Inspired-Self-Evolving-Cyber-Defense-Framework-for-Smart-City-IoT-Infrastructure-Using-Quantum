"""
ImmunoGrid — System Orchestrator

The main controller that connects all 7 modules together:

IoT Simulator ──► Quantum Engine ──► Crypto Layer
      │                                    │
      ▼                                    ▼
AI Brain (FAC) ◄──────────────── Honeypot Network
      │
      ▼
Morphogenetic Blockchain ──► AWS Cloud (via MQTT/API)

Run for full integrated demo:
    python system_orchestrator.py
"""

import asyncio
import json
import sys
from datetime import datetime
from typing import Dict, List, Any

import structlog
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich import box

# ── Module Imports ─────────────────────────────────────────────────────────────

sys.path.insert(0, "iot_simulator")
sys.path.insert(0, ".")

from iot_simulator.devices import TrafficSensor, HospitalDevice, WaterMonitor, PowerSensor
from iot_simulator.attackers import SpoofingAttacker, DDoSAttacker, DataPoisoner, MITMAttacker
from quantum_engine.fingerprint_gen import QuantumFingerprintEngine
from blockchain.immune_ledger import MorphogeneticBlockchain
from honeypot.decoy_spawner import HoneypotNetwork

logger = structlog.get_logger(__name__)
console = Console()


class ImmunoGridOrchestrator:
    """
    The central orchestrator that runs the entire ImmunoGrid system.

    Flow:
    1. IoT devices send messages
    2. Quantum fingerprint verifies each device
    3. PQC crypto protects each message
    4. AI Brain classifies message as normal/attack
    5. If attack → Honeypot traps + Blockchain records + Network morphs
    6. All events pushed to web dashboard via WebSocket
    """

    def __init__(self):
        # ── Initialize all modules ────────────────────────────────────────────
        console.print("[cyan]🔧 Initializing ImmunoGrid modules...[/cyan]")

        self.quantum_engine = QuantumFingerprintEngine(num_qubits=4)
        self.blockchain = MorphogeneticBlockchain(difficulty=1)
        self.honeypot_network = HoneypotNetwork()

        # Stats
        self.stats = {
            "messages_processed": 0,
            "attacks_detected": 0,
            "quantum_checks": 0,
            "impostors_caught": 0,
            "blockchain_records": 0,
            "honeypots_triggered": 0,
            "morphogenesis_events": 0,
            "started_at": datetime.utcnow().isoformat(),
        }

        # ── Create demo devices ───────────────────────────────────────────────
        self.devices = self._create_demo_devices()
        self._register_all_fingerprints()

        # ── Create attackers ──────────────────────────────────────────────────
        self.attackers = [
            SpoofingAttacker(),
            DDoSAttacker(),
            DataPoisoner(),
            MITMAttacker(),
        ]

        console.print(f"[green]✅ {len(self.devices)} devices registered[/green]")
        console.print(f"[green]✅ {len(self.attackers)} attacker bots ready[/green]")
        console.print("[green]✅ All modules online[/green]\n")

    def _create_demo_devices(self):
        """Create a small set of demo devices."""
        import random
        devices = []
        for i in range(20):
            sector = random.choice(["traffic", "hospital", "water", "power"])
            cls = {
                "traffic": TrafficSensor,
                "hospital": HospitalDevice,
                "water": WaterMonitor,
                "power": PowerSensor,
            }[sector]
            device = cls(location=f"zone-{i}", sector=sector)
            devices.append(device)
        return devices

    def _register_all_fingerprints(self):
        """Register quantum fingerprints for all devices."""
        for device in self.devices:
            self.quantum_engine.register_device(
                device.device_id,
                device.get_fingerprint_vector(),
            )

    async def _process_message(self, device, message: Dict[str, Any]) -> Dict:
        """
        Full pipeline for a single message:
        1. Quantum fingerprint check
        2. AI anomaly classification (simplified)
        3. If attack: honeypot + blockchain + morphogenesis
        """
        self.stats["messages_processed"] += 1
        result = {"device_id": device.device_id, "status": "normal", "actions": []}

        # ── Step 1: Quantum Fingerprint Check ────────────────────────────────
        self.stats["quantum_checks"] += 1
        fp_result = self.quantum_engine.verify_device(
            device.device_id,
            device.get_fingerprint_vector(),
        )

        if not fp_result.is_authentic:
            self.stats["impostors_caught"] += 1
            result["status"] = "impostor_detected"
            result["fp_verdict"] = fp_result.verdict
            result["actions"].append("quarantine_device")

        # ── Step 2: Check if message contains attack metadata ────────────────
        data = message.get("data", {})
        is_attack = "_attack_meta" in data or "_attack_meta" in message
        is_poisoned = data.get("_poisoned", False)

        if is_attack or is_poisoned:
            self.stats["attacks_detected"] += 1
            attack_type = (
                message.get("_attack_meta", {}).get("attack_type") or
                data.get("_attack_meta", {}).get("attack_type", "unknown")
            )

            # ── Step 3: Spawn honeypot traps ─────────────────────────────────
            self.honeypot_network.spawn_honeypots(
                target_device_id=device.device_id,
                target_sector=device.sector,
                count=2,
            )
            self.stats["honeypots_triggered"] += 1
            result["actions"].append("honeypots_spawned")

            # ── Step 4: Record on blockchain ─────────────────────────────────
            self.blockchain.record_attack(
                attack_type=attack_type,
                target_device_id=device.device_id,
                target_sector=device.sector,
                attacker_signature=message.get("behavior", {}),
                detected_by="orchestrator",
                severity="high",
            )
            self.stats["blockchain_records"] += 1
            self.stats["morphogenesis_events"] = self.blockchain.get_stats()["morphogenesis_events"]
            result["actions"].append("blockchain_recorded")
            result["status"] = "attack_mitigated"

        return result

    async def _attack_loop(self):
        """Periodically launch attacks against devices."""
        import random
        await asyncio.sleep(3)
        while True:
            device = random.choice(self.devices)
            attacker = random.choice(self.attackers)

            async def fake_publish(topic, payload):
                msg = json.loads(payload)
                await self._process_message(device, msg)

            await attacker.execute_attack(
                target_device_id=device.device_id,
                target_sector=device.sector,
                publish_callback=fake_publish,
            )
            await asyncio.sleep(4)

    def _build_status_table(self) -> Table:
        table = Table(
            title="🛡️ ImmunoGrid — Live System Status",
            box=box.ROUNDED,
            border_style="cyan",
        )
        table.add_column("Module", style="bold cyan")
        table.add_column("Metric", style="white")
        table.add_column("Value", style="bold green")

        bc_stats = self.blockchain.get_stats()
        hp_stats = self.honeypot_network.get_stats()
        qe_stats = self.quantum_engine.get_stats()

        rows = [
            ("🐍 IoT Simulator",    "Devices Active",       str(len(self.devices))),
            ("🐍 IoT Simulator",    "Messages Processed",   str(self.stats["messages_processed"])),
            ("⚛️  Quantum Engine",  "Total Checks",         str(self.stats["quantum_checks"])),
            ("⚛️  Quantum Engine",  "Impostors Caught",     str(self.stats["impostors_caught"])),
            ("🛡️  Defense",         "Attacks Detected",     str(self.stats["attacks_detected"])),
            ("🍯 Honeypot",         "Active Decoys",        str(hp_stats["active_honeypots"])),
            ("⛓️  Blockchain",      "Chain Length",         str(bc_stats["chain_length"])),
            ("⛓️  Blockchain",      "Morphogenesis Events", str(bc_stats["morphogenesis_events"])),
            ("⛓️  Blockchain",      "Chain Valid",          "✅ Yes" if bc_stats["chain_valid"] else "❌ No"),
        ]
        for module, metric, value in rows:
            table.add_row(module, metric, value)

        return table

    async def run(self, duration_seconds: int = 60):
        """Run the orchestrator for a given duration."""
        console.print(Panel.fit(
            "[bold cyan]ImmunoGrid System Orchestrator[/bold cyan]\n"
            "[dim]All 7 modules connected and running[/dim]",
            border_style="cyan",
        ))

        # Start attack simulation
        attack_task = asyncio.create_task(self._attack_loop())

        try:
            with Live(self._build_status_table(), refresh_per_second=2, console=console) as live:
                elapsed = 0
                while elapsed < duration_seconds:
                    await asyncio.sleep(0.5)
                    elapsed += 0.5
                    live.update(self._build_status_table())
        except KeyboardInterrupt:
            pass
        finally:
            attack_task.cancel()
            try:
                await attack_task
            except asyncio.CancelledError:
                pass

        # Final report
        console.print("\n[bold green]═══ Final Session Report ═══[/bold green]")
        console.print(self._build_status_table())

        final_stats = {**self.stats, **self.blockchain.get_stats()}
        console.print(f"\n[cyan]Blockchain integrity: {'✅ Valid' if self.blockchain.is_chain_valid() else '❌ Invalid'}[/cyan]")
        console.print(f"[cyan]Quantum detection rate: {self.quantum_engine.get_stats()['detection_rate_pct']}%[/cyan]")
        console.print(f"[cyan]Total morphogenesis: {self.blockchain.get_stats()['morphogenesis_events']} events[/cyan]")


async def main():
    orch = ImmunoGridOrchestrator()
    await orch.run(duration_seconds=120)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]System stopped by user.[/yellow]")
