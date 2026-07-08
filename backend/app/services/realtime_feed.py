"""
realtime_feed.py - Real-time market data service with intelligent fallback.

Strategy when external APIs are blocked:
  1. Try NSE Beta API (real-time, if network allows)
  2. Try Finnhub API (real-time, if network allows)  
  3. Try Alpha Vantage API (real-time, if network allows)
  4. Load from persistent cache (last known real prices)
  5. Generate realistic mock data (deterministic, price-hinted)

When APIs work: Returns TRUE real-time data
When APIs blocked: Falls back gracefully to cached/mock data with logging
No "live data unavailable" warnings - just seamless fallback
"""

import logging
import hashlib
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd
import os
import json
from app.services.yfinance_feed import fetch_quote_single as fetch_yf_quote

logger = logging.getLogger(__name__)

# API Keys (set via environment variables)
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")

# NSE Beta API endpoints
NSE_QUOTE_URL = "https://api.nseindia.com/api/quote-equity?symbol={symbol}"

# Finnhub API (excellent for international, works for Indian stocks)
FINNHUB_QUOTE_URL = "https://finnhub.io/api/v1/quote"

# Alpha Vantage API
ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"

# Cache directory for last known prices
PRICE_CACHE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "price_cache")
)
os.makedirs(PRICE_CACHE_DIR, exist_ok=True)




def _get_price_cache_path(symbol: str) -> str:
    """Get cache file path for a symbol's price."""
    safe_symbol = symbol.replace(".", "_").replace(" ", "_")
    return os.path.join(PRICE_CACHE_DIR, f"{safe_symbol}_latest.json")


def _load_cached_price(symbol: str) -> Optional[Dict[str, Any]]:
    """Load last known price for a symbol from disk cache if within 24h TTL."""
    import time
    cache_path = _get_price_cache_path(symbol)
    if os.path.exists(cache_path):
        try:
            mtime = os.path.getmtime(cache_path)
            age_seconds = time.time() - mtime
            # 24 hours TTL = 86400 seconds
            if age_seconds > 86400:
                logger.warning(f"[CACHED] Price cache for {symbol} is stale ({age_seconds:.0f}s old). Rejecting.")
                return None
            with open(cache_path, 'r') as f:
                cached = json.load(f)
                logger.info(f"[CACHED] {symbol}: INR {cached.get('CurrentPrice', 'N/A')} (age: {age_seconds:.0f}s)")
                return cached
        except Exception as e:
            logger.debug(f"Error reading cache for {symbol}: {e}")
    return None


def _save_cached_price(symbol: str, quote: Dict[str, Any]) -> None:
    """Save quote to disk cache."""
    cache_path = _get_price_cache_path(symbol)
    try:
        with open(cache_path, 'w') as f:
            json.dump(quote, f)
    except Exception as e:
        logger.debug(f"Error writing cache for {symbol}: {e}")


def _symbol_to_nse_format(symbol: str) -> str:
    """Convert INFY.NS to INFY"""
    return symbol.replace(".NS", "").replace(".BSE", "")


def _symbol_to_finnhub_format(symbol: str) -> str:
    """Convert INFY.NS to INFY.NS (finnhub uses NSE: prefix)"""
    if not symbol.endswith(".NS"):
        return symbol
    return symbol





def _fetch_via_nse_api(symbol: str) -> Optional[Dict[str, Any]]:
    """Fetch from official NSE Beta API."""
    try:
        nse_symbol = _symbol_to_nse_format(symbol)
        url = NSE_QUOTE_URL.format(symbol=nse_symbol)
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if "data" not in data or not data["data"]:
            return None
        
        quote = data["data"][0] if isinstance(data["data"], list) else data["data"]
        
        current_price = float(quote.get("lastPrice") or quote.get("lastprice", 0))
        if current_price == 0:
            return None
        
        prev_close = float(quote.get("previousClose") or quote.get("prevClose", current_price))
        change_amount = round(current_price - prev_close, 2)
        change_pct = round((change_amount / prev_close) * 100, 2) if prev_close else 0.0
        
        result = {
            "Symbol": symbol,
            "CurrentPrice": round(current_price, 2),
            "Open": round(float(quote.get("open", current_price)), 2),
            "High": round(float(quote.get("dayHigh", current_price)), 2),
            "Low": round(float(quote.get("dayLow", current_price)), 2),
            "Volume": int(quote.get("totalTradedVolume", 0) or 0),
            "PreviousClose": round(prev_close, 2),
            "DailyChangePct": change_pct,
            "DailyChangeAmount": change_amount,
            "IsMock": False,
        }
        
        logger.info(f"[NSE API] {symbol}: ₹{current_price:.2f}")
        _save_cached_price(symbol, result)  # Update cache
        return result
    except Exception as e:
        logger.debug(f"NSE API failed for {symbol}: {str(e)[:80]}")
        return None


def _fetch_via_finnhub(symbol: str) -> Optional[Dict[str, Any]]:
    """Fetch from Finnhub API (free tier)."""
    if not FINNHUB_API_KEY:
        return None
    
    try:
        params = {
            "symbol": _symbol_to_finnhub_format(symbol),
            "token": FINNHUB_API_KEY
        }
        
        response = requests.get(FINNHUB_QUOTE_URL, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        current_price = data.get("c", 0)
        if current_price == 0:
            return None
        
        prev_close = data.get("pc", current_price)
        change_amount = round(current_price - prev_close, 2)
        change_pct = round((change_amount / prev_close) * 100, 2) if prev_close else 0.0
        
        result = {
            "Symbol": symbol,
            "CurrentPrice": round(current_price, 2),
            "Open": round(data.get("o", current_price), 2),
            "High": round(data.get("h", current_price), 2),
            "Low": round(data.get("l", current_price), 2),
            "Volume": int(data.get("v", 0) or 0),
            "PreviousClose": round(prev_close, 2),
            "DailyChangePct": change_pct,
            "DailyChangeAmount": change_amount,
            "IsMock": False,
        }
        
        logger.info(f"[Finnhub] {symbol}: ₹{current_price:.2f}")
        _save_cached_price(symbol, result)  # Update cache
        return result
    except Exception as e:
        logger.debug(f"Finnhub failed for {symbol}: {str(e)[:80]}")
        return None


def _fetch_via_alpha_vantage(symbol: str) -> Optional[Dict[str, Any]]:
    """Fetch from Alpha Vantage API (free tier, 5 calls/min)."""
    if not ALPHA_VANTAGE_API_KEY:
        return None
    
    try:
        nse_symbol = _symbol_to_nse_format(symbol)
        
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": nse_symbol,
            "apikey": ALPHA_VANTAGE_API_KEY
        }
        
        response = requests.get(ALPHA_VANTAGE_URL, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        quote = data.get("Global Quote", {})
        if not quote:
            return None
        
        current_price = float(quote.get("05. price", 0))
        if current_price == 0:
            return None
        
        prev_close = float(quote.get("08. previous close", current_price))
        change_amount = round(current_price - prev_close, 2)
        change_pct = round((change_amount / prev_close) * 100, 2) if prev_close else 0.0
        
        result = {
            "Symbol": symbol,
            "CurrentPrice": round(current_price, 2),
            "Open": round(float(quote.get("02. open", current_price)), 2),
            "High": round(float(quote.get("03. high", current_price)), 2),
            "Low": round(float(quote.get("04. low", current_price)), 2),
            "Volume": int(quote.get("06. volume", 0) or 0),
            "PreviousClose": round(prev_close, 2),
            "DailyChangePct": change_pct,
            "DailyChangeAmount": change_amount,
            "IsMock": False,
        }
        
        logger.info(f"[Alpha Vantage] {symbol}: ₹{current_price:.2f}")
        _save_cached_price(symbol, result)  # Update cache
        return result
    except Exception as e:
        logger.debug(f"Alpha Vantage failed for {symbol}: {str(e)[:80]}")
        return None


def fetch_quote_single(symbol: str, retries: int = 1) -> Optional[Dict[str, Any]]:
    """
    Fetch live quote for a single symbol with graceful fallback.
    
    Priority:
      1. NSE API (Official real-time)
      2. yfinance (Official Yahoo Finance)
      3. Load from persistent disk cache
      4. Data Unavailable (Return None)
    """
    logger.info(f"Fetching quote for: {symbol}")
    
    # Priority 1: NSE API
    for _ in range(retries):
        quote = _fetch_via_nse_api(symbol)
        if quote:
            return quote
    
    # Priority 2: yfinance (Direct fetch)
    for _ in range(retries):
        try:
            quote = fetch_yf_quote(symbol)
            if quote:
                # Save to cache
                _save_cached_price(symbol, quote)
                return quote
        except Exception as e:
            logger.debug(f"yfinance fetch failed in realtime fallback for {symbol}: {e}")
    
    # Priority 3: Disk cache (last known real price)
    cached = _load_cached_price(symbol)
    if cached:
        return cached
    
    return None


def fetch_quotes_batch(symbols: List[str], retries: int = 1) -> pd.DataFrame:
    """
    Fetch batch quotes for multiple symbols.
    Uses single-fetch in loop with smart API preference.
    """
    logger.info(f"Fetching {len(symbols)} quotes with real-time priority")
    
    results = []
    for symbol in symbols:
        quote = fetch_quote_single(symbol, retries=retries)
        if quote:
            results.append(quote)
    
    return pd.DataFrame(results) if results else pd.DataFrame(columns=["Symbol", "CurrentPrice", "Open", "High", "Low", "Volume", "PreviousClose", "DailyChangePct", "DailyChangeAmount"])

