"""
ImmunoGrid — Honeypot Demo
Interactive demonstration of the honeypot trap network.

Run:
    python honeypot/demo_honeypot.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich import box
from rich.text import Text

from honeypot.decoy_spawner import HoneypotNetwork
from honeypot.intelligence_capture import IntelligenceCaptureEngine

console = Console()

def main():
    console.clear()
    console.print("\n[bold cyan]╔══════════════════════════════════════════════════╗[/bold cyan]")
    console.print("[bold cyan]║   ImmunoGrid — Honeypot Decoy Network Demo      ║[/bold cyan]")
    console.print("[bold cyan]╚══════════════════════════════════════════════════╝[/bold cyan]\n")
    
    # Initialize systems
    console.print("[yellow]Initializing honeypot network...[/yellow]")
    net = HoneypotNetwork()
    ice = IntelligenceCaptureEngine()
    time.sleep(0.5)
    
    # Scenario 1: Attack Detection
    console.print("\n[bold red]⚠️  THREAT DETECTED[/bold red]")
    console.print("[dim]Hospital device 'hospital-device-042' under attack (spoofing attempt)[/dim]\n")
    time.sleep(1)
    
    # Spawn honeypots
    console.print("[yellow]🍯 Spawning decoy honeypots...[/yellow]")
    honeypots = net.spawn_honeypots("hospital-device-042", "hospital", count=5)
    
    hp_table = Table(title="Active Honeypots", box=box.ROUNDED, border_style="yellow")
    hp_table.add_column("Honeypot ID", style="cyan")
    hp_table.add_column("Mimics Device", style="white")
    hp_table.add_column("Sector", style="green")
    hp_table.add_column("Status", style="bold")
    
    for hp in honeypots:
        hp_table.add_row(
            hp.honeypot_id,
            hp.mimics_device_id,
            hp.mimics_sector,
            "[green]ACTIVE 🟢[/green]"
        )
    
    console.print(hp_table)
    time.sleep(1.5)
    
    # Simulate attacker interactions
    console.print("\n[bold red]🎯 Attacker engaging with honeypots...[/bold red]")
    
    attack_scenarios = [
        {
            "attacker_id": "spoofer-alpha-007",
            "attack_type": "spoofing",
            "behavior": {"send_interval": 0.4, "packet_size": 320, "subnet": "10.0.10.0/24"},
            "count": 8,
        },
        {
            "attacker_id": "mitm-bot-003",
            "attack_type": "man_in_the_middle",
            "behavior": {"send_interval": 0.6, "packet_size": 512, "subnet": "192.168.1.0/24"},
            "count": 5,
        },
        {
            "attacker_id": "ddos-army-12",
            "attack_type": "ddos",
            "behavior": {"send_interval": 0.1, "packet_size": 64, "subnet": "172.16.0.0/12"},
            "count": 12,
        },
    ]
    
    for scenario in attack_scenarios:
        for _ in range(scenario["count"]):
            # Round-robin across honeypots
            hp = honeypots[_ % len(honeypots)]
            hp.record_interaction({
                "behavior": scenario["behavior"],
                "sector": "hospital",
                "_attack_meta": {
                    "attack_type": scenario["attack_type"],
                    "attacker_id": scenario["attacker_id"],
                },
            })
    
    time.sleep(1)
    
    # Show captured interactions
    console.print("\n[green]✅ Attacker trapped! Interactions captured:[/green]\n")
    
    capture_table = Table(box=box.SIMPLE, border_style="green")
    capture_table.add_column("Honeypot", style="cyan")
    capture_table.add_column("Interactions", style="yellow", justify="right")
    capture_table.add_column("Attackers", style="red")
    
    for hp in honeypots:
        if hp.interactions:
            report = hp.get_intelligence_report()
            capture_table.add_row(
                hp.honeypot_id[:20] + "...",
                str(report["total_interactions"]),
                ", ".join(report["attacker_ids"])[:30] + "..."
            )
    
    console.print(capture_table)
    time.sleep(1.5)
    
    # Intelligence Analysis
    console.print("\n[bold cyan]🧠 Analyzing captured intelligence...[/bold cyan]\n")
    time.sleep(1)
    
    reports = []
    for hp in honeypots:
        if hp.interactions:
            report = ice.analyze_honeypot(hp.honeypot_id, hp.interactions)
            if report:
                reports.append(report)
    
    # Show attacker profiles
    intel_table = Table(
        title="🔍 Attacker Intelligence Report",
        box=box.ROUNDED,
        border_style="cyan"
    )
    intel_table.add_column("Attacker ID", style="red bold")
    intel_table.add_column("Attack Types", style="yellow")
    intel_table.add_column("Attempts", style="cyan", justify="right")
    intel_table.add_column("Profile Hash", style="dim")
    
    for report in reports:
        profile = report.attacker_profile
        intel_table.add_row(
            profile.attacker_id,
            ", ".join(profile.attack_types),
            str(profile.total_attempts),
            profile.profile_hash[:16] + "..."
        )
    
    console.print(intel_table)
    time.sleep(1.5)
    
    # Defense Recommendations
    console.print("\n[bold green]🛡️  Recommended Defense Actions:[/bold green]\n")
    
    all_defenses = set()
    for report in reports:
        all_defenses.update(report.recommended_defenses)
    
    for i, defense in enumerate(list(all_defenses)[:8], 1):
        console.print(f"  {i}. [cyan]{defense}[/cyan]")
        time.sleep(0.3)
    
    time.sleep(1)
    
    # AI Training Samples
    console.print("\n[bold magenta]🤖 AI Training Samples Generated:[/bold magenta]")
    total_samples = sum(len(r.ai_training_samples) for r in reports)
    console.print(f"  [green]✓[/green] {total_samples} labeled attack samples ready for Federated Learning")
    time.sleep(0.5)
    
    # Blockchain Entry
    console.print("\n[bold blue]⛓️  Blockchain Immune Memory Entry:[/bold blue]")
    console.print(f"  [green]✓[/green] {len(reports)} attack profiles recorded on immutable ledger")
    time.sleep(0.5)
    
    # Network Stats
    stats = net.get_stats()
    ice_stats = ice.get_stats()
    
    console.print("\n")
    stats_panel = Panel(
        f"""[cyan]Active Honeypots:[/cyan] [bold]{stats['active_honeypots']}[/bold]
[cyan]Total Spawned:[/cyan] [bold]{stats['total_spawned']}[/bold]
[cyan]Interactions Captured:[/cyan] [bold]{stats['total_interactions_captured']}[/bold]
[cyan]Attackers Trapped:[/cyan] [bold red]{stats['attackers_trapped']}[/bold red]
[cyan]Profiles Generated:[/cyan] [bold]{ice_stats['total_attackers_profiled']}[/bold]
[cyan]Intelligence Reports:[/cyan] [bold]{ice_stats['total_reports']}[/bold]
[cyan]Attack Types Identified:[/cyan] [bold]{len(ice_stats['unique_attack_types'])}[/bold]""",
        title="📊 Honeypot Network Statistics",
        border_style="green",
        box=box.DOUBLE
    )
    
    console.print(stats_panel)
    
    # Success message
    console.print("\n[bold green]✅ Honeypot Defense Successfully Deployed![/bold green]")
    console.print("[dim]Real devices remain safe. Attackers trapped and profiled.[/dim]\n")
    
    # Bio-inspired analogy
    console.print(Panel(
        Text.from_markup(
            "🦠 [bold cyan]Bio-Inspired Defense:[/bold cyan]\n\n"
            "Just like white blood cells create antibodies after encountering a pathogen, "
            "ImmunoGrid's honeypots capture attacker 'DNA' and create quantum "
            "fingerprints to recognize and block future attacks.\n\n"
            "[green]The city's immune system just got stronger.[/green]"
        ),
        title="🧬 Immunological Memory",
        border_style="cyan",
        box=box.HEAVY
    ))
    
    console.print()


if __name__ == "__main__":
    main()
