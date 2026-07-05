"""
cross_indicator.py — Multi-indicator combinations analysis & ranking engine.
"""

import logging
import itertools
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

from app.lab.backtester import load_ohlcv, run_backtest, generate_signals
from app.lab.metrics import compute_all_metrics
from app.lab.indicators import get_indicator_list

logger = logging.getLogger(__name__)

SUPPORTED_COMBOS = [
    # Individual indicators
    ("rsi",),
    ("macd",),
    ("ema",),
    ("sma",),
    # Dual indicator systems
    ("rsi", "macd"),
    ("rsi", "ema"),
    ("macd", "ema"),
    ("ema", "sma"),
    # Triple indicator systems
    ("rsi", "macd", "ema"),
    ("rsi", "ema", "sma"),
]

def combine_signals(df_list: List[pd.DataFrame]) -> pd.DataFrame:
    """
    Intersect signals from multiple indicator DataFrames.
    BUY (+1) if ALL indicators signal BUY (+1)
    SELL (-1) if ALL indicators signal SELL (-1)
    otherwise HOLD (0).
    """
    if not df_list:
        return pd.DataFrame()
        
    out = df_list[0].copy()
    signals = [df["Signal"] for df in df_list]
    
    # Intersect
    combined = pd.Series(0, index=out.index)
    
    # BUY intersection
    buys = pd.Series(True, index=out.index)
    for s in signals:
        buys = buys & (s == 1)
    combined[buys] = 1
    
    # SELL intersection
    sells = pd.Series(True, index=out.index)
    for s in signals:
        sells = sells & (s == -1)
    combined[sells] = -1
    
    out["Signal"] = combined
    return out

def run_cross_indicator_backtest(
    symbol: str,
    indicators: Tuple[str, ...],
    period: str = "3Y",
    initial_capital: float = 100000.0
) -> Dict:
    """Run backtest on a single, dual, or triple indicator combination."""
    df = load_ohlcv(symbol, period)
    if df is None or df.empty:
        raise ValueError(f"Could not load OHLCV data for {symbol}")
        
    dfs = []
    for ind in indicators:
        # Generate default parameters
        params = {}
        if ind == "rsi":
            params = {"period": 14, "buy_threshold": 30.0, "sell_threshold": 70.0}
        elif ind == "macd":
            params = {"fast": 12, "slow": 26, "signal": 9}
        elif ind == "ema":
            params = {"fast_period": 9, "slow_period": 21}
        elif ind == "sma":
            params = {"fast_period": 50, "slow_period": 200}
            
        sig_df = generate_signals(df, ind, params)
        dfs.append(sig_df)
        
    combined_df = combine_signals(dfs)
    bt = run_backtest(combined_df, initial_capital=initial_capital)
    metrics = compute_all_metrics(bt["equity_series"], bt["trade_log"])
    
    return {
        "combination": " + ".join(ind.upper() for ind in indicators),
        "complexity": "Single" if len(indicators) == 1 else ("Dual" if len(indicators) == 2 else "Triple"),
        "cagr": metrics.get("cagr_pct", 0.0),
        "sharpe": metrics.get("sharpe_ratio", 0.0),
        "max_drawdown": metrics.get("max_drawdown_pct", 0.0),
        "win_rate": metrics.get("win_rate_pct", 0.0),
        "trades_count": len(bt["trade_log"]),
        "equity_curve": [{"date": d, "portfolio": float(p)} for d, p in zip(bt["equity_dates"], bt["equity_series"])],
    }

def rank_indicator_combinations(
    symbol: str,
    period: str = "3Y",
    target_metric: str = "sharpe"
) -> Dict:
    """Evaluate and rank all single, dual, and triple indicator combinations."""
    results = []
    
    for combo in SUPPORTED_COMBOS:
        try:
            res = run_cross_indicator_backtest(symbol, combo, period=period)
            results.append(res)
        except Exception as e:
            logger.error(f"Failed combination {combo}: {e}")
            
    # Sort results
    if target_metric == "sharpe":
        results.sort(key=lambda x: x.get("sharpe") or -999.0, reverse=True)
    elif target_metric == "cagr":
        results.sort(key=lambda x: x.get("cagr") or -999.0, reverse=True)
    else:
        results.sort(key=lambda x: x.get("win_rate") or -999.0, reverse=True)
        
    return {
        "symbol": symbol,
        "period": period,
        "target_metric": target_metric,
        "rankings": [
            {
                "rank": i + 1,
                "combination": r["combination"],
                "complexity": r["complexity"],
                "cagr": round(r["cagr"], 2),
                "sharpe": round(r["sharpe"], 4),
                "max_drawdown": round(r["max_drawdown"], 2),
                "win_rate": round(r["win_rate"], 2),
                "trades_count": r["trades_count"],
            }
            for i, r in enumerate(results)
        ],
        "top_equity_curve": results[0]["equity_curve"] if results else []
    }
