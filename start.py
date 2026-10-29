"""
ImmunoGrid — Quick Start Script

Runs the IoT simulator + backend API + shows status.

Usage:
    python start.py           # Show available commands
    python start.py sim       # Run IoT city simulation
    python start.py quantum   # Run quantum engine demo
    python start.py attack    # Run quantum attack simulation
    python start.py demo      # Full system demo
"""

import sys
import subprocess
import os

ROOT = os.path.dirname(os.path.abspath(__file__))


def banner():
    print("""
╔══════════════════════════════════════════════════════════╗
║                    🛡️  IMMUNOGRID                        ║
║       Bio-Inspired Smart City Cyber Defense Platform      ║
║                                                          ║
║  Quantum Behavioral Fingerprinting                       ║
║  Federated Adversarial Consciousness                     ║
║  Morphogenetic Blockchain                                ║
╚══════════════════════════════════════════════════════════╝
""")


def run_simulator():
    print("🏙️  Starting IoT City Simulator (500+ devices)...")
    print("   Press Ctrl+C to stop\n")
    subprocess.run([sys.executable, "city_builder.py"], cwd=os.path.join(ROOT, "iot_simulator"))


def run_quantum_demo():
    print("⚛️  Running Quantum Fingerprint Demo...")
    demo_code = """
import sys
sys.path.insert(0, r'{root}')
from quantum_engine.fingerprint_gen import QuantumFingerprintEngine

engine = QuantumFingerprintEngine(num_qubits=4)

# Register a device
behavior = {{
    "send_interval": 2.347,
    "packet_size": 48.0,
    "timing_jitter": 0.8,
    "size_variance": 2.0,
    "cpu_usage": 0.142,
    "active_start": 6.0,
    "active_end": 22.0,
}}
fp = engine.register_device("traffic-sensor-0001", behavior)
print(f"✅ Device registered. Fingerprint hash: {{fp.behavior_hash[:16]}}...")

# Verify real device
result = engine.verify_device("traffic-sensor-0001", behavior)
print(f"🛡️  Real device check: {{result.verdict}} (fidelity: {{result.fidelity_score:.4f}})")

# Verify impostor (slightly different behavior)
impostor_behavior = dict(behavior)
impostor_behavior["send_interval"] = 2.5   # Off by 0.15s
impostor_behavior["packet_size"] = 60.0    # Wrong size
result2 = engine.verify_device("traffic-sensor-0001", impostor_behavior)
print(f"🚨 Impostor check: {{result2.verdict}} (fidelity: {{result2.fidelity_score:.4f}})")

print(f"\\n📊 Engine Stats: {{engine.get_stats()}}")
""".format(root=ROOT)
    subprocess.run([sys.executable, "-c", demo_code])


def run_attack_demo():
    print("⚔️  Running Quantum Attack Simulation...")
    demo_code = """
import sys
sys.path.insert(0, r'{root}')
from quantum_engine.attack_simulator import QuantumAttackSimulator

sim = QuantumAttackSimulator()

print("\\n🔬 Simulating Grover's Attack on AES-128...")
r1 = sim.simulate_grover_attack(128)
print(f"   Result: {{r1.attack_name}} on {{r1.target_algorithm}}")
print(f"   Classical time: {{r1.classical_time_years:.2e}} years")
print(f"   Quantum time:   {{r1.quantum_time_seconds:.0f}} seconds")
print(f"   Vulnerable: {{r1.attack_success}}")

print("\\n🔬 Simulating Shor's Attack on RSA-2048...")
r2 = sim.simulate_shor_attack(2048)
print(f"   Result: {{r2.attack_name}} on {{r2.target_algorithm}}")
print(f"   Classical time: {{r2.classical_time_years:.2e}} years")
print(f"   Quantum time:   {{r2.quantum_time_seconds/3600:.1f}} hours")
print(f"   Vulnerable: {{r2.attack_success}}")

print("\\n✅ PQC Resistance Test...")
pqc = sim.test_pqc_resistance()
for alg, info in pqc.items():
    print(f"   {{alg}}: {{info['status']}}")
""".format(root=ROOT)
    subprocess.run([sys.executable, "-c", demo_code])


def run_demo():
    banner()
    print("Running full system demo...\n")
    run_quantum_demo()
    print()
    run_attack_demo()


COMMANDS = {
    "sim":     (run_simulator,    "Run IoT City Simulation (500+ devices)"),
    "quantum": (run_quantum_demo, "Demo Quantum Behavioral Fingerprinting"),
    "attack":  (run_attack_demo,  "Demo Quantum Attack Simulation"),
    "demo":    (run_demo,         "Full system demo"),
}

if __name__ == "__main__":
    banner()

    cmd = sys.argv[1] if len(sys.argv) > 1 else None

    if cmd in COMMANDS:
        COMMANDS[cmd][0]()
    else:
        print("Available commands:\n")
        for name, (_, desc) in COMMANDS.items():
            print(f"  python start.py {name:<10} — {desc}")
        print()
        print("Backend API:")
        print("  cd backend && uvicorn main:app --reload --port 8000")
        print()
        print("Frontend:")
        print("  cd frontend && npm install && npm run dev")
        print()
        print("Docker (full stack):")
        print("  cd backend && docker-compose up")
