from typing import List, Dict, Any
from app.models.schemas import (
    Contribution,
    ValidationMetric,
    ResearchReference,
    ScoreInterpretation,
    ExplainScoreResponse,
)

class BaseExplainer:
    def get_purpose(self) -> str:
        raise NotImplementedError

    def get_formula(self) -> str:
        raise NotImplementedError

    def get_references(self) -> List[ResearchReference]:
        raise NotImplementedError

    def get_validation(self) -> List[ValidationMetric]:
        raise NotImplementedError

    def get_interpretation(self) -> List[ScoreInterpretation]:
        raise NotImplementedError

    def get_limitations(self) -> List[str]:
        raise NotImplementedError

    def explain(self, stock_data: Dict[str, Any], history: List[Dict[str, Any]]) -> ExplainScoreResponse:
        raise NotImplementedError
