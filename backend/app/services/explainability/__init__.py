from .technical import TechnicalExplainer
from .ensemble import EnsembleExplainer
from .gru import GruExplainer
from .momentum import MomentumExplainer
from .trend import TrendExplainer
from .risk import RiskExplainer
from .reliability import ReliabilityExplainer
from .confidence import ConfidenceExplainer
from .composite import CompositeExplainer

EXPLAINERS = {
    "technical": TechnicalExplainer(),
    "ensemble": EnsembleExplainer(),
    "gru": GruExplainer(),
    "momentum": MomentumExplainer(),
    "trend": TrendExplainer(),
    "risk": RiskExplainer(),
    "reliability": ReliabilityExplainer(),
    "confidence": ConfidenceExplainer(),
    "composite": CompositeExplainer(),
}
