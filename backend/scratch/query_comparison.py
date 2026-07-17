import sys
import os
import json

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from app.services import db
from app.services.comparison_service import ComparisonEngine

def main():
    db.init_db()
    # List snapshot dates first
    dates = db.list_snapshot_dates()
    print("Available Snapshots:")
    for d in dates:
        print(f" - ID: {d['snapshot_id']}, Date: {d['snapshot_date']}, Official: {d['is_official']}, Status: {d['status']}, Stocks: {d['stocks_processed']}")
    
    # Use the dates from the screenshot (2026-07-15 and 2026-07-17)
    try:
        res = ComparisonEngine.run_comparison(
            snap1_sel="2026-07-13",
            snap2_sel="2026-07-14"
        )
        print("\nComparison Metadata:")
        print(json.dumps(res["comparison_metadata"], indent=2))
        
        print("\nPortfolio Summary:")
        # Print without lists to avoid clutter
        ps = res["portfolio_summary"].copy()
        ps["strongest_improving"] = [x["symbol"] for x in ps.get("strongest_improving", [])]
        ps["largest_deteriorating"] = [x["symbol"] for x in ps.get("largest_deteriorating", [])]
        print(json.dumps(ps, indent=2))
        
        print("\nSector Summary:")
        print(json.dumps(res["sector_summary"], indent=2))
        
        print("\nRecommendation Summary (upgrades/downgrades count):")
        print(f"Upgrades List Count: {len(res['recommendation_summary']['upgrade_list'])}")
        print(f"Downgrades List Count: {len(res['recommendation_summary']['downgrade_list'])}")
        print("Matrix:")
        print(json.dumps(res["recommendation_summary"]["matrix"], indent=2))
        
        print("\nVisualizations:")
        print(json.dumps(res["visualizations"], indent=2))
        
        if res["stock_deltas"]:
            print("\nFirst Stock Delta Example:")
            # Print first stock delta details
            sd = res["stock_deltas"][0]
            print(json.dumps(sd, indent=2))
            
    except Exception as e:
        print(f"Error executing comparison: {e}")

if __name__ == "__main__":
    main()
