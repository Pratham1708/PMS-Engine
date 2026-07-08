"""
yfinance_feed.py - Service layer for Yahoo Finance real-time data downloads.
Optimized for batch Nifty 50 processing to prevent rate limiting.

Priority strategy for live prices:
  1. fast_info (real-time last price, most accurate)
  2. 1-minute intraday history (last bar close)
  3. Daily OHLCV history (yesterday close, last resort)
  4. Deterministic simulation fallback (if Yahoo Finance is fully blocked)

The mock fallback price range is calibrated to Nifty 50 stocks (100-12000 INR).
"""

import logging
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd

# Suppress yfinance's own logging to avoid "possibly delisted" spam
logging.getLogger("yfinance").setLevel(logging.CRITICAL)

import yfinance as yf

logger = logging.getLogger(__name__)



def _fetch_via_fast_info(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Attempt to get the real-time last price using yf.Ticker.fast_info.
    
    NOTE: Skips NSE stocks (.NS) since yfinance doesn't support them reliably.
    """

    
    try:
        ticker = yf.Ticker(symbol)
        fi = ticker.fast_info

        last_price = getattr(fi, "last_price", None)
        prev_close = getattr(fi, "previous_close", None)
        open_val = getattr(fi, "open", None)
        day_high = getattr(fi, "day_high", None)
        day_low = getattr(fi, "day_low", None)
        volume = getattr(fi, "last_volume", None) or getattr(fi, "three_month_average_volume", None)

        if last_price is None or float(last_price) == 0:
            return None

        prev_close = prev_close or last_price
        change_amount = round(float(last_price) - float(prev_close), 2)
        change_pct = round((change_amount / float(prev_close)) * 100, 2) if prev_close else 0.0

        return {
            "Symbol": symbol,
            "CurrentPrice": round(float(last_price), 2),
            "Open": round(float(open_val), 2) if open_val else round(float(last_price), 2),
            "High": round(float(day_high), 2) if day_high else round(float(last_price), 2),
            "Low": round(float(day_low), 2) if day_low else round(float(last_price), 2),
            "Volume": int(volume) if volume else 0,
            "PreviousClose": round(float(prev_close), 2),
            "DailyChangePct": change_pct,
            "DailyChangeAmount": change_amount,
            "IsMock": False,
        }
    except Exception as e:
        logger.debug("fast_info fetch failed for %s: %s", symbol, e)
        return None


def _fetch_via_intraday(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Fetch the most recent price via intraday 1-minute bars (Strategy A) or
    5-day daily bars (Strategy B) as a fallback.
    
    NOTE: Skips NSE stocks (.NS) since yfinance doesn't support them reliably.
    """

    
    # Strategy A: 1-minute intraday (live price during market hours)
    try:
        df = yf.download(
            tickers=symbol,
            period="1d",
            interval="1m",
            progress=False,
            auto_adjust=True,
        )
        if not df.empty:
            df = df.dropna(subset=["Close"])
            if not df.empty:
                current_price = float(df["Close"].iloc[-1])
                open_val = float(df["Open"].iloc[0])
                high_val = float(df["High"].max())
                low_val = float(df["Low"].min())
                volume = int(df["Volume"].sum())

                # Get previous session close from daily data
                try:
                    daily_df = yf.download(
                        tickers=symbol, period="5d", interval="1d",
                        progress=False, auto_adjust=True,
                    )
                    daily_df = daily_df.dropna(subset=["Close"])
                    prev_close = (
                        float(daily_df["Close"].iloc[-2])
                        if len(daily_df) >= 2
                        else float(daily_df["Close"].iloc[-1])
                    )
                except Exception:
                    prev_close = open_val

                change_amount = round(current_price - prev_close, 2)
                change_pct = round((change_amount / prev_close) * 100, 2) if prev_close else 0.0

                return {
                    "Symbol": symbol,
                    "CurrentPrice": round(current_price, 2),
                    "Open": round(open_val, 2),
                    "High": round(high_val, 2),
                    "Low": round(low_val, 2),
                    "Volume": volume,
                    "PreviousClose": round(prev_close, 2),
                    "DailyChangePct": change_pct,
                    "DailyChangeAmount": change_amount,
                    "IsMock": False,
                }
    except Exception as e:
        logger.debug("Intraday 1m fetch failed for %s: %s", symbol, e)

    # Strategy B: 5-day daily bars (EOD price, most reliable after-hours)
    try:
        df = yf.download(
            tickers=symbol,
            period="5d",
            interval="1d",
            progress=False,
            auto_adjust=True,
        )
        df = df.dropna(subset=["Close"])
        if not df.empty:
            current_price = float(df["Close"].iloc[-1])
            open_val = float(df["Open"].iloc[-1])
            high_val = float(df["High"].iloc[-1])
            low_val = float(df["Low"].iloc[-1])
            volume = int(df["Volume"].iloc[-1])
            prev_close = float(df["Close"].iloc[-2]) if len(df) >= 2 else open_val
            change_amount = round(current_price - prev_close, 2)
            change_pct = round((change_amount / prev_close) * 100, 2) if prev_close else 0.0
            return {
                "Symbol": symbol,
                "CurrentPrice": round(current_price, 2),
                "Open": round(open_val, 2),
                "High": round(high_val, 2),
                "Low": round(low_val, 2),
                "Volume": volume,
                "PreviousClose": round(prev_close, 2),
                "DailyChangePct": change_pct,
                "DailyChangeAmount": change_amount,
                "IsMock": False,
            }
    except Exception as e:
        logger.debug("Daily 5d fetch failed for %s: %s", symbol, e)

    return None


def fetch_quotes_batch(symbols: List[str], retries: int = 2) -> pd.DataFrame:
    """
    Download latest live quotes for a list of symbols.

    Per-symbol priority:
      1. fast_info        - real-time last price (lightest API call)
      2. 1-min intraday   - live price during market hours
      3. 5-day daily      - last EOD close (after-hours fallback)
      4. Mock fallback    - deterministic, price-hinted simulation

    Returns a DataFrame with columns:
        Symbol, CurrentPrice, Open, High, Low, Volume,
        PreviousClose, DailyChangePct, DailyChangeAmount, IsMock
    """
    logger.info("Fetching live market quotes for %d symbols", len(symbols))
    if not symbols:
        return pd.DataFrame()

    results = []
    for sym in symbols:
        quote = None

        # Priority 1: fast_info
        for _ in range(retries):
            quote = _fetch_via_fast_info(sym)
            if quote:
                logger.info("[fast_info] %s: %.2f", sym, quote["CurrentPrice"])
                break

        # Priority 2 & 3: intraday / daily history
        if not quote:
            for _ in range(retries):
                quote = _fetch_via_intraday(sym)
                if quote:
                    logger.info("[intraday/daily] %s: %.2f", sym, quote["CurrentPrice"])
                    break

        # If quote could not be fetched, skip it
        if not quote:
            logger.warning("No live data available for %s", sym)
            continue

        results.append(quote)

    return pd.DataFrame(results)


def fetch_quote_single(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Fetch live quote for a single symbol.
    Priority: fast_info -> intraday/daily -> mock fallback.
    """
    logger.info("Fetching live quote for: %s", symbol)

    quote = _fetch_via_fast_info(symbol)
    if quote:
        logger.info("[fast_info] %s: %.2f", symbol, quote["CurrentPrice"])
        return quote

    quote = _fetch_via_intraday(symbol)
    if quote:
        logger.info("[intraday/daily] %s: %.2f", symbol, quote["CurrentPrice"])
        return quote

    return None
