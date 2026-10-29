# ImmunoGrid — AI Brain Package
# Federated Adversarial Consciousness (FAC)

from .local_trainer import LocalDeviceTrainer, DefenderNet, AttackerNet, ATTACK_CLASSES
from .aggregator import FederatedAggregator, ClientUpdate, GlobalModelState
from .threat_classifier import ThreatClassifier, ClassificationResult
from .model_monitor import ModelDriftMonitor, ModelSnapshot, DriftAlert, DriftSeverity
from .privacy_engine import DifferentialPrivacyEngine, PrivacyAccountant
from .scenario_generator import AttackScenarioGenerator, ATTACK_LABELS, FEATURE_NAMES
from .model_evaluator import ModelEvaluator, EvaluationResult, ClassMetrics
from .byzantine_defense import ByzantineDefenseEngine
from .explainability import ThreatExplainer, Explanation
from .fl_coordinator import FLCoordinator, RoundConfig, RoundSummary
from .federated_gan import FederatedGAN, Generator, Discriminator, GANTrainMetrics

__all__ = [
    # local trainer
    "LocalDeviceTrainer", "DefenderNet", "AttackerNet", "ATTACK_CLASSES",
    # aggregator
    "FederatedAggregator", "ClientUpdate", "GlobalModelState",
    # threat classifier
    "ThreatClassifier", "ClassificationResult",
    # model monitor
    "ModelDriftMonitor", "ModelSnapshot", "DriftAlert", "DriftSeverity",
    # privacy
    "DifferentialPrivacyEngine", "PrivacyAccountant",
    # scenario generator
    "AttackScenarioGenerator", "ATTACK_LABELS", "FEATURE_NAMES",
    # evaluator
    "ModelEvaluator", "EvaluationResult", "ClassMetrics",
    # byzantine defense
    "ByzantineDefenseEngine",
    # explainability
    "ThreatExplainer", "Explanation",
    # fl coordinator
    "FLCoordinator", "RoundConfig", "RoundSummary",
    # federated gan
    "FederatedGAN", "Generator", "Discriminator", "GANTrainMetrics",
]
