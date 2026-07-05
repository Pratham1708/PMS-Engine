"""
portfolio_construction.py — Portfolio Optimization & Efficient Frontier Engine.
"""

import logging
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

from app.lab.backtester import load_ohlcv

logger = logging.getLogger(__name__)

def optimize_portfolio_construction(
    symbols: List[str],
    period: str = "3Y",
    rf_rate: float = 0.065
) -> Dict:
    """
    Build efficient frontier and compute optimized portfolio weights for a set of stock tickers.
    1. Fetch historical returns.
    2. Compute covariance matrix and mean expected returns.
    3. Generate random portfolios for Efficient Frontier scatter.
    4. Compute Max Sharpe, Min Variance, and Risk Parity weights.
    """
    # Safeguard ticker count
    if len(symbols) < 2:
        symbols = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS"]
        
    prices = {}
    for sym in symbols:
        df = load_ohlcv(sym, period)
        if df is not None and not df.empty:
            prices[sym] = df["Close"]
            
    if len(prices) < 2:
        raise ValueError("Insufficient pricing history for portfolio construction")
        
    prices_df = pd.DataFrame(prices).dropna()
    returns_df = prices_df.pct_change().dropna()
    
    # Expected returns (annualized)
    exp_rets = returns_df.mean() * 252
    # Covariance (annualized)
    cov_mat = returns_df.cov() * 252
    
    n_assets = len(exp_rets)
    n_portfolios = 200
    
    frontier_points = []
    best_sharpe = -999.0
    best_weights_max_sharpe = None
    min_vol = 999.0
    best_weights_min_var = None
    
    # Simulate random weights to build Efficient Frontier scatter
    rng = np.random.default_rng(42)
    for _ in range(n_portfolios):
        w = rng.random(n_assets)
        w /= np.sum(w)
        
        p_ret = float(np.sum(exp_rets * w))
        p_vol = float(np.sqrt(w.T @ cov_mat @ w))
        p_sharpe = (p_ret - rf_rate) / p_vol if p_vol > 0 else 0.0
        
        frontier_points.append({
            "volatility": round(p_vol * 100, 2),
            "return": round(p_ret * 100, 2),
            "sharpe": round(p_sharpe, 4)
        })
        
        # Max Sharpe
        if p_sharpe > best_sharpe:
            best_sharpe = p_sharpe
            best_weights_max_sharpe = w.copy()
            
        # Min Variance
        if p_vol < min_vol:
            min_vol = p_vol
            best_weights_min_var = w.copy()
            
    # Risk Parity weight proxy (inverse volatility scaling)
    vols = np.sqrt(np.diag(cov_mat))
    inv_vols = 1.0 / vols
    weights_risk_parity = inv_vols / np.sum(inv_vols)
    
    # Equal Weight weights
    weights_equal = np.ones(n_assets) / n_assets
    
    # Map weights
    def map_weights(w):
        return {symbols[i]: round(float(w[i]) * 100, 1) for i in range(n_assets)}
        
    return {
        "assets": symbols,
        "efficient_frontier": frontier_points,
        "max_sharpe": {
            "return": round(float(np.sum(exp_rets * best_weights_max_sharpe)) * 100, 2),
            "volatility": round(float(np.sqrt(best_weights_max_sharpe.T @ cov_mat @ best_weights_max_sharpe)) * 100, 2),
            "sharpe": round(best_sharpe, 4),
            "weights": map_weights(best_weights_max_sharpe)
        },
        "min_variance": {
            "return": round(float(np.sum(exp_rets * best_weights_min_var)) * 100, 2),
            "volatility": round(min_vol * 100, 2),
            "sharpe": round((float(np.sum(exp_rets * best_weights_min_var)) - rf_rate) / min_vol, 4),
            "weights": map_weights(best_weights_min_var)
        },
        "risk_parity": {
            "return": round(float(np.sum(exp_rets * weights_risk_parity)) * 100, 2),
            "volatility": round(float(np.sqrt(weights_risk_parity.T @ cov_mat @ weights_risk_parity)) * 100, 2),
            "sharpe": round((float(np.sum(exp_rets * weights_risk_parity)) - rf_rate) / float(np.sqrt(weights_risk_parity.T @ cov_mat @ weights_risk_parity)), 4),
            "weights": map_weights(weights_risk_parity)
        },
        "equal_weight": {
            "return": round(float(np.sum(exp_rets * weights_equal)) * 100, 2),
            "volatility": round(float(np.sqrt(weights_equal.T @ cov_mat @ weights_equal)) * 100, 2),
            "sharpe": round((float(np.sum(exp_rets * weights_equal)) - rf_rate) / float(np.sqrt(weights_equal.T @ cov_mat @ weights_equal)), 4),
            "weights": map_weights(weights_equal)
        }
    }
