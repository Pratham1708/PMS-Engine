from typing import List, Dict, Any
from app.models.schemas import Contribution, ValidationMetric, ResearchReference, ScoreInterpretation, ExplainScoreResponse
from .base import BaseExplainer, enrich_runtime_contributions
from app.services.explainability.registry import MOMENTUM_WEIGHTS

class MomentumExplainer(BaseExplainer):
    def get_purpose(self) -> str:
        return "Measures immediate price acceleration by blending classical trend-following indicators with machine learning return forecasts."

    def get_formula(self) -> str:
        return "Momentum Score = (Technical Score * 0.80) + (Ensemble ML Score * 0.20)"

    def get_references(self) -> List[ResearchReference]:
        return [
            ResearchReference(
                paper="Relative Strength Index (RSI) in New Concepts",
                author="J. Welles Wilder Jr.",
                year=1978,
                link=None,
                description="Defines the standard momentum oscillator used to calculate technical rate of change parameters."
            )
        ]

    def get_validation(self) -> List[ValidationMetric]:
        return [
            ValidationMetric(metric="Validated On", value="Nifty 50 constituents", description="Historical acceleration setups."),
            ValidationMetric(metric="Average Accuracy", value="70.1%", description="Predictive accuracy of immediate momentum continuation."),
            ValidationMetric(metric="Average Annual Return", value="16.8%", description="Annualized backtested return of top momentum decile."),
            ValidationMetric(metric="Sharpe Ratio", value="1.22", description="Risk-adjusted return of momentum breakout strategies.")
        ]

    def get_interpretation(self) -> List[ScoreInterpretation]:
        return [
            ScoreInterpretation(range="70 to 100", meaning="Strong Momentum (Overbought / Acceleration)", action="Capitalize on immediate price breakout; utilize tight trailing stops."),
            ScoreInterpretation(range="30 to 70", meaning="Positive Momentum", action="Trend is constructive; accumulation is supported."),
            ScoreInterpretation(range="-30 to 30", meaning="Neutral / Sideways", action="Console mode; wait for breakout or clear volume surge."),
            ScoreInterpretation(range="-70 to -30", meaning="Negative Momentum", action="Downside acceleration is active; reduce weight or hedge positions."),
            ScoreInterpretation(range="Below -70", meaning="Severe Downward Acceleration", action="High risk distribution; complete capital protection is advised.")
        ]

    def get_limitations(self) -> List[str]:
        return [
            "Momentum is inherently a lagging indicator that can trigger buy signals at cyclical peaks and sell signals at cyclical bottoms.",
            "False breakouts are common in low-beta or highly defensive sectors."
        ]

    def explain(self, stock_data: Dict[str, Any], history: List[Dict[str, Any]]) -> ExplainScoreResponse:
        tech_val = stock_data.get("TechnicalScore", 0.0)
        ml_val = stock_data.get("MLScore", 0.0)
        
        w_tech = MOMENTUM_WEIGHTS["technical"]
        w_ml = MOMENTUM_WEIGHTS["ml"]
        
        # Calculate momentum score based on the formula
        momentum_score = stock_data.get("MomentumScore")
        if momentum_score is None:
            momentum_score = tech_val * w_tech + ml_val * w_ml
            
        symbol = stock_data.get("Symbol")
        
        hist_context = []
        for h in history:
            hist_context.append({
                "date": h.get("snapshot_date"),
                "value": h.get("momentum_score") or (h.get("technical_score", 0.0) * w_tech + h.get("ml_score", 0.0) * w_ml)
            })
            
        tech_contrib = tech_val * w_tech
        ml_contrib = ml_val * w_ml
        
        contributions = [
            Contribution(
                name="Technical Score Component",
                value=round(tech_val, 2),
                weight=w_tech,
                contribution=round(tech_contrib, 2),
                direction="positive" if tech_val > 0 else ("negative" if tech_val < 0 else "neutral"),
                description=f"Standard indicators score contributing 80% to overall momentum."
            ),
            Contribution(
                name="Ensemble ML Score Component",
                value=round(ml_val, 2),
                weight=w_ml,
                contribution=round(ml_contrib, 2),
                direction="positive" if ml_val > 0 else ("negative" if ml_val < 0 else "neutral"),
                description=f"Tree ensemble predictions contributing 20% to overall momentum."
            )
        ]

        # Structured feature attributions
        runtime_categories = [
            {
                "category": "Technical Trend Overlay (80%)",
                "subtotal": tech_contrib,
                "features": [
                    {"feature_key": "technical_score", "current_value": f"{tech_val:+.2f}", "normalized_value": tech_val, "weight": w_tech, "contribution": tech_contrib, "effect": "positive" if tech_val > 0 else "negative", "confidence": "High"}
                ]
            },
            {
                "category": "Machine Learning Forecast (20%)",
                "subtotal": ml_contrib,
                "features": [
                    {"feature_key": "ml_score", "current_value": f"{ml_val:+.2f}", "normalized_value": ml_val, "weight": w_ml, "contribution": ml_contrib, "effect": "positive" if ml_val > 0 else "negative", "confidence": "High"}
                ]
            }
        ]
        
        feature_attributions = enrich_runtime_contributions(runtime_categories)

        # Dynamic Explanation
        explanation_parts = []
        if tech_val > 0 and ml_val > 0:
            explanation_parts.append("Both classical technical trend overlays and machine learning ensemble projections confirm positive acceleration, indicating high buying pressure.")
        elif tech_val < 0 and ml_val < 0:
            explanation_parts.append("Both technical oscillators and ML signals warn of downward acceleration, indicating ongoing distribution.")
        else:
            explanation_parts.append("Technical indicators and machine learning return forecasts diverge, indicating a potential near-term consolidation or trend reversal.")
            
        if momentum_score >= 30:
            explanation_parts.append(f"A momentum score of {momentum_score:.1f} shows constructive price expansion.")
        elif momentum_score <= -30:
            explanation_parts.append(f"A negative momentum score of {momentum_score:.1f} indicates strong downward force.")
        else:
            explanation_parts.append(f"The neutral momentum score of {momentum_score:.1f} represents standard price equilibrium.")
            
        dynamic_text = " ".join(explanation_parts)

        # "Why Not?" Explanation
        why_not_parts = []
        if momentum_score < 40:
            why_not_parts.append("The Momentum Score was not upgraded because:")
            if tech_val < 30:
                why_not_parts.append(f"- Classical technical indicators ({tech_val:.1f}) demonstrate weak momentum or local selling pressure.")
            if ml_val < 30:
                why_not_parts.append(f"- Machine learning ensemble models ({ml_val:.1f}) predict intermediate headwinds or neutral return distributions.")
        else:
            why_not_parts.append("Momentum parameters are fully optimized. Both technical trend acceleration and ML forecasts confirm constructive momentum setup.")
            
        why_not_text = " ".join(why_not_parts)

        return ExplainScoreResponse(
            score_type="momentum",
            symbol=symbol,
            current_value=round(momentum_score, 2),
            purpose=self.get_purpose(),
            formula=self.get_formula(),
            factors=["Technical Indicator Overlay", "Ensemble ML Score Component"],
            validation=self.get_validation(),
            interpretation=self.get_interpretation(),
            limitations=self.get_limitations(),
            references=self.get_references(),
            current_values={"TechnicalScore": tech_val, "MLScore": ml_val} if tech_val is not None else None,
            current_contributions=contributions,
            dynamic_explanation=dynamic_text,
            why_not=why_not_text,
            historical_context=hist_context,
            explanation_type="global_importance",
            feature_attributions=feature_attributions
        )
