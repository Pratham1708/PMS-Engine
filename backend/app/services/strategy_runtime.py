"""
strategy_runtime.py — Build scoring runtime configuration from canonical JSON strategy definitions.
"""

from typing import Dict, Any, List

def build_runtime_config(definition: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a canonical JSON strategy definition into a flattened runtime scoring profile.
    """
    features = definition.get("features", [])
    weights = definition.get("weights", [])
    scoring_config = definition.get("scoring_config", {})
    
    enabled_feature_ids = {f["feature_id"] for f in features if f.get("enabled", True)}
    
    # Flat mapping of feature_id -> weight (fraction)
    weight_alloc = {}
    for w in weights:
        fid = w.get("feature_id")
        wt = w.get("weight", 0.0)
        if fid in enabled_feature_ids:
            # Convert weight percent to fraction
            weight_alloc[fid] = wt / 100.0

    return {
        "features": list(enabled_feature_ids),
        "weights": weight_alloc,
        "scoring_method": scoring_config.get("scoring_method", "Weighted Average"),
        "threshold_buy": scoring_config.get("threshold_buy", 35.0),
        "threshold_hold": scoring_config.get("threshold_hold", -15.0),
        "threshold_sell": scoring_config.get("threshold_sell", -15.0),
        "normalization": scoring_config.get("normalization", "Default"),
        "recommendation_method": scoring_config.get("recommendation_method", "Standard"),
        "risk_profile": definition.get("risk_profile", "Medium")
    }
