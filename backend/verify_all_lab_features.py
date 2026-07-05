import time
import requests
import json
import sys

BASE_URL = "http://localhost:8000/api"

def run_tests():
    print("=" * 60)
    print("   PMS QUANT LAB FEATURES VERIFICATION SCRIPT")
    print("=" * 60)
    print()

    # Wait for server to start if not yet ready
    for attempt in range(10):
        try:
            r = requests.get(f"{BASE_URL.replace('/api', '')}/api/docs", timeout=2)
            if r.status_code == 200:
                print("[SUCCESS] Server is online and ready.")
                break
        except Exception:
            pass
        print(f"[INFO] Waiting for server (attempt {attempt+1}/10)...")
        time.sleep(3)
    else:
        print("[ERROR] Server did not start. Exiting.")
        sys.exit(1)

    all_passed = True

    # ----------------------------------------------------
    # 1. INDICATOR LAB
    # ----------------------------------------------------
    print("\n--- Testing Feature 1: Indicator Lab ---")
    try:
        # Test List Indicators
        r_list = requests.get(f"{BASE_URL}/lab/indicators", timeout=10)
        assert r_list.status_code == 200, f"Expected 200, got {r_list.status_code}"
        indicators = r_list.json()
        print(f"[OK] GET /api/lab/indicators: Returned {len(indicators)} indicators")

        # Test Start Indicator Backtest
        payload = {
            "symbol": "RELIANCE.NS",
            "indicator": "rsi",
            "params": {"period": 14},
            "period": "3Y"
        }
        r_run = requests.post(f"{BASE_URL}/lab/indicator/run", json=payload, timeout=10)
        assert r_run.status_code == 200, f"Expected 200, got {r_run.status_code}"
        res = r_run.json()
        print(f"[OK] POST /api/lab/indicator/run: Started backtest, ID = {res.get('experiment_id')}, Status = {res.get('status')}")
    except Exception as e:
        print(f"[FAIL] Indicator Lab failed: {e}")
        all_passed = False

    # ----------------------------------------------------
    # 2. CROSS-INDICATOR LAB
    # ----------------------------------------------------
    print("\n--- Testing Feature 2: Cross-Indicator Lab ---")
    try:
        payload = {
            "symbol": "RELIANCE.NS",
            "period": "3Y",
            "target_metric": "sharpe"
        }
        r = requests.post(f"{BASE_URL}/lab/cross-indicator/run", json=payload, timeout=30)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        res = r.json()
        print(f"[OK] POST /api/lab/cross-indicator/run: Backtest complete. Best strategy metric: {res.get('best_metric_value', 'N/A')}")
        print(f"     Found {len(res.get('ranked_strategies', []))} combinations ranked.")
    except Exception as e:
        print(f"[FAIL] Cross-Indicator Lab failed: {e}")
        all_passed = False

    # ----------------------------------------------------
    # 3. ENGINE VALIDATION
    # ----------------------------------------------------
    print("\n--- Testing Feature 3: Engine Validation ---")
    try:
        # Test Score Distribution
        r_dist = requests.get(f"{BASE_URL}/lab/engine/score-distribution?score_column=TechnicalScore", timeout=10)
        assert r_dist.status_code == 200, f"Expected 200, got {r_dist.status_code}"
        dist = r_dist.json()
        print(f"[OK] GET /api/lab/engine/score-distribution: TechnicalScore distribution has {len(dist.get('histogram', []))} bins")

        # Test Validate Engine
        payload = {"horizon": "1M"}
        r_val = requests.post(f"{BASE_URL}/lab/engine/validate", json=payload, timeout=10)
        assert r_val.status_code == 200, f"Expected 200, got {r_val.status_code}"
        res = r_val.json()
        print(f"[OK] POST /api/lab/engine/validate: Validation triggered, ID = {res.get('experiment_id')}, Status = {res.get('status')}")
    except Exception as e:
        print(f"[FAIL] Engine Validation failed: {e}")
        all_passed = False

    # ----------------------------------------------------
    # 4. MODEL LAB
    # ----------------------------------------------------
    print("\n--- Testing Feature 4: Model Lab ---")
    try:
        # Test List Models
        r_list = requests.get(f"{BASE_URL}/lab/models/list", timeout=10)
        assert r_list.status_code == 200, f"Expected 200, got {r_list.status_code}"
        models = r_list.json()
        model_names = [m["name"] if isinstance(m, dict) else m for m in models]
        print(f"[OK] GET /api/lab/models/list: Available models: {', '.join(model_names)}")

        # Test Feature Importance
        r_imp = requests.get(f"{BASE_URL}/lab/models/feature-importance", timeout=10)
        assert r_imp.status_code == 200, f"Expected 200, got {r_imp.status_code}"
        imp = r_imp.json()
        print(f"[OK] GET /api/lab/models/feature-importance: Returned {len(imp.get('importance', {}))} model feature importances")
    except Exception as e:
        print(f"[FAIL] Model Lab failed: {e}")
        all_passed = False

    # ----------------------------------------------------
    # 5. FEATURE LAB
    # ----------------------------------------------------
    print("\n--- Testing Feature 5: Feature Lab ---")
    try:
        r = requests.get(f"{BASE_URL}/lab/features/full-analysis", timeout=15)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        res = r.json()
        print(f"[OK] GET /api/lab/features/full-analysis: Succeeded")
        print(f"     Correlation matrix size: {len(res.get('correlation', []))} columns")
        print(f"     VIF features evaluated: {len(res.get('vif', []))}")
        print(f"     Mutual Information features: {len(res.get('mutual_information', {}))}")
    except Exception as e:
        print(f"[FAIL] Feature Lab failed: {e}")
        all_passed = False

    # ----------------------------------------------------
    # 6. COMPOSITE LAB
    # ----------------------------------------------------
    print("\n--- Testing Feature 6: Composite Lab ---")
    try:
        # Test Current Weights Analysis
        r_curr = requests.get(f"{BASE_URL}/lab/composite/current-analysis", timeout=10)
        assert r_curr.status_code == 200, f"Expected 200, got {r_curr.status_code}"
        curr = r_curr.json()
        print(f"[OK] GET /api/lab/composite/current-analysis: Sub-scores evaluated: {len(curr.get('partial_correlations', {}))}")

        # Test Regime Optimal Weights
        r_reg = requests.get(f"{BASE_URL}/lab/composite/regime-weights", timeout=15)
        assert r_reg.status_code == 200, f"Expected 200, got {r_reg.status_code}"
        reg = r_reg.json()
        print(f"[OK] GET /api/lab/composite/regime-weights: Optimal weight sets found: {list(reg.get('regime_weights', {}).keys())}")
    except Exception as e:
        print(f"[FAIL] Composite Lab failed: {e}")
        all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("          ALL LAB CORE FEATURES VERIFIED: SUCCESS!")
    else:
        print("         SOME LAB CORE FEATURES FAILED VERIFICATION!")
    print("=" * 60)
    
    if not all_passed:
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
