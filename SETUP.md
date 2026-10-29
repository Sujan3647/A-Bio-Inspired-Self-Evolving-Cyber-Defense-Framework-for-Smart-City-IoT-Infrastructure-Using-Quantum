# ImmunoGrid — Complete Setup Guide

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.11+ | python.org |
| Node.js | 20+ | nodejs.org |
| Docker | 29+ | docker.com |
| Git | Any | git-scm.com |

---

## 1. Clone & Setup Python Environment

```bash
git clone <repo-url>
cd immunogrid

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install all Python dependencies
pip install -r requirements.txt
```

---

## 2. Environment Variables

```bash
# Copy the example file
copy .env.example .env       # Windows
cp .env.example .env         # Linux/Mac

# Edit .env with your values
# Minimum required for local dev:
#   APP_SECRET_KEY  — any random string
#   JWT_SECRET_KEY  — any random string
```

---

## 3. Run Integration Tests

```bash
python test_integration.py
# Expected: 15/15 PASS (3 skipped if torch is blocked by system policy)
```

---

## 4. Start Backend API

```bash
cd backend
uvicorn main:app --reload --port 8000

# API docs: http://localhost:8000/api/docs
# Health:   http://localhost:8000/api/health
```

---

## 5. Start Frontend

```bash
cd frontend
npm install
npm run dev

# App: http://localhost:3000
```

**Demo Login Accounts:**

| Email | Password | Role |
|-------|----------|------|
| admin@immunogrid.gov | Admin@123 | Super Admin |
| security@immunogrid.gov | Security@123 | National Security Officer |
| traffic@immunogrid.gov | Traffic@123 | Traffic Ministry |
| hospital@immunogrid.gov | Health@123 | Health Ministry |
| water@immunogrid.gov | Water@123 | Water Authority |
| energy@immunogrid.gov | Energy@123 | Energy Ministry |
| quantum@immunogrid.gov | Quantum@123 | Quantum Analyst |
| auditor@immunogrid.gov | Audit@123 | Government Auditor |
| devops@immunogrid.gov | DevOps@123 | DevOps Engineer |

---

## 6. Run Full Docker Stack

```bash
cd backend
docker-compose up -d

# Services started:
#   immunogrid-api       → :8000
#   immunogrid-postgres  → :5432
#   immunogrid-mongo     → :27017
#   immunogrid-redis     → :6379
#   immunogrid-mqtt      → :1883
```

---

## 7. Run IoT City Simulation

```bash
# Start virtual city (500+ devices)
python start.py sim

# Run quantum attack demo
python start.py attack

# Run quantum fingerprint demo
python start.py quantum

# Full system demo (all modules)
python start.py demo

# Full orchestrator
python system_orchestrator.py
```

---

## 8. Generate Paper Figures

```bash
pip install matplotlib
cd paper
python generate_figures.py
# Figures saved to: paper/figures/
```

---

## 9. Run Crypto Benchmark (Table II)

```bash
cd crypto_layer
python benchmark.py
```

---

## 10. Run Quantum Benchmark (Tables I, III, IV)

```bash
cd quantum_engine
python benchmark.py
```

---

## 11. Run Attack Scenarios

```bash
# Individual scenarios available:
#   coordinated_spoofing
#   ddos_hospital
#   slow_poison
#   ransomware_chain
#   insider_threat
#   full_city_assault

python -c "
import asyncio, sys
sys.path.insert(0, 'iot_simulator')
sys.path.insert(0, '.')
from iot_simulator.devices import TrafficSensor
from iot_simulator.scenario_runner import ScenarioRunner

async def main():
    devices = [TrafficSensor(location=f'z{i}', sector='traffic') for i in range(20)]
    async def pub(topic, payload): pass
    runner = ScenarioRunner(devices, pub)
    result = await runner.run_scenario('coordinated_spoofing')
    print(f'Detection rate: {result.detection_rate}%')

asyncio.run(main())
"
```

---

## 12. AWS Deployment (Production)

```bash
# Install Terraform
# https://developer.hashicorp.com/terraform/downloads

cd aws_infra/terraform

# Configure AWS credentials
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret

# Deploy
terraform init
terraform plan -var="environment=dev"
terraform apply -var="environment=dev" -auto-approve
```

---

## 13. Kubernetes Deployment (AWS EKS)

```bash
# Configure kubectl for EKS
aws eks update-kubeconfig --name immunogrid-cluster --region us-east-1

# Deploy all services
kubectl apply -f devops/k8s/deployment.yaml

# Check pods
kubectl get pods -n immunogrid

# Get ingress URL
kubectl get ingress -n immunogrid
```

---

## Project Structure

```
immunogrid/
├── iot_simulator/          Python smart city simulator
│   ├── devices/            8 device types
│   ├── attackers/          6 attack types
│   ├── city_builder.py     Main simulation runner
│   └── scenario_runner.py  Pre-defined attack scenarios
├── quantum_engine/         Quantum fingerprinting
│   ├── fingerprint_gen.py  4-qubit QBF
│   ├── multi_qubit_fp.py   8-qubit QBF (enhanced)
│   ├── attack_simulator.py Grover/Shor attacks
│   └── benchmark.py        Paper benchmark data
├── crypto_layer/           Post-quantum cryptography
│   ├── hybrid_crypto.py    Kyber + AES-256 hybrid
│   ├── key_manager.py      Key lifecycle management
│   └── benchmark.py        Crypto overhead data
├── ai_brain/               Federated Adversarial Consciousness
│   ├── local_trainer.py    Per-device GAN trainer
│   ├── aggregator.py       FedAvg aggregation server
│   ├── threat_classifier.py RF-based classifier
│   └── model_monitor.py    Drift detection
├── blockchain/             Morphogenetic blockchain
│   ├── immune_ledger.py    Core blockchain
│   └── smart_contract.py   Chaincode simulation
├── honeypot/               Decoy trap network
│   ├── decoy_spawner.py    Honeypot management
│   └── intelligence_capture.py Attack intelligence
├── backend/                FastAPI microservices (13 routers)
├── frontend/               React web app (17 dashboards)
├── aws_infra/              Terraform + Lambda
├── devops/                 CI/CD + Docker + K8s
├── paper/                  LaTeX manuscript + figures
├── test_integration.py     Full integration test suite
├── system_orchestrator.py  All modules connected
└── start.py                Quick-start helper
```

---

## Troubleshooting

**PyTorch blocked (Windows):**
The AI Brain module requires PyTorch. If blocked by Windows Application Control,
deploy on Linux or use AWS SageMaker where it runs natively.

**liboqs not available:**
PQC runs in simulation mode by default.
For real Kyber/Dilithium: `pip install liboqs-python`
See: https://github.com/open-quantum-safe/liboqs-python

**Qiskit AerSimulator slow:**
Reduce num_qubits from 4 to 2 for faster demos:
`QuantumFingerprintEngine(num_qubits=2)`

---

## Research Paper

- Manuscript: `paper/main.tex`
- Figures: `paper/figures/` (auto-generated)
- Target journal: IEEE Transactions on Information Forensics & Security
- Novel contributions: QBF + FAC + Morphogenetic Blockchain
