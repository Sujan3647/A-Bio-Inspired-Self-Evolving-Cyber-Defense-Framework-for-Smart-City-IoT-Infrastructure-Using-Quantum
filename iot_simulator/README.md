# ImmunoGrid — IoT City Simulator

> **500+ virtual smart city devices** — test security without risking a real city.

---

## Overview

Since we can't attack a real smart city to test security, we simulate one in Python.
500+ virtual devices send realistic data, and 6 attacker bots launch attacks
that the ImmunoGrid defense system must detect and stop.

---

## Structure

```
iot_simulator/
├── city_builder.py          Main simulator — spawns all devices
├── scenario_runner.py       Pre-defined attack scenarios
├── traffic_generator.py     Labeled ML training dataset generator
├── network_topology.py      Mesh network topology model
├── devices/
│   ├── base_device.py       Base class + behavioral fingerprint
│   ├── traffic_sensor.py    🚦 Road intersection sensors
│   ├── street_camera.py     🎥 Surveillance cameras
│   ├── water_monitor.py     💧 Pipeline pressure/quality monitors
│   ├── hospital_device.py   🏥 Medical equipment
│   ├── power_sensor.py      ⚡ Power grid sensors
│   ├── metro_sensor.py      🚇 Metro/transit sensors
│   ├── airport_device.py    ✈️  Airport security devices
│   └── govt_office_node.py  🏛️  Government network nodes
└── attackers/
    ├── base_attacker.py     Base attacker class
    ├── spoofer.py           Impersonation attacks
    ├── ddos_attacker.py     Flood attacks
    ├── data_poisoner.py     Fake sensor data injection
    ├── mitm_attacker.py     Message interception + modification
    ├── replay_attacker.py   Captured message replay
    └── ransomware_bot.py    Device lockdown attacks
```

---

## Quick Start

```bash
# Run virtual city (press Ctrl+C to stop)
python start.py sim

# Or directly
cd iot_simulator && python city_builder.py
```

---

## Device Types

| Device | Sector | Send Interval | Packet Size |
|---|---|---|---|
| TrafficSensor | traffic | 2.0s | 48 bytes |
| StreetCamera | surveillance | 1.5s | 96 bytes |
| WaterMonitor | water | 5.0s | 52 bytes |
| HospitalDevice | hospital | 3.0s | 72 bytes |
| PowerSensor | power | 1.0s | 56 bytes |
| MetroSensor | metro | 3.0s | 60 bytes |
| AirportDevice | airport | 4.0s | 80 bytes |
| GovtOfficeNode | government | 6.0s | 72 bytes |

---

## Creating Devices

```python
from iot_simulator.devices import TrafficSensor, HospitalDevice

# Create device
sensor = TrafficSensor(location="intersection-A1", sector="traffic")

# Get behavioral fingerprint (for quantum engine)
fp = sensor.get_fingerprint_vector()
# → {"send_interval": 2.347, "packet_size": 48, "cpu_usage": 0.142, ...}

# Build MQTT message
msg = sensor.build_message()
# → {"device_id": "...", "sector": "traffic", "data": {...}, "behavior": {...}}

# Run device loop (sends messages continuously)
import asyncio
asyncio.run(sensor.run(publish_callback=my_mqtt_publish))
```

---

## Attacker Simulators

```python
from iot_simulator.attackers import SpoofingAttacker, DDoSAttacker

spoofer = SpoofingAttacker()
event   = await spoofer.execute_attack(
    target_device_id="traffic-sensor-001",
    target_sector="traffic",
    publish_callback=bus.publish,
)
# event.detected → True/False
# event.success  → True/False
```

---

## Scenario Runner

```python
from iot_simulator.scenario_runner import ScenarioRunner

runner = ScenarioRunner(devices, publish_callback)

# Available scenarios
print(runner.get_scenario_list())
# "coordinated_spoofing", "ddos_hospital", "slow_poison",
# "ransomware_chain", "insider_threat", "full_city_assault"

result = await runner.run_scenario("full_city_assault")
# result.attacks_launched → 35
# result.attacks_detected → 32
# result.detection_rate   → 91.4%
```

---

## City Configuration

```python
CITY_CONFIG = {
    "traffic":    {"count": 100, "class": TrafficSensor},
    "camera":     {"count": 80,  "class": StreetCamera},
    "water":      {"count": 60,  "class": WaterMonitor},
    "hospital":   {"count": 80,  "class": HospitalDevice},
    "power":      {"count": 80,  "class": PowerSensor},
    "metro":      {"count": 50,  "class": MetroSensor},
    "airport":    {"count": 30,  "class": AirportDevice},
    "government": {"count": 20,  "class": GovtOfficeNode},
}
# Total: 500 devices
```

---

## Test Results

```
IoT Simulator tests (in test_integration.py):
  ✅ 8 device types build + fingerprint
  ✅ 6 attacker types
```
