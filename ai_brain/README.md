# ImmunoGrid — AI Brain (Federated Adversarial Consciousness)

> Every IoT device thinks like a hacker to pre-harden defenses before attacks happen.

---

## Overview

The AI Brain implements **Federated Adversarial Consciousness (FAC)** — ImmunoGrid's novel
federated learning architecture where each device maintains dual AI personalities:

```
🛡️ Defender (Discriminator) — "How do I protect myself?"
⚔️  Attacker  (Generator)    — "If I were a hacker, how would I attack myself?"
```

Devices share adversarial imaginations (not raw data) → collective pre-hardening.

---

## Modules

```
ai_brain/
├── local_trainer.py      Per-device FAC trainer (GAN-based)
├── aggregator.py         FedAvg aggregation server (runs on AWS SageMaker)
├── federated_gan.py      Full conditional GAN implementation
├── threat_classifier.py  RandomForest classifier (sklearn, no PyTorch needed)
├── model_monitor.py      FL model drift + Byzantine poisoning detection
├── privacy_engine.py     Differential privacy (Gaussian mechanism)
├── scenario_generator.py Attack scenario generation for training data
├── model_evaluator.py    Evaluation, benchmarking, paper table generation
└── test_ai_brain_complete.py  38 tests for all modules
```

---

## Quick Start

```bash
# Run all AI Brain tests
python ai_brain/test_ai_brain_complete.py
# Expected: 38/38 PASS

# Train classifier on synthetic data
python -c "
from ai_brain.threat_classifier import ThreatClassifier
clf = ThreatClassifier()
result = clf.train()
print(f'Accuracy: {result[\"accuracy\"]}%')
"

# Generate training dataset
python -c "
from ai_brain.scenario_generator import AttackScenarioGenerator
gen = AttackScenarioGenerator()
X, y, desc = gen.generate_dataset(n_samples=5000, attack_ratio=0.25)
gen.save_dataset(__import__(\"pandas\").DataFrame({\"label\":y}), \"dataset.csv\")
print(f'Generated {len(X)} samples')
"
```

---

## Module Reference

### local_trainer.py — Per-Device FAC

```python
from ai_brain.local_trainer import LocalDeviceTrainer

trainer = LocalDeviceTrainer(device_id="dev-001", device_type="traffic_sensor")

# Add messages to training buffer
trainer.add_to_buffer(device_message, label=0)  # 0=normal, 1-4=attacks

# Train defender personality
metrics = trainer.train_defender(epochs=5)
# → {"loss": 0.12, "accuracy": 0.94, "samples": 200, "rounds": 1}

# Generate adversarial imaginations (Attacker personality)
imaginations = trainer.generate_attack_imaginations(count=5)
# → [AdversarialImagination(device_id, attack_type, feature_vector, confidence)]

# Classify an incoming message
result = trainer.classify_message(message)
# → {"predicted_label": "normal", "confidence": 0.97, "is_attack": False}

# Extract weights for FL aggregation
weights = trainer.get_model_weights()
# → {"defender": {...layer weights...}, "attacker": {...}}

# Load global weights from FL server
trainer.load_global_weights(global_weights)
```

### aggregator.py — FedAvg Server

```python
from ai_brain.aggregator import FederatedAggregator, ClientUpdate

agg = FederatedAggregator(min_clients=10)

# Submit device update
update = ClientUpdate(
    device_id="dev-001", round_number=1,
    weights=trainer.get_model_weights()["defender"],
    num_samples=200, metrics=metrics, imaginations=imaginations,
)
global_state = agg.submit_update(update)
# → Triggers aggregation when >= min_clients submit

# Get global model for distribution
global_weights = agg.get_global_weights()

# Get imaginations for a specific device (excludes its own)
device_imaginations = agg.get_imaginations_for_device("dev-001")
```

### threat_classifier.py — RF Classifier (no PyTorch)

```python
from ai_brain.threat_classifier import ThreatClassifier

clf = ThreatClassifier(n_estimators=100)
result = clf.train()          # Uses synthetic data by default
# result["accuracy"] → 99.75%

cr = clf.classify(message)
# cr.predicted_label   → "normal" | "spoofing" | "ddos" | ...
# cr.confidence        → 0.0-1.0
# cr.is_attack         → True/False
# cr.feature_values    → [12 numeric features]

clf.save_model("model.pkl")
clf.load_model("model.pkl")
fi = clf.get_feature_importance()
# → {"send_interval": 0.31, "packet_size": 0.18, ...}
```

### model_monitor.py — Drift Detection

```python
from ai_brain.model_monitor import ModelDriftMonitor, ModelSnapshot

monitor = ModelDriftMonitor(expected_participants=500)

snap = ModelSnapshot(
    round_number=5, accuracy=97.2, loss=0.11,
    participants=492, blockchain_hash="0x3f..."
)
alerts = monitor.record_round(snap)
# alerts = [] if healthy
# alerts = [DriftAlert(severity=MODERATE, metric="accuracy", ...)] if degrading

health = monitor.get_health_summary()
# → {"status": "healthy", "rounds_completed": 5, "peak_accuracy": 97.2}

warning = monitor.detect_model_degradation(threshold_pct=5.0)
# → None (healthy) or string warning message
```

### privacy_engine.py — Differential Privacy

```python
from ai_brain.privacy_engine import DifferentialPrivacyEngine

pe = DifferentialPrivacyEngine(epsilon=1.0, delta=1e-5, max_grad_norm=1.0)

# Privatize gradient vector
private_grads = pe.privatize_gradients(gradients, num_samples=200)

# Privatize full model weights
private_weights = pe.privatize_model_weights(weights_dict, num_samples=200)

# Check privacy budget
report = pe.get_privacy_report()
# → {"epsilon_per_round": 1.0, "total_epsilon_spent": 3.2, "remaining_budget": 6.8, ...}
```

### scenario_generator.py — Training Data

```python
from ai_brain.scenario_generator import AttackScenarioGenerator

gen = AttackScenarioGenerator(seed=42)

# Generate labeled dataset
X, y, descriptions = gen.generate_dataset(
    n_samples=5000, attack_ratio=0.25,
    device_types=["traffic_sensor", "hospital_device"]
)
# X.shape → (5000, 12)
# y values → 0=normal, 1=spoofing, 2=ddos, 3=data_poisoning, 4=replay, 5=mitm, 6=ransomware

# Single adversarial imagination
imagination = gen.generate_adversarial_imagination("dev-001", "traffic_sensor", "spoofing")
```

### model_evaluator.py — Benchmarking

```python
from ai_brain.model_evaluator import ModelEvaluator

evaluator = ModelEvaluator()
result = evaluator.evaluate_predictions(y_pred, y_test, round_number=1)
# result.overall_accuracy → 97.3
# result.macro_f1         → 96.8
# result.per_class        → [ClassMetrics(...), ...]

rates = evaluator.get_detection_rates()
# → {"spoofing": 95.2, "ddos": 88.3, "data_poisoning": 91.7, ...}

latex_table = evaluator.generate_paper_table()
# → LaTeX Table III for research paper

comparison = evaluator.compare_rounds()
# → {"best_accuracy": 97.3, "converged": True, "accuracy_trend": [...]}
```

---

## FAC Architecture

```
Device Training Loop (per round):
    ┌─────────────────────────────────────┐
    │  Local IoT Device                   │
    │                                     │
    │  Real data → Defender training      │
    │              ↕ adversarial          │
    │  Attacker generates imaginations    │
    │                                     │
    │  Share:  imaginations + weights     │
    │  Keep:   raw sensor data (private)  │
    └─────────────────────────────────────┘
              ↓ (via PQC-encrypted channel)
    ┌─────────────────────────────────────┐
    │  FL Aggregator (AWS SageMaker)      │
    │                                     │
    │  FedAvg(weights₁, ..., weightsₙ)   │
    │  Collect all imaginations           │
    │  Commit model hash on blockchain    │
    │                                     │
    │  Share: global_weights + all_imag  │
    └─────────────────────────────────────┘
              ↓
    All devices receive:
    ✅ Stronger global defender
    ✅ Others' attack imaginations
    ❌ Nobody's raw sensor data
```

---

## Test Results

```
38/38 tests PASS
Modules tested:
  scenario_generator  — 6 tests
  threat_classifier   — 4 tests
  model_monitor       — 5 tests
  privacy_engine      — 7 tests
  model_evaluator     — 6 tests
  local_trainer       — 5 tests
  aggregator          — 1 test
  integration         — 4 tests
```

---

## Privacy Guarantee

ImmunoGrid AI Brain provides **(ε=1.0, δ=1e-5)-differential privacy** per FL round.

This means:
- Any individual device's data contributes at most e^1.0 ≈ 2.72× more to the model
  than if it had not participated
- With probability ≥ 1 - 1e-5, the privacy guarantee holds

Strong privacy at minimal accuracy cost — typical accuracy drop < 2% with DP enabled.
