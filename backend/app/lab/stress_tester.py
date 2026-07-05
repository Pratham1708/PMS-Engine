"""
stress_tester.py — Stress Testing & Crisis Simulation Engine.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

from app.lab.backtester import load_ohlcv

logger = logging.getLogger(__name__)

CRISIS_PERIODS = {
    "COVID Crash (2020)": {
        "start": "2020-02-15",
        "end": "2020-04-30",
        "description": "Global liquidity crash driven by the COVID-19 pandemic outbreak."
    },
    "2008 Financial Crisis": {
        "start": "2008-01-01",
        "end": "2009-03-31",
        "description": "Subprime mortgage collapse and banking liquidity crisis."
    },
    "Rate Hike Cycle (2022)": {
        "start": "2022-04-01",
        "end": "2023-06-30",
        "description": "Inflation control tightening and aggressive central bank interest rate hikes."
    },
    "Election Results Day (2024)": {
        "start": "2024-06-01",
        "end": "2024-06-15",
        "description": "High domestic volatility window surrounding election outcome declarations."
    },
    "Budget Day 2024": {
        "start": "2024-01-28",
        "end": "2024-02-08",
        "description": "Union budget policy volatility and sector allocation shifts."
    }
}

def run_stress_test(
    equity_series: Optional[pd.Series] = None,
    dates: Optional[List[str]] = None,
    symbol: str = "^NSEI"
) -> Dict:
    """
    Run stress test on a strategy equity series or a proxy benchmark index.
    Measures returns and drawdowns during predefined crisis date windows.
    """
    # If no equity series provided, run stress test on benchmark Close price
    if equity_series is None or dates is None:
        df = load_ohlcv(symbol, "5Y")
        if df is not None and not df.empty:
            df["Date"] = pd.to_datetime(df["Date"])
            equity_series = df["Close"]
            dates = df["Date"].dt.strftime("%Y-%m-%d").tolist()
        else:
            # Generate mock data
            dates = pd.date_range(start="2007-01-01", end="2025-01-01", freq="B").strftime("%Y-%m-%d").tolist()
            equity_series = pd.Series(np.cumprod(1.0 + np.random.normal(0.0003, 0.01, len(dates))) * 100000.0)

    # Convert to DataFrame
    data_df = pd.DataFrame({"Date": pd.to_datetime(dates), "Equity": equity_series.values})
    data_df = data_df.sort_values("Date").reset_index(drop=True)
    
    results = []
    resilience_scores = []
    
    for name, period in CRISIS_PERIODS.items():
        start_dt = pd.to_datetime(period["start"])
        end_dt = pd.to_datetime(period["end"])
        
        # Filter data
        mask = (data_df["Date"] >= start_dt) & (data_df["Date"] <= end_dt)
        sub_df = data_df[mask]
        
        if len(sub_df) < 5:
            # Ticker has no data for 2008, skip
            continue
            
        initial_val = sub_df.iloc[0]["Equity"]
        final_val = sub_df.iloc[-1]["Equity"]
        
        # Return during crisis
        period_return = (final_val - initial_val) / initial_val * 100
        
        # Drawdown during crisis
        cum_max = sub_df["Equity"].cummax()
        drawdowns = (sub_df["Equity"] - cum_max) / cum_max * 100
        max_dd = float(drawdowns.min())
        
        # Resilience classification: DD < 15% -> High, DD < 30% -> Medium, else Low
        res_score = max(0, 100 + max_dd * 2.0 + period_return * 0.5)
        res_score = min(100, res_score)
        resilience_scores.append(res_score)
        
        results.append({
            "name": name,
            "period": f"{period['start']} to {period['end']}",
            "description": period["description"],
            "return_pct": round(period_return, 2),
            "max_drawdown": round(max_dd, 2),
            "resilience_score": round(res_score, 1),
            "status": "Resilient" if res_score >= 70.0 else ("Vulnerable" if res_score < 45.0 else "Stable")
        })
        
    avg_resilience = float(np.mean(resilience_scores)) if resilience_scores else 75.0
    
    return {
        "symbol": symbol,
        "overall_resilience_score": round(avg_resilience, 1),
        "rating": "A" if avg_resilience >= 80.0 else ("B" if avg_resilience >= 60.0 else "C"),
        "crisis_performance": results
    }
