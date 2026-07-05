import requests
import time
import sys

BASE_URL = "http://localhost:8000/api"

def main():
    print("=" * 70)
    print("      VERIFYING THE SIX RISK SIMULATION & PORTFOLIO OPTIMIZATION FEATURES")
    print("=" * 70)
    
    # 1. Wait for server to start if not yet ready
    print("[INFO] Checking backend connection...")
    for attempt in range(15):
        try:
            r = requests.get(f"{BASE_URL}/health", timeout=2)
            if r.status_code == 200:
                print("[SUCCESS] Server is online and ready.")
                break
        except Exception:
            pass
        print(f"[INFO] Waiting for server (attempt {attempt+1}/15)...")
        time.sleep(2)
    else:
        print("[ERROR] Server did not start. Exiting.")
        sys.exit(1)
        
    all_passed = True
    
    # ----------------------------------------------------
    # 1. Monte Carlo Sandbox
    # ----------------------------------------------------
    print("\n--- 1. Testing Monte Carlo Sandbox ---")
    try:
        payload = {
            "symbol": "^NSEI",
            "period": "1Y", # 1Y is faster
            "n_simulations": 100, # 100 is faster
            "horizon_days": 252
        }
        r = requests.post(f"{BASE_URL}/lab/monte-carlo/run", json=payload, timeout=30)
        assert r.status_code == 200, f"Status code {r.status_code}: {r.text}"
        res = r.json()
        print("[SUCCESS] Monte Carlo Sandbox works correctly.")
        print(f"          Expected CAGR: {res.get('expected_cagr')}%")
        print(f"          Expected Max Drawdown: {res.get('expected_max_dd')}%")
        print(f"          Simulated paths count: {len(res.get('simulated_paths', []))}")
    except Exception as e:
        print(f"[FAILED] Monte Carlo Sandbox failed: {e}")
        all_passed = False
        
    # ----------------------------------------------------
    # 2. Crisis Stress Tester
    # ----------------------------------------------------
    print("\n--- 2. Testing Crisis Stress Tester ---")
    try:
        payload = {
            "symbol": "^NSEI"
        }
        r = requests.post(f"{BASE_URL}/lab/stress-test/run", json=payload, timeout=30)
        assert r.status_code == 200, f"Status code {r.status_code}: {r.text}"
        res = r.json()
        print("[SUCCESS] Crisis Stress Tester works correctly.")
        print(f"          Overall Resilience Score: {res.get('overall_resilience_score')}")
        print(f"          Rating: {res.get('rating')}")
        print(f"          Crisis periods evaluated: {len(res.get('crisis_performance', []))}")
    except Exception as e:
        print(f"[FAILED] Crisis Stress Tester failed: {e}")
        all_passed = False
        
    # ----------------------------------------------------
    # 3. Parameter Hyperopt
    # ----------------------------------------------------
    print("\n--- 3. Testing Parameter Hyperopt ---")
    for target in ["ml_model", "risk_thresholds", "position_sizing"]:
        print(f"       Sub-test Target: {target}...")
        try:
            payload = {
                "target": target,
                "symbol": "^NSEI",
                "period": "1Y",
                "target_metric": "sharpe_ratio"
            }
            r = requests.post(f"{BASE_URL}/lab/hyperopt/run", json=payload, timeout=30)
            assert r.status_code == 200, f"Status code {r.status_code}: {r.text}"
            res = r.json()
            print(f"[SUCCESS] Hyperopt for {target} works correctly.")
            print(f"          Best score: {res.get('best_score')}")
            print(f"          Best params: {res.get('best_params')}")
        except Exception as e:
            print(f"[FAILED] Hyperopt for {target} failed: {e}")
            all_passed = False
            
    # ----------------------------------------------------
    # 4. Position Sizing Lab
    # ----------------------------------------------------
    print("\n--- 4. Testing Position Sizing Lab ---")
    try:
        payload = {
            "symbol": "RELIANCE.NS",
            "period": "1Y",
            "risk_pct": 2.0
        }
        r = requests.post(f"{BASE_URL}/lab/position-sizing/run", json=payload, timeout=30)
        assert r.status_code == 200, f"Status code {r.status_code}: {r.text}"
        res = r.json()
        print("[SUCCESS] Position Sizing Lab works correctly.")
        print(f"          Compounding models evaluated: {[s.get('model') for s in res.get('summary', [])]}")
        print(f"          Curve points generated: {len(res.get('curves', []))}")
    except Exception as e:
        print(f"[FAILED] Position Sizing Lab failed: {e}")
        all_passed = False
        
    # ----------------------------------------------------
    # 5. Portfolio Optimizer
    # ----------------------------------------------------
    print("\n--- 5. Testing Portfolio Optimizer ---")
    try:
        payload = {
            "symbols": ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS"],
            "period": "1Y"
        }
        r = requests.post(f"{BASE_URL}/lab/portfolio-construction/run", json=payload, timeout=30)
        assert r.status_code == 200, f"Status code {r.status_code}: {r.text}"
        res = r.json()
        print("[SUCCESS] Portfolio Optimizer works correctly.")
        print(f"          Assets optimized: {res.get('assets')}")
        print(f"          Efficient Frontier points: {len(res.get('efficient_frontier', []))}")
        print(f"          Max Sharpe Weights: {res.get('max_sharpe', {}).get('weights')}")
        print(f"          Min Variance Weights: {res.get('min_variance', {}).get('weights')}")
        print(f"          Risk Parity Weights: {res.get('risk_parity', {}).get('weights')}")
        print(f"          Equal Weight Weights: {res.get('equal_weight', {}).get('weights')}")
    except Exception as e:
        print(f"[FAILED] Portfolio Optimizer failed: {e}")
        all_passed = False
        
    # ----------------------------------------------------
    # 6. Portfolio Lab
    # ----------------------------------------------------
    print("\n--- 6. Testing Portfolio Lab ---")
    strategies = ["top_n_monthly", "equal_weight", "smart_beta", "sector_momentum"]
    for strat in strategies:
        print(f"       Sub-test Strategy: {strat}...")
        try:
            payload = {
                "strategy": strat,
                "n": 5,
                "period": "1Y",
                "initial_capital": 100000.0
            }
            r = requests.post(f"{BASE_URL}/lab/portfolio/backtest", json=payload, timeout=30)
            assert r.status_code == 200, f"Status code {r.status_code}: {r.text}"
            start_res = r.json()
            exp_id = start_res.get("experiment_id")
            print(f"          Backtest task started. Experiment ID: {exp_id}. Waiting for completion...")
            
            # Poll for results
            completed = False
            for _ in range(40):
                time.sleep(3)
                r_check = requests.get(f"{BASE_URL}/lab/portfolio/result/{exp_id}", timeout=5)
                assert r_check.status_code == 200, f"Check status code {r_check.status_code}: {r_check.text}"
                check_res = r_check.json()
                if check_res.get("status") == "complete":
                    completed = True
                    print(f"[SUCCESS] Portfolio Lab strategy {strat} backtest completed.")
                    print(f"          Metrics: CAGR={check_res.get('metrics', {}).get('cagr')}%, Sharpe={check_res.get('metrics', {}).get('sharpe')}, MaxDD={check_res.get('metrics', {}).get('max_drawdown')}%")
                    break
                elif check_res.get("status") == "failed":
                    raise Exception(f"Backtest task failed internally: {check_res.get('detail') or check_res}")
            
            if not completed:
                raise Exception("Backtest task timeout (did not complete in 120 seconds)")
        except Exception as e:
            print(f"[FAILED] Portfolio Lab strategy {strat} failed: {e}")
            all_passed = False
            
    print("\n" + "=" * 70)
    if all_passed:
        print("          ALL RISK SIMULATION & PORTFOLIO OPTIMIZATION FEATURES VERIFIED!")
    else:
        print("          SOME FEATURES FAILED VERIFICATION!")
    print("=" * 70)
    
    if not all_passed:
        sys.exit(1)

if __name__ == "__main__":
    main()
