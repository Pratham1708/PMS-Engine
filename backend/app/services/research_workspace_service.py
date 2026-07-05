"""
research_workspace_service.py — Compile Research Workspace Home View Data.
Gathers data from user_stock_service, analysis_history_service, and report_generator
to build a single unified response for the workspace view.
"""

import logging
from typing import Dict, Any, List

from app.services import user_stock_service
from app.services import analysis_history_service
from app.services import report_generator
from app.data.loader import data_loader

logger = logging.getLogger(__name__)


def get_workspace_data() -> Dict[str, Any]:
    """Aggregate all metrics and lists required by the Research Workspace homepage."""
    
    # 1. Fetch user interest stocks
    my_stocks_raw = user_stock_service.get_my_stocks()
    df = data_loader.get_df()
    
    my_stocks_list = []
    for item in my_stocks_raw:
        symbol = item["symbol"]
        added_at = item["added_at"]
        
        # Get live market fields from cache df
        match = df[df["Symbol"].str.upper() == symbol.upper()]
        current_price = None
        daily_change_pct = None
        sector = "—"
        
        if not match.empty:
            row = match.iloc[0]
            current_price = float(row["CurrentPrice"]) if row.get("CurrentPrice") is not None else None
            daily_change_pct = float(row["DailyChangePct"]) if row.get("DailyChangePct") is not None else None
            sector = row.get("Sector", "—")
            
        # Get last analysis run
        last_run = analysis_history_service.get_last_analysis(symbol)
        
        my_stocks_list.append({
            "symbol": symbol,
            "added_at": added_at,
            "sector": sector,
            "current_price": current_price,
            "daily_change_pct": daily_change_pct,
            "last_rating": last_run["rating"] if last_run else "Not Analyzed",
            "last_confidence": last_run["confidence"] if last_run else None,
            "last_composite": last_run["composite_score"] if last_run else None,
            "analyzed_at": last_run["analyzed_at"] if last_run else None,
            "last_status": last_run["status"] if last_run else "Stale"
        })
        
    # 2. Fetch recently analyzed stocks (global across all symbols)
    recent_runs = analysis_history_service.get_recent_analysis(limit=5)
    
    # Enrich recent runs with sector and current price
    recent_runs_enriched = []
    for run in recent_runs:
        symbol = run["symbol"]
        match = df[df["Symbol"].str.upper() == symbol.upper()]
        sector = "—"
        price = None
        if not match.empty:
            row = match.iloc[0]
            sector = row.get("Sector", "—")
            price = float(row["CurrentPrice"]) if row.get("CurrentPrice") is not None else None
            
        recent_runs_enriched.append({
            **run,
            "sector": sector,
            "current_price": price
        })
        
    # 3. Fetch saved PDF research reports
    try:
        saved_reports = report_generator.list_all_reports()[:5]
    except Exception as e:
        logger.warning(f"Failed to fetch saved reports for workspace: {e}")
        saved_reports = []
        
    # 4. Compute Universe Stats (Nifty 50 count, My Stocks count, and Analysis coverage)
    total_universe_stocks = len(df)
    analyzed_count = 0
    if not df.empty:
        # Check how many of our Nifty 50 stocks have at least one analysis record in SQLite
        conn = db_conn_check()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(DISTINCT symbol) FROM analysis_history")
            row = cursor.fetchone()
            if row:
                analyzed_count = row[0]
        except Exception as ex:
            logger.warning(f"Failed to fetch analyzed count for stats: {ex}")
        finally:
            conn.close()

    return {
        "my_stocks": my_stocks_list,
        "recent_analysis": recent_runs_enriched,
        "saved_reports": saved_reports,
        "universe_stats": {
            "total_universe": total_universe_stocks,
            "my_stocks_count": len(my_stocks_list),
            "analyzed_universe_count": analyzed_count
        }
    }


def db_conn_check():
    """Helper connection."""
    from app.services.db import get_db_connection
    return get_db_connection()
