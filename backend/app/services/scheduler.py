"""
scheduler.py — Background scheduler task for automated scanner refreshes.
Coordinates the refresh pipeline every 15 minutes during active NSE market hours.
"""

import asyncio
import logging
from datetime import datetime, time
import pytz
import pandas as pd

from app.data.loader import data_loader
from app.services.realtime_feed import fetch_quotes_batch

logger = logging.getLogger(__name__)

IST = pytz.timezone("Asia/Kolkata")


def is_nse_market_hours() -> bool:
    """
    Determine if the current IST time is within active NSE market hours.
    NSE Market Hours: Monday to Friday, 09:15 AM to 03:30 PM IST.
    """
    now = datetime.now(IST)
    
    # Check if weekend (5 = Saturday, 6 = Sunday)
    if now.weekday() >= 5:
        return False
    
    current_time = now.time()
    market_start = time(9, 15)
    market_end = time(15, 30)
    
    return market_start <= current_time <= market_end


async def run_refresh_pipeline() -> bool:
    """
    Executes the automated refresh pipeline:
    yfinance download -> Cache reloads -> Live Quote Merge -> Cache Update.
    Preserves existing cache if yfinance fails.
    """
    logger.info("Starting automated scanner refresh pipeline run")
    try:
        # 1. Fetch current stock list to extract active symbols
        df = data_loader.get_df()
        if df.empty:
            logger.warning("Scanner cache is empty; cannot retrieve symbol list for refresh.")
            return False
        
        symbols = df["Symbol"].tolist()
        
        # 2. Fetch live quotes in batch from Yahoo Finance
        # run in an executor to prevent blocking the async loop
        loop = asyncio.get_event_loop()
        quotes_df = await loop.run_in_executor(None, fetch_quotes_batch, symbols)
        
        if quotes_df is None or quotes_df.empty:
            logger.warning("Yahoo Finance download failed or returned empty. Preserving previous cache data.")
            return False
        
        # 3. Reload baseline scoring and models calculations from local CSV files
        # This acts as our 'scoring engine / rating engine run' ensuring all baseline mappings are fresh
        data_loader.refresh()
        
        # 4. Merge live quotes into data_loader._df
        fresh_df = data_loader.get_df()
        live_cols = [
            "CurrentPrice", "Open", "High", "Low", "Volume",
            "PreviousClose", "DailyChangePct", "DailyChangeAmount"
        ]
        # Drop to prevent suffix duplication (_x, _y) during merge
        fresh_df = fresh_df.drop(columns=[c for c in live_cols if c in fresh_df.columns], errors="ignore")
        merged_df = pd.merge(fresh_df, quotes_df, on="Symbol", how="left")
        
        # 5. Lock and update data_loader state with enriched data
        data_loader._df = merged_df
        
        # 6. Update data freshness timestamps
        timestamp_str = datetime.now(IST).strftime("%Y-%m-%d %I:%M:%S %p IST")
        data_loader.last_market_update = timestamp_str
        data_loader.last_scanner_run = timestamp_str
        
        logger.info(f"Automated refresh pipeline completed successfully at {timestamp_str}")
        return True
    except Exception as e:
        logger.error(f"Error during refresh pipeline execution: {e}. Cache preserved.", exc_info=True)
        return False


async def start_scheduler() -> None:
    """
    Background worker loop. Checks market hours and runs the refresh pipeline
    every 15 minutes.
    """
    logger.info("Initializing background refresh scheduler worker")
    # Wait 5 seconds after server startup to allow complete initialization
    await asyncio.sleep(5)
    
    # Run once on startup to enrich cache with initial quotes
    logger.info("Triggering initial scanner quote enrichment run")
    await run_refresh_pipeline()
    
    while True:
        try:
            # Sleep for 5 minutes (300 seconds) before the next run
            await asyncio.sleep(300)
            if is_nse_market_hours():
                logger.info("Scheduler: Current time is within NSE market hours. Running refresh.")
                await run_refresh_pipeline()
            else:
                logger.info("Scheduler: Outside NSE market hours. Skipping automated run.")
        except Exception as e:
            logger.error(f"Error inside scheduler daemon loop: {e}")
