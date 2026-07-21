"""
Test dynamic score calculation and change computation between 2026-07-15 and 2026-07-17.
"""
from app.services.historical_data_service import historical_data_service
from app.services.snapshot_pipeline import compute_stock_indicators_stage
import pandas as pd

symbols = ['RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'BHARTIARTL.NS', 'ITC.NS', 'SBIN.NS', 'LTIM.NS', 'LT.NS']

def calc_tech_score(ind):
    if not ind:
        return 0.0
    rsi = float(ind.get("rsi") or 50.0)
    rsi_score = (rsi - 50.0) * 2.0
    
    macd = float(ind.get("macd") or 0.0)
    macd_sig = float(ind.get("macd_signal") or 0.0)
    macd_score = 50.0 if macd > macd_sig else -50.0
    
    close = float(ind.get("close") or 0.0)
    ema20 = float(ind.get("ema20") or close)
    ema50 = float(ind.get("ema50") or close)
    ema200 = float(ind.get("ema200") or close)
    
    ma_score = 0.0
    if close > ema20: ma_score += 25.0
    else: ma_score -= 25.0
    if close > ema50: ma_score += 25.0
    else: ma_score -= 25.0
    if close > ema200: ma_score += 25.0
    else: ma_score -= 25.0
    if ema20 > ema50: ma_score += 25.0
    else: ma_score -= 25.0
    
    tech = ma_score * 0.40 + macd_score * 0.30 + rsi_score * 0.30
    return round(max(min(tech, 100.0), -100.0), 2)

print("=== Dynamic Scores Comparison ===")
for sym in symbols:
    dummy_quote = {"Open": 100, "High": 105, "Low": 95, "CurrentPrice": 100, "Volume": 1000000}
    
    ind_15 = compute_stock_indicators_stage(sym, "2026-07-15", dummy_quote)
    ind_17 = compute_stock_indicators_stage(sym, "2026-07-17", dummy_quote)
    
    t15 = calc_tech_score(ind_15)
    t17 = calc_tech_score(ind_17)
    
    comp15 = round(t15 * 0.40 + 20 * 0.35 + 10 * 0.15 + 70 * 0.10, 2)
    comp17 = round(t17 * 0.40 + 20 * 0.35 + 10 * 0.15 + 70 * 0.10, 2)
    
    print(f"[{sym:12}] 2026-07-15 Tech={t15:6.2f} Comp={comp15:6.2f} | 2026-07-17 Tech={t17:6.2f} Comp={comp17:6.2f} | Diff={comp17-comp15:+6.2f}")
