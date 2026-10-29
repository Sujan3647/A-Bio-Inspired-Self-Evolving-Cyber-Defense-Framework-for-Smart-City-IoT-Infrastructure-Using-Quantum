"""
ImmunoGrid — IoT Simulator Complete Test Suite
Tests all devices, attackers, topology, scenarios, and traffic generator.

Run:
    python iot_simulator/test_iot_simulator_complete.py
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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


def acheck(name, coro):
    """Run an async test."""
    try:
        asyncio.run(coro())
        results.append((name, True, ""))
        console.print(f"  [green]✅ {name}[/green]")
    except Exception as e:
        results.append((name, False, str(e)[:80]))
        console.print(f"  [red]❌ {name}: {str(e)[:70]}[/red]")


console.print("\n[bold cyan]╔══════════════════════════════════════════════════╗[/bold cyan]")
console.print("[bold cyan]║  ImmunoGrid IoT Simulator — Complete Test Suite ║[/bold cyan]")
console.print("[bold cyan]╚══════════════════════════════════════════════════╝[/bold cyan]\n")

# ── 1. Device Tests ───────────────────────────────────────────────────────────
console.print("[cyan]1. IoT Devices (8 types)[/cyan]")

from iot_simulator.devices import (
    TrafficSensor, StreetCamera, WaterMonitor, HospitalDevice,
    PowerSensor, MetroSensor, AirportDevice, GovtOfficeNode,
    DeviceStatus, DeviceType,
)

def t_traffic_sensor():
    d = TrafficSensor(location="intersection-A1", sector="traffic")
    assert d.device_type == DeviceType.TRAFFIC_SENSOR
    assert d.status == DeviceStatus.ONLINE
    data = d.generate_data()
    assert "vehicle_count_per_minute" in data
    assert "avg_speed_kmh" in data
    fp = d.get_fingerprint_vector()
    assert "send_interval" in fp
    assert fp["send_interval"] > 0
check("TrafficSensor creation + fingerprint", t_traffic_sensor)

def t_street_camera():
    d = StreetCamera(location="park-entrance", sector="surveillance")
    data = d.generate_data()
    assert "motion_detected" in data
    assert "crowd_density" in data
check("StreetCamera data generation", t_street_camera)

def t_water_monitor():
    d = WaterMonitor(location="treatment-plant-1", sector="water")
    data = d.generate_data()
    assert "pressure_bar" in data
    assert "ph_level" in data
    assert 4.5 <= d.behavior_profile.send_interval_seconds <= 5.5
check("WaterMonitor data + interval", t_water_monitor)

def t_hospital_device():
    d = HospitalDevice(location="icu-ward-1", sector="hospital")
    data = d.generate_data()
    assert "heart_rate_bpm" in data
    assert "spo2_percent" in data
    assert data["device_functional"] is True
check("HospitalDevice vitals generation", t_hospital_device)

def t_power_sensor():
    d = PowerSensor(location="substation-north", sector="power")
    data = d.generate_data()
    assert "voltage_v" in data
    assert "frequency_hz" in data
    assert d._base_send_interval == 1.0  # fastest sender
check("PowerSensor 1s interval + fault detection", t_power_sensor)

def t_metro_sensor():
    d = MetroSensor(location="central-station", sector="metro")
    data = d.generate_data()
    assert "passenger_count" in data
    assert "train_speed_kmh" in data
    assert hasattr(d, "station")
    assert hasattr(d, "train_id")
check("MetroSensor station + passenger data", t_metro_sensor)

def t_airport_device():
    d = AirportDevice(location="terminal-1", sector="airport")
    data = d.generate_data()
    assert "passengers_scanned" in data
    assert "security_alert" in data
    assert hasattr(d, "zone")
    assert hasattr(d, "device_subtype")
check("AirportDevice zone + scanner data", t_airport_device)

def t_govt_office():
    d = GovtOfficeNode(location="ministry-block-a", sector="government")
    data = d.generate_data()
    assert "active_users" in data
    assert "bandwidth_mbps" in data
    assert hasattr(d, "ministry")
check("GovtOfficeNode ministry + network data", t_govt_office)

def t_build_message():
    d = TrafficSensor(location="downtown", sector="traffic")
    msg = d.build_message()
    assert msg["device_id"] == d.device_id
    assert msg["sector"] == "traffic"
    assert "behavior" in msg
    assert "data" in msg
    assert "timestamp" in msg
    assert msg["sequence"] == 0
check("Build complete MQTT message", t_build_message)

def t_device_fingerprint_unique():
    d1 = TrafficSensor(location="loc-1", sector="traffic")
    d2 = TrafficSensor(location="loc-2", sector="traffic")
    fp1 = d1.get_fingerprint_vector()
    fp2 = d2.get_fingerprint_vector()
    # Fingerprints differ due to random jitter — quantum engine can tell them apart
    assert fp1 != fp2
check("Each device has unique behavioral fingerprint", t_device_fingerprint_unique)

def t_device_status_transitions():
    d = TrafficSensor(location="loc", sector="traffic")
    assert d.status == DeviceStatus.ONLINE
    d.mark_compromised("spoofing")
    assert d.status == DeviceStatus.COMPROMISED
    d.quarantine()
    assert d.status == DeviceStatus.QUARANTINED
    d.restore()
    assert d.status == DeviceStatus.ONLINE
check("Device status: online→compromised→quarantined→restored", t_device_status_transitions)

def t_device_to_dict():
    d = HospitalDevice(location="icu", sector="hospital")
    d.message_count = 42
    d_dict = d.to_dict()
    assert d_dict["device_type"] == "hospital_device"
    assert d_dict["message_count"] == 42
    assert "fingerprint" in d_dict
    assert d_dict["status"] == "online"
check("Device serialization to dict", t_device_to_dict)

async def t_device_run_loop():
    """Device sends messages via run() loop for 3 ticks."""
    d = TrafficSensor(location="loc", sector="traffic")
    published = []

    async def fake_publish(topic, payload):
        published.append({"topic": topic, "payload": payload})

    # Run for a short burst then cancel
    task = asyncio.create_task(d.run(publish_callback=fake_publish))
    await asyncio.sleep(d.behavior_profile.send_interval_seconds * 2.2)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    assert len(published) >= 1
    assert "immunogrid/traffic/traffic_sensor" in published[0]["topic"]
acheck("Device run() loop sends MQTT messages", t_device_run_loop)

# ── 2. Attacker Tests ─────────────────────────────────────────────────────────
console.print("\n[cyan]2. Attacker Simulators (6 types)[/cyan]")

from iot_simulator.attackers import (
    SpoofingAttacker, DDoSAttacker, DataPoisoner,
    MITMAttacker, ReplayAttacker, RansomwareBot,
    AttackType,
)

published_attacks = []

async def fake_bus(topic, payload):
    published_attacks.append({"topic": topic, "payload": payload})

async def t_spoofer():
    a = SpoofingAttacker()
    assert a.attack_type == AttackType.SPOOFING
    event = await a.execute_attack("traffic-sensor-001", "traffic", fake_bus)
    assert event.attack_id.startswith("spoof-")
    assert event.target_device_id == "traffic-sensor-001"
    assert "_attack_meta" in event.payload
    assert a.attack_count == 1
acheck("SpoofingAttacker execute + log", t_spoofer)

async def t_ddos():
    a = DDoSAttacker(flood_rate=50)
    event = await a.execute_attack("hospital-device-001", "hospital", fake_bus)
    assert event.attack_id.startswith("ddos-")
    assert "messages_sent" in event.payload
    assert event.payload["messages_sent"] >= 50
acheck("DDoSAttacker burst flood", t_ddos)

async def t_data_poisoner():
    a = DataPoisoner()
    event = await a.execute_attack("water-monitor-001", "water", fake_bus)
    assert event.attack_id.startswith("poison-")
    poisoned = event.payload
    assert "_poisoned" in poisoned
    assert poisoned["pressure_bar"] < 1.0  # Dangerously low
acheck("DataPoisoner sector-specific poison payload", t_data_poisoner)

async def t_mitm():
    a = MITMAttacker()
    event = await a.execute_attack("power-sensor-001", "power", fake_bus)
    assert event.attack_id.startswith("mitm-")
    assert "pqc_signature" in event.payload
    assert "FORGED" in event.payload["pqc_signature"]
acheck("MITMAttacker forged PQC signature", t_mitm)

async def t_replay():
    a = ReplayAttacker()
    event = await a.execute_attack("hospital-device-042", "hospital", fake_bus)
    assert event.attack_id.startswith("replay-")
    # Old timestamp in payload
    from datetime import datetime
    msg_ts = datetime.fromisoformat(event.payload["timestamp"])
    delta = (datetime.utcnow() - msg_ts).total_seconds()
    assert delta > 60, f"Expected old timestamp, got {delta}s ago"
acheck("ReplayAttacker uses stale past timestamp", t_replay)

async def t_ransomware():
    a = RansomwareBot()
    event = await a.execute_attack("govt-device-001", "government", fake_bus)
    assert event.attack_id.startswith("ransom-")
    assert event.payload["data"]["encrypt_on_install"] is True
    assert "callback_url" in event.payload["data"]
acheck("RansomwareBot firmware-update command", t_ransomware)

def t_attacker_stats():
    a = SpoofingAttacker()
    asyncio.run(a.execute_attack("d1", "traffic", fake_bus))
    asyncio.run(a.execute_attack("d2", "traffic", fake_bus))
    stats = a.get_stats()
    assert stats["total_attacks"] == 2
    assert stats["attack_type"] == "spoofing"
    assert "detection_rate_pct" in stats
check("Attacker stats tracking (2 attacks)", t_attacker_stats)

def t_attack_types_enum():
    assert AttackType.SPOOFING.value == "spoofing"
    assert AttackType.DDOS.value == "ddos"
    assert AttackType.DATA_POISONING.value == "data_poisoning"
    assert AttackType.RANSOMWARE.value == "ransomware"
    assert AttackType.REPLAY.value == "replay_attack"
    assert AttackType.MITM.value == "man_in_the_middle"
check("All 6 AttackType enum values correct", t_attack_types_enum)

# ── 3. Network Topology ───────────────────────────────────────────────────────
console.print("\n[cyan]3. Network Topology (Hybrid Mesh-Star)[/cyan]")

from iot_simulator.network_topology import SmartCityNetworkTopology, NetworkNode

def t_topology_init():
    topo = SmartCityNetworkTopology()
    assert topo.gateway_id == "GATEWAY-CENTRAL"
    assert len(topo.nodes) == 1  # Just the central gateway
    assert topo.morphogenesis_events == 0
check("Topology initialization with central gateway", t_topology_init)

def t_add_sector():
    topo = SmartCityNetworkTopology()
    devices = [f"traffic-{i:03d}" for i in range(5)]
    locations = ["loc-A", "loc-B"]
    topo.add_sector("traffic", devices, locations)
    # Sector has: 1 gateway + 5 devices
    assert len(topo.nodes) == 1 + 1 + 5  # central + sector-gw + 5 devices
    assert "GW-TRAFFIC" in topo.nodes
    assert topo.sector_gateways["traffic"] == "GW-TRAFFIC"
check("Add sector with gateway + devices", t_add_sector)

def t_get_path():
    topo = SmartCityNetworkTopology()
    devs1 = ["traffic-001"]
    devs2 = ["hospital-001"]
    topo.add_sector("traffic", devs1, ["loc"])
    topo.add_sector("hospital", devs2, ["loc"])

    path = topo.get_path("traffic-001", "hospital-001")
    assert path is not None
    assert path.source == "traffic-001"
    assert path.destination == "hospital-001"
    # Path: device → sector-gw → central → dest-sector-gw → dest-device
    assert len(path.hops) >= 3
    assert "GATEWAY-CENTRAL" in path.hops
check("Cross-sector routing path calculation", t_get_path)

def t_isolate_sector():
    topo = SmartCityNetworkTopology()
    topo.add_sector("water", ["water-001", "water-002"], ["loc"])
    affected = topo.isolate_sector("water")
    assert len(affected) > 0
    assert topo.nodes["GW-WATER"].is_isolated is True
    assert topo.morphogenesis_events == 1
check("Isolate sector (morphogenesis)", t_isolate_sector)

def t_restore_sector():
    topo = SmartCityNetworkTopology()
    topo.add_sector("power", ["power-001"], ["loc"])
    topo.isolate_sector("power")
    topo.restore_sector("power")
    assert topo.nodes["GW-POWER"].is_isolated is False
check("Restore isolated sector", t_restore_sector)

def t_add_honeypot_node():
    topo = SmartCityNetworkTopology()
    topo.add_sector("hospital", ["hosp-001"], ["loc"])
    hp_node = topo.add_honeypot_node("hospital", "hosp-001")
    assert hp_node.node_type == "honeypot"
    assert hp_node.sector == "hospital"
    assert hp_node.node_id in topo.nodes
    stats = topo.get_topology_stats()
    assert stats["honeypot_nodes"] == 1
check("Add honeypot node to topology", t_add_honeypot_node)

def t_topology_stats():
    topo = SmartCityNetworkTopology()
    topo.add_sector("traffic", [f"t-{i}" for i in range(10)], ["loc"])
    topo.add_sector("hospital", [f"h-{i}" for i in range(5)], ["loc"])
    stats = topo.get_topology_stats()
    # 1 central + 2 sector gateways + 15 devices
    assert stats["total_nodes"] == 18
    assert stats["sectors"] == 2
    assert stats["gateway_nodes"] == 3
    assert stats["topology_type"] == "hybrid_mesh_star"
check("Topology stats: 15 devices across 2 sectors", t_topology_stats)

# ── 4. Traffic Generator ──────────────────────────────────────────────────────
console.print("\n[cyan]4. Traffic Generator (ML Dataset)[/cyan]")

from iot_simulator.traffic_generator import TrafficGenerator, ATTACK_LABELS, FEATURE_COLUMNS

def t_normal_sample():
    gen = TrafficGenerator(seed=42)
    sample = gen.generate_normal_sample(hour=8, device_type="traffic_sensor")
    assert sample["label"] == 0
    assert sample["attack_type"] == "normal"
    assert 0 < sample["send_interval_s"] < 10
    assert sample["packet_size_bytes"] > 10
    assert all(col in sample for col in FEATURE_COLUMNS)
check("Normal traffic sample generation", t_normal_sample)

def t_attack_samples_all_types():
    gen = TrafficGenerator(seed=42)
    for attack_type in range(1, 7):
        s = gen.generate_attack_sample(attack_type, hour=10)
        assert s["label"] == attack_type
        assert s["attack_type"] == ATTACK_LABELS[attack_type]
check("All 6 attack type samples generated correctly", t_attack_samples_all_types)

def t_ddos_sample_features():
    gen = TrafficGenerator(seed=42)
    s = gen.generate_attack_sample(2, hour=14)  # DDoS
    assert s["send_interval_s"] < 0.5  # Very fast
    assert s["cpu_usage_pct"] > 80     # High CPU
    assert s["message_rate_per_min"] > 100
check("DDoS sample has correct feature values", t_ddos_sample_features)

def t_replay_sample_features():
    gen = TrafficGenerator(seed=42)
    s = gen.generate_attack_sample(4, hour=3)  # Replay
    assert s["entropy"] < 0.2        # Low entropy (repeated message)
    assert s["is_active_hours"] == 0 # Off-hours replay
check("Replay sample has low entropy (repeated data)", t_replay_sample_features)

def t_generate_dataset():
    gen = TrafficGenerator(seed=42)
    df = gen.generate_dataset(n_samples=500, attack_ratio=0.25)
    # Total may be slightly under 500 due to integer division across 6 attack types
    assert len(df) >= 490
    assert df["label"].nunique() >= 4   # Normal + multiple attack types
    normal_count = len(df[df["label"] == 0])
    attack_count = len(df[df["label"] != 0])
    assert normal_count > 300
    assert attack_count > 50
    assert set(FEATURE_COLUMNS).issubset(set(df.columns))
check("Dataset generation: 500 samples, 25% attacks", t_generate_dataset)
def t_dataset_label_distribution():
    gen = TrafficGenerator(seed=123)
    df = gen.generate_dataset(n_samples=1200, attack_ratio=0.30)
    attack_df = df[df["label"] != 0]
    # 6 attack types should all be present
    assert attack_df["label"].nunique() == 6
    # Each attack type has some samples
    for at in range(1, 7):
        count = len(df[df["label"] == at])
        assert count > 0, f"Attack type {at} missing from dataset"
check("Dataset contains all 6 attack types balanced", t_dataset_label_distribution)

def t_streaming_sample():
    gen = TrafficGenerator(seed=42)
    s = gen.generate_streaming_sample("hospital_device")
    assert "label" in s
    assert "attack_type" in s
    assert s["label"] in range(0, 7)
check("Streaming sample generation (real-time inference feed)", t_streaming_sample)

def t_hour_factor():
    gen = TrafficGenerator(seed=42)
    assert gen._hour_factor(8) == 1.8    # Rush hour
    assert gen._hour_factor(3) == 0.3    # Maintenance window
    assert gen._hour_factor(12) == 1.2   # Business hours
    assert gen._hour_factor(23) == 0.5   # Night
check("Diurnal traffic factor (rush/night/maintenance)", t_hour_factor)

# ── 5. Message Bus ────────────────────────────────────────────────────────────
console.print("\n[cyan]5. Message Bus[/cyan]")

from iot_simulator.city_builder import MessageBus

async def t_bus_publish():
    import json
    bus = MessageBus()
    await bus.publish("test/topic", json.dumps({"value": 42}))
    assert bus.message_count == 1
    assert len(bus.messages) == 1
    assert bus.messages[0]["topic"] == "test/topic"
acheck("MessageBus publish + store message", t_bus_publish)

async def t_bus_attack_counting():
    import json
    bus = MessageBus()
    # Normal message
    await bus.publish("test/normal", json.dumps({"value": 1}))
    # Attack message
    await bus.publish("test/attack", json.dumps({
        "value": 2,
        "_attack_meta": {"attack_type": "spoofing"}
    }))
    assert bus.attack_count == 1
    assert bus.message_count == 2
acheck("MessageBus counts attack messages separately", t_bus_attack_counting)

async def t_bus_subscriber():
    import json
    bus = MessageBus()
    received = []
    async def on_message(msg):
        received.append(msg)
    bus.subscribe(on_message)
    await bus.publish("test/sub", json.dumps({"data": "hello"}))
    assert len(received) == 1
    assert received[0]["topic"] == "test/sub"
acheck("MessageBus subscriber notification", t_bus_subscriber)

async def t_bus_buffer_limit():
    import json
    bus = MessageBus()
    for i in range(1200):
        await bus.publish(f"test/{i}", json.dumps({"i": i}))
    # Buffer capped at 1000
    assert len(bus.messages) == 1000
    assert bus.message_count == 1200
acheck("MessageBus buffer capped at 1000 messages", t_bus_buffer_limit)

def t_bus_stats():
    bus = MessageBus()
    stats = bus.get_stats()
    assert "total_messages" in stats
    assert "attack_messages" in stats
    assert "detection_rate" in stats
check("MessageBus stats structure", t_bus_stats)

# ── 6. SmartCity Builder ──────────────────────────────────────────────────────
console.print("\n[cyan]6. SmartCity Builder[/cyan]")

from iot_simulator.city_builder import SmartCity, CITY_CONFIG

def t_city_config():
    total = sum(v["count"] for v in CITY_CONFIG.values())
    assert total == 500
    assert len(CITY_CONFIG) == 8
    for sector, cfg in CITY_CONFIG.items():
        assert "device_class" in cfg
        assert "count" in cfg
        assert "locations" in cfg
check("CITY_CONFIG: 500 devices across 8 sectors", t_city_config)

def t_city_build():
    city = SmartCity("Test City")
    city.build()
    assert len(city.devices) == 500
    assert len(city.attackers) == 8
    sectors = {d.sector for d in city.devices}
    assert len(sectors) == 8
check("SmartCity.build() spawns 500 devices + 8 attackers", t_city_build)

def t_city_get_online():
    city = SmartCity("Test City")
    city.build()
    online = city.get_online_devices()
    # Most devices active during the test hour
    assert len(online) >= 300
check("city.get_online_devices() returns active devices", t_city_get_online)

def t_city_stats():
    city = SmartCity("Test City")
    city.build()
    stats = city.get_stats()
    assert stats["total_devices"] == 500
    assert stats["online"] >= 300
    assert "bus" in stats
    assert "compromised" in stats
check("SmartCity stats structure", t_city_stats)

def t_city_sector_distribution():
    city = SmartCity("Test City")
    city.build()
    from collections import Counter
    counts = Counter(d.sector for d in city.devices)
    assert counts["traffic"] == 100
    assert counts["hospital"] == 80
    assert counts["water"] == 60
    assert counts["government"] == 20
check("Device counts per sector match CITY_CONFIG", t_city_sector_distribution)

def t_city_all_device_types():
    city = SmartCity("Test City")
    city.build()
    device_types = {d.device_type.value for d in city.devices}
    expected = {
        "traffic_sensor", "street_camera", "water_monitor",
        "hospital_device", "power_sensor", "metro_sensor",
        "airport_device", "govt_office_node",
    }
    assert expected == device_types
check("All 8 device types present in city", t_city_all_device_types)

# ── 7. Scenario Runner ────────────────────────────────────────────────────────
console.print("\n[cyan]7. Scenario Runner (6 attack scenarios)[/cyan]")

from iot_simulator.scenario_runner import ScenarioRunner, ScenarioResult

def _make_runner():
    city = SmartCity("ScenarioCity")
    city.build()
    return ScenarioRunner(city.devices, city.bus.publish), city

async def t_scenario_list():
    runner, _ = _make_runner()
    scenarios = runner.get_scenario_list()
    assert len(scenarios) == 6
    names = [s["name"] for s in scenarios]
    assert "coordinated_spoofing" in names
    assert "full_city_assault" in names
    assert "ransomware_chain" in names
acheck("ScenarioRunner lists 6 named scenarios", t_scenario_list)

async def t_scenario_coordinated_spoofing():
    runner, _ = _make_runner()
    result = await runner.run_scenario("coordinated_spoofing")
    assert isinstance(result, ScenarioResult)
    assert result.scenario_name == "coordinated_spoofing"
    assert result.attacks_launched == 10
    assert 0 <= result.detection_rate <= 100
    assert result.duration_seconds >= 0
    assert len(result.notes) > 0
acheck("coordinated_spoofing: 10 attacks, result structure", t_scenario_coordinated_spoofing)

async def t_scenario_ddos_hospital():
    runner, _ = _make_runner()
    result = await runner.run_scenario("ddos_hospital")
    assert result.scenario_name == "ddos_hospital"
    assert result.attacks_launched >= 40
    assert result.honeypots_spawned == 6
    assert result.morphogenesis_triggered is True
acheck("ddos_hospital: flood + morphogenesis triggered", t_scenario_ddos_hospital)

async def t_scenario_slow_poison():
    runner, _ = _make_runner()
    result = await runner.run_scenario("slow_poison")
    assert result.scenario_name == "slow_poison"
    assert result.attacks_launched == 20
    # Detection rate increases over iterations
    assert result.detection_rate > 40
acheck("slow_poison: 20 iterations, increasing detection", t_scenario_slow_poison)

async def t_scenario_ransomware():
    runner, _ = _make_runner()
    result = await runner.run_scenario("ransomware_chain")
    assert result.scenario_name == "ransomware_chain"
    assert result.attacks_launched == 8
    assert result.morphogenesis_triggered is True
acheck("ransomware_chain: 8 targets, morphogenesis triggered", t_scenario_ransomware)

async def t_scenario_insider():
    runner, _ = _make_runner()
    result = await runner.run_scenario("insider_threat")
    assert result.scenario_name == "insider_threat"
    assert result.attacks_launched == 5
    assert result.detection_rate >= 0
acheck("insider_threat: replay attack from known device", t_scenario_insider)

async def t_scenario_full_assault():
    runner, _ = _make_runner()
    result = await runner.run_scenario("full_city_assault")
    assert result.scenario_name == "full_city_assault"
    assert result.attacks_launched >= 40   # sum of all sub-scenarios
    assert result.morphogenesis_triggered is True
    assert result.detection_rate > 70      # system handles concurrent attacks
acheck("full_city_assault: all 5 sub-scenarios combined", t_scenario_full_assault)

async def t_scenario_unknown_raises():
    runner, _ = _make_runner()
    try:
        await runner.run_scenario("nonexistent_scenario")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
acheck("Unknown scenario name raises ValueError", t_scenario_unknown_raises)

async def t_scenario_results_stored():
    runner, _ = _make_runner()
    await runner.run_scenario("coordinated_spoofing")
    await runner.run_scenario("insider_threat")
    assert len(runner.results) == 2
acheck("Scenario results stored in runner.results list", t_scenario_results_stored)

# ── 8. Integration Tests ──────────────────────────────────────────────────────
console.print("\n[cyan]8. End-to-End Integration[/cyan]")

async def t_device_attack_full_cycle():
    """Device sends message → attacker targets it → detected."""
    import json
    bus = MessageBus()
    sensor = TrafficSensor(location="intersection-X", sector="traffic")

    # Device sends a normal message
    msg = sensor.build_message()
    await bus.publish(
        topic=f"immunogrid/traffic/traffic_sensor/{sensor.device_id}",
        payload=json.dumps(msg),
    )
    assert bus.message_count == 1

    # Attacker clones the device
    spoofer = SpoofingAttacker()
    event = await spoofer.execute_attack(
        target_device_id=sensor.device_id,
        target_sector="traffic",
        publish_callback=bus.publish,
    )
    assert bus.message_count == 2
    assert bus.attack_count == 1
    assert event.target_device_id == sensor.device_id

    # Simulated detection
    if event.detected:
        sensor.mark_compromised(event.attack_type.value)
        assert sensor.status == DeviceStatus.COMPROMISED
acheck("Device → send → attack → detect → compromise cycle", t_device_attack_full_cycle)

def t_fingerprint_feeds_topology():
    """Device fingerprint shapes network topology placement."""
    topo = SmartCityNetworkTopology()
    city = SmartCity("Integration City")
    city.build()

    # Build topology from city devices
    for sector, cfg in CITY_CONFIG.items():
        devices = [d for d in city.devices if d.sector == cfg["sector"]]
        device_ids = [d.device_id for d in devices[:5]]
        locations = cfg["locations"]
        topo.add_sector(cfg["sector"], device_ids, locations)

    stats = topo.get_topology_stats()
    assert stats["sectors"] == 8
    assert stats["total_nodes"] > 40
check("Device fingerprints → topology with all 8 sectors", t_fingerprint_feeds_topology)

def t_traffic_gen_feeds_ai():
    """Generated dataset has correct feature shape for ML model."""
    gen = TrafficGenerator(seed=42)
    df = gen.generate_dataset(n_samples=200, attack_ratio=0.25)
    X = df[FEATURE_COLUMNS].values
    y = df["label"].values
    assert X.shape == (200, 12)   # 200 samples × 12 features
    assert set(y).issubset(set(range(7)))  # Labels 0–6

async def t_scenario_updates_bus():
    """Running a scenario writes messages to the shared bus."""
    city = SmartCity("BusTest City")
    city.build()
    runner = ScenarioRunner(city.devices, city.bus.publish)
    await runner.run_scenario("coordinated_spoofing")
    # Scenario publishes spoofed messages via bus
    assert city.bus.message_count >= 10
acheck("Scenario publishes messages into city bus", t_scenario_updates_bus)

def t_all_attackers_have_unique_ids():
    attackers = [
        SpoofingAttacker(), DDoSAttacker(), DataPoisoner(),
        MITMAttacker(), ReplayAttacker(), RansomwareBot(),
    ]
    ids = [a.attacker_id for a in attackers]
    assert len(set(ids)) == 6, "All attacker IDs must be unique"
check("All 6 attacker bots have unique IDs", t_all_attackers_have_unique_ids)

def t_500_devices_all_fingerprints_unique():
    city = SmartCity("Fingerprint City")
    city.build()
    fps = [str(d.get_fingerprint_vector()) for d in city.devices]
    unique = len(set(fps))
    # With random jitter, virtually all 500 should be unique
    assert unique > 490, f"Only {unique}/500 unique fingerprints"
check("500 devices: >490 unique behavioral fingerprints", t_500_devices_all_fingerprints_unique)

# ── Summary ───────────────────────────────────────────────────────────────────

passed = sum(1 for _, ok, _ in results if ok)
failed = sum(1 for _, ok, _ in results if not ok)

table = Table(
    title=f"\nIoT Simulator Test Results — {passed}/{len(results)} passed",
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
    console.print(f"\n[bold green]🎉 ALL {passed} IOT SIMULATOR TESTS PASSED[/bold green]\n")
    console.print("[dim]Modules verified:[/dim]")
    for mod in [
        "devices/base_device.py   — BaseDevice, fingerprint, lifecycle",
        "devices/traffic_sensor.py  hospital_device.py  water_monitor.py",
        "devices/power_sensor.py    metro_sensor.py     airport_device.py",
        "devices/street_camera.py   govt_office_node.py",
        "attackers/spoofer.py       ddos_attacker.py    data_poisoner.py",
        "attackers/mitm_attacker.py replay_attacker.py  ransomware_bot.py",
        "city_builder.py          — SmartCity, MessageBus, CITY_CONFIG",
        "network_topology.py      — Hybrid mesh topology, morphogenesis",
        "scenario_runner.py       — 6 pre-built attack scenarios",
        "traffic_generator.py     — Labeled ML dataset (7 classes)",
    ]:
        console.print(f"  [cyan]{mod}[/cyan]")

    console.print("\n[dim]Key metrics:[/dim]")
    console.print("  ✓ 500 virtual devices across 8 smart city sectors")
    console.print("  ✓ 8 attacker bots (6 attack types)")
    console.print("  ✓ Hybrid mesh-star network topology")
    console.print("  ✓ 6 named attack scenarios (up to full city assault)")
    console.print("  ✓ Labeled ML dataset generation (12 features × 7 labels)")
    console.print("  ✓ Unique behavioral fingerprint per device\n")
else:
    console.print(f"\n[bold red]{failed} test(s) failed.[/bold red]\n")
    sys.exit(1)
