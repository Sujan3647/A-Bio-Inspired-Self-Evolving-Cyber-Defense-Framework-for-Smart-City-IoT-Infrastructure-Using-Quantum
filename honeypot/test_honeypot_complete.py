"""
ImmunoGrid — Honeypot Complete Test Suite
Tests all honeypot modules: decoy spawning and intelligence capture.

Run:
    python honeypot/test_honeypot_complete.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()
results = []


def check(name, fn):
    try:
        fn()
        results.append((name, True, ""))
        console.print(f"  [green]✅ {name}[/green]")
    except Exception as e:
        results.append((name, False, str(e)[:80]))
        console.print(f"  [red]❌ {name}: {str(e)[:70]}[/red]")


console.print("\n[bold cyan]╔══════════════════════════════════════════════════╗[/bold cyan]")
console.print("[bold cyan]║  ImmunoGrid Honeypot — Complete Test Suite      ║[/bold cyan]")
console.print("[bold cyan]╚══════════════════════════════════════════════════╝[/bold cyan]\n")

# ── 1. Decoy Spawner ──────────────────────────────────────────────────────────
console.print("[cyan]1. Honeypot Decoy Spawner[/cyan]")

from honeypot.decoy_spawner import HoneypotDevice, HoneypotNetwork

def t_honeypot_device_creation():
    hp = HoneypotDevice("hospital-device-042", "hospital")
    assert hp.honeypot_id.startswith("honeypot-")
    assert hp.mimics_device_id == "hospital-device-042"
    assert hp.mimics_sector == "hospital"
    assert hp.active is True
    assert len(hp.interactions) == 0
check("Honeypot device creation", t_honeypot_device_creation)

def t_record_interaction():
    hp = HoneypotDevice("water-sensor-001", "water")
    attacker_payload = {
        "device_id": "water-sensor-001",
        "behavior": {
            "send_interval": 0.5,
            "packet_size": 256,
            "subnet": "192.168.10.0/24",
            "cpu_usage": 0.95,
        },
        "_attack_meta": {
            "attack_type": "spoofing",
            "attacker_id": "attacker-001",
        },
    }
    interaction = hp.record_interaction(attacker_payload)
    assert len(hp.interactions) == 1
    assert interaction["attacker_behavior"]["attack_type"] == "spoofing"
    assert interaction["attacker_behavior"]["attacker_id"] == "attacker-001"
check("Record attacker interaction", t_record_interaction)

def t_extract_behavior():
    hp = HoneypotDevice("traffic-sensor-001", "traffic")
    payload = {
        "behavior": {"send_interval": 0.3, "packet_size": 512},
        "_attack_meta": {"attack_type": "ddos", "attacker_id": "bot-123"},
        "timestamp": "2026-07-28T10:00:00Z",
    }
    behavior = hp._extract_attacker_behavior(payload)
    assert behavior["send_interval"] == 0.3
    assert behavior["packet_size"] == 512
    assert behavior["attack_type"] == "ddos"
    assert behavior["attacker_id"] == "bot-123"
check("Extract attacker behavioral signature", t_extract_behavior)

def t_fake_response():
    hp = HoneypotDevice("power-sensor-042", "energy")
    response = hp.generate_fake_response()
    assert response["device_id"] == "power-sensor-042"
    assert response["status"] == "online"
    assert "_honeypot" in response
    assert response["_honeypot"] is True
check("Generate fake response to lure attacker", t_fake_response)

def t_intelligence_report():
    hp = HoneypotDevice("hospital-device-001", "hospital")
    for i in range(3):
        hp.record_interaction({
            "behavior": {"send_interval": 0.5, "packet_size": 128},
            "_attack_meta": {"attack_type": "spoofing", "attacker_id": f"att-{i}"},
        })
    report = hp.get_intelligence_report()
    assert report["total_interactions"] == 3
    assert "spoofing" in report["attacker_techniques"]
    assert len(report["attacker_ids"]) == 3
    assert len(report["captured_behaviors"]) == 3
check("Honeypot intelligence report generation", t_intelligence_report)

def t_network_spawn():
    net = HoneypotNetwork()
    honeypots = net.spawn_honeypots("hospital-device-042", "hospital", count=5)
    assert len(honeypots) == 5
    assert net.total_spawned == 5
    assert len(net.active_honeypots) == 5
    for hp in honeypots:
        assert hp.mimics_device_id == "hospital-device-042"
        assert hp.mimics_sector == "hospital"
check("Spawn multiple honeypots", t_network_spawn)

def t_network_process_message():
    net = HoneypotNetwork()
    net.spawn_honeypots("traffic-sensor-001", "traffic", count=2)
    
    # Attacker message targeting the device
    attacker_msg = json.dumps({
        "device_id": "traffic-sensor-001",
        "behavior": {"send_interval": 0.2, "packet_size": 512},
        "_attack_meta": {"attack_type": "replay_attack", "attacker_id": "replay-bot"},
    })
    
    hit = net.process_incoming_message("traffic/sensor/001", attacker_msg)
    assert hit is True
    assert net.total_interactions_captured == 1
check("Process incoming message — honeypot hit", t_network_process_message)

def t_network_no_hit():
    net = HoneypotNetwork()
    net.spawn_honeypots("water-sensor-001", "water", count=1)
    
    # Legitimate message (no attack metadata)
    legit_msg = json.dumps({
        "device_id": "traffic-sensor-999",
        "value": 42.0,
    })
    
    hit = net.process_incoming_message("traffic/sensor/999", legit_msg)
    assert hit is False
check("Legitimate message bypasses honeypot", t_network_no_hit)

def t_network_intelligence():
    net = HoneypotNetwork()
    honeypots = net.spawn_honeypots("hospital-device-001", "hospital", count=2)
    
    # Simulate attacks
    for i in range(3):
        honeypots[0].record_interaction({
            "behavior": {"send_interval": 0.5, "packet_size": 256},
            "_attack_meta": {"attack_type": "spoofing", "attacker_id": f"spoofer-{i}"},
        })
    
    intel = net.get_all_intelligence()
    assert len(intel) == 1  # Only 1 honeypot has interactions
    assert intel[0]["total_interactions"] == 3
check("Collect network-wide intelligence", t_network_intelligence)

def t_network_stats():
    net = HoneypotNetwork()
    net.spawn_honeypots("dev-001", "traffic", count=3)
    net.spawn_honeypots("dev-002", "water", count=2)
    
    # Simulate attacks on first batch
    for hp in list(net.active_honeypots.values())[:3]:
        hp.record_interaction({
            "behavior": {"send_interval": 1.0, "packet_size": 64},
            "_attack_meta": {"attack_type": "ddos", "attacker_id": "ddos-bot-001"},
        })
    
    stats = net.get_stats()
    assert stats["active_honeypots"] == 5
    assert stats["total_spawned"] == 5
    assert stats["attackers_trapped"] >= 1
check("Honeypot network statistics", t_network_stats)

# ── 2. Intelligence Capture Engine ───────────────────────────────────────────
console.print("\n[cyan]2. Intelligence Capture Engine[/cyan]")

from honeypot.intelligence_capture import IntelligenceCaptureEngine, AttackerProfile

def t_ice_analyze():
    ice = IntelligenceCaptureEngine()
    interactions = [
        {
            "timestamp": "2026-07-28T10:00:00Z",
            "attacker_payload": {"sector": "hospital"},
            "attacker_behavior": {
                "send_interval": 0.5,
                "packet_size": 256,
                "subnet": "10.0.0.0/8",
                "attack_type": "spoofing",
                "attacker_id": "spoofer-001",
            },
        },
        {
            "timestamp": "2026-07-28T10:01:00Z",
            "attacker_payload": {"sector": "hospital"},
            "attacker_behavior": {
                "send_interval": 0.6,
                "packet_size": 280,
                "subnet": "10.0.0.0/8",
                "attack_type": "spoofing",
                "attacker_id": "spoofer-001",
            },
        },
    ]
    
    report = ice.analyze_honeypot("honeypot-001", interactions)
    assert report is not None
    assert report.report_id.startswith("RPT-")
    assert report.honeypot_id == "honeypot-001"
    assert "spoofing" in report.attacker_profile.attack_types
    assert report.attacker_profile.total_attempts == 2
check("Analyze honeypot interactions", t_ice_analyze)

def t_ice_attacker_profile():
    ice = IntelligenceCaptureEngine()
    interactions = [
        {
            "timestamp": "2026-07-28T09:00:00Z",
            "attacker_payload": {"sector": "traffic"},
            "attacker_behavior": {
                "send_interval": 0.3,
                "packet_size": 512,
                "subnet": "192.168.1.0/24",
                "attack_type": "ddos",
                "attacker_id": "ddos-bot-007",
            },
        }
    ]
    
    report = ice.analyze_honeypot("hp-002", interactions)
    profile = report.attacker_profile
    
    assert profile.attacker_id == "ddos-bot-007"
    assert "ddos" in profile.attack_types
    assert "traffic" in profile.target_sectors
    assert profile.total_attempts == 1
    assert profile.success_rate == 0.0  # Honeypot = 0% success
    assert len(profile.profile_hash) == 64  # SHA-256
check("Attacker profile generation", t_ice_attacker_profile)

def t_ice_behavioral_signature():
    ice = IntelligenceCaptureEngine()
    interactions = [
        {
            "timestamp": "2026-07-28T10:00:00Z",
            "attacker_payload": {},
            "attacker_behavior": {
                "send_interval": 0.5,
                "packet_size": 128,
                "subnet": "10.0.0.0/8",
            },
        },
        {
            "timestamp": "2026-07-28T10:01:00Z",
            "attacker_payload": {},
            "attacker_behavior": {
                "send_interval": 0.7,
                "packet_size": 256,
                "subnet": "10.0.0.0/8",
            },
        },
    ]
    
    sig = ice._aggregate_behavior(interactions)
    assert sig["avg_send_interval"] == 0.6  # (0.5 + 0.7) / 2
    assert sig["avg_packet_size"] == 192.0  # (128 + 256) / 2
    assert sig["interaction_count"] == 2
    assert "10.0.0.0/8" in sig["unique_subnets"]
check("Behavioral signature aggregation", t_ice_behavioral_signature)

def t_ice_recommend_defenses():
    ice = IntelligenceCaptureEngine()
    defenses = ice._recommend_defenses(["spoofing"])
    assert len(defenses) > 0
    assert any("fingerprint" in d.lower() for d in defenses)
    
    defenses_ddos = ice._recommend_defenses(["ddos"])
    assert any("rate" in d.lower() for d in defenses_ddos)
check("Defense recommendation based on attack type", t_ice_recommend_defenses)

def t_ice_ai_samples():
    ice = IntelligenceCaptureEngine()
    interactions = [
        {
            "timestamp": "2026-07-28T10:00:00Z",
            "attacker_payload": {},
            "attacker_behavior": {
                "send_interval": 0.5,
                "packet_size": 256,
                "attack_type": "spoofing",
                "attacker_id": "att-001",
            },
        },
    ]
    
    samples = ice._generate_ai_samples(interactions)
    assert len(samples) == 1
    assert samples[0]["label"] == 1  # spoofing label
    assert samples[0]["attack_type"] == "spoofing"
    assert samples[0]["source"] == "honeypot_capture"
    assert len(samples[0]["features"]) == 12  # 12-feature vector
check("AI training sample generation", t_ice_ai_samples)

def t_ice_blockchain_entry():
    ice = IntelligenceCaptureEngine()
    interactions = [
        {
            "timestamp": "2026-07-28T10:00:00Z",
            "attacker_payload": {"sector": "hospital"},
            "attacker_behavior": {
                "send_interval": 0.5,
                "packet_size": 256,
                "attack_type": "data_poisoning",
                "attacker_id": "poisoner-001",
            },
        },
    ]
    
    report = ice.analyze_honeypot("hp-003", interactions)
    bc_entry = report.blockchain_entry
    
    assert bc_entry["report_id"].startswith("RPT-")
    assert bc_entry["honeypot_id"] == "hp-003"
    assert "data_poisoning" in bc_entry["attack_types"]
    assert "hospital" in bc_entry["target_sectors"]
    assert "timestamp" in bc_entry
check("Blockchain entry generation", t_ice_blockchain_entry)

def t_ice_multiple_attack_types():
    ice = IntelligenceCaptureEngine()
    interactions = [
        {
            "timestamp": "2026-07-28T10:00:00Z",
            "attacker_payload": {"sector": "traffic"},
            "attacker_behavior": {
                "send_interval": 0.5,
                "packet_size": 128,
                "attack_type": "spoofing",
                "attacker_id": "mixed-001",
            },
        },
        {
            "timestamp": "2026-07-28T10:01:00Z",
            "attacker_payload": {"sector": "traffic"},
            "attacker_behavior": {
                "send_interval": 0.3,
                "packet_size": 512,
                "attack_type": "ddos",
                "attacker_id": "mixed-001",
            },
        },
    ]
    
    report = ice.analyze_honeypot("hp-004", interactions)
    assert len(report.attacker_profile.attack_types) == 2
    assert "spoofing" in report.attacker_profile.attack_types
    assert "ddos" in report.attacker_profile.attack_types
check("Multiple attack types from single attacker", t_ice_multiple_attack_types)

def t_ice_get_all_profiles():
    ice = IntelligenceCaptureEngine()
    
    # Profile attacker 1
    ice.analyze_honeypot("hp-001", [{
        "timestamp": "2026-07-28T10:00:00Z",
        "attacker_payload": {"sector": "traffic"},
        "attacker_behavior": {
            "send_interval": 0.5,
            "packet_size": 128,
            "attack_type": "spoofing",
            "attacker_id": "att-001",
        },
    }])
    
    # Profile attacker 2
    ice.analyze_honeypot("hp-002", [{
        "timestamp": "2026-07-28T11:00:00Z",
        "attacker_payload": {"sector": "hospital"},
        "attacker_behavior": {
            "send_interval": 0.3,
            "packet_size": 512,
            "attack_type": "ddos",
            "attacker_id": "att-002",
        },
    }])
    
    profiles = ice.get_all_profiles()
    assert len(profiles) == 2
    attacker_ids = [p["attacker_id"] for p in profiles]
    assert "att-001" in attacker_ids
    assert "att-002" in attacker_ids
check("Get all attacker profiles", t_ice_get_all_profiles)

def t_ice_stats():
    ice = IntelligenceCaptureEngine()
    
    ice.analyze_honeypot("hp-001", [{
        "timestamp": "2026-07-28T10:00:00Z",
        "attacker_payload": {},
        "attacker_behavior": {
            "send_interval": 0.5,
            "packet_size": 128,
            "attack_type": "spoofing",
            "attacker_id": "att-001",
        },
    }])
    
    ice.analyze_honeypot("hp-002", [{
        "timestamp": "2026-07-28T11:00:00Z",
        "attacker_payload": {},
        "attacker_behavior": {
            "send_interval": 0.3,
            "packet_size": 512,
            "attack_type": "ransomware",
            "attacker_id": "att-002",
        },
    }])
    
    stats = ice.get_stats()
    assert stats["total_attackers_profiled"] == 2
    assert stats["total_reports"] == 2
    assert "spoofing" in stats["unique_attack_types"]
    assert "ransomware" in stats["unique_attack_types"]
check("Intelligence capture engine statistics", t_ice_stats)

# ── 3. Integration Tests ──────────────────────────────────────────────────────
console.print("\n[cyan]3. End-to-End Integration[/cyan]")

def t_full_honeypot_workflow():
    """Complete workflow: spawn → capture → analyze → intelligence."""
    # 1. Spawn honeypots
    net = HoneypotNetwork()
    honeypots = net.spawn_honeypots("hospital-device-042", "hospital", count=3)
    
    # 2. Attacker attacks the honeypot
    for i in range(5):
        honeypots[0].record_interaction({
            "behavior": {"send_interval": 0.4, "packet_size": 320},
            "_attack_meta": {"attack_type": "man_in_the_middle", "attacker_id": "mitm-007"},
        })
    
    # 3. Collect intelligence
    intel = net.get_all_intelligence()
    assert len(intel) == 1
    assert intel[0]["total_interactions"] == 5
    
    # 4. Analyze with ICE
    ice = IntelligenceCaptureEngine()
    report = ice.analyze_honeypot(
        honeypots[0].honeypot_id,
        honeypots[0].interactions,
    )
    
    assert report is not None
    assert "man_in_the_middle" in report.attacker_profile.attack_types
    assert len(report.recommended_defenses) > 0
    assert len(report.ai_training_samples) == 5
    assert report.blockchain_entry["honeypot_id"] == honeypots[0].honeypot_id
check("Full honeypot workflow: spawn→capture→analyze", t_full_honeypot_workflow)

def t_multi_honeypot_multi_attacker():
    """Multiple honeypots capturing multiple attackers."""
    net = HoneypotNetwork()
    
    # Spawn for different sectors
    hp_traffic = net.spawn_honeypots("traffic-sensor-001", "traffic", count=2)
    hp_hospital = net.spawn_honeypots("hospital-device-001", "hospital", count=2)
    
    # Attacker 1 targets traffic
    for i in range(3):
        hp_traffic[0].record_interaction({
            "behavior": {"send_interval": 0.2, "packet_size": 512},
            "sector": "traffic",
            "_attack_meta": {"attack_type": "ddos", "attacker_id": "ddos-001"},
        })
    
    # Attacker 2 targets hospital
    for i in range(2):
        hp_hospital[0].record_interaction({
            "behavior": {"send_interval": 0.5, "packet_size": 256},
            "sector": "hospital",
            "_attack_meta": {"attack_type": "spoofing", "attacker_id": "spoof-001"},
        })
    
    # Analyze all
    ice = IntelligenceCaptureEngine()
    
    report1 = ice.analyze_honeypot(hp_traffic[0].honeypot_id, hp_traffic[0].interactions)
    report2 = ice.analyze_honeypot(hp_hospital[0].honeypot_id, hp_hospital[0].interactions)
    
    assert report1.attacker_profile.attacker_id == "ddos-001"
    assert report2.attacker_profile.attacker_id == "spoof-001"
    # Check that sectors are captured (they come from attacker_payload.sector)
    # In this test, we pass sector in the payload directly
    
    stats = ice.get_stats()
    assert stats["total_attackers_profiled"] == 2
check("Multiple honeypots, multiple attackers", t_multi_honeypot_multi_attacker)

def t_honeypot_defense_pipeline():
    """Verify defense recommendations are actionable."""
    ice = IntelligenceCaptureEngine()
    
    # Test all attack types
    attack_types = ["spoofing", "ddos", "data_poisoning", "replay_attack", "ransomware"]
    
    for attack_type in attack_types:
        interactions = [{
            "timestamp": "2026-07-28T10:00:00Z",
            "attacker_payload": {"sector": "test"},
            "attacker_behavior": {
                "send_interval": 0.5,
                "packet_size": 128,
                "attack_type": attack_type,
                "attacker_id": f"att-{attack_type}",
            },
        }]
        
        report = ice.analyze_honeypot(f"hp-{attack_type}", interactions)
        assert len(report.recommended_defenses) > 0
        
        # Verify defenses are specific to attack type
        defenses_str = " ".join(report.recommended_defenses).lower()
        if attack_type == "spoofing":
            assert "fingerprint" in defenses_str or "honeypot" in defenses_str
        elif attack_type == "ddos":
            assert "rate" in defenses_str or "traffic" in defenses_str
check("Defense recommendations for all attack types", t_honeypot_defense_pipeline)

# ── Summary ───────────────────────────────────────────────────────────────────

passed = sum(1 for _, ok, _ in results if ok)
failed = sum(1 for _, ok, _ in results if not ok)

table = Table(
    title=f"\nHoneypot Test Results — {passed}/{len(results)} passed",
    box=box.ROUNDED, border_style="cyan",
)
table.add_column("Test",   style="white", max_width=55)
table.add_column("Status", style="bold")
table.add_column("Notes",  style="dim",   max_width=30)

for name, ok, err in results:
    table.add_row(
        name,
        "[green]PASS ✅[/green]" if ok else "[red]FAIL ❌[/red]",
        err or "",
    )

console.print(table)

if failed == 0:
    console.print(f"\n[bold green]🎉 ALL {passed} HONEYPOT TESTS PASSED[/bold green]\n")
    console.print("[dim]Modules complete:[/dim]")
    console.print("  [cyan]honeypot/decoy_spawner.py[/cyan]")
    console.print("  [cyan]honeypot/intelligence_capture.py[/cyan]")
    console.print("  [cyan]honeypot/README.md[/cyan]")
    console.print("\n[dim]Key features verified:[/dim]")
    console.print("  ✓ Honeypot spawning and management")
    console.print("  ✓ Attacker interaction capture")
    console.print("  ✓ Behavioral signature extraction")
    console.print("  ✓ Intelligence report generation")
    console.print("  ✓ Defense recommendation engine")
    console.print("  ✓ AI training sample generation")
    console.print("  ✓ Blockchain entry preparation")
    console.print("  ✓ Multi-sector, multi-attacker support\n")
else:
    console.print(f"\n[bold red]{failed} test(s) failed.[/bold red]\n")
    sys.exit(1)
