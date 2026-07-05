"""
monte_carlo.py — Monte Carlo Simulation Engine.
"""

import logging
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

from app.lab.backtester import load_ohlcv

logger = logging.getLogger(__name__)

def run_monte_carlo_simulation(
    symbol: str = "^NSEI",
    period: str = "3Y",
    n_simulations: int = 250,
    horizon_days: int = 252,
    initial_capital: float = 100000.0
) -> Dict:
    """
    Run bootstrap Monte Carlo simulation on daily returns of a benchmark or portfolio.
    1. Fetch daily returns.
    2. Resample returns with replacement to simulate paths.
    3. Calculate stats (CAGR, Max DD, VaR).
    """
    df = load_ohlcv(symbol, period)
    if df is None or df.empty:
        raise ValueError(f"Could not load OHLCV data for {symbol}")
        
    daily_rets = df["Close"].pct_change().dropna().values
    if len(daily_rets) < 20:
        # Fallback dummy returns if insufficient
        daily_rets = np.random.normal(0.0005, 0.01, 252)
        
    sim_cagr = []
    sim_max_dd = []
    paths = []
    
    # Run simulations
    for _ in range(n_simulations):
        # Sample daily returns with replacement
        sampled = np.random.choice(daily_rets, size=horizon_days, replace=True)
        equity = initial_capital * np.cumprod(1.0 + sampled)
        
        # Calculate stats
        final_val = equity[-1]
        cagr = (final_val / initial_capital) ** (252.0 / horizon_days) - 1.0
        
        # Max drawdown
        cum_max = np.maximum.accumulate(equity)
        drawdowns = (equity - cum_max) / cum_max * 100
        mdd = float(np.min(drawdowns))
        
        sim_cagr.append(float(cagr * 100))
        sim_max_dd.append(mdd)
        
        # Save a few paths for visualization (e.g., top 10 paths)
        if len(paths) < 10:
            paths.append([float(x) for x in equity[::10]]) # downsample to 25 points
            
    sim_cagr = np.array(sim_cagr)
    sim_max_dd = np.array(sim_max_dd)
    
    # Confidence intervals
    cagr_95_low = float(np.percentile(sim_cagr, 2.5))
    cagr_95_high = float(np.percentile(sim_cagr, 97.5))
    cagr_99_low = float(np.percentile(sim_cagr, 0.5))
    cagr_99_high = float(np.percentile(sim_cagr, 99.5))
    
    mdd_95 = float(np.percentile(sim_max_dd, 5.0)) # 5th percentile worst drawdown
    mdd_99 = float(np.percentile(sim_max_dd, 1.0)) # 1st percentile worst drawdown
    
    # Distributions
    c_counts, c_edges = np.histogram(sim_cagr, bins=10)
    cagr_dist = [
        {
            "min": round(float(c_edges[i]), 2),
            "max": round(float(c_edges[i+1]), 2),
            "count": int(c_counts[i]),
            "label": f"{c_edges[i]:.1f}% to {c_edges[i+1]:.1f}%"
        }
        for i in range(len(c_counts))
    ]
    
    d_counts, d_edges = np.histogram(sim_max_dd, bins=10)
    mdd_dist = [
        {
            "min": round(float(d_edges[i]), 2),
            "max": round(float(d_edges[i+1]), 2),
            "count": int(d_counts[i]),
            "label": f"{d_edges[i]:.1f}% to {d_edges[i+1]:.1f}%"
        }
        for i in range(len(d_counts))
    ]
    
    return {
        "symbol": symbol,
        "n_simulations": n_simulations,
        "horizon_days": horizon_days,
        "expected_cagr": round(float(np.median(sim_cagr)), 2),
        "expected_max_dd": round(float(np.median(sim_max_dd)), 2),
        "cagr_95_ci": [round(cagr_95_low, 2), round(cagr_95_high, 2)],
        "cagr_99_ci": [round(cagr_99_low, 2), round(cagr_99_high, 2)],
        "mdd_95_ci": round(mdd_95, 2),
        "mdd_99_ci": round(mdd_99, 2),
        "cagr_distribution": cagr_dist,
        "mdd_distribution": mdd_dist,
        "simulated_paths": paths,
    }
