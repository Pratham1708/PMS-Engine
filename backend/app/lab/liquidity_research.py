"""
liquidity_research.py — Liquidity Research & Suitability Auditor.
"""

import logging
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

from app.lab.backtester import load_ohlcv

logger = logging.getLogger(__name__)

def evaluate_stock_liquidity(
    symbol: str,
    period: str = "3M",
    min_adv_inr: float = 5000000.0, # 50 Lakhs minimum ADV (simulated proxy)
    max_gap_freq: float = 15.0      # Max 15% days with gap opens
) -> Dict:
    """
    Perform a complete liquidity audit for a ticker:
    - ADV (Average Daily Volume)
    - Amihud Illiquidity Ratio
    - Gap Open Frequency
    - Rolling Volatility
    - Rejection decision
    """
    df = load_ohlcv(symbol, period)
    if df is None or df.empty:
        return {
            "symbol": symbol,
            "decision": "REJECT",
            "reason": "No price history available on yFinance feed.",
            "adv_inr": 0.0,
            "gap_frequency": 0.0,
            "amihud_illiquidity": 999.0
        }
        
    df = df.copy()
    df["Daily_Return"] = df["Close"].pct_change()
    
    # ADV proxy (using Volume * Close as proxy for turnover)
    df["ADV_INR"] = df["Volume"] * df["Close"]
    adv = float(df["ADV_INR"].mean())
    
    # Gap frequency
    prev_close = df["Close"].shift(1)
    df["Gap_Pct"] = (df["Open"] - prev_close).abs() / prev_close * 100.0
    gap_days = (df["Gap_Pct"] > 1.5).sum()
    gap_freq = float(gap_days / len(df) * 100) if len(df) > 0 else 0.0
    
    # Amihud Illiquidity (absolute return per unit volume)
    # Scaled by 10^6 for readability
    denom = df["Volume"] * df["Close"]
    df["Amihud"] = (df["Daily_Return"].abs() / denom.replace(0, np.nan)) * 1e6
    amihud = float(df["Amihud"].dropna().mean()) if not df["Amihud"].dropna().empty else 999.0
    
    # Volatility
    vol = float(df["Daily_Return"].std() * np.sqrt(252) * 100) if len(df) > 5 else 0.0
    
    # Automatic Rejection Filters
    rejections = []
    if adv < min_adv_inr:
        rejections.append(f"ADV (Average Daily Volume) of ₹{adv:,.0f} is below minimum threshold ₹{min_adv_inr:,.0f}")
    if gap_freq > max_gap_freq:
        rejections.append(f"Gap frequency of {gap_freq:.1f}% exceeds max threshold {max_gap_freq}%")
    if amihud > 5.0:
        rejections.append(f"Amihud Illiquidity score {amihud:.3f} is too high (market impact risk)")
        
    decision = "REJECT" if rejections else "ACCEPT"
    
    return {
        "symbol": symbol,
        "decision": decision,
        "reasons": rejections,
        "adv_inr": round(adv, 2),
        "gap_frequency": round(gap_freq, 2),
        "amihud_illiquidity": round(amihud, 4),
        "annualized_volatility": round(vol, 2),
        "turnover_ratio_proxy": round(float(df["Volume"].mean()) / 100000, 2)
    }
