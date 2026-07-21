"""
Test running indicator calculation on 2026-07-15 vs 2026-07-17 with target_date filtering.
"""
from app.services.historical_data_service import historical_data_service
from app.services.snapshot_pipeline import compute_stock_indicators_stage
import pandas as pd
import numpy as np

# Test symbols
symbols = ['RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS']

print("=== Comparing calculated indicators for 2026-07-15 vs 2026-07-17 ===")
for sym in symbols:
    # Dummy quote (price will come from history)
    dummy_quote = {"Open": 100, "High": 105, "Low": 95, "CurrentPrice": 100, "Volume": 1000000}
    
    ind_15 = compute_stock_indicators_stage(sym, "2026-07-15", dummy_quote)
    ind_17 = compute_stock_indicators_stage(sym, "2026-07-17", dummy_quote)
    
    if ind_15 and ind_17:
        print(f"\n[{sym}]")
        print(f"  2026-07-15: RSI={ind_15.get('rsi')}, EMA20={ind_15.get('ema20')}, MACD={ind_15.get('macd')}")
        print(f"  2026-07-17: RSI={ind_17.get('rsi')}, EMA20={ind_17.get('ema20')}, MACD={ind_17.get('macd')}")
