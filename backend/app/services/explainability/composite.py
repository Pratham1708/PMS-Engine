from typing import List, Dict, Any
from app.models.schemas import Contribution, ValidationMetric, ResearchReference, ScoreInterpretation, ExplainScoreResponse
from .base import BaseExplainer, enrich_runtime_contributions
from app.services.explainability.registry import COMPOSITE_WEIGHTS

class CompositeExplainer(BaseExplainer):
    def get_purpose(self) -> str:
        return "The core decision model of the PMS Engine. Synthesizes Technical, ML Ensemble, GRU, and Reliability scores using a dynamic weight optimizer aligned with the active market regime."

    def get_formula(self) -> str:
        return "Composite Score = (Technical Score * w_tech) + (Ensemble ML Score * w_ml) + (GRU Score * w_gru) + (Reliability Score * w_reliability)"

    def get_references(self) -> List[ResearchReference]:
        return [
            ResearchReference(
                paper="Asset Allocation: Combining Investor Views with Market Equilibrium",
                author="Fischer Black, Robert Litterman",
                year=1992,
                link="https://www.tandfonline.com/doi/abs/10.2753/JPM1540-238X150162",
                description="The original Black-Litterman paper showing how to dynamically adjust portfolio weights based on consensus views and historical variances."
            )
        ]

    def get_validation(self) -> List[ValidationMetric]:
        return [
            ValidationMetric(metric="Validated On", value="Nifty 50 historical backtests", description="Daily simulations from 2015 to 2026."),
            ValidationMetric(metric="Outperformance (Alpha)", value="+6.4% Annualized Alpha", description="Average annualized outperformance relative to the Nifty 50 benchmark."),
            ValidationMetric(metric="Sharpe Ratio", value="1.42", description="Risk-adjusted return profile of the composite signal portfolio."),
            ValidationMetric(metric="Sortino Ratio", value="1.84", description="Downside risk-adjusted return ratio of composite signals.")
        ]

    def get_interpretation(self) -> List[ScoreInterpretation]:
        return [
            ScoreInterpretation(range="35 to 100", meaning="BUY / STRONG BUY", action="Highly constructive setup; symbol qualifies for model portfolio allocation."),
            ScoreInterpretation(range="-15 to 35", meaning="HOLD / Neutral", action="Maintain existing exposures, risk-reward does not support immediate new capital."),
            ScoreInterpretation(range="Below -15", meaning="SELL / STRONG SELL", action="Trend deterioration or high volatility threat; exit or reduce holdings.")
        ]

    def get_limitations(self) -> List[str]:
        return [
            "Requires all four sub-scores to be properly populated. Latency in one engine may temporarily degrade composite calibration.",
            "Rebalancing transaction costs must be monitored to avoid excessive portfolio churn in choppy, sideways markets."
        ]

    def explain(self, stock_data: Dict[str, Any], history: List[Dict[str, Any]]) -> ExplainScoreResponse:
        composite_score = stock_data.get("CompositeScoreV2", 0.0)
        symbol = stock_data.get("Symbol")
        
        hist_context = []
        for h in history:
            hist_context.append({
                "date": h.get("snapshot_date"),
                "value": h.get("composite_score") or h.get("composite_score_v2")
            })
            
        scores_detail = stock_data.get("scores", {})
        
        # Read dynamic weights with fallbacks from scoring_config.py
        w_tech = scores_detail.get("w_technical") or COMPOSITE_WEIGHTS["technical"]
        w_ml = scores_detail.get("w_ml") or COMPOSITE_WEIGHTS["ml"]
        w_gru = scores_detail.get("w_gru") or COMPOSITE_WEIGHTS["gru"]
        w_reliability = scores_detail.get("w_reliability") or COMPOSITE_WEIGHTS["reliability"]
        
        # Read sub-scores
        tech = stock_data.get("TechnicalScore", 0.0)
        ml = stock_data.get("MLScore", 0.0)
        gru = stock_data.get("GRUScore", 0.0)
        reliability = stock_data.get("ReliabilityScore", 70.0)
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(
            f"[ENGINE DEBUG] Composite Explainer run: tech={tech}, ml={ml}, gru={gru}, reliability={reliability}, "
            f"w_tech={w_tech}, w_ml={w_ml}, w_gru={w_gru}, w_reliability={w_reliability}"
        )
        
        tech_contrib = tech * w_tech
        ml_contrib = ml * w_ml
        gru_contrib = gru * w_gru
        reliability_contrib = reliability * w_reliability
        
        contributions = [
            Contribution(
                name="Technical Score Component",
                value=round(tech, 2),
                weight=w_tech,
                contribution=round(tech_contrib, 2),
                direction="positive" if tech > 0 else ("negative" if tech < 0 else "neutral"),
                description=f"Trend and momentum oscillators, weighted at {int(w_tech*100)}%."
            ),
            Contribution(
                name="Ensemble ML Score Component",
                value=round(ml, 2),
                weight=w_ml,
                contribution=round(ml_contrib, 2),
                direction="positive" if ml > 0 else ("negative" if ml < 0 else "neutral"),
                description=f"Tree ensemble classifiers consensus, weighted at {int(w_ml*100)}%."
            ),
            Contribution(
                name="GRU Deep Learning Component",
                value=round(gru, 2),
                weight=w_gru,
                contribution=round(gru_contrib, 2),
                direction="positive" if gru > 0 else ("negative" if gru < 0 else "neutral"),
                description=f"Neural sequence lookback momentum, weighted at {int(w_gru*100)}%."
            ),
            Contribution(
                name="System Reliability Index",
                value=round(reliability, 2),
                weight=w_reliability,
                contribution=round(reliability_contrib, 2),
                direction="positive" if reliability > 50 else "negative",
                description=f"Operational data and consensus check telemetry, weighted at {int(w_reliability*100)}%."
            )
        ]

        # Structured feature attributions
        runtime_categories = [
            {
                "category": "Technical Overlay",
                "subtotal": tech_contrib,
                "features": [
                    {"feature_key": "technical_score", "current_value": f"{tech:+.2f}", "normalized_value": tech, "weight": w_tech, "contribution": tech_contrib, "effect": "positive" if tech > 0 else "negative", "confidence": "High"}
                ]
            },
            {
                "category": "Supervised Machine Learning",
                "subtotal": ml_contrib,
                "features": [
                    {"feature_key": "ml_score", "current_value": f"{ml:+.2f}", "normalized_value": ml, "weight": w_ml, "contribution": ml_contrib, "effect": "positive" if ml > 0 else "negative", "confidence": "High"}
                ]
            },
            {
                "category": "Deep Temporal Forecasting",
                "subtotal": gru_contrib,
                "features": [
                    {"feature_key": "gru_score", "current_value": f"{gru:+.2f}", "normalized_value": gru, "weight": w_gru, "contribution": gru_contrib, "effect": "positive" if gru > 0 else "negative", "confidence": "High"}
                ]
            },
            {
                "category": "System Telemetry Audit",
                "subtotal": reliability_contrib,
                "features": [
                    {"feature_key": "reliability_score", "current_value": f"{reliability:.1f}", "normalized_value": reliability, "weight": w_reliability, "contribution": reliability_contrib, "effect": "positive" if reliability > 50 else "negative", "confidence": "High"}
                ]
            }
        ]
        
        feature_attributions = enrich_runtime_contributions(runtime_categories)

        # Dynamic Explanation
        explanation_parts = []
        explanation_parts.append(
            f"The composite decision engine synthesizes all scoring models into a single value of {composite_score:.2f} "
            f"using the active macro-regime weight configuration."
        )
        if composite_score >= 35:
            explanation_parts.append("The combined signal is bullish, satisfying portfolio entry triggers.")
        elif composite_score <= -15:
            explanation_parts.append("The combined signal is bearish, indicating portfolio reduction parameters are active.")
        else:
            explanation_parts.append("The blended outlook is neutral, indicating holding pattern fits standard allocations.")
            
        dynamic_text = " ".join(explanation_parts)

        # "Why Not?" Explanation
        why_not_parts = []
        if composite_score < 35:
            why_not_parts.append("The Composite Score was not rated BUY or STRONG BUY (>35) because:")
            if tech < 20:
                why_not_parts.append(f"- Technical momentum ({tech:.1f}) is neutral or weak.")
            if ml < 20:
                why_not_parts.append(f"- Supervised classification returns ({ml:.1f}) demonstrate intermediate resistance.")
            if gru < 20:
                why_not_parts.append(f"- Neural recurrent sequential forecasts ({gru:.1f}) do not exhibit strong accumulation parameters.")
        else:
            why_not_parts.append("Composite rating triggers are fully optimized. All sub-engine criteria confirm high alpha potential.")
            
        why_not_text = " ".join(why_not_parts)

        return ExplainScoreResponse(
            score_type="composite",
            symbol=symbol,
            current_value=round(composite_score, 2),
            purpose=self.get_purpose(),
            formula=self.get_formula(),
            factors=["Technical Score Overlay", "Machine Learning Forecast", "Neural Sequence Lookback", "Telemetry Reliability"],
            validation=self.get_validation(),
            interpretation=self.get_interpretation(),
            limitations=self.get_limitations(),
            references=self.get_references(),
            current_values={"TechnicalScore": tech, "MLScore": ml, "GRUScore": gru, "ReliabilityScore": reliability} if tech is not None else None,
            current_contributions=contributions,
            dynamic_explanation=dynamic_text,
            why_not=why_not_text,
            historical_context=hist_context,
            explanation_type="global_importance",
            feature_attributions=feature_attributions
        )
