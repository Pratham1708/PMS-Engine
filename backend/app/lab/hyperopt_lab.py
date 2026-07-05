"""
hyperopt_lab.py — Hyperparameter Optimization Laboratory.
"""

import logging
import itertools
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

from app.data.loader import data_loader
from app.lab.backtester import load_ohlcv, run_backtest
from app.lab.metrics import compute_all_metrics
from app.lab.db_lab import save_weight_snapshot

logger = logging.getLogger(__name__)

def optimize_ml_thresholds(
    symbol: str = "^NSEI",
    period: str = "3Y",
    target_metric: str = "sharpe_ratio",
    experiment_id: Optional[str] = None
) -> Dict:
    """Optimize ML model buy/sell decision thresholds."""
    df = load_ohlcv(symbol, period)
    if df is None or df.empty:
        raise ValueError("Could not load price history")
        
    # Generate scores
    from app.lab.indicators import compute_rsi
    rsi = compute_rsi(df, 14)["RSI"]
    
    buy_grids = [55.0, 60.0, 65.0, 70.0]
    sell_grids = [30.0, 35.0, 40.0, 45.0]
    
    results = []
    best_params = {}
    best_score = -999.0
    
    for b_th, s_th in itertools.product(buy_grids, sell_grids):
        sig_df = df.copy()
        sig_df["Signal"] = 0
        # Simulated ML score based on inverse RSI momentum
        sig_df.loc[rsi > b_th, "Signal"] = 1
        sig_df.loc[rsi < s_th, "Signal"] = -1
        
        bt = run_backtest(sig_df)
        metrics = compute_all_metrics(bt["equity_series"], bt["trade_log"])
        val = metrics.get(target_metric, 0.0)
        
        row = {"buy_threshold": b_th, "sell_threshold": s_th, target_metric: val}
        results.append(row)
        
        if val > best_score:
            best_score = val
            best_params = {"buy_threshold": b_th, "sell_threshold": s_th}
            
    return {
        "best_params": best_params,
        "best_score": round(best_score, 4),
        "results": results[:20]
    }

def optimize_risk_thresholds(
    symbol: str = "^NSEI",
    period: str = "3Y",
    target_metric: str = "sharpe_ratio"
) -> Dict:
    """Optimize stop-loss / risk caps parameters."""
    df = load_ohlcv(symbol, period)
    if df is None or df.empty:
        raise ValueError("Could not load price history")
        
    sl_grids = [0.01, 0.02, 0.03, 0.05]  # Stop loss %
    tp_grids = [0.05, 0.10, 0.15, 0.20]  # Take profit %
    
    results = []
    best_params = {}
    best_score = -999.0
    
    from app.lab.indicators import compute_macd
    macd = compute_macd(df)["Signal"]
    
    for sl, tp in itertools.product(sl_grids, tp_grids):
        # Simulated backtest with SL/TP
        sig_df = df.copy()
        sig_df["Signal"] = macd
        
        bt = run_backtest(sig_df)
        # Apply simulated SL/TP cuts to trade logs
        log = bt["trade_log"]
        adj_log = []
        for t in log:
            ret = t["return_pct"] / 100.0
            if ret < -sl:
                ret = -sl
            elif ret > tp:
                ret = tp
            t_copy = t.copy()
            t_copy["return_pct"] = ret * 100.0
            adj_log.append(t_copy)
            
        metrics = compute_all_metrics(bt["equity_series"], adj_log)
        val = metrics.get(target_metric, 0.0)
        
        row = {"stop_loss": sl, "take_profit": tp, target_metric: val}
        results.append(row)
        
        if val > best_score:
            best_score = val
            best_params = {"stop_loss": sl, "take_profit": tp}
            
    return {
        "best_params": best_params,
        "best_score": round(best_score, 4),
        "results": results
    }

def optimize_position_sizing(
    symbol: str = "^NSEI",
    period: str = "3Y",
    target_metric: str = "sharpe_ratio"
) -> Dict:
    """Optimize Kelly fraction and ATR sizing multipliers."""
    df = load_ohlcv(symbol, period)
    if df is None or df.empty:
        raise ValueError("Could not load price history")
        
    frac_grids = [0.25, 0.50, 0.75, 1.0] # Kelly fraction
    atr_grids = [1.0, 1.5, 2.0, 2.5]     # ATR multipliers
    
    results = []
    best_params = {}
    best_score = -999.0
    
    from app.lab.indicators import compute_rsi
    rsi = compute_rsi(df, 14)["RSI"]
    
    for frac, atr in itertools.product(frac_grids, atr_grids):
        sig_df = df.copy()
        sig_df["Signal"] = rsi.apply(lambda x: 1 if x < 30 else (-1 if x > 70 else 0))
        
        bt = run_backtest(sig_df)
        # Sizing modifications: scale return by fraction/multiplier
        log = bt["trade_log"]
        adj_log = []
        for t in log:
            # Scale return by sizing multiplier proxy
            ret = t["return_pct"] * frac * (2.0 / atr)
            t_copy = t.copy()
            t_copy["return_pct"] = ret
            adj_log.append(t_copy)
            
        metrics = compute_all_metrics(bt["equity_series"], adj_log)
        val = metrics.get(target_metric, 0.0)
        
        row = {"kelly_fraction": frac, "atr_multiplier": atr, target_metric: val}
        results.append(row)
        
        if val > best_score:
            best_score = val
            best_params = {"kelly_fraction": frac, "atr_multiplier": atr}
            
    return {
        "best_params": best_params,
        "best_score": round(best_score, 4),
        "results": results
    }
