"""
market_breadth.py — Market Breadth Research Laboratory.
"""

import logging
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

from app.lab.backtester import load_ohlcv

logger = logging.getLogger(__name__)

# Representative subset of high liquidity stock tickers for fast breadth checks
BREADTH_TICKERS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS",
    "LT.NS", "AXISBANK.NS", "ASIANPAINT.NS", "MARUTI.NS", "TITAN.NS"
]

def calculate_market_breadth(period: str = "6M") -> Dict:
    """
    Compute daily market breadth metrics across representative universe:
    - Advance-Decline Ratio (ADR)
    - Participation Index (% stocks above 50D SMA)
    - 52-Week Highs / Lows proxies
    """
    prices = {}
    for sym in BREADTH_TICKERS:
        df = load_ohlcv(sym, period)
        if df is not None and not df.empty:
            prices[sym] = df["Close"]
            
    if not prices:
        raise ValueError("Could not load stock histories for breadth computation")
        
    prices_df = pd.DataFrame(prices).dropna()
    dates = prices_df.index
    
    # Calculate daily returns
    returns_df = prices_df.pct_change().dropna()
    
    # daily advances / declines
    advances = (returns_df > 0).sum(axis=1)
    declines = (returns_df < 0).sum(axis=1)
    ad_ratio = (advances / declines.replace(0, 1)).round(2)
    
    # Participation: % of stocks above 50 SMA
    above_50_sma_pct = []
    for date in returns_df.index:
        sub_df = prices_df.loc[:date].tail(50)
        if len(sub_df) < 50:
            above_50_sma_pct.append(100.0)
            continue
            
        smas = sub_df.mean()
        latest = prices_df.loc[date]
        above = (latest > smas).sum()
        pct = (above / len(latest)) * 100
        above_50_sma_pct.append(round(float(pct), 1))
        
    # Highs / Lows: 20-day high/low proxies
    high_count = []
    low_count = []
    for date in returns_df.index:
        sub_df = prices_df.loc[:date].tail(20)
        latest = prices_df.loc[date]
        
        highs = (latest >= sub_df.max()).sum()
        lows = (latest <= sub_df.min()).sum()
        
        high_count.append(int(highs))
        low_count.append(int(lows))
        
    # Format timeseries
    ts = []
    for i, date in enumerate(returns_df.index):
        ts.append({
            "date": date.strftime("%Y-%m-%d") if hasattr(date, "strftime") else str(date),
            "ad_ratio": float(ad_ratio.iloc[i]),
            "participation_pct": float(above_50_sma_pct[i]),
            "new_highs": int(high_count[i]),
            "new_lows": int(low_count[i])
        })
        
    # Current snapshot
    latest_idx = -1 if len(ts) > 0 else 0
    current = ts[latest_idx] if ts else {"ad_ratio": 1.0, "participation_pct": 50.0, "new_highs": 0, "new_lows": 0}
    
    return {
        "current_ad_ratio": current["ad_ratio"],
        "current_participation_pct": current["participation_pct"],
        "current_new_highs": current["new_highs"],
        "current_new_lows": current["new_lows"],
        "timeline": ts[::5] # downsample
    }
