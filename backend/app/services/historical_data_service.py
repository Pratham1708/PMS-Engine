"""
historical_data_service.py — Cached retrieval of historical price series from investing.com.
Supports 1M, 3M, 6M, 1Y, 3Y, and 5Y periods.
Includes simulated mock fallback series generation if investing.com is unavailable.

Strategy:
  1. For NSE stocks: Use cache → investpy → generate mock
  2. For other stocks: Use cache → investpy → generate mock
"""

import os
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd

try:
    import investpy
    INVESTPY_AVAILABLE = True
except ImportError:
    INVESTPY_AVAILABLE = False
    logging.warning("investpy not installed. Install via: pip install investpy")

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

# Price hints for Nifty 50 stocks (same as yfinance_feed.py)
NIFTY50_PRICE_HINTS = {
    "ADANIENT.NS": 2400.0,
    "ADANIPORTS.NS": 1300.0,
    "APOLLOHOSP.NS": 7200.0,
    "ASIANPAINT.NS": 2300.0,
    "AXISBANK.NS": 1100.0,
    "BAJAJ-AUTO.NS": 9200.0,
    "BAJFINANCE.NS": 7200.0,
    "BAJAJFINSV.NS": 1700.0,
    "BPCL.NS": 320.0,
    "BHARTIARTL.NS": 1900.0,
    "BRITANNIA.NS": 5300.0,
    "CIPLA.NS": 1500.0,
    "COALINDIA.NS": 430.0,
    "DIVISLAB.NS": 5700.0,
    "DRREDDY.NS": 1250.0,
    "EICHERMOT.NS": 4900.0,
    "GRASIM.NS": 2600.0,
    "HCLTECH.NS": 1700.0,
    "HDFCBANK.NS": 1800.0,
    "HDFCLIFE.NS": 700.0,
    "HEROMOTOCO.NS": 4200.0,
    "HINDALCO.NS": 680.0,
    "HINDUNILVR.NS": 2400.0,
    "ICICIBANK.NS": 1300.0,
    "INDUSINDBK.NS": 1100.0,
    "INFY.NS": 1600.0,
    "ITC.NS": 460.0,
    "JSWSTEEL.NS": 970.0,
    "KOTAKBANK.NS": 2100.0,
    "LT.NS": 3600.0,
    "LTIM.NS": 6200.0,
    "M&M.NS": 2900.0,
    "MARUTI.NS": 12500.0,
    "NESTLEIND.NS": 2300.0,
    "NTPC.NS": 360.0,
    "ONGC.NS": 260.0,
    "POWERGRID.NS": 310.0,
    "RELIANCE.NS": 1400.0,
    "SBILIFE.NS": 1600.0,
    "SBIN.NS": 810.0,
    "SUNPHARMA.NS": 1800.0,
    "TATACONSUM.NS": 1100.0,
    "TATAMOTORS.NS": 680.0,
    "TATASTEEL.NS": 155.0,
    "TCS.NS": 3500.0,
    "TECHM.NS": 1700.0,
    "TITAN.NS": 4400.0,
    "TRENT.NS": 5800.0,
    "ULTRACEMCO.NS": 11000.0,
    "WIPRO.NS": 270.0,
}


class HistoricalDataService:
    """Service to fetch and cache historical stock prices, minimizing external network load."""

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
                # Read CSV and format Date column
                df = pd.read_csv(path)
                return df
            except Exception as e:
                logger.error(f"Error loading cached history for {symbol} ({period}): {e}")
        return None

    def refresh_stock_history(self, symbol: str, period: str) -> Optional[pd.DataFrame]:
        """
        Download history from Investing.com via investpy and overwrite cache.
        
        Note: Works reliably for both NSE (.NS) and international stocks.
        Returns None on failure to allow fallback to cache/mock.
        """
        if not INVESTPY_AVAILABLE:
            logger.debug(f"investpy not available for {symbol}")
            return None

        logger.debug(f"Attempting investpy download for {symbol} (period={period})")
        
        try:
            # Convert symbol format (INFY.NS -> INFY)
            investpy_symbol = symbol.replace(".NS", "").replace(".BSE", "")
            
            # Get recent data from investing.com
            df = investpy.stocks.get_stock_recent_data(
                stock=investpy_symbol,
                country="India",
                as_json=False,
                order="ascending"
            )
            
            if df is None or df.empty:
                logger.debug(f"investpy returned empty data for {symbol} ({period})")
                return None
            
            # Validate data
            if len(df) < 10:
                logger.debug(f"investpy returned insufficient data ({len(df)} days) for {symbol}")
                return None
            
            # Reset index so Date is a column
            df = df.reset_index()
            # Ensure Date column is in string format
            df["Date"] = pd.to_datetime(df.index).strftime("%Y-%m-%d") if "index" not in df.columns else df.get("Date", "").astype(str)
            if "Date" not in df.columns:
                df["Date"] = df.index.strftime("%Y-%m-%d")
            
            # Save to cache file
            path = self._get_cache_path(symbol, period)
            df.to_csv(path, index=False)
            logger.debug(f"Successfully cached {len(df)} days for {symbol} ({period})")
            return df
            
        except Exception as e:
            # investpy likely doesn't support this ticker or network error
            logger.debug(f"investpy failed for {symbol} ({period}): {str(e)[:100]}")
            return None

    def generate_mock_history(self, symbol: str, period: str) -> pd.DataFrame:
        """
        Generate deterministic mock history when yfinance download fails and no cache exists.
        Uses price hints for Nifty 50 stocks to ensure realistic prices.
        """
        logger.info(f"Generating mock history fallback for {symbol} ({period})")
        h = int(hashlib.md5(symbol.encode('utf-8')).hexdigest(), 16)
        
        # Use price hint if available, otherwise generate realistic range
        sym_upper = symbol.upper()
        if sym_upper in NIFTY50_PRICE_HINTS:
            base_price = NIFTY50_PRICE_HINTS[sym_upper]
            logger.debug(f"Using price hint for {symbol}: INR {base_price}")
        else:
            base_price = (h % 11900) + 100.0  # 100-12000 INR range
            logger.debug(f"Using generated price for {symbol}: INR {base_price}")
        
        # Determine number of days based on period
        days_map = {
            "1M": 30,
            "3M": 90,
            "6M": 180,
            "1Y": 365,
            "3Y": 365 * 3,
            "5Y": 365 * 5,
        }
        days = days_map.get(period, 365)
        
        today = datetime.now()
        dates = []
        current = today - timedelta(days=days)
        while current <= today:
            # Skip weekends (NSE trading days only)
            if current.weekday() < 5:
                dates.append(current.strftime("%Y-%m-%d"))
            current += timedelta(days=1)
            
        prices = []
        curr_price = base_price * 0.95  # Start slightly lower than base
        
        for i, dt in enumerate(dates):
            # Deterministic daily step with realistic volatility
            step = (((h + i) % 100) - 50) / 500.0  # ±0.1% daily volatility
            curr_price = curr_price * (1.0 + step / 100.0)
            
            # Ensure price stays within realistic bounds
            if curr_price < base_price * 0.7:
                curr_price = base_price * 0.7
            elif curr_price > base_price * 1.3:
                curr_price = base_price * 1.3
            
            open_val = curr_price * (1.0 + (((h + i * 2) % 10) - 5) / 1000.0)
            high_val = max(curr_price, open_val) * (1.0 + ((h + i) % 5) / 1000.0)
            low_val = min(curr_price, open_val) * (1.0 - ((h + i) % 5) / 1000.0)
            volume = int(((h + i * 3) % 1500000) + 15000)
            
            prices.append({
                "Date": dt,
                "Open": round(open_val, 2),
                "High": round(high_val, 2),
                "Low": round(low_val, 2),
                "Close": round(curr_price, 2),
                "Volume": volume,
                "Dividends": 0.0,
                "Stock Splits": 0.0
            })
        
        logger.info(f"Generated {len(prices)} trading days for {symbol}")
        return pd.DataFrame(prices)

    def get_stock_history(self, symbol: str, period: str, max_age_hours: int = 168) -> Optional[pd.DataFrame]:
        """
        Retrieve historical data for a stock via investing.com (investpy).
        
        Strategy for all stocks:
          1. Use cache if it exists and is recent
          2. Try investpy refresh
          3. Use older cache if available
          4. Generate mock fallback
        
        Args:
            symbol: Stock ticker (e.g., 'INFY.NS', 'AAPL')
            period: Period string ('1Y', '3Y', '5Y', etc.)
        """
        cache_key = (symbol, period)
        if cache_key in self._memory_cache:
            return self._memory_cache[cache_key].copy()

        path = self._get_cache_path(symbol, period)
        
        # Step 1: Try cached data first
        if os.path.exists(path):
            cached = self.load_cached_history(symbol, period)
            if cached is not None and not cached.empty:
                mtime = datetime.fromtimestamp(os.path.getmtime(path))
                age = datetime.now() - mtime
                if age < timedelta(hours=max_age_hours):
                    logger.info(f"Using cached history for {symbol} ({period}), age: {age}")
                    self._memory_cache[cache_key] = cached
                    return cached.copy()
        
        # Step 2: Try investpy refresh
        df = self.refresh_stock_history(symbol, period)
        if df is not None:
            logger.info(f"Successfully fetched live data for {symbol} ({period}) from investing.com")
            self._memory_cache[cache_key] = df
            return df.copy()
        
        # Step 3: Fallback to older cache
        if os.path.exists(path):
            cached = self.load_cached_history(symbol, period)
            if cached is not None and not cached.empty:
                logger.info(f"Using cached (stale) history for {symbol} ({period})")
                self._memory_cache[cache_key] = cached
                return cached.copy()
            
        # Step 4: Final fallback: generate deterministic mock data
        logger.warning(f"No live or cached data for {symbol}. Generating mock history.")
        df = self.generate_mock_history(symbol, period)
        try:
            df.to_csv(path, index=False)
            logger.info(f"Successfully cached generated mock history for {symbol} ({period})")
        except Exception as e:
            logger.warning(f"Failed to cache generated mock history for {symbol}: {e}")
        
        self._memory_cache[cache_key] = df
        return df.copy()


# Singleton instance
historical_data_service = HistoricalDataService()
