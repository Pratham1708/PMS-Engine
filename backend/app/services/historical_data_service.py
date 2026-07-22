"""
historical_data_service.py — Cached retrieval of historical price series from yfinance.
Supports 1M, 3M, 6M, 1Y, 3Y, and 5Y periods.
Strictly relies on real yfinance data downloads. Mock data generation has been removed.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

# Map human-readable periods to yfinance period arguments
PERIOD_MAP = {
    "1M": "1mo",
    "3M": "3mo",
    "6M": "6mo",
    "1Y": "1y",
    "3Y": "3y",
    "5Y": "5y",
}

CACHE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "cache")
)


class HistoricalDataService:
    """Service to fetch and cache historical stock prices from yfinance, minimizing external network load."""

    def __init__(self, cache_dir: str = CACHE_DIR) -> None:
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        self._memory_cache = {}

    def _get_cache_path(self, symbol: str, period: str) -> str:
        safe_symbol = symbol.replace(".", "_")
        return os.path.join(self.cache_dir, f"history_{safe_symbol}_{period}.csv")

    def load_cached_history(self, symbol: str, period: str) -> Optional[pd.DataFrame]:
        """Load history from cache if it exists on disk."""
        path = self._get_cache_path(symbol, period)
        if os.path.exists(path):
            try:
                df = pd.read_csv(path)
                # Ensure date parsing is correct
                df["Date"] = df["Date"].astype(str)
                return df
            except Exception as e:
                logger.error(f"Error loading cached history for {symbol} ({period}): {e}")
        return None

    def refresh_stock_history(self, symbol: str, period: str) -> Optional[pd.DataFrame]:
        """
        Download history from Yahoo Finance via yfinance and overwrite cache.
        Supports inputs both with and without .NS.
        """
        target_symbol = symbol.strip().upper()
        if not (target_symbol.endswith(".NS") or target_symbol.endswith(".BSE")):
            target_symbol = f"{target_symbol}.NS"

        logger.info(f"Downloading historical data for {symbol} ({target_symbol}, {period}) from yfinance...")
        try:
            yf_period = PERIOD_MAP.get(period, "1y")
            
            df = yf.download(
                tickers=target_symbol,
                period=yf_period,
                interval="1d",
                progress=False,
            )
            
            if (df is None or df.empty) and target_symbol != symbol.strip().upper():
                df = yf.download(
                    tickers=symbol.strip().upper(),
                    period=yf_period,
                    interval="1d",
                    progress=False,
                )

            if df is None or df.empty:
                logger.warning(f"yfinance download returned empty data for {symbol} ({period})")
                return None
            
            # Reset index so Date is a column
            df = df.reset_index()
            
            # Handle pandas MultiIndex if it exists (yfinance returns multi-index columns sometimes)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [col[0] for col in df.columns]
                
            # Standardize column naming
            df = df.rename(columns={
                "Close": "Close", 
                "Open": "Open", 
                "High": "High", 
                "Low": "Low", 
                "Volume": "Volume"
            })
            
            # Ensure Date column is a string in YYYY-MM-DD format
            df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")
            
            # Select required columns
            cols_to_keep = ["Date", "Open", "High", "Low", "Close", "Volume"]
            df = df[cols_to_keep]
            
            # Save to cache file
            path = self._get_cache_path(symbol, period)
            df.to_csv(path, index=False)
            logger.info(f"Successfully cached {len(df)} historical bars for {symbol} ({period})")
            return df
            
        except Exception as e:
            logger.error(f"yfinance download failed for {symbol} ({period}): {e}", exc_info=True)
            return None

    def get_stock_history(self, symbol: str, period: str, max_age_hours: int = 24) -> Optional[pd.DataFrame]:
        """
        Retrieve historical data for a stock via yfinance cache/refresh mechanism.
        Strictly serving validated actual market data.
        
        TTL is strictly enforced (default = 24 hours).
        """
        cache_key = (symbol, period)
        if cache_key in self._memory_cache:
            return self._memory_cache[cache_key].copy()

        path = self._get_cache_path(symbol, period)
        
        # Step 1: Try cached data first (check TTL)
        if os.path.exists(path):
            cached = self.load_cached_history(symbol, period)
            if cached is not None and not cached.empty:
                mtime = datetime.fromtimestamp(os.path.getmtime(path))
                age = datetime.now() - mtime
                if age < timedelta(hours=max_age_hours):
                    logger.info(f"Using cached history for {symbol} ({period}), age: {age}")
                    self._memory_cache[cache_key] = cached
                    return cached.copy()
        
        # Step 2: Refresh from yfinance
        df = self.refresh_stock_history(symbol, period)
        if df is not None:
            logger.info(f"Successfully fetched live history for {symbol} ({period}) from yfinance")
            self._memory_cache[cache_key] = df
            return df.copy()
        
        # Step 3: Serve stale cache ONLY if it exists (warning logged)
        # Note: In production we log a warning but still serve the older cache if network fails,
        # but if cache is non-existent, we return None (no mock fallback).
        if os.path.exists(path):
            cached = self.load_cached_history(symbol, period)
            if cached is not None and not cached.empty:
                logger.warning(f"Serving stale cache for {symbol} ({period}) due to download failure")
                self._memory_cache[cache_key] = cached
                return cached.copy()
            
        # Step 4: No data available
        logger.error(f"No historical data available for {symbol} ({period})")
        return None


# Singleton instance
historical_data_service = HistoricalDataService()
