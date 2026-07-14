"""
scheduler.py — Background scheduler task for automated scanner refreshes and daily market snapshot pipeline.
"""

import asyncio
import logging
from datetime import datetime, time, timedelta
import pytz
import pandas as pd
import yfinance as yf

from app.data.loader import data_loader
from app.services.realtime_feed import fetch_quotes_batch
from app.services import db
from app.services.snapshot_pipeline import run_pipeline

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


def is_trading_day(target_date_str: str) -> bool:
    """Check if the target date was a valid trading day on NSE by looking at ^NSEI index bars."""
    try:
        nsei = yf.Ticker("^NSEI")
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
        start = (target_date - timedelta(days=5)).strftime("%Y-%m-%d")
        end = (target_date + timedelta(days=2)).strftime("%Y-%m-%d")
        
        df = nsei.history(start=start, end=end, progress=False)
        if df.empty:
            return False
            
        df = df.reset_index()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] for col in df.columns]
            
        df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")
        return target_date_str in df["Date"].values
    except Exception as e:
        logger.error(f"Error checking trading day via ^NSEI: {e}")
        # Fallback: check if weekend
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
        return target_date.weekday() < 5


def snapshot_exists_and_completed(snapshot_date: str) -> bool:
    """Check if an official snapshot has already completed/published for this date."""
    snap = db.get_snapshot_by_date(snapshot_date, official_only=True)
    return snap is not None and snap["status"] in ("completed", "completed_with_warnings", "published")


async def run_refresh_pipeline() -> bool:
    """
    Executes the automated refresh pipeline:
    yfinance download -> Cache reloads -> Live Quote Merge -> Cache Update.
    Preserves existing cache if yfinance fails.
    """
    logger.info("Starting automated scanner refresh pipeline run")
    try:
        df = data_loader.get_df()
        if df.empty:
            logger.warning("Scanner cache is empty; cannot retrieve symbol list for refresh.")
            return False
        
        symbols = df["Symbol"].tolist()
        
        loop = asyncio.get_event_loop()
        quotes_df = await loop.run_in_executor(None, fetch_quotes_batch, symbols)
        
        if quotes_df is None or quotes_df.empty:
            logger.warning("Yahoo Finance download failed or returned empty. Preserving previous cache data.")
            return False
        
        data_loader.refresh()
        
        fresh_df = data_loader.get_df()
        live_cols = [
            "CurrentPrice", "Open", "High", "Low", "Volume",
            "PreviousClose", "DailyChangePct", "DailyChangeAmount"
        ]
        fresh_df = fresh_df.drop(columns=[c for c in live_cols if c in fresh_df.columns], errors="ignore")
        merged_df = pd.merge(fresh_df, quotes_df, on="Symbol", how="left")
        
        data_loader._df = merged_df
        
        timestamp_str = datetime.now(IST).strftime("%Y-%m-%d %I:%M:%S %p IST")
        data_loader.last_market_update = timestamp_str
        data_loader.last_scanner_run = timestamp_str
        
        logger.info(f"Automated refresh pipeline completed successfully at {timestamp_str}")
        return True
    except Exception as e:
        logger.error(f"Error during refresh pipeline execution: {e}. Cache preserved.", exc_info=True)
        return False


from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

_scheduler = AsyncIOScheduler()

async def trigger_daily_pipeline_job() -> None:
    """
    Cron-triggered job wrapper for the daily snapshot pipeline.
    Runs once at 7:00 PM IST.
    """
    logger.info("Cron Scheduler: Triggered daily snapshot check.")
    try:
        now = datetime.now(IST)
        today_str = now.strftime("%Y-%m-%d")
        
        # Check if snapshot already exists
        if not snapshot_exists_and_completed(today_str):
            logger.info(f"Cron Scheduler: Checking if {today_str} was a NSE trading day...")
            
            loop = asyncio.get_event_loop()
            is_trade = await loop.run_in_executor(None, is_trading_day, today_str)
            
            if is_trade:
                logger.info(f"Cron Scheduler: {today_str} was a trading day. Triggering daily pipeline...")
                await loop.run_in_executor(None, run_pipeline, True, None, today_str)
                logger.info(f"Cron Scheduler: Daily pipeline completed for {today_str}")
            else:
                logger.info(f"Cron Scheduler: {today_str} was not a trading day (holiday/weekend). Skipping.")
        else:
            logger.info(f"Cron Scheduler: Snapshot already exists and is completed for {today_str}.")
    except Exception as e:
        logger.error(f"Error inside daily cron scheduler job execution: {e}", exc_info=True)


async def start_scheduler() -> None:
    """
    Initialize and start the cron scheduler.
    """
    logger.info("Initializing background cron scheduler")
    
    # 1. Add Daily Snapshot Pipeline Job at 7:00 PM (19:00) IST
    cron_trigger = CronTrigger(hour=19, minute=0, timezone=IST)
    _scheduler.add_job(trigger_daily_pipeline_job, cron_trigger, id="daily_pipeline")
    
    # 2. Add Market Hours Refresh Job (every 15 minutes during market hours)
    async def refresh_job():
        if is_nse_market_hours():
            logger.info("Cron Scheduler: Running refresh pipeline inside market hours.")
            await run_refresh_pipeline()
        else:
            logger.info("Cron Scheduler: Outside NSE market hours. Skipping automated refresh.")

    _scheduler.add_job(refresh_job, "interval", minutes=15, id="market_refresh")
    
    _scheduler.start()
    logger.info("Cron scheduler started successfully")
    
    # Wait 5 seconds after startup to trigger initial quotes enrich run
    await asyncio.sleep(5)
    logger.info("Triggering initial scanner quote enrichment run on startup")
    await run_refresh_pipeline()

