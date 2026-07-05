"""
position_sizer.py — Position Sizing & Capital Allocation Simulation Engine.
"""

import logging
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

def simulate_position_sizing(
    trade_log: List[Dict],
    initial_capital: float = 100000.0,
    risk_pct: float = 2.0,  # For fixed fractional (2% risk)
    atr_multiplier: float = 2.0 # For ATR position sizing
) -> Dict:
    """
    Simulate different capital allocation and position sizing models over a sequence of trades.
    """
    if not trade_log:
        return {"sizing_comparison": [], "curves": []}
        
    df = pd.DataFrame(trade_log)
    df["entry_date"] = pd.to_datetime(df["entry_date"])
    df = df.sort_values("entry_date").reset_index(drop=True)
    
    # 1. FIXED CAPITAL (Equal amount per trade, e.g. 10% of initial capital per trade)
    fixed_cap = initial_capital * 0.10
    equity_fixed = [initial_capital]
    for _, row in df.iterrows():
        pnl = fixed_cap * (row["return_pct"] / 100.0)
        equity_fixed.append(equity_fixed[-1] + pnl)
        
    # 2. FIXED FRACTIONAL (Risk 2% of current equity per trade)
    equity_frac = [initial_capital]
    for _, row in df.iterrows():
        current_eq = equity_frac[-1]
        size = current_eq * (risk_pct / 100.0) / 0.05 # assumes 5% stop distance
        pnl = size * (row["return_pct"] / 100.0)
        equity_frac.append(current_eq + pnl)
        
    # 3. KELLY CRITERION
    # Calculate Kelly fraction from historical trades
    wins = df[df["return_pct"] > 0]["return_pct"]
    losses = df[df["return_pct"] <= 0]["return_pct"].abs()
    
    win_rate = len(wins) / len(df) if len(df) > 0 else 0.5
    avg_win = wins.mean() if not wins.empty else 1.0
    avg_loss = losses.mean() if not losses.empty else 1.0
    win_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 1.0
    
    kelly_f = win_rate - ((1.0 - win_rate) / win_loss_ratio)
    kelly_f = max(0.01, min(0.50, kelly_f)) # clamp Kelly fraction (half Kelly limit)
    
    equity_kelly = [initial_capital]
    for _, row in df.iterrows():
        current_eq = equity_kelly[-1]
        size = current_eq * kelly_f
        pnl = size * (row["return_pct"] / 100.0)
        equity_kelly.append(current_eq + pnl)
        
    # 4. VOLATILITY/ATR SIZING
    # Inverse volatility proxy
    equity_vol = [initial_capital]
    for _, row in df.iterrows():
        current_eq = equity_vol[-1]
        # Volatility multiplier (simulated inverse volatility)
        vol_multiplier = 1.0
        size = current_eq * 0.10 * vol_multiplier
        pnl = size * (row["return_pct"] / 100.0)
        equity_vol.append(current_eq + pnl)
        
    # Build growth curves list
    dates_list = ["Start"] + df["entry_date"].dt.strftime("%Y-%m-%d").tolist()
    
    curves = []
    for i in range(len(dates_list)):
        curves.append({
            "date": dates_list[i],
            "Fixed Capital": float(equity_fixed[i]),
            "Fixed Fractional": float(equity_frac[i]),
            "Kelly Fraction": float(equity_kelly[i]),
            "Volatility Sizing": float(equity_vol[i]),
        })
        
    # Summarize stats
    def get_stats(eq_series):
        final = eq_series[-1]
        cagr = (final / initial_capital) - 1.0
        # Drawdown
        cum_max = np.maximum.accumulate(eq_series)
        dd = (eq_series - cum_max) / cum_max * 100
        return {
            "cagr": round(cagr * 100, 2),
            "max_dd": round(float(np.min(dd)), 2),
            "final_value": round(float(final), 2)
        }
        
    summary = [
        {"model": "Fixed Capital", **get_stats(np.array(equity_fixed))},
        {"model": "Fixed Fractional", **get_stats(np.array(equity_frac))},
        {"model": "Kelly Fraction", **get_stats(np.array(equity_kelly))},
        {"model": "Volatility Sizing", **get_stats(np.array(equity_vol))},
    ]
    
    return {
        "summary": summary,
        "curves": curves
    }
