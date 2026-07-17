import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from app.services import db
from app.services.comparison_service import ComparisonEngine, IntegrityValidator

def test_comparison():
    print("Testing Modular Snapshot Comparison Engine...")
    
    # Initialize DB (creates snapshot_comparisons table)
    db.init_db()
    
    # Run comparison between mock snapshots we seeded
    res = ComparisonEngine.run_comparison(
        snap1_sel="2026-07-13",
        snap2_sel="2026-07-14"
    )
    
    # Assert metadata
    meta = res["comparison_metadata"]
    assert meta["date1"] == "2026-07-13"
    assert meta["date2"] == "2026-07-14"
    print("[OK] Metadata resolved correctly")
    
    # Assert portfolio summaries
    summary = res["portfolio_summary"]
    print("DEBUG SUMMARY:", summary)
    assert summary["upgrades"] == 2 # TCS (BUY -> STRONG BUY) and HDFCBANK (SELL -> BUY)
    assert summary["downgrades"] == 2 # INFY (BUY -> HOLD) and ICICIBANK (BUY -> SELL)
    assert summary["unchanged"] == 1 # RELIANCE (HOLD -> HOLD)
    print("[OK] Upgrade, Downgrade, and Unchanged counts match expected numbers")
    
    # Assert individual stock deltas
    deltas = {d["symbol"]: d for d in res["stock_deltas"]}
    
    tcs = deltas["TCS.NS"]
    assert tcs["prev_rating"] == "BUY"
    assert tcs["new_rating"] == "STRONG BUY"
    assert tcs["transition_type"] == "UPGRADE"
    assert tcs["score_changes"]["composite_score"]["delta"] == 13.0
    assert tcs["score_changes"]["technical_score"]["delta"] == 15.0
    assert tcs["score_changes"]["expected_return"]["delta"] == 1.95 # (85 * 0.15) - (72 * 0.15) = 1.95
    print("[OK] TCS rating transition and score delta calculations are accurate")
    
    infy = deltas["INFY.NS"]
    assert infy["prev_rating"] == "BUY"
    assert infy["new_rating"] == "HOLD"
    assert infy["transition_type"] == "DOWNGRADE"
    assert infy["score_changes"]["composite_score"]["delta"] == -16.0
    assert infy["score_changes"]["composite_score"]["category"] == "Major Decline"
    print("[OK] INFY score movement classification is correct")
    
    # Assert transition matrix
    matrix = res["recommendation_summary"]["matrix"]
    assert matrix["BUY"]["STRONG BUY"] == 1
    assert matrix["BUY"]["HOLD"] == 1
    assert matrix["HOLD"]["HOLD"] == 1
    assert matrix["SELL"]["BUY"] == 1
    assert matrix["BUY"]["SELL"] == 1
    print("[OK] Transition Matrix populated correctly")
    
    # Assert sector summary
    sector = res["sector_summary"]
    assert sector["best_sector"] == "Energy" # average composite change is 1.0 (RELIANCE)
    assert sector["worst_sector"] == "Technology" # average composite change is (13 - 16)/2 = -1.5
    print("[OK] Sector Analytics isolation worked")
    
    # Assert visuals
    visuals = res["visualizations"]
    assert len(visuals["waterfall"]) > 0
    assert len(visuals["histogram"]) > 0
    assert len(visuals["sector_heatmap"]) > 0
    print("[OK] Recharts visualization builder structures are valid")
    
    print("\nALL COMPARISON VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    try:
        test_comparison()
        sys.exit(0)
    except AssertionError as e:
        print(f"Assertion failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error executing verification: {e}")
        sys.exit(1)
