"""
correlation_lab.py — Correlation & Redundancy Analysis Engine.
"""

import logging
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

from app.data.loader import data_loader
from app.lab.backtester import load_ohlcv

logger = logging.getLogger(__name__)

def run_correlation_research(
    symbol: str = "RELIANCE.NS",
    period: str = "3Y"
) -> Dict:
    """
    Calculate and analyze correlations:
    1. Feature/Score correlation matrix.
    2. Model correlation matrix.
    3. Rolling returns correlation with benchmark.
    4. Redundant indicators detection.
    """
    df = data_loader.get_df()
    
    # 1. Feature / Score Correlation
    features = ["TechnicalScore", "MLScore", "GRUScore", "ReliabilityScore", "CompositeScoreV2", "Confidence"]
    avail_feats = [f for f in features if f in df.columns]
    
    feat_corr = {}
    feat_flat = []
    if len(avail_feats) >= 2:
        corr = df[avail_feats].corr(method="pearson")
        for col in corr.columns:
            for idx in corr.index:
                val = corr.loc[idx, col]
                feat_flat.append({
                    "a": col,
                    "b": idx,
                    "val": round(float(val), 4) if not pd.isna(val) else 1.0
                })
        feat_corr = {"features": avail_feats, "matrix": feat_flat}
        
    # 2. Indicator Correlation & Redundancy
    # Fetch price data, generate indicators, correlate their signals
    redundant_indicators = []
    ind_flat = []
    ind_keys = ["rsi", "macd", "ema", "sma"]
    
    ohlcv = load_ohlcv(symbol, period)
    if ohlcv is not None and not ohlcv.empty:
        from app.lab.backtester import generate_signals
        ind_dfs = {}
        for ind in ind_keys:
            params = {}
            if ind == "rsi": params = {"period": 14}
            elif ind == "macd": params = {"fast": 12, "slow": 26, "signal": 9}
            elif ind == "ema": params = {"fast_period": 9, "slow_period": 21}
            elif ind == "sma": params = {"fast_period": 50, "slow_period": 200}
            
            sig_df = generate_signals(ohlcv, ind, params)
            ind_dfs[ind] = sig_df["Signal"]
            
        ind_df = pd.DataFrame(ind_dfs)
        corr_ind = ind_df.corr().fillna(0.0)
        
        # Format list and flag redundancy (|r| > 0.60)
        for col in corr_ind.columns:
            for idx in corr_ind.index:
                val = corr_ind.loc[idx, col]
                ind_flat.append({
                    "a": col.upper(),
                    "b": idx.upper(),
                    "val": round(float(val), 4)
                })
                if col != idx and abs(val) > 0.60:
                    pair = sorted([col.upper(), idx.upper()])
                    pair_str = " & ".join(pair)
                    if pair_str not in redundant_indicators:
                        redundant_indicators.append(pair_str)
                        
    # 3. Rolling Correlation Strategy vs Benchmark
    rolling_corr = []
    nifty = load_ohlcv("^NSEI", period)
    stock = load_ohlcv(symbol, period)
    if nifty is not None and stock is not None:
        merged = pd.DataFrame({
            "nifty": nifty["Close"].pct_change(),
            "stock": stock["Close"].pct_change()
        }).dropna()
        
        # 60-day rolling correlation
        r_corr = merged["stock"].rolling(60).corr(merged["nifty"]).dropna()
        dates = nifty["Date"].iloc[r_corr.index]
        
        rolling_corr = [
            {"date": d, "correlation": round(float(v), 4)}
            for d, v in zip(pd.to_datetime(dates).dt.strftime("%Y-%m-%d"), r_corr.values)
            if not pd.isna(v)
        ][::10] # downsample
        
    return {
        "symbol": symbol,
        "feature_correlation": feat_corr,
        "indicator_correlation": {
            "indicators": [i.upper() for i in ind_keys],
            "matrix": ind_flat
        },
        "redundant_indicators": redundant_indicators,
        "rolling_correlation": rolling_corr
    }
