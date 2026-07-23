"""
strategy_validator.py — Strategy configuration validation and health auditing.
"""

from typing import Dict, Any, List, Tuple
from app.services.explainability.registry.features import METADATA_REGISTRY

# Define dependency relationships for features
FEATURE_DEPENDENCIES = {
    "macd_signal": ["macd"],
    "volume_confirmation": ["resistance_break", "donchian_breakout"],
    "confidence_inverse": ["baseline", "consensus_boost"],
}

def validate_strategy_config(definition: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate strategy definition dictionary and return validation diagnostics,
    health score breakdown, complexity, and estimated behavior.
    """
    errors: List[str] = []
    warnings: List[str] = []
    
    features = definition.get("features", [])
    weights = definition.get("weights", [])
    scoring_config = definition.get("scoring_config", {})
    
    # 1. Base validation
    if not features:
        errors.append("No features selected. You must select at least one feature.")
        
    enabled_features = [f for f in features if f.get("enabled", True)]
    enabled_feature_ids = {f["feature_id"] for f in enabled_features if "feature_id" in f}
    
    # Ensure no duplicate features selected
    feature_ids_all = [f["feature_id"] for f in features if "feature_id" in f]
    if len(feature_ids_all) != len(set(feature_ids_all)):
        errors.append("Duplicate feature selections detected in configuration.")

    # 2. Weights validation
    weight_map = {}
    total_weight = 0.0
    for w in weights:
        fid = w.get("feature_id")
        wt = w.get("weight", 0.0)
        weight_map[fid] = wt
        if fid in enabled_feature_ids:
            total_weight += wt
            
        # Enforce weight >= 0
        if wt < 0:
            errors.append(f"Feature '{fid}' has invalid weight {wt}%. Weights cannot be negative.")

    # Require non-zero total weight allocation across enabled features
    if enabled_features and total_weight <= 0:
        errors.append("Total weight allocation across enabled features must be greater than 0%.")

    if enabled_features and abs(total_weight - 100.0) > 0.5:
        warnings.append(f"Total weight is {total_weight:.1f}%. Weights will be normalized to 100% during scoring.")

    # 3. Thresholds validation
    t_buy = scoring_config.get("threshold_buy", 35.0)
    t_hold = scoring_config.get("threshold_hold", -15.0)
    t_sell = scoring_config.get("threshold_sell", -15.0)
    
    if t_buy < t_hold:
        errors.append(f"Invalid thresholds: Buy threshold ({t_buy}) cannot be lower than Hold threshold ({t_hold}).")
    if t_hold < t_sell:
        errors.append(f"Invalid thresholds: Hold threshold ({t_hold}) cannot be lower than Sell threshold ({t_sell}).")

    # 4. Dependency checks
    for fid in enabled_feature_ids:
        deps = FEATURE_DEPENDENCIES.get(fid, [])
        for dep in deps:
            if dep not in enabled_feature_ids:
                warnings.append(f"Missing dependency: feature '{fid}' performs best when '{dep}' is also selected.")

    # 5. Component-wise Health Score Calculation (Max 100 pts)
    # Component A: Diversification (Max 20)
    # Count unique categories represented in selected features
    categories = set()
    for fid in enabled_feature_ids:
        feat_meta = METADATA_REGISTRY.get(fid)
        if feat_meta:
            categories.add(feat_meta.get("category"))
    
    # 4 points per category, capped at 20
    diversification_score = min(len(categories) * 4, 20)
    if len(categories) <= 1:
        warnings.append("Low diversification: Strategy is concentrated in a single feature category.")

    # Component B: Weight Balance (Max 20)
    max_weight = max(weight_map.values()) if weight_map else 0.0
    if max_weight <= 15.0:
        weight_balance_score = 20
    elif max_weight <= 30.0:
        weight_balance_score = 15
    elif max_weight <= 50.0:
        weight_balance_score = 10
    else:
        weight_balance_score = 5
        max_feat = max(weight_map, key=weight_map.get) if weight_map else ""
        warnings.append(f"High concentration: Feature '{max_feat}' holds {max_weight}% of the strategy weight.")

    # Component C: Feature Independence (Max 20)
    # Look for overlaps like multiple EMAs or MACDs
    ema_count = sum(1 for fid in enabled_feature_ids if fid.startswith("ema"))
    macd_count = sum(1 for fid in enabled_feature_ids if fid.startswith("macd"))
    
    independence_deductions = 0
    if ema_count > 1:
        independence_deductions += (ema_count - 1) * 3
    if macd_count > 1:
        independence_deductions += (macd_count - 1) * 3
        
    feature_independence_score = max(20 - independence_deductions, 5)
    if independence_deductions > 5:
        warnings.append("High collinearity risk: Strategy contains multiple highly correlated moving averages or oscillators.")

    # Component D: Normalization Validity (Max 20)
    # Deduct 5 points per unrecognized normalization type
    norm_deductions = 0
    for w in weights:
        method = w.get("normalization_method", "Default")
        if method not in ["Default", "Min-Max", "Z-Score", "Percentile Rank"]:
            norm_deductions += 5
            
    normalization_score = max(20 - norm_deductions, 5)

    # Component E: Risk/Reliability Coverage (Max 20)
    # Checks if risk and telemetry coverage exist
    has_risk = any(METADATA_REGISTRY.get(fid, {}).get("category") in ["Systematic Volatility", "Drawdown Risk"] for fid in enabled_feature_ids)
    has_reliability = any(METADATA_REGISTRY.get(fid, {}).get("category") in ["Model Performance", "Data & Telemetry"] for fid in enabled_feature_ids)
    
    if has_risk and has_reliability:
        risk_coverage_score = 20
    elif has_risk or has_reliability:
        risk_coverage_score = 10
        warnings.append("Partial coverage: Add both risk and reliability/telemetry features to improve strategy robustness.")
    else:
        risk_coverage_score = 0
        warnings.append("No risk coverage: Strategy does not include risk or reliability telemetry features.")

    overall_health = diversification_score + weight_balance_score + feature_independence_score + normalization_score + risk_coverage_score

    # 6. Complexity classification
    features_count = len(enabled_feature_ids)
    if features_count <= 4:
        complexity = "Low"
    elif features_count <= 8:
        complexity = "Medium"
    else:
        complexity = "High"

    # 7. Estimated Behavior
    # Assess conservative vs aggressive based on features weight profile
    # Heavy weights on ML models and GRUs makes it aggressive, heavy weights on baseline, moving averages, and risk makes it conservative
    ml_gru_weight = sum(wt for fid, wt in weight_map.items() if fid in enabled_feature_ids and METADATA_REGISTRY.get(fid, {}).get("category") in ["Ensemble Models", "GRU Neural Components"])
    risk_weight = sum(wt for fid, wt in weight_map.items() if fid in enabled_feature_ids and METADATA_REGISTRY.get(fid, {}).get("category") in ["Systematic Volatility", "Drawdown Risk"])
    
    if ml_gru_weight > 50.0:
        estimated_behavior = "Aggressive"
    elif risk_weight > 30.0:
        estimated_behavior = "Conservative"
    else:
        estimated_behavior = "Moderate"

    return {
        "valid": len(errors) == 0,
        "health_score": overall_health,
        "health_breakdown": {
            "diversification": diversification_score,
            "weight_balance": weight_balance_score,
            "feature_independence": feature_independence_score,
            "normalization": normalization_score,
            "risk_coverage": risk_coverage_score,
            "overall": overall_health,
        },
        "errors": errors,
        "warnings": warnings,
        "complexity": complexity,
        "estimated_behavior": estimated_behavior,
    }
