"""
investpy_feed.py - Service layer for real-time market data from Investing.com
Provides live prices for Indian stocks (NSE) via investpy scraping.

Priority strategy for live prices:
  1. investpy quote data (real-time last price from investing.com)
  2. investpy recent data (last close if live unavailable)
  3. Deterministic mock fallback (if all sources fail)

Advantages over yfinance:
  - Reliable for NSE stocks (.NS)
  - No "possibly delisted" errors
  - Actual real-time data from investing.com
"""

import logging
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd

try:
    import investpy
    INVESTPY_AVAILABLE = True
except ImportError:
    INVESTPY_AVAILABLE = False
    logging.warning("investpy not installed. Install via: pip install investpy")

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Known approximate prices for Nifty 50 stocks.
# Used ONLY as fallback base for mock generator so prices stay realistic.
# ---------------------------------------------------------------------------
NIFTY50_PRICE_HINTS: Dict[str, float] = {
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


def generate_mock_quote(symbol: str) -> Dict[str, Any]:
    """
    Generate deterministic simulated quote data based on symbol hash.
    Used only as last-resort fallback.
    """
    h = int(hashlib.md5(symbol.encode("utf-8")).hexdigest(), 16)

    sym_upper = symbol.upper()
    if sym_upper in NIFTY50_PRICE_HINTS:
        base_price = NIFTY50_PRICE_HINTS[sym_upper]
    else:
        base_price = (h % 11900) + 100.0  # 100 - 12000 INR

    now = datetime.now()
    change_pct = ((h + now.minute) % 600 - 300) / 100.0  # -3.0% to +3.0%

    current_price = round(base_price * (1 + change_pct / 100.0), 2)
    prev_close = round(base_price, 2)
    change_amount = round(current_price - prev_close, 2)

    open_val = round(prev_close * (1 + (h % 10 - 5) / 500.0), 2)
    high_val = round(max(current_price, open_val) * (1 + (h % 5) / 1000.0), 2)
    low_val = round(min(current_price, open_val) * (1 - (h % 5) / 1000.0), 2)
    volume = int((h % 1500000) + 20000)

    logger.warning(
        "[MOCK] Simulated price for %s: %.2f (live data unavailable)", symbol, current_price
    )

    return {
        "Symbol": symbol,
        "CurrentPrice": current_price,
        "Open": open_val,
        "High": high_val,
        "Low": low_val,
        "Volume": volume,
        "PreviousClose": prev_close,
        "DailyChangePct": round(change_pct, 2),
        "DailyChangeAmount": change_amount,
        "IsMock": True,
    }


def _symbol_to_investpy_format(symbol: str) -> str:
    """Convert symbol from INFY.NS to INFY format for investpy."""
    return symbol.replace(".NS", "").replace(".BSE", "")


def _fetch_via_investpy(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Fetch real-time quote from investing.com via investpy.
    Works for NSE stocks (Indian stocks).
    """
    if not INVESTPY_AVAILABLE:
        logger.debug("investpy not available for %s", symbol)
        return None

    try:
        # Convert symbol format (INFY.NS -> INFY)
        investpy_symbol = _symbol_to_investpy_format(symbol)
        
        # Get current quote from investing.com
        quote = investpy.stocks.get_stock_information(
            stock=investpy_symbol,
            country="India",
            as_json=False
        )
        
        if quote is None:
            return None

        # Extract data from quote dict
        current_price = quote.get("Last Price") or quote.get("Last")
        if current_price is None:
            return None

        current_price = float(current_price)
        prev_close = float(quote.get("Prev. Close", current_price))
        open_val = float(quote.get("Open", current_price))
        high_val = float(quote.get("High", current_price))
        low_val = float(quote.get("Low", current_price))
        volume = int(quote.get("Volume", 0) or 0)

        change_amount = round(current_price - prev_close, 2)
        change_pct = round((change_amount / prev_close) * 100, 2) if prev_close else 0.0

        logger.info("[investpy] %s: ₹%.2f (real-time from investing.com)", symbol, current_price)

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
        logger.debug("investpy fetch failed for %s: %s", symbol, str(e)[:100])
        return None


def _fetch_via_investpy_historical(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Fetch last close price from investpy historical data.
    Used as fallback when live quote unavailable.
    """
    if not INVESTPY_AVAILABLE:
        return None

    try:
        investpy_symbol = _symbol_to_investpy_format(symbol)
        
        # Get last 5 days of data
        df = investpy.stocks.get_stock_recent_data(
            stock=investpy_symbol,
            country="India",
            as_json=False,
            order="ascending"
        )

        if df is None or df.empty:
            return None

        # Get last row (most recent close)
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2] if len(df) >= 2 else last_row

        current_price = float(last_row["Close"])
        prev_close = float(prev_row["Close"])
        open_val = float(last_row["Open"])
        high_val = float(last_row["High"])
        low_val = float(last_row["Low"])
        volume = int(last_row.get("Volume", 0) or 0)

        change_amount = round(current_price - prev_close, 2)
        change_pct = round((change_amount / prev_close) * 100, 2) if prev_close else 0.0

        logger.info("[investpy historical] %s: ₹%.2f (last close)", symbol, current_price)

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
        logger.debug("investpy historical fetch failed for %s: %s", symbol, str(e)[:100])
        return None


def fetch_quotes_batch(symbols: List[str], retries: int = 2) -> pd.DataFrame:
    """
    Download latest live quotes for a list of symbols.

    Per-symbol priority:
      1. investpy quote (real-time last price from investing.com)
      2. investpy historical (last close if live unavailable)
      3. Mock fallback (deterministic simulation)

    Returns a DataFrame with columns:
        Symbol, CurrentPrice, Open, High, Low, Volume,
        PreviousClose, DailyChangePct, DailyChangeAmount, IsMock
    """
    logger.info("Fetching live quotes for %d symbols from investing.com", len(symbols))
    if not symbols:
        return pd.DataFrame()

    results = []
    for sym in symbols:
        quote = None

        # Priority 1: investpy live quote
        for _ in range(retries):
            quote = _fetch_via_investpy(sym)
            if quote:
                break

        # Priority 2: investpy historical fallback
        if not quote:
            for _ in range(retries):
                quote = _fetch_via_investpy_historical(sym)
                if quote:
                    break

        # Priority 3: mock fallback
        if not quote:
            quote = generate_mock_quote(sym)

        results.append(quote)

    return pd.DataFrame(results)


def fetch_quote_single(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Fetch live quote for a single symbol.
    Priority: investpy -> investpy historical -> mock fallback.
    """
    logger.info("Fetching live quote for: %s from investing.com", symbol)

    # Priority 1: investpy live
    quote = _fetch_via_investpy(symbol)
    if quote:
        return quote

    # Priority 2: investpy historical
    quote = _fetch_via_investpy_historical(symbol)
    if quote:
        return quote

    # Priority 3: mock
    return generate_mock_quote(symbol)
