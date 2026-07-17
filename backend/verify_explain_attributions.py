import sys
import os
import json

# Add backend directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../backend")))

# Setup dummy app settings if needed
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.services.explainability import EXPLAINERS

def run_verification():
    print("=======================================")
    print("PMS ENGINE EXPLAINABILITY VERIFICATION")
    print("=======================================")
    
    # Construct mock stock data inputs
    mock_stock_data = {
        "Symbol": "RELIANCE",
        "Close": 2450.0,
        "CurrentPrice": 2455.0,
        "TechnicalScore": 85.0,
        "MLScore": 72.0,
        "GRUScore": 64.0,
        "ReliabilityScore": 88.0,
        "Confidence": 80.0,
        "CompositeScoreV2": 78.5,
        "GRU_LONG": 65.0,
        "GRU_HOLD": 25.0,
        "GRU_SHORT": 10.0,
        "scores": {
            "w_technical": 0.40,
            "w_ml": 0.35,
            "w_gru": 0.15,
            "w_reliability": 0.10,
            "rf_signal": 68.0,
            "xgb_signal": 75.0,
            "lgbm_signal": 73.0,
        },
        "indicators": {
            "above_ema20": 1,
            "above_ema50": 1,
            "above_ema200": 1,
            "adx": 28.5,
            "supertrend_signal": 1,
            "rsi_14": 62.5,
            "macd": 15.4,
            "macd_signal": 12.1,
            "stoch_k": 71.0,
            "cci": 115.0,
            "roc": 2.4,
            "williams_r": -18.0,
            "bb_upper": 2500.0,
            "bb_lower": 2400.0,
            "atr": 45.0,
            "atr_percentile": 38.0,
            "beta": 1.15,
            "hist_vol": 22.4,
            "sharpe": 1.45,
            "max_drawdown": -12.4
        }
    }
    
    mock_history = [
        {"snapshot_date": "2026-07-14", "technical_score": 82.0, "ml_score": 70.0, "gru_score": 60.0, "reliability_score": 85.0, "confidence": 78.0, "composite_score": 75.5},
        {"snapshot_date": "2026-07-13", "technical_score": 80.0, "ml_score": 68.0, "gru_score": 58.0, "reliability_score": 85.0, "confidence": 78.0, "composite_score": 73.5}
    ]
    
    all_ok = True
    
    for score_type, explainer in EXPLAINERS.items():
        print(f"\n[TESTING ENGINE] score_type: '{score_type}'")
        try:
            res = explainer.explain(mock_stock_data, mock_history)
            
            # Basic validation
            assert res.score_type == score_type, f"score_type mismatch: {res.score_type} vs {score_type}"
            assert res.symbol == "RELIANCE", f"symbol mismatch: {res.symbol}"
            
            print(f"  - Value: {res.current_value}")
            print(f"  - Explanation Type: {getattr(res, 'explanation_type', 'N/A')}")
            
            # Hierarchy checks
            feature_attributions = getattr(res, "feature_attributions", [])
            print(f"  - Category Contribution Count: {len(feature_attributions)}")
            
            if len(feature_attributions) == 0:
                print("    WARNING: Zero category contributions found!")
                all_ok = False
                
            for cat in feature_attributions:
                print(f"    * Category: '{cat.category}' (Subtotal: {cat.subtotal:.2f})")
                assert len(cat.features) > 0, "Empty features in category!"
                for feat in cat.features:
                    print(f"      + Feature: '{feat.name}' | Key: '{feat.feature_key}' | Contribution: {feat.contribution:+.2f} | Effect: {feat.effect}")
                    
                    # Verify metadata fields are not N/A or empty
                    assert feat.metadata is not None, "Metadata object is missing!"
                    assert feat.metadata.plain_formula != "N/A", f"Formula missing for {feat.feature_key}"
                    assert feat.metadata.normalization is not None, "Normalization missing!"
                    assert feat.metadata.reference is not None, "Reference paper missing!"
            
            print("  [SUCCESS] Explainer passed checks.")
        except Exception as e:
            print(f"  [FAILED] Explainer threw exception: {e}")
            import traceback
            traceback.print_exc()
            all_ok = False
            
    print("\n=======================================")
    if all_ok:
        print("ALL VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    else:
        print("SOME VERIFICATION CHECKS FAILED.")
    print("=======================================")
    
    if not all_ok:
        sys.exit(1)

if __name__ == "__main__":
    run_verification()
