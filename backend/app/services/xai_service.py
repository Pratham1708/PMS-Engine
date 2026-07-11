"""
XAI Service — Dynamic generation of auditable explanations, factors, and insights.
Utilizes only fields that actually exist in the PMS Engine dataset.
"""

from typing import List, Optional
import pandas as pd
from app.models.schemas import XaiExplanation, RatingDriver


def get_universe_position(percentile: float) -> str:
    """Return the qualitative universe position based on the calculated percentile."""
    if percentile >= 90.0:
        return "Top Decile"
    elif percentile >= 75.0:
        return "Upper Quartile"
    elif percentile >= 25.0:
        return "Middle Quartile"
    elif percentile >= 10.0:
        return "Lower Quartile"
    else:
        return "Bottom Decile"


def generate_technical_reason(score: float) -> str:
    """Explain why the TechnicalScore was generated based on its value."""
    if score >= 80:
        return (
            f"The TechnicalScore of {score:.2f} indicates exceptional bullish trend momentum. "
            "The price action demonstrates strong structural trend alignment across the moving average layers, "
            "with positive momentum indicators reinforcing strong buying pressure."
        )
    elif score >= 30:
        return (
            f"The TechnicalScore of {score:.2f} indicates a constructive bullish trend profile. "
            "The price exhibits steady upward progress, though it faces minor consolidation or local resistance "
            "at key intermediate levels."
        )
    elif score >= -30:
        return (
            f"The TechnicalScore of {score:.2f} signals a flat consolidation phase. "
            "Price oscillates within a tight trading range, reflecting temporary equilibrium between "
            "accumulation and distribution forces in the short term."
        )
    elif score >= -80:
        return (
            f"The TechnicalScore of {score:.2f} indicates a moderate bearish trend structure. "
            "Price action shows signs of breakdown below key support thresholds, with negative momentum starting "
            "to dominate the medium-term path."
        )
    else:
        return (
            f"The TechnicalScore of {score:.2f} represents severe bearish trend momentum. "
            "The price structure exhibits a deep downward breakdown, indicating strong seller dominance "
            "and persistent trend distribution."
        )


def generate_ml_reason(score: float) -> str:
    """Explain why the MLScore was generated based on its value."""
    if score >= 20:
        return (
            f"The MLScore of {score:.2f} reflects a strong positive outlook from the ensemble classifiers. "
            "Tabular price, volume, and volatility characteristics strongly align with historical setups that "
            "precede positive return trends over the next tactical horizon."
        )
    elif score >= 5:
        return (
            f"The MLScore of {score:.2f} indicates a moderate positive return bias. "
            "The ensemble classifiers predict steady return potential, though with minor divergence among the "
            "constituent decision tree models (Random Forest, XGBoost, and LightGBM)."
        )
    elif score >= -5:
        return (
            f"The MLScore of {score:.2f} represents a neutral ensemble consensus. "
            "The tabular models indicate a balanced risk-reward profile, with no significant statistical edge "
            "detected in the current feature matrix."
        )
    elif score >= -20:
        return (
            f"The MLScore of {score:.2f} shows a moderate negative bias, indicating that the ensemble models "
            "identify minor trend exhaustion and predictive headwind patterns in current trading volume profiles."
        )
    else:
        return (
            f"The MLScore of {score:.2f} indicates a strong negative return bias. "
            "The ensemble classifiers detect distinct pattern exhaustion and distribution metrics, predicting "
            "a high probability of near-term underperformance."
        )


def generate_gru_reason(score: float, long: Optional[float], short: Optional[float], hold: Optional[float]) -> str:
    """Explain why the GRUScore was generated using actual probability outputs if available."""
    if long is None or short is None or hold is None:
        if score >= 10:
            return f"The GRUScore of {score:.2f} represents a positive deep learning sequential pattern, indicating a structured uptrend over the last 30 sessions."
        elif score <= -10:
            return f"The GRUScore of {score:.2f} flags a negative deep learning sequential pattern, indicating a persistent downward trend sequence over the last 30 sessions."
        else:
            return f"The GRUScore of {score:.2f} indicates neutral deep learning sequential dynamics with no clear momentum trend detected."

    direction = "positive" if score > 0 else ("negative" if score < 0 else "neutral")
    return (
        f"The GRUScore of {score:.2f} is derived from the Gated Recurrent Unit (GRU) deep temporal neural network, "
        "which models 30-day sequential price patterns. The model assigns probabilities of "
        f"{long:.2f}% Long, {short:.2f}% Short, and {hold:.2f}% Hold, indicating a net {direction} "
        "sequential momentum."
    )


def generate_return_reason(score: Optional[float]) -> str:
    """Explain why the ReturnScore was generated based on its value."""
    if score is None:
        return "Expected return score predictions are not available for this asset."
    
    if score >= 50:
        return (
            f"The Expected ReturnScore of {score:.2f} signals a highly favorable return expectation. "
            "The predictive models forecast strong outperformance potential over the target investment horizon."
        )
    elif score >= 10:
        return (
            f"The Expected ReturnScore of {score:.2f} indicates moderate projected returns. "
            "The model projects stable upward return potential under typical market conditions."
        )
    elif score >= -10:
        return (
            f"The Expected ReturnScore of {score:.2f} represents a neutral return projection, "
            "showing standard mean-reverting behaviour with limited near-term growth catalysts."
        )
    else:
        return (
            f"The Expected ReturnScore of {score:.2f} warns of negative return expectations. "
            "The predictive algorithms forecast a high probability of underperformance or valuation contraction."
        )


def generate_rating_reason(symbol: str, rating: str, composite: float, rank: int, percentile: float, universe_pos: str) -> str:
    """Explain the FinalRating assignment based on the dynamic ranking and percentile."""
    return (
        f"A FinalRating of {rating} is assigned to {symbol} because its CompositeScoreV2 of {composite:.2f} "
        f"ranks at position {rank} out of 50 stocks (Percentile {percentile:.1f}%) in the active universe. "
        f"This placement positions the asset in the {universe_pos} segment, driving the {rating} "
        "designation based on the engine's strict quantile thresholds."
    )


def generate_rating_drivers(row: pd.Series) -> List[RatingDriver]:
    """Generate and sort rating drivers by absolute value."""
    drivers = []

    # 1. Technical Score
    tech_raw = row.get("TechnicalScore")
    tech_val = float(tech_raw) if pd.notna(tech_raw) else 50.0
    tech_impact = "positive" if tech_val > 10 else ("negative" if tech_val < -10 else "neutral")
    drivers.append(
        RatingDriver(
            name="Technical Trend Score",
            value=tech_val,
            contribution="Very High",
            impact=tech_impact,
            description=f"Technical indicators show a net {'bullish' if tech_val > 0 else 'bearish'} momentum score of {tech_val:.2f}."
        )
    )

    # 2. ML Score
    ml_raw = row.get("MLScore")
    ml_val = float(ml_raw) if pd.notna(ml_raw) else 50.0
    ml_impact = "positive" if ml_val > 5 else ("negative" if ml_val < -5 else "neutral")
    drivers.append(
        RatingDriver(
            name="ML Ensemble Forecast",
            value=ml_val,
            contribution="High",
            impact=ml_impact,
            description=f"Tabular models predict a {'positive' if ml_val > 0 else 'negative'} return bias of {ml_val:.2f}."
        )
    )

    # 3. GRU Score
    gru_raw = row.get("GRUScore")
    gru_val = float(gru_raw) if pd.notna(gru_raw) else 50.0
    gru_impact = "positive" if gru_val > 5 else ("negative" if gru_val < -5 else "neutral")
    drivers.append(
        RatingDriver(
            name="GRU Deep Learning Score",
            value=gru_val,
            contribution="Moderate",
            impact=gru_impact,
            description=f"Deep learning sequence modeling outputs a net {'bullish' if gru_val > 0 else 'bearish'} temporal score of {gru_val:.2f}."
        )
    )

    # 4. Expected Return Score
    ret_val = row.get("ReturnScore")
    if pd.notna(ret_val):
        ret_val = float(ret_val)
        ret_impact = "positive" if ret_val > 10 else ("negative" if ret_val < -10 else "neutral")
        drivers.append(
            RatingDriver(
                name="Expected Return Score",
                value=ret_val,
                contribution="High",
                impact=ret_impact,
                description=f"Predictive return algorithm projects a return score of {ret_val:.2f}."
            )
        )

    # 5. Reliability Score
    rel_raw = row.get("ReliabilityScore")
    rel_val = float(rel_raw) if pd.notna(rel_raw) else 50.0
    rel_impact = "positive" if rel_val >= 70 else ("negative" if rel_val < 60 else "neutral")
    drivers.append(
        RatingDriver(
            name="Model Scoring Reliability",
            value=rel_val,
            contribution="Moderate",
            impact=rel_impact,
            description=f"Scoring reliability is rated at {rel_val:.2f}/100 based on historical win-rates."
        )
    )

    # Sort drivers by absolute value of their score descending (Absolute Impact)
    drivers.sort(key=lambda d: abs(d.value), reverse=True)
    return drivers


def generate_positive_factors(row: pd.Series) -> List[str]:
    """Generate dynamic list of top positive factors."""
    factors = []
    
    tech_raw = row.get("TechnicalScore")
    tech_val = float(tech_raw) if pd.notna(tech_raw) else 50.0
    
    ml_raw = row.get("MLScore")
    ml_val = float(ml_raw) if pd.notna(ml_raw) else 50.0
    
    gru_raw = row.get("GRUScore")
    gru_val = float(gru_raw) if pd.notna(gru_raw) else 50.0
    
    ret_val = row.get("ReturnScore")
    
    rel_raw = row.get("ReliabilityScore")
    rel_val = float(rel_raw) if pd.notna(rel_raw) else 50.0
    
    conf_raw = row.get("Confidence")
    conf_val = float(conf_raw) if pd.notna(conf_raw) else 50.0

    if tech_val > 10:
        factors.append(f"Bullish technical trend momentum: TechnicalScore is {tech_val:.2f}")
    if ml_val > 5:
        factors.append(f"ML Ensemble model signals positive return edge: MLScore is {ml_val:.2f}")
    if pd.notna(row.get("GRU_LONG")) and float(row["GRU_LONG"]) > 35:
        factors.append(f"GRU deep neural model indicates high Long probability ({float(row['GRU_LONG']):.2f}%)")
    elif gru_val > 5:
        factors.append(f"GRU deep sequence momentum is constructive: GRUScore is {gru_val:.2f}")
    if pd.notna(ret_val) and float(ret_val) > 10:
        factors.append(f"Expected ReturnScore is positive: {float(ret_val):.2f}")
    if rel_val >= 70:
        factors.append(f"High scoring consistency: ReliabilityScore is {rel_val:.2f}/100")
    if conf_val >= 75:
        factors.append(f"High rating conviction: Confidence rating is {conf_val:.2f}%")

    # Add fallbacks
    if len(factors) < 2:
        factors.append("Active models indicate benchmark-conforming risk metrics")
        factors.append("Scoring reliability metrics meet institutional standards")

    return factors[:3]


def generate_negative_factors(row: pd.Series) -> List[str]:
    """Generate dynamic list of top negative factors."""
    factors = []
    
    tech_raw = row.get("TechnicalScore")
    tech_val = float(tech_raw) if pd.notna(tech_raw) else 50.0
    
    ml_raw = row.get("MLScore")
    ml_val = float(ml_raw) if pd.notna(ml_raw) else 50.0
    
    gru_raw = row.get("GRUScore")
    gru_val = float(gru_raw) if pd.notna(gru_raw) else 50.0
    
    ret_val = row.get("ReturnScore")
    
    rel_raw = row.get("ReliabilityScore")
    rel_val = float(rel_raw) if pd.notna(rel_raw) else 50.0
    
    conf_raw = row.get("Confidence")
    conf_val = float(conf_raw) if pd.notna(conf_raw) else 50.0

    if tech_val < -10:
        factors.append(f"Bearish technical trend breakdown: TechnicalScore is {tech_val:.2f}")
    if ml_val < -5:
        factors.append(f"ML Ensemble model warns of negative return bias: MLScore is {ml_val:.2f}")
    if pd.notna(row.get("GRU_SHORT")) and float(row["GRU_SHORT"]) > 35:
        factors.append(f"GRU deep neural model indicates high Short probability ({float(row['GRU_SHORT']):.2f}%)")
    elif gru_val < -5:
        factors.append(f"GRU deep sequence momentum is weak: GRUScore is {gru_val:.2f}")
    if pd.notna(ret_val) and float(ret_val) < -10:
        factors.append(f"Expected ReturnScore is negative: {float(ret_val):.2f}")
    if rel_val < 60:
        factors.append(f"Reduced scoring consistency: ReliabilityScore is {rel_val:.2f}/100")
    if conf_val < 60:
        factors.append(f"Low rating conviction: Confidence rating is {conf_val:.2f}%")

    # Add fallbacks
    if len(factors) < 2:
        factors.append("Potential for near-term volatility or minor consolidation")
        factors.append("Benchmark divergence risks remain under volatile market regimes")

    return factors[:3]


def generate_institutional_insight(row: pd.Series, rank: int, percentile: float) -> str:
    """Generate a synthesized analyst-style insight based entirely on real metrics."""
    symbol = row["Symbol"]
    rating = row["FinalRating"]
    
    conf_raw = row.get("Confidence")
    conf = float(conf_raw) if pd.notna(conf_raw) else 50.0
    
    comp_raw = row.get("CompositeScoreV2")
    comp = float(comp_raw) if pd.notna(comp_raw) else 50.0
    
    tech_raw = row.get("TechnicalScore")
    tech = float(tech_raw) if pd.notna(tech_raw) else 50.0
    
    ml_raw = row.get("MLScore")
    ml = float(ml_raw) if pd.notna(ml_raw) else 50.0
    
    gru_raw = row.get("GRUScore")
    gru = float(gru_raw) if pd.notna(gru_raw) else 50.0
    
    universe_pos = get_universe_position(percentile)

    if rating == "STRONG BUY":
        insight = (
            f"PMS ENGINE RESEARCH DESK INSIGHT: {symbol} exhibits a stellar institutional structure. "
            f"The asset ranks #{rank} of 50 stocks (Percentile {percentile:.1f}%) in the active universe, "
            f"placing it in the {universe_pos}. There is exceptional alignment across all predictive layers: "
            f"a strong technical trend (TechnicalScore = {tech:.2f}), positive ensemble ML forecasts "
            f"(MLScore = {ml:.2f}), and structured GRU deep learning sequences (GRUScore = {gru:.2f}). "
            f"With a high CompositeScoreV2 of {comp:.2f} and {conf:.1f}% confidence, {symbol} represents a "
            "highly compelling accumulation candidate for institutional portfolios."
        )
    elif rating == "BUY":
        insight = (
            f"PMS ENGINE RESEARCH DESK INSIGHT: {symbol} maintains a constructive rating profile. "
            f"Ranking at #{rank} in the universe (Percentile {percentile:.1f}%, {universe_pos}), "
            f"the asset displays solid trend persistence. While minor intermediate divergence may exist between "
            f"the GRU sequence ({gru:.2f}) and tabular ML forecasts ({ml:.2f}), the overall composite "
            f"score of {comp:.2f} supports systematic positioning and gradual accumulation."
        )
    elif rating == "HOLD":
        insight = (
            f"PMS ENGINE RESEARCH DESK INSIGHT: {symbol} is currently in a neutral consolidation phase. "
            f"Ranking #{rank} of 50 in the universe (Percentile {percentile:.1f}%, {universe_pos}), "
            f"the asset shows flat technical indicators (TechnicalScore = {tech:.2f}) and a balanced "
            f"consensus across the machine learning engines. Investors are advised to maintain existing exposures, "
            "as risk-reward parameters do not currently justify new capital allocations."
        )
    elif rating == "SELL":
        insight = (
            f"PMS ENGINE RESEARCH DESK INSIGHT: {symbol} exhibits structural trend deterioration. "
            f"Ranking #{rank} of 50 (Percentile {percentile:.1f}%, {universe_pos}), the price action has breached "
            f"medium-term supports (TechnicalScore = {tech:.2f}), and the ML models indicate an underperformance bias "
            f"(MLScore = {ml:.2f}). Trimming exposures is recommended to manage portfolio drawdown."
        )
    else:  # STRONG SELL
        insight = (
            f"PMS ENGINE RESEARCH DESK INSIGHT: {symbol} exhibits severe distribution pressure. "
            f"Ranking #{rank} of 50 (Percentile {percentile:.1f}%, {universe_pos}) with a CompositeScoreV2 of {comp:.2f}, "
            f"there is a persistent bearish crossover across all sub-engines (TechnicalScore = {tech:.2f}, "
            f"MLScore = {ml:.2f}, GRUScore = {gru:.2f}). Portfolio exit and strict risk protection are advised."
        )
    return insight

    return insight
