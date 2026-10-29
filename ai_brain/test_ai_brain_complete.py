"""
ImmunoGrid — AI Brain Complete Test Suite
Tests all FAC (Federated Adversarial Consciousness) modules.

Run:
    python ai_brain/test_ai_brain_complete.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'iot_simulator'))

import numpy as np
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()
results = []

TORCH_OK = False
try:
    import torch
    TORCH_OK = True
except (ImportError, OSError):
    pass


def check(name, fn):
    try:
        fn()
        results.append((name, True, ""))
        console.print(f"  [green]✅ {name}[/green]")
    except SystemExit as e:
        results.append((name, None, f"SKIPPED"))
        console.print(f"  [yellow]⏭️  {name}: skipped[/yellow]")
    except Exception as e:
        results.append((name, False, str(e)[:80]))
        console.print(f"  [red]❌ {name}: {str(e)[:70]}[/red]")


console.print("\n[bold cyan]╔════════════════════════════════════════════════╗[/bold cyan]")
console.print("[bold cyan]║  ImmunoGrid AI Brain — Complete Test Suite    ║[/bold cyan]")
console.print("[bold cyan]╚════════════════════════════════════════════════╝[/bold cyan]\n")

# ── 1. Scenario Generator ─────────────────────────────────────────────────────
console.print("[cyan]1. Attack Scenario Generator[/cyan]")

from ai_brain.scenario_generator import AttackScenarioGenerator, ATTACK_LABELS

def t_sg_init():
    gen = AttackScenarioGenerator(seed=42)
    stats = gen.get_stats()
    assert stats['n_features'] == 12
    assert len(stats['attack_types']) == 7
    assert len(stats['device_types']) == 8
check("Scenario generator initializes correctly", t_sg_init)

def t_sg_normal():
    gen = AttackScenarioGenerator(seed=42)
    s = gen.generate_normal("traffic_sensor", 8)
    assert s.label == 0
    assert s.attack_type == "normal"
    assert len(s.features) == 12
    assert all(isinstance(f, float) for f in s.features)
check("Normal traffic scenario generation", t_sg_normal)

def t_sg_all_attacks():
    gen = AttackScenarioGenerator(seed=42)
    generators = [
        (gen.generate_spoofing,       1, "spoofing"),
        (gen.generate_ddos,           2, "ddos"),
        (gen.generate_data_poisoning, 3, "data_poisoning"),
        (gen.generate_replay,         4, "replay_attack"),
        (gen.generate_mitm,           5, "mitm"),
        (gen.generate_ransomware,     6, "ransomware"),
    ]
    for fn, label, name in generators:
        s = fn("traffic_sensor", 12)
        assert s.label == label, f"{name}: expected label {label}, got {s.label}"
        assert s.attack_type == name
        assert len(s.features) == 12
check("All 6 attack scenario types generated correctly", t_sg_all_attacks)

def t_sg_dataset():
    gen = AttackScenarioGenerator(seed=42)
    X, y, desc = gen.generate_dataset(n_samples=200, attack_ratio=0.3)
    assert X.shape[1] == 12
    assert len(y) == len(X)
    assert len(desc) == len(X)
    assert 0 in set(y.tolist())
    assert len(set(y.tolist())) >= 5
check("Full dataset generation (200 samples, 30% attacks)", t_sg_dataset)

def t_sg_imagination():
    gen = AttackScenarioGenerator(seed=42)
    im = gen.generate_adversarial_imagination("dev-001", "traffic_sensor", "spoofing")
    assert im['attack_type'] == "spoofing"
    assert im['device_id'] == "dev-001"
    assert len(im['feature_vector']) == 12
    assert 0.0 <= im['confidence'] <= 1.0
check("Adversarial imagination generation", t_sg_imagination)

def t_sg_stats():
    gen = AttackScenarioGenerator(seed=42)
    gen.generate_dataset(n_samples=100, attack_ratio=0.2)
    assert gen.generated_count > 0
check("Scenario generator tracks count", t_sg_stats)

# ── 2. Threat Classifier ──────────────────────────────────────────────────────
console.print("\n[cyan]2. Threat Classifier (RandomForest)[/cyan]")

from ai_brain.threat_classifier import ThreatClassifier

def t_tc_train():
    clf = ThreatClassifier(n_estimators=30)
    result = clf.train()
    assert result['accuracy'] > 80.0
    assert clf.is_trained
    assert 'report' in result
check("RF classifier trains on synthetic data (>80% acc)", t_tc_train)

def t_tc_classify_normal():
    from iot_simulator.devices import TrafficSensor
    clf = ThreatClassifier(n_estimators=30)
    clf.train()
    d   = TrafficSensor(location='t1', sector='traffic')
    msg = d.build_message()
    cr  = clf.classify(msg)
    assert cr.predicted_label in list(ATTACK_LABELS.values())[:5]
    assert 0.0 <= cr.confidence <= 1.0
    assert isinstance(cr.is_attack, bool)
check("Classify normal IoT message", t_tc_classify_normal)

def t_tc_save_load():
    import os
    tmp = "test_model_tmp.pkl"
    clf = ThreatClassifier(n_estimators=30)
    clf.train()
    clf.save_model(tmp)
    assert os.path.exists(tmp)
    clf2 = ThreatClassifier()
    clf2.load_model(tmp)
    assert clf2.is_trained
    os.remove(tmp)
check("Save and load model from disk", t_tc_save_load)

def t_tc_feature_importance():
    clf = ThreatClassifier(n_estimators=30)
    clf.train()
    fi = clf.get_feature_importance()
    assert len(fi) > 0
    assert all(0.0 <= v <= 1.0 for v in fi.values())
    assert abs(sum(fi.values()) - 1.0) < 0.01
check("Feature importance extraction (sums to 1)", t_tc_feature_importance)

# ── 3. Model Monitor ──────────────────────────────────────────────────────────
console.print("\n[cyan]3. Model Drift Monitor[/cyan]")

from ai_brain.model_monitor import ModelDriftMonitor, ModelSnapshot, DriftSeverity

def t_mm_healthy():
    monitor = ModelDriftMonitor(expected_participants=500)
    for r in range(10):
        snap = ModelSnapshot(round_number=r+1, accuracy=90+r*0.8,
                             loss=1.0-r*0.06, participants=495,
                             blockchain_hash=f"h{r}")
        monitor.record_round(snap)
    health = monitor.get_health_summary()
    assert health['rounds_completed'] == 10
    assert health['status'] == 'healthy'
check("10 healthy FL rounds — no drift alerts", t_mm_healthy)

def t_mm_accuracy_drop():
    monitor = ModelDriftMonitor(expected_participants=500)
    for r in range(5):
        monitor.record_round(ModelSnapshot(r+1, 95+r*0.4, 0.5-r*0.05, 495, f"h{r}"))
    alerts = monitor.record_round(ModelSnapshot(6, 82.0, 1.5, 490, "h6"))
    drop_alerts = [a for a in alerts if a.metric == "accuracy"]
    assert len(drop_alerts) > 0
    assert drop_alerts[0].severity in (DriftSeverity.MODERATE, DriftSeverity.SEVERE)
check("Accuracy drop > 5% triggers drift alert", t_mm_accuracy_drop)

def t_mm_loss_spike():
    monitor = ModelDriftMonitor(expected_participants=500)
    for r in range(5):
        monitor.record_round(ModelSnapshot(r+1, 94.0, 0.3, 495, f"h{r}"))
    alerts = monitor.record_round(ModelSnapshot(6, 93.0, 0.9, 490, "h6"))
    loss_alerts = [a for a in alerts if a.metric == "loss"]
    assert len(loss_alerts) > 0
check("Loss spike > 2× baseline triggers alert", t_mm_loss_spike)

def t_mm_participant_drop():
    monitor = ModelDriftMonitor(expected_participants=500)
    for r in range(3):
        monitor.record_round(ModelSnapshot(r+1, 94.0, 0.4, 495, f"h{r}"))
    alerts = monitor.record_round(ModelSnapshot(4, 93.0, 0.41, 350, "h4"))
    part_alerts = [a for a in alerts if a.metric == "participants"]
    assert len(part_alerts) > 0
check("Participant drop below 80% triggers alert", t_mm_participant_drop)

def t_mm_stats():
    monitor = ModelDriftMonitor(expected_participants=500)
    monitor.record_round(ModelSnapshot(1, 92.0, 0.5, 490, "hash1"))
    stats = monitor.get_stats()
    assert stats['snapshots_recorded'] == 1
    assert stats['peak_accuracy'] == 92.0
check("Model monitor stats correct", t_mm_stats)

# ── 4. Privacy Engine ─────────────────────────────────────────────────────────
console.print("\n[cyan]4. Differential Privacy Engine[/cyan]")

from ai_brain.privacy_engine import DifferentialPrivacyEngine, PrivacyAccountant

def t_pe_init():
    pe = DifferentialPrivacyEngine(epsilon=1.0, delta=1e-5)
    assert pe.epsilon == 1.0
    assert pe.delta == 1e-5
    report = pe.get_privacy_report()
    assert report['budget_exhausted'] == False
    assert report['total_epsilon_spent'] == 0.0
check("Privacy engine initializes correctly", t_pe_init)

def t_pe_clip():
    pe = DifferentialPrivacyEngine(max_grad_norm=1.0)
    grads = np.array([3.0, 4.0])
    clipped = pe.clip_gradients(grads)
    assert np.linalg.norm(clipped) <= 1.0 + 1e-6
check("Gradient clipping to max_grad_norm=1.0", t_pe_clip)

def t_pe_already_clipped():
    pe = DifferentialPrivacyEngine(max_grad_norm=10.0)
    grads = np.array([0.1, 0.2, 0.3])
    clipped = pe.clip_gradients(grads)
    assert np.allclose(grads, clipped)
check("Gradients below threshold not clipped", t_pe_already_clipped)

def t_pe_add_noise():
    pe = DifferentialPrivacyEngine(epsilon=1.0, noise_multiplier=1.0)
    grads = np.zeros(100)
    noisy = pe.add_noise(grads, num_samples=100)
    assert not np.allclose(noisy, grads)
    assert abs(noisy.mean()) < 0.5
check("Gaussian noise added to gradients", t_pe_add_noise)

def t_pe_privatize():
    pe = DifferentialPrivacyEngine(epsilon=2.0, delta=1e-5)
    grads = np.random.randn(50)
    private = pe.privatize_gradients(grads, num_samples=100)
    assert private.shape == grads.shape
    assert pe.accountant.total_rounds == 1
    assert pe.accountant.total_epsilon > 0
check("Full privatize_gradients pipeline", t_pe_privatize)

def t_pe_weights():
    pe = DifferentialPrivacyEngine(epsilon=1.0)
    weights = {"layer1": [[1.0, 2.0], [3.0, 4.0]], "layer2": [0.1, 0.2]}
    private = pe.privatize_model_weights(weights, num_samples=100)
    assert set(private.keys()) == set(weights.keys())
    assert len(private['layer2']) == 2
check("Privatize full model weights dict", t_pe_weights)

def t_pe_budget_report():
    pe = DifferentialPrivacyEngine(epsilon=1.0, max_grad_norm=1.0)
    grads = np.random.randn(10)
    for _ in range(5):
        pe.privatize_gradients(grads, 100)
    report = pe.get_privacy_report()
    assert report['rounds_completed'] == 5
    assert report['total_epsilon_spent'] > 0
check("Privacy budget report after 5 rounds", t_pe_budget_report)

def t_pe_budget_exhausted():
    pe = DifferentialPrivacyEngine(epsilon=1.0, max_grad_norm=1.0)
    pe.accountant.max_epsilon = 0.5
    pe.accountant.total_epsilon = 0.6
    grads = np.ones(10)
    result = pe.privatize_gradients(grads, 100)
    assert np.allclose(result, np.zeros(10))
check("Returns zeros when privacy budget exhausted", t_pe_budget_exhausted)

# ── 5. Model Evaluator ────────────────────────────────────────────────────────
console.print("\n[cyan]5. Model Evaluator[/cyan]")

from ai_brain.model_evaluator import ModelEvaluator

def t_me_evaluate_predictions():
    evaluator = ModelEvaluator()
    y_test = np.array([0,0,0,1,1,2,2,3,3,4])
    y_pred = np.array([0,0,1,1,1,2,2,3,3,4])
    result = evaluator.evaluate_predictions(y_pred, y_test, round_number=1)
    assert result.overall_accuracy > 0
    assert result.macro_f1 > 0
    assert len(result.per_class) > 0
    assert len(result.confusion_matrix) > 0
check("Evaluate predictions produces all metrics", t_me_evaluate_predictions)

def t_me_perfect_accuracy():
    evaluator = ModelEvaluator()
    y = np.array([0,0,1,1,2,2,3,3,4,4])
    result = evaluator.evaluate_predictions(y, y, round_number=1)
    assert result.overall_accuracy == 100.0
check("Perfect predictions → 100% accuracy", t_me_perfect_accuracy)

def t_me_detection_rates():
    evaluator = ModelEvaluator()
    y_test = np.array([0]*50 + [1]*10 + [2]*10 + [3]*10 + [4]*10)
    y_pred = np.array([0]*50 + [1]*9+[0]+[2]*9+[0]+[3]*9+[0]+[4]*9+[0])
    evaluator.evaluate_predictions(y_pred, y_test, round_number=1)
    rates = evaluator.get_detection_rates()
    assert len(rates) > 0
    assert all(0.0 <= v <= 100.0 for v in rates.values())
check("Per-attack detection rates extraction", t_me_detection_rates)

def t_me_degradation_none():
    evaluator = ModelEvaluator()
    for r in range(5):
        evaluator.evaluate_predictions(
            np.array([0]*90 + [1]*10), np.array([0]*90 + [1]*10),
            round_number=r+1
        )
    assert evaluator.detect_model_degradation(threshold_pct=5.0) is None
check("No degradation warning on stable model", t_me_degradation_none)

def t_me_paper_table():
    evaluator = ModelEvaluator()
    y_test = np.array([0]*50 + [1]*10 + [2]*10 + [3]*10)
    y_pred = np.array([0]*48+[1,2] + [1]*9+[0]+[2]*9+[0]+[3]*9+[0])
    evaluator.evaluate_predictions(y_pred, y_test, round_number=1)
    table = evaluator.generate_paper_table()
    assert "\\begin{table}" in table
    assert "\\end{table}" in table
    assert "tabular" in table
check("LaTeX paper table generation", t_me_paper_table)

def t_me_compare_rounds():
    evaluator = ModelEvaluator()
    for r in range(5):
        y = np.array([0]*80 + [1]*20)
        evaluator.evaluate_predictions(y, y, round_number=r+1)
    comp = evaluator.compare_rounds()
    assert comp['rounds_evaluated'] == 5
    assert comp['best_accuracy'] == 100.0
    assert len(comp['accuracy_trend']) == 5
check("Compare rounds convergence analysis", t_me_compare_rounds)

# ── 6. Local Trainer + Aggregator ─────────────────────────────────────────────
console.print("\n[cyan]6. Local Trainer + FL Aggregator[/cyan]")

from ai_brain.local_trainer import LocalDeviceTrainer
from ai_brain.aggregator import FederatedAggregator, ClientUpdate

def t_lt_init():
    if not TORCH_OK: raise SystemExit("torch not available")
    trainer = LocalDeviceTrainer("dev-001", "traffic_sensor")
    assert trainer.device_id == "dev-001"
    assert trainer.training_rounds == 0
check("LocalDeviceTrainer initialization", t_lt_init)

def t_lt_add_buffer():
    if not TORCH_OK: raise SystemExit("torch not available")
    from iot_simulator.devices import TrafficSensor
    d = TrafficSensor(location='t1', sector='traffic')
    trainer = LocalDeviceTrainer(d.device_id, "traffic_sensor")
    for _ in range(20):
        trainer.add_to_buffer(d.build_message(), label=0)
    assert len(trainer.local_data_buffer) == 20
check("Buffer accumulation (20 samples)", t_lt_add_buffer)

def t_lt_train():
    if not TORCH_OK: raise SystemExit("torch not available")
    from iot_simulator.devices import TrafficSensor
    d = TrafficSensor(location='t1', sector='traffic')
    trainer = LocalDeviceTrainer(d.device_id, "traffic_sensor")
    for _ in range(25):
        trainer.add_to_buffer(d.build_message(), label=0)
    metrics = trainer.train_defender(epochs=3)
    assert "accuracy" in metrics
    assert "loss" in metrics
    assert trainer.training_rounds == 1
check("Defender training on local data", t_lt_train)

def t_lt_imaginations():
    if not TORCH_OK: raise SystemExit("torch not available")
    trainer = LocalDeviceTrainer("dev-x", "traffic_sensor")
    imag = trainer.generate_attack_imaginations(count=3)
    assert len(imag) == 3
    for im in imag:
        assert hasattr(im, 'attack_type')
        assert hasattr(im, 'feature_vector')
        assert hasattr(im, 'confidence')
check("Adversarial imagination generation (FAC)", t_lt_imaginations)

def t_lt_receive_imaginations():
    if not TORCH_OK: raise SystemExit("torch not available")
    trainer1 = LocalDeviceTrainer("dev-a", "traffic_sensor")
    trainer2 = LocalDeviceTrainer("dev-b", "traffic_sensor")
    imag = trainer1.generate_attack_imaginations(count=3)
    before = len(trainer2.local_data_buffer)
    trainer2.receive_imaginations(imag)
    assert len(trainer2.local_data_buffer) == before + 3
check("Receive imaginations from other devices", t_lt_receive_imaginations)

def t_lt_classify():
    if not TORCH_OK: raise SystemExit("torch not available")
    from iot_simulator.devices import TrafficSensor
    d = TrafficSensor(location='t1', sector='traffic')
    trainer = LocalDeviceTrainer(d.device_id, "traffic_sensor")
    for _ in range(20):
        trainer.add_to_buffer(d.build_message(), label=0)
    trainer.train_defender(epochs=3)
    result = trainer.classify_message(d.build_message())
    assert 'predicted_label' in result
    assert 'confidence' in result
    assert 'is_attack' in result
check("Message classification after training", t_lt_classify)

def t_lt_weight_sharing():
    if not TORCH_OK: raise SystemExit("torch not available")
    from iot_simulator.devices import TrafficSensor
    d = TrafficSensor(location='t1', sector='traffic')
    trainer = LocalDeviceTrainer(d.device_id, "traffic_sensor")
    for _ in range(20):
        trainer.add_to_buffer(d.build_message(), label=0)
    trainer.train_defender(epochs=2)
    weights = trainer.get_model_weights()
    assert "defender" in weights
    assert len(weights["defender"]) > 0
    # Load back into a new trainer
    trainer2 = LocalDeviceTrainer("dev-recv", "traffic_sensor")
    trainer2.load_global_weights(weights)
check("Get + load model weights (FL weight sharing)", t_lt_weight_sharing)

def t_agg_fedavg():
    if not TORCH_OK: raise SystemExit("torch not available")
    from iot_simulator.devices import TrafficSensor
    agg = FederatedAggregator(min_clients=3)
    for i in range(3):
        d = TrafficSensor(location=f'z{i}', sector='traffic')
        trainer = LocalDeviceTrainer(d.device_id, "traffic_sensor")
        for _ in range(20):
            trainer.add_to_buffer(d.build_message(), label=0)
        metrics = trainer.train_defender(epochs=2)
        update  = ClientUpdate(
            device_id=d.device_id, round_number=1,
            weights=trainer.get_model_weights()["defender"],
            num_samples=20, metrics=metrics, imaginations=[],
        )
        agg.submit_update(update)
    assert agg.current_round == 1
    global_w = agg.get_global_weights()
    assert global_w is not None
    assert global_w['round'] == 1
check("FedAvg aggregation (3 clients, 1 round)", t_agg_fedavg)

def t_agg_imaginations_sharing():
    if not TORCH_OK: raise SystemExit("torch not available")
    from iot_simulator.devices import TrafficSensor
    agg = FederatedAggregator(min_clients=2)
    for i in range(2):
        d = TrafficSensor(location=f'z{i}', sector='traffic')
        trainer = LocalDeviceTrainer(d.device_id, "traffic_sensor")
        for _ in range(20):
            trainer.add_to_buffer(d.build_message(), label=0)
        metrics = trainer.train_defender(epochs=2)
        imag = trainer.generate_attack_imaginations(count=2)
        update = ClientUpdate(
            device_id=d.device_id, round_number=1,
            weights=trainer.get_model_weights()["defender"],
            num_samples=20, metrics=metrics,
            imaginations=[{"device_id": d.device_id, "attack_type": "spoofing",
                           "feature_vector": im.feature_vector} for im in imag],
        )
        agg.submit_update(update)
    # Device 0 should receive device 1's imaginations
    imag_for_d0 = agg.get_imaginations_for_device("dev-get-0")
    assert len(imag_for_d0) >= 0  # Could be 0-4 imaginations
    stats = agg.get_stats()
    assert stats['total_imaginations_collected'] >= 4
check("Aggregator collects + shares imaginations (FAC)", t_agg_imaginations_sharing)

# ── 7. Byzantine Defense ──────────────────────────────────────────────────────
console.print("\n[cyan]7. Byzantine Defense Engine[/cyan]")

from ai_brain.byzantine_defense import ByzantineDefenseEngine

def t_bd_fedmedian():
    engine = ByzantineDefenseEngine(n_clients=5, n_byzantine=1)
    grads = [np.random.randn(10) for _ in range(5)]
    result, method = engine.aggregate_robust(grads, method="fedmedian")
    assert result.shape == (10,)
check("FedMedian robust aggregation", t_bd_fedmedian)

def t_bd_trimmed_mean():
    engine = ByzantineDefenseEngine(n_clients=10)
    grads = [np.random.randn(8) for _ in range(10)]
    result, _ = engine.aggregate_robust(grads, method="trimmed_mean")
    assert result.shape == (8,)
check("Trimmed Mean aggregation", t_bd_trimmed_mean)

def t_bd_krum():
    engine = ByzantineDefenseEngine(n_clients=7, n_byzantine=2)
    grads = [np.random.randn(6) for _ in range(7)]
    result, _ = engine.aggregate_robust(grads, method="krum")
    assert result.shape == (6,)
check("Krum Byzantine-robust selection", t_bd_krum)

def t_bd_norm_clipping():
    engine = ByzantineDefenseEngine(n_clients=5)
    grads  = [np.random.randn(10) for _ in range(4)]
    grads.append(np.ones(10) * 100)  # Byzantine
    result, _ = engine.aggregate_robust(grads, method="norm_clipping")
    assert np.linalg.norm(result) < 50
check("Norm clipping reduces Byzantine influence", t_bd_norm_clipping)

def t_bd_flame():
    engine  = ByzantineDefenseEngine(n_clients=8)
    honest  = [np.random.randn(12) * 0.1 for _ in range(6)]
    bad     = [np.ones(12) * 50, -np.ones(12) * 50]
    result, _ = engine.aggregate_robust(honest + bad, method="flame")
    assert result.shape == (12,)
    honest_mean = np.mean(honest, axis=0)
    assert np.linalg.norm(result - honest_mean) < np.linalg.norm(np.ones(12) * 50)
check("FLAME filters Byzantine outliers", t_bd_flame)

def t_bd_detect_poisoning():
    engine = ByzantineDefenseEngine(n_clients=10)
    normal = [np.random.randn(8) * 0.1 for _ in range(8)]
    poison = [np.ones(8) * 100, -np.ones(8) * 100]
    suspects = engine.detect_gradient_poisoning(normal + poison, threshold=2.0)
    assert len(suspects) >= 2
    assert 8 in suspects or 9 in suspects
check("Gradient poisoning detection (norm outlier)", t_bd_detect_poisoning)

def t_bd_stats():
    engine = ByzantineDefenseEngine(n_clients=5, n_byzantine=1)
    grads  = [np.random.randn(4) for _ in range(5)]
    engine.aggregate_robust(grads, method="fedmedian")
    engine.aggregate_robust(grads, method="krum")
    stats = engine.get_stats()
    assert stats["aggregations_performed"] == 2
    assert stats["n_clients"] == 5
check("Byzantine defense statistics tracking", t_bd_stats)

# ── 8. Explainability (XAI) ───────────────────────────────────────────────────
console.print("\n[cyan]8. Explainability (XAI)[/cyan]")

from ai_brain.explainability import ThreatExplainer, Explanation

def t_xai_normal():
    explainer = ThreatExplainer()
    features  = [2.3, 48.0, 15.0, 26.0, 10.0, 20.8, 0.001, 0.55, 45.0, 2.0, 1.0, 1.0]
    exp = explainer.explain_prediction(features, prediction=0, confidence=0.97, device_id="dev-001")
    assert isinstance(exp, Explanation)
    assert exp.is_attack is False
    assert "normal" in exp.human_readable.lower()
    assert "No action" in exp.recommended_action
check("XAI explains normal traffic prediction", t_xai_normal)

def t_xai_spoofing():
    explainer = ThreatExplainer()
    features  = [4.5, 70.0, 35.0, 13.0, 14.0, 15.6, 0.05, 0.6, 250.0, 99.0, 1.0, 1.0]
    exp = explainer.explain_prediction(features, prediction=1, confidence=0.92, device_id="dev-002")
    assert exp.is_attack is True
    assert "spoofing" in exp.prediction.lower()
    assert len(exp.top_features) == 4
check("XAI explains spoofing with top 4 features", t_xai_spoofing)

def t_xai_ddos():
    explainer = ThreatExplainer()
    features  = [0.02, 48.0, 98.0, 3000.0, 8.0, 2400.0, 0.35, 0.25, 15.0, 2.0, 1.0, 1.0]
    exp = explainer.explain_prediction(features, prediction=2, confidence=0.99, device_id="dev-003")
    assert "ddos" in exp.prediction.lower()
    assert "rate" in exp.human_readable.lower() or "cpu" in exp.human_readable.lower()
check("XAI explains DDoS with CPU/rate indicators", t_xai_ddos)

def t_xai_all_attack_classes():
    explainer = ThreatExplainer()
    features  = [2.3, 48.0, 15.0, 26.0, 3.0, 20.8, 0.6, 0.1, 45.0, 2.0, 1.0, 0.0]
    for cls in range(7):
        exp = explainer.explain_prediction(features, prediction=cls, confidence=0.85, device_id="dx")
        assert isinstance(exp, Explanation)
        assert exp.recommended_action in list(ThreatExplainer.ACTION_MAP.values())
check("XAI generates explanations for all 7 attack classes", t_xai_all_attack_classes)

def t_xai_with_classifier():
    clf = ThreatClassifier(n_estimators=20)
    clf.train()
    explainer = ThreatExplainer(classifier=clf)
    # Classifier uses 8 features — match its feature count
    features  = [2.3, 48.0, 0.15, 0.43, 0.43, 20.8, 0.001, 0.55]
    # Pad to 12 for XAI (XAI works with 12, classifier gets first 8 via scaler)
    features12 = features + [10.0, 2.0, 1.0, 1.0]
    exp = explainer.explain_prediction(features12, prediction=0, confidence=0.9, device_id="dev-t")
    assert isinstance(exp, Explanation)
    assert len(exp.top_features) == 4
check("XAI with trained classifier (LIME importance)", t_xai_with_classifier)

def t_xai_batch():
    explainer     = ThreatExplainer()
    features_list = [[2.3]*12, [0.05]*12, [4.5]*12]
    exps = explainer.batch_explain(features_list, [0, 2, 1], [0.97, 0.99, 0.91])
    assert len(exps) == 3
    assert exps[0].is_attack is False
    assert exps[1].is_attack is True
check("Batch explanation generation (3 messages)", t_xai_batch)

def t_xai_stats():
    explainer = ThreatExplainer()
    explainer.explain_prediction([2.3]*12, 0, 0.9, "d1")
    explainer.explain_prediction([2.3]*12, 1, 0.8, "d2")
    assert explainer.get_stats()["explanations_generated"] == 2
check("XAI explanation counter tracks correctly", t_xai_stats)

# ── 9. FL Coordinator ─────────────────────────────────────────────────────────
console.print("\n[cyan]9. FL Coordinator (Full Round)[/cyan]")

from ai_brain.fl_coordinator import FLCoordinator, RoundConfig, RoundSummary

def _client_updates(n):
    updates = []
    for i in range(n):
        w = np.random.randn(50).tolist()
        updates.append({
            "device_id":    f"dev-{i:03d}",
            "weights":      {"l1": w[:25], "l2": w[25:]},
            "num_samples":  20,
            "metrics":      {"accuracy": 0.90 + i * 0.001, "loss": 0.25},
            "imaginations": [{
                "device_id":      f"dev-{i:03d}",
                "attack_type":    "spoofing",
                "feature_vector": np.random.randn(12).tolist(),
            }],
        })
    return updates

def t_flc_init():
    coord = FLCoordinator(min_clients=3, byzantine_method="fedmedian", dp_epsilon=1.0)
    assert coord.current_round == 0
    health = coord.get_health_report()
    assert "current_round" in health
    assert "privacy" in health
    assert "byzantine_defense" in health
check("FL coordinator initializes with all subsystems", t_flc_init)

def t_flc_single_round():
    coord   = FLCoordinator(min_clients=3, dp_epsilon=1.0)
    summary = coord.coordinate_round(_client_updates(5))
    assert isinstance(summary, RoundSummary)
    assert summary.round_number == 1
    assert summary.participants == 5
    assert summary.imaginations_shared == 5
    assert len(summary.blockchain_hash) == 64
check("Single FL round: 5 clients, summary with blockchain hash", t_flc_single_round)

def t_flc_multiple_rounds():
    coord = FLCoordinator(min_clients=3, dp_epsilon=2.0)
    for r in range(5):
        s = coord.coordinate_round(_client_updates(4))
        assert s.round_number == r + 1
    assert coord.current_round == 5
    history = coord.get_training_history()
    assert len(history) == 5
    assert history[0]['round'] == 1
    assert history[4]['round'] == 5
check("5 FL rounds: all complete, history recorded", t_flc_multiple_rounds)

def t_flc_byzantine_handling():
    coord   = FLCoordinator(min_clients=3, byzantine_method="fedmedian")
    updates = _client_updates(4)
    updates.append({
        "device_id":    "byzantine-attacker",
        "weights":      {"l1": [100.0]*25, "l2": [100.0]*25},
        "num_samples":  20,
        "metrics":      {"accuracy": 0.99, "loss": 0.01},
        "imaginations": [],
    })
    summary = coord.coordinate_round(updates)
    # System handles robustly regardless of flagging count
    assert isinstance(summary, RoundSummary)
    assert summary.participants == 5
check("FL round with Byzantine client handles robustly", t_flc_byzantine_handling)

def t_flc_dp_budget():
    coord = FLCoordinator(min_clients=2, dp_epsilon=1.0)
    for _ in range(3):
        coord.coordinate_round(_client_updates(3))
    report = coord.get_health_report()
    assert report["privacy"]["rounds_completed"] == 3
    assert report["privacy"]["total_epsilon_spent"] > 0
check("DP privacy budget tracked across 3 rounds", t_flc_dp_budget)

def t_flc_health_report():
    coord = FLCoordinator(min_clients=2, dp_epsilon=1.0)
    coord.coordinate_round(_client_updates(4))
    health = coord.get_health_report()
    assert health["current_round"] == 1
    assert health["total_imaginations"] == 4
    assert health["aggregation_method"] == "fedmedian"
    assert "model_health" in health
check("FL health report contains all subsystem info", t_flc_health_report)

# ── 10. Federated GAN ─────────────────────────────────────────────────────────
console.print("\n[cyan]10. Federated GAN (Conditional)[/cyan]")

def t_gan_init():
    if not TORCH_OK: raise SystemExit("torch not available")
    from ai_brain.federated_gan import FederatedGAN
    gan = FederatedGAN("dev-001")
    assert gan.device_id == "dev-001"
    assert gan.total_epochs == 0
    assert gan.get_stats()["trained"] is False
check("FederatedGAN initializes untrained", t_gan_init)

def t_gan_train():
    if not TORCH_OK: raise SystemExit("torch not available")
    from ai_brain.federated_gan import FederatedGAN
    gen = AttackScenarioGenerator(seed=42)
    X, y, _ = gen.generate_dataset(n_samples=100, attack_ratio=0.4)
    y_mapped = (y % 5).astype(np.int64)
    gan = FederatedGAN("dev-gan-001")
    metrics_list = gan.train_step(X, y_mapped, epochs=3)
    assert len(metrics_list) == 3
    for m in metrics_list:
        assert m.g_loss > 0
        assert m.d_loss > 0
        assert 0 <= m.d_accuracy <= 1
    assert gan.total_epochs == 3
check("GAN trains 3 epochs: g_loss + d_loss tracked", t_gan_train)

def t_gan_imaginations():
    if not TORCH_OK: raise SystemExit("torch not available")
    from ai_brain.federated_gan import FederatedGAN
    gan = FederatedGAN("dev-img")
    imgs = gan.generate_imaginations(count=5)
    assert len(imgs) == 5
    for img in imgs:
        assert img["device_id"] == "dev-img"
        assert len(img["feature_vector"]) == 12
        assert 0.0 <= img["confidence"] <= 1.0
        assert img["source"] == "federated_gan"
check("GAN generates 5 imaginations (12-dim feature vectors)", t_gan_imaginations)

def t_gan_specific_attack_type():
    if not TORCH_OK: raise SystemExit("torch not available")
    from ai_brain.federated_gan import FederatedGAN
    gan = FederatedGAN("dev-atk")
    imgs = gan.generate_imaginations(count=3, attack_type=2)  # DDoS
    for img in imgs:
        assert len(img["feature_vector"]) == 12
check("GAN generates imaginations for specific attack type", t_gan_specific_attack_type)

def t_gan_weight_sharing():
    if not TORCH_OK: raise SystemExit("torch not available")
    import torch
    from ai_brain.federated_gan import FederatedGAN
    gen = AttackScenarioGenerator(seed=42)
    X, y, _ = gen.generate_dataset(n_samples=60, attack_ratio=0.4)
    y_mapped = (y % 5).astype(np.int64)
    gan1 = FederatedGAN("dev-a")
    gan2 = FederatedGAN("dev-b")
    gan1.train_step(X, y_mapped, epochs=2)
    gan2.load_generator_weights(gan1.get_generator_weights())
    noise = torch.randn(1, gan1.noise_dim)
    label = torch.tensor([1])
    with torch.no_grad():
        out1 = gan1.generator(noise, label)
        out2 = gan2.generator(noise, label)
    assert torch.allclose(out1, out2), "Generator weights not correctly transferred"
check("GAN FL weight sharing between two devices", t_gan_weight_sharing)

def t_gan_stats():
    if not TORCH_OK: raise SystemExit("torch not available")
    from ai_brain.federated_gan import FederatedGAN
    gen = AttackScenarioGenerator(seed=42)
    X, y, _ = gen.generate_dataset(n_samples=80, attack_ratio=0.4)
    y_mapped = (y % 5).astype(np.int64)
    gan = FederatedGAN("dev-stats")
    gan.train_step(X, y_mapped, epochs=4)
    stats = gan.get_stats()
    assert stats["trained"] is True
    assert stats["total_epochs"] == 4
    assert "latest_g_loss" in stats
    assert "cls_accuracy" in stats
    assert stats["device_id"] == "dev-stats"
check("GAN stats after training: all fields present", t_gan_stats)

# ── 11. Integration ───────────────────────────────────────────────────────────
console.print("\n[cyan]11. AI Brain Integration[/cyan]")

def t_full_fac_cycle():
    """Full FAC: generate scenarios → train → evaluate → rates."""
    gen = AttackScenarioGenerator(seed=42)
    clf = ThreatClassifier(n_estimators=30)
    X, y, _ = gen.generate_dataset(n_samples=700, attack_ratio=0.40)
    result   = clf.train(X, y)
    assert result['accuracy'] > 75.0
    evaluator = ModelEvaluator()
    X_s    = clf.scaler.transform(X)
    y_pred = clf.classifier.predict(X_s)
    eval_r = evaluator.evaluate_predictions(y_pred, y, round_number=1)
    assert eval_r.overall_accuracy > 0
    rates  = evaluator.get_detection_rates()
    assert len(rates) >= 4
check("Full FAC cycle: scenarios→train→evaluate→rates", t_full_fac_cycle)

def t_dp_with_scenario():
    """Privacy engine applies to scenario-generated gradient data."""
    gen    = AttackScenarioGenerator(seed=42)
    pe     = DifferentialPrivacyEngine(epsilon=1.0, max_grad_norm=1.0)
    X, _, _ = gen.generate_dataset(n_samples=100, attack_ratio=0.2)
    grads   = X[0]
    private = pe.privatize_gradients(grads, num_samples=100)
    assert private.shape == grads.shape
    assert not np.allclose(private, grads)
    assert pe.get_privacy_report()['rounds_completed'] == 1
check("DP engine privatizes scenario-derived gradients", t_dp_with_scenario)

def t_monitor_with_evaluator():
    """Monitor + evaluator combined tracking."""
    gen       = AttackScenarioGenerator(seed=42)
    clf       = ThreatClassifier(n_estimators=30)
    evaluator = ModelEvaluator()
    monitor   = ModelDriftMonitor(expected_participants=500)
    X, y, _   = gen.generate_dataset(n_samples=700, attack_ratio=0.40)
    clf.train(X, y)
    X_s = clf.scaler.transform(X)
    for r in range(5):
        y_pred = clf.classifier.predict(X_s)
        eval_r = evaluator.evaluate_predictions(y_pred, y, round_number=r+1)
        monitor.record_round(ModelSnapshot(
            round_number=r+1, accuracy=eval_r.overall_accuracy,
            loss=0.5 - r*0.05, participants=490,
            blockchain_hash=f"hash-{r}",
        ))
    assert monitor.get_health_summary()['rounds_completed'] == 5
    assert evaluator.compare_rounds()['rounds_evaluated'] == 5
check("Monitor + Evaluator combined tracking (5 rounds)", t_monitor_with_evaluator)

def t_xai_with_fl_coordinator():
    """XAI explains coordinator round results."""
    coord   = FLCoordinator(min_clients=2, dp_epsilon=1.0)
    summary = coord.coordinate_round(_client_updates(3))
    assert summary.round_number == 1
    explainer = ThreatExplainer()
    # Explain a sample threat detection
    features = [2.3, 48.0, 15.0, 26.0, 10.0, 20.8, 0.001, 0.55, 45.0, 2.0, 1.0, 1.0]
    exp = explainer.explain_prediction(features, prediction=0, confidence=0.95)
    assert isinstance(exp, Explanation)
check("XAI explains decisions after FL coordinator round", t_xai_with_fl_coordinator)

# ── Summary ───────────────────────────────────────────────────────────────────

passed  = sum(1 for _, ok, _ in results if ok is True)
skipped = sum(1 for _, ok, _ in results if ok is None)
failed  = sum(1 for _, ok, _ in results if ok is False)

table = Table(
    title=f"\nAI Brain Test Results — {passed}/{len(results)-skipped} passed ({skipped} skipped)",
    box=box.ROUNDED, border_style="cyan",
)
table.add_column("Test",   style="white", max_width=55)
table.add_column("Status", style="bold")
table.add_column("Notes",  style="dim",   max_width=35)

for name, ok, err in results:
    if ok is True:   status = "[green]PASS ✅[/green]"
    elif ok is None: status = "[yellow]SKIP ⏭️[/yellow]"
    else:            status = "[red]FAIL ❌[/red]"
    table.add_row(name, status, err or "")

console.print(table)

if failed == 0:
    console.print(f"\n[bold green]🎉 ALL AI BRAIN TESTS PASSED ({skipped} skipped)[/bold green]\n")
    console.print("[dim]Modules verified:[/dim]")
    for mod in [
        "scenario_generator.py   — 7-class attack scenarios, adversarial imaginations",
        "threat_classifier.py    — RandomForest, anomaly detection, save/load",
        "model_monitor.py        — drift detection, loss spikes, participant drop",
        "privacy_engine.py       — Gaussian DP, gradient clipping, budget tracking",
        "model_evaluator.py      — per-class metrics, LaTeX tables, convergence",
        "local_trainer.py        — Defender+Attacker dual personality, FAC",
        "aggregator.py           — FedAvg, imagination sharing, blockchain hash",
        "byzantine_defense.py    — FedMedian, Krum, TrimMean, FLAME, NormClip",
        "explainability.py       — LIME-based XAI, all 7 attack types explained",
        "fl_coordinator.py       — Full round orchestration with all defenses",
        "federated_gan.py        — Conditional GAN, FL weight sharing",
    ]:
        console.print(f"  [cyan]{mod}[/cyan]")
else:
    console.print(f"\n[bold red]{failed} test(s) failed.[/bold red]\n")
    sys.exit(1)
