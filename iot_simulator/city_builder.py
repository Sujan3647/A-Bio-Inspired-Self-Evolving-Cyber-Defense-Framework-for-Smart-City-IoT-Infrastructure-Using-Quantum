"""
ImmunoGrid — City Builder
Main entry point for the IoT simulator.
Spawns 500+ virtual smart city devices and runs attack simulations.

Run this to start the virtual city:
    python city_builder.py
"""

import asyncio
import json
import random
import sys
from datetime import datetime
from typing import Dict, List

import structlog
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich import box

from iot_simulator.devices import (
    TrafficSensor,
    StreetCamera,
    WaterMonitor,
    HospitalDevice,
    PowerSensor,
    MetroSensor,
    AirportDevice,
    GovtOfficeNode,
    DeviceStatus,
)
from iot_simulator.attackers import SpoofingAttacker, DDoSAttacker, DataPoisoner, MITMAttacker, ReplayAttacker, RansomwareBot

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ]
)
logger = structlog.get_logger(__name__)
console = Console()


# ─── City Configuration ───────────────────────────────────────────────────────

CITY_CONFIG = {
    "traffic": {
        "device_class": TrafficSensor,
        "count": 100,
        "sector": "traffic",
        "locations": ["intersection-A1", "intersection-B2", "highway-north",
                      "downtown-main", "airport-road", "metro-junction"],
    },
    "camera": {
        "device_class": StreetCamera,
        "count": 80,
        "sector": "surveillance",
        "locations": ["park-entrance", "market-square", "govt-district",
                      "hospital-zone", "port-area", "train-station"],
    },
    "water": {
        "device_class": WaterMonitor,
        "count": 60,
        "sector": "water",
        "locations": ["treatment-plant-1", "treatment-plant-2", "distribution-main",
                      "residential-zone-a", "industrial-zone", "hospital-supply"],
    },
    "hospital": {
        "device_class": HospitalDevice,
        "count": 80,
        "sector": "hospital",
        "locations": ["icu-ward-1", "icu-ward-2", "emergency-room",
                      "surgery-block", "maternity-ward", "radiology"],
    },
    "power": {
        "device_class": PowerSensor,
        "count": 80,
        "sector": "power",
        "locations": ["substation-north", "substation-south", "grid-east",
                      "industrial-feeder", "hospital-supply-grid", "govt-building"],
    },
    "metro": {
        "device_class": MetroSensor,
        "count": 50,
        "sector": "metro",
        "locations": ["central-station", "airport-terminal", "city-mall",
                      "government-district", "university", "hospital-junction"],
    },
    "airport": {
        "device_class": AirportDevice,
        "count": 30,
        "sector": "airport",
        "locations": ["terminal-1", "terminal-2", "runway-north",
                      "cargo-bay", "immigration", "customs"],
    },
    "government": {
        "device_class": GovtOfficeNode,
        "count": 20,
        "sector": "government",
        "locations": ["ministry-block-a", "ministry-block-b", "national-assembly",
                      "prime-minister-office", "supreme-court", "customs-house"],
    },
}

# ─── Message Bus (In-Memory for Simulation) ───────────────────────────────────

class MessageBus:
    """
    Simple in-memory message bus for the simulation.
    In production, this is AWS IoT Core + MQTT.
    """

    def __init__(self):
        self.messages: List[Dict] = []
        self.message_count = 0
        self.attack_count = 0
        self.detected_count = 0
        self._subscribers = []

    async def publish(self, topic: str, payload: str):
        """Publish a message to the bus."""
        message = {
            "topic": topic,
            "payload": json.loads(payload),
            "received_at": datetime.utcnow().isoformat(),
        }
        self.messages.append(message)
        self.message_count += 1

        # Keep only last 1000 messages in memory
        if len(self.messages) > 1000:
            self.messages = self.messages[-1000:]

        # Check if it's an attack message
        payload_data = message["payload"]
        if "_attack_meta" in payload_data.get("data", {}) or "_attack_meta" in payload_data:
            self.attack_count += 1

        # Notify subscribers
        for callback in self._subscribers:
            await callback(message)

    def subscribe(self, callback):
        self._subscribers.append(callback)

    def get_stats(self) -> Dict:
        return {
            "total_messages": self.message_count,
            "attack_messages": self.attack_count,
            "detection_rate": f"{(self.detected_count / max(self.attack_count, 1)) * 100:.1f}%",
            "messages_in_buffer": len(self.messages),
        }


# ─── Smart City ───────────────────────────────────────────────────────────────

class SmartCity:
    """
    The complete virtual smart city.
    Manages all 500+ devices and coordinates attacks + defense.
    """

    def __init__(self, name: str = "ImmunoGrid City"):
        self.name = name
        self.devices = []
        self.attackers = []
        self.bus = MessageBus()
        self._tasks = []
        self.started_at = datetime.utcnow()

        console.print(Panel.fit(
            f"[bold cyan]🏙️  {self.name}[/bold cyan]\n"
            f"[green]ImmunoGrid Smart City Simulator[/green]\n"
            f"[dim]Bio-Inspired Cyber Defense Platform[/dim]",
            border_style="cyan",
        ))

    def build(self):
        """Spawn all devices according to CITY_CONFIG."""
        total = 0
        for sector_name, config in CITY_CONFIG.items():
            count = config["count"]
            for i in range(count):
                location = random.choice(config["locations"])
                device = config["device_class"](
                    location=location,
                    sector=config["sector"],
                )
                self.devices.append(device)
                total += 1

        # Create attackers — all 6 types
        self.attackers = [
            SpoofingAttacker(),
            SpoofingAttacker(),
            DDoSAttacker(flood_rate=100),
            DataPoisoner(),
            DataPoisoner(),
            MITMAttacker(),
            ReplayAttacker(),
            RansomwareBot(),
        ]

        console.print(f"\n[green]✅ City built:[/green] {total} devices across "
                      f"{len(CITY_CONFIG)} sectors")
        console.print(f"[yellow]⚠️  Attack bots:[/yellow] {len(self.attackers)} attackers ready\n")
        return self

    def get_online_devices(self):
        return [d for d in self.devices if d.status == DeviceStatus.ONLINE]

    def get_stats(self) -> Dict:
        status_counts = {}
        for d in self.devices:
            s = d.status.value
            status_counts[s] = status_counts.get(s, 0) + 1

        return {
            "total_devices": len(self.devices),
            "online": status_counts.get("online", 0),
            "compromised": status_counts.get("compromised", 0),
            "quarantined": status_counts.get("quarantined", 0),
            "bus": self.bus.get_stats(),
        }

    async def run_attack_simulation(self):
        """Periodically launch random attacks against city devices."""
        await asyncio.sleep(5)  # Give devices time to start
        attack_interval = 8     # Attack every 8 seconds

        while True:
            try:
                online_devices = self.get_online_devices()
                if online_devices:
                    # Pick a random target
                    target = random.choice(online_devices)
                    # Pick a random attacker
                    attacker = random.choice(self.attackers)

                    event = await attacker.execute_attack(
                        target_device_id=target.device_id,
                        target_sector=target.sector,
                        publish_callback=self.bus.publish,
                    )

                    if event.detected:
                        self.bus.detected_count += 1
                        target.mark_compromised(event.attack_type.value)

                await asyncio.sleep(attack_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("attack_simulation_error", error=str(e))
                await asyncio.sleep(2)

    def _build_status_table(self) -> Table:
        """Build a rich table showing city status."""
        stats = self.get_stats()

        table = Table(
            title="🛡️ ImmunoGrid — Live City Status",
            box=box.ROUNDED,
            border_style="cyan",
        )
        table.add_column("Metric", style="bold white")
        table.add_column("Value", style="bold green")

        uptime = (datetime.utcnow() - self.started_at).seconds
        table.add_row("⏱️  Uptime", f"{uptime}s")
        table.add_row("🏙️  Total Devices", str(stats["total_devices"]))
        table.add_row("✅ Online Devices", str(stats["online"]))
        table.add_row("🚨 Compromised", str(stats["compromised"]))
        table.add_row("🔒 Quarantined", str(stats["quarantined"]))
        table.add_row("📨 Total Messages", str(stats["bus"]["total_messages"]))
        table.add_row("⚔️  Attack Messages", str(stats["bus"]["attack_messages"]))
        table.add_row("🛡️  Detection Rate", stats["bus"]["detection_rate"])

        return table

    async def run(self):
        """
        Start the entire city simulation:
        1. All devices start sending data
        2. Attack bots periodically launch attacks
        3. Live dashboard shows city status
        """
        console.print("[bold green]🚀 Starting city simulation...[/bold green]\n")

        # Start all device loops
        for device in self.devices:
            task = asyncio.create_task(device.run(self.bus.publish))
            self._tasks.append(task)

        # Start attack simulation
        attack_task = asyncio.create_task(self.run_attack_simulation())
        self._tasks.append(attack_task)

        # Live status display
        try:
            with Live(
                self._build_status_table(),
                refresh_per_second=1,
                console=console,
            ) as live:
                while True:
                    await asyncio.sleep(1)
                    live.update(self._build_status_table())

        except KeyboardInterrupt:
            console.print("\n[yellow]⏹️  Stopping city simulation...[/yellow]")
            for task in self._tasks:
                task.cancel()
            await asyncio.gather(*self._tasks, return_exceptions=True)
            console.print("[green]✅ City simulation stopped.[/green]")


# ─── Main ─────────────────────────────────────────────────────────────────────

async def main():
    city = SmartCity(name="ImmunoGrid — Smart City Alpha")
    city.build()
    await city.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[bold red]Simulation terminated by user.[/bold red]")
        sys.exit(0)
