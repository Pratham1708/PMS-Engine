import os
import sys

# Ensure backend directory is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.explainability import EXPLAINERS

def run_tests():
    print("==================================================")
    print("     PMS ENGINE EXPLAINABILITY SYSTEM AUDIT")
    print("==================================================")
    
    # Mock stock data matching expected dictionary shape
    mock_stock = {
        "Symbol": "RELIANCE.NS",
        "TechnicalScore": 85.0,
        "MLScore": 45.0,
        "GRUScore": 60.0,
        "ReliabilityScore": 75.0,
        "RiskScore": 25.0,
        "MomentumScore": 77.0,
        "TrendScore": 70.0,
        "Confidence": 75.0,
        "CompositeScoreV2": 65.5,
        "CurrentPrice": 2450.50,
        "GRU_LONG": 65.0,
        "GRU_HOLD": 20.0,
        "GRU_SHORT": 15.0,
        
        "indicators": {
            "rsi_14": 72.5,
            "ema_20": 2400.0,
            "ema_50": 2350.0,
            "ema_200": 2200.0,
            "above_ema20": 1,
            "above_ema50": 1,
            "above_ema200": 1,
            "macd": 15.4,
            "macd_signal": 12.1,
            "bb_upper": 2500.0,
            "bb_lower": 2300.0,
            "near_52w_high": 1,
            "near_52w_low": 0
        },
        
        "scores": {
            "w_technical": 0.40,
            "w_ml": 0.35,
            "w_gru": 0.15,
            "w_reliability": 0.10,
            "rf_signal": 40.0,
            "xgb_signal": 50.0,
            "lgbm_signal": 45.0
        }
    }
    
    # Mock history records
    mock_history = [
        {"snapshot_date": "2026-07-10", "technical_score": 82.0, "ml_score": 40.0, "gru_score": 58.0, "risk_score": 27.0, "momentum_score": 75.0, "trend_score": 68.0, "confidence": 73.0, "composite_score": 63.0, "reliability_score": 75.0},
        {"snapshot_date": "2026-07-09", "technical_score": 78.0, "ml_score": 38.0, "gru_score": 55.0, "risk_score": 30.0, "momentum_score": 70.0, "trend_score": 65.0, "confidence": 70.0, "composite_score": 60.0, "reliability_score": 75.0}
    ]
    
    passed_count = 0
    
    for key, explainer in EXPLAINERS.items():
        print(f"\nAudit: Testing explainer [{key}]...")
        try:
            # 1. Test basic attributes
            purpose = explainer.get_purpose()
            formula = explainer.get_formula()
            refs = explainer.get_references()
            val = explainer.get_validation()
            interp = explainer.get_interpretation()
            limits = explainer.get_limitations()
            
            assert len(purpose) > 0, "Purpose must not be empty"
            assert len(formula) > 0, "Formula must not be empty"
            assert len(interp) > 0, "Interpretation list must not be empty"
            assert len(limits) > 0, "Limitations list must not be empty"
            
            # 2. Test explanation generation
            res = explainer.explain(mock_stock, mock_history)
            
            # 3. Assert correct schema fields
            assert res.score_type == key
            assert res.current_value is not None
            assert len(res.dynamic_explanation) > 0
            assert len(res.why_not) > 0
            assert len(res.current_contributions) > 0 or key in ["risk", "reliability"] # risk/reliability can have empty if mock
            
            print(f"  Result: PASS")
            print(f"  Current value: {res.current_value}")
            print(f"  Dynamic reason: {res.dynamic_explanation[:80]}...")
            print(f"  Why Not reason: {res.why_not[:80]}...")
            passed_count += 1
            
        except Exception as e:
            print(f"  Result: FAILED — Exception: {e}")
            import traceback
            traceback.print_exc()

    print("\n==================================================")
    print(f"Audit Summary: {passed_count}/{len(EXPLAINERS)} explainers passed validation.")
    print("==================================================")

def test_routes():
    print("\n==================================================")
    print("     PMS ENGINE EXPLAIN ROUTE TEST")
    print("==================================================")
    try:
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)
        
        # Test default endpoint without symbol (conceptual explanation)
        response = client.get("/api/explain/technical")
        print(f"Status Code without symbol: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        print(f"Success: Technical explanation fetched.")
        print(f"Purpose: {data.get('purpose')}")
        assert data.get("score_type") == "technical"
            
        # Test invalid endpoint
        response_invalid = client.get("/api/explain/nonexistent")
        print(f"Status Code for invalid: {response_invalid.status_code}")
        assert response_invalid.status_code == 404
        
        print("\nAll routes test: PASS")

    except Exception as e:
        print(f"Routes test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_tests()
    test_routes()
