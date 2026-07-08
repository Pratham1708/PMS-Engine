"""
user_stocks.py — Endpoints for personalized research workspace, company details, and manual analysis.
"""

import logging
from typing import List
from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    UserStockAdd,
    UserStockResponse,
    RecentAnalysisResponse,
    AnalysisHistoryEntry,
    CompanyProfile,
    WorkspaceResponse,
    StockDetail,
    AnalyzeResponse
)
from app.services import user_stock_service, analysis_history_service, company_service, research_workspace_service, stock_service
from app.services.realtime_feed import fetch_quote_single
from app.data.loader import data_loader

logger = logging.getLogger(__name__)

router = APIRouter(tags=["user-research"])


@router.get("/mystocks", response_model=List[UserStockResponse])
async def list_my_stocks():
    """Return all user interest stocks with their latest cached analysis results."""
    # This uses research_workspace_service to fetch enriched list with prices & ratings
    data = research_workspace_service.get_workspace_data()
    return data["my_stocks"]


@router.post("/mystocks", response_model=List[UserStockResponse])
async def add_to_my_stocks(payload: UserStockAdd):
    """Add a stock to My Stocks and return the updated list."""
    symbol = payload.symbol.strip()
    success = user_stock_service.add_to_my_stocks(symbol)
    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Symbol '{symbol}' is invalid or not in the security master"
        )
    return await list_my_stocks()


@router.delete("/mystocks/{symbol}", response_model=List[UserStockResponse])
async def remove_from_my_stocks(symbol: str):
    """Remove a stock from My Stocks and return the updated list."""
    success = user_stock_service.remove_from_my_stocks(symbol)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Symbol '{symbol}' not found in user stocks"
        )
    return await list_my_stocks()


@router.get("/recent-analysis", response_model=List[RecentAnalysisResponse])
async def list_recent_analysis():
    """Return recently analyzed stocks with their last ratings."""
    data = research_workspace_service.get_workspace_data()
    return data["recent_analysis"]


@router.get("/analysis-history/{symbol}", response_model=List[AnalysisHistoryEntry])
async def get_analysis_history(symbol: str):
    """Return the lightweight historical analysis logs for a symbol."""
    if not user_stock_service.is_valid_symbol(symbol):
        raise HTTPException(status_code=404, detail=f"Stock '{symbol}' not in universe")
    return analysis_history_service.get_analysis_history(symbol)


@router.get("/company/{symbol}", response_model=CompanyProfile)
async def get_company_profile_info(symbol: str):
    """Return detailed company profile info."""
    if not user_stock_service.is_valid_symbol(symbol):
        raise HTTPException(status_code=404, detail=f"Stock '{symbol}' not in universe")
    return company_service.get_company_profile(symbol)


@router.get("/research-workspace", response_model=WorkspaceResponse)
async def get_research_workspace():
    """Return aggregated data for the user's research workspace home page."""
    return research_workspace_service.get_workspace_data()


@router.post("/analyze/{symbol}", response_model=AnalyzeResponse)
async def analyze_stock(symbol: str):
    """
    Execute user-driven PMS analysis:
    1. Download live quote from yfinance & update the backend in-memory cache.
    2. Retrieve rating and scores from baseline calculations.
    3. Save the run in SQLite analysis_history with a generated UUID.
    4. Return UUID-wrapped analysis detail.
    """
    if not user_stock_service.is_valid_symbol(symbol):
        raise HTTPException(status_code=404, detail=f"Stock '{symbol}' not in universe")
        
    canonical_symbol = user_stock_service.get_canonical_symbol(symbol)
    
    # Block analysis for non-Nifty-50 stocks (not in data_loader)
    if not user_stock_service.is_in_data_loader(canonical_symbol):
        raise HTTPException(
            status_code=400,
            detail=f"Stock '{canonical_symbol}' is recognized but not yet analyzed by PMS Engine. Full analysis is available only for the pre-computed Nifty 50 universe."
        )
    
    # 1. Fetch live quote and recalculate scores based on the latest OHLCV data
    try:
        quote = fetch_quote_single(canonical_symbol)
        if quote:
            df = data_loader._df
            if df is not None and not df.empty:
                idx = df[df["Symbol"].str.upper() == canonical_symbol.upper()].index
                if not idx.empty:
                    # Update live price details in DataFrame
                    for col in ["CurrentPrice", "Open", "High", "Low", "Volume",
                                "PreviousClose", "DailyChangePct", "DailyChangeAmount"]:
                        if col in quote:
                            df.at[idx[0], col] = quote[col]
                    
                    # Update live market timestamp
                    import pytz
                    from datetime import datetime
                    ist = pytz.timezone("Asia/Kolkata")
                    data_loader.last_market_update = datetime.now(ist).strftime("%d-%b-%Y %I:%M %p IST")
                    
                    # --- DYNAMIC SCORE RECALCULATION USING LAST TRADING DAY DATA ---
                    from app.services.historical_data_service import historical_data_service
                    from app.lab.indicators import compute_rsi, compute_macd, compute_ema, compute_bollinger
                    import numpy as np
                    import pandas as pd
                    
                    # Fetch 1Y history
                    df_hist = historical_data_service.get_stock_history(canonical_symbol, "1Y")
                    if df_hist is not None and not df_hist.empty:
                        # Append/update the latest live price as the last row
                        today_str = datetime.now(ist).strftime("%Y-%m-%d")
                        if df_hist.iloc[-1]["Date"] == today_str:
                            df_hist.at[df_hist.index[-1], "Open"] = quote.get("Open") or df_hist.iloc[-1]["Open"]
                            df_hist.at[df_hist.index[-1], "High"] = quote.get("High") or df_hist.iloc[-1]["High"]
                            df_hist.at[df_hist.index[-1], "Low"] = quote.get("Low") or df_hist.iloc[-1]["Low"]
                            df_hist.at[df_hist.index[-1], "Close"] = quote.get("CurrentPrice") or df_hist.iloc[-1]["Close"]
                            df_hist.at[df_hist.index[-1], "Volume"] = quote.get("Volume") or df_hist.iloc[-1]["Volume"]
                        else:
                            new_row = {
                                "Date": today_str,
                                "Open": quote.get("Open") or quote.get("CurrentPrice"),
                                "High": quote.get("High") or quote.get("CurrentPrice"),
                                "Low": quote.get("Low") or quote.get("CurrentPrice"),
                                "Close": quote.get("CurrentPrice"),
                                "Volume": quote.get("Volume") or 0,
                                "Dividends": 0.0,
                                "Stock Splits": 0.0
                            }
                            df_hist = pd.concat([df_hist, pd.DataFrame([new_row])], ignore_index=True)
                        
                        # Get baseline scores
                        baseline_row = df.iloc[idx[0]]
                        base_tech = float(baseline_row.get("TechnicalScore", 0.0) or 0.0)
                        base_ml = float(baseline_row.get("MLScore", 0.0) or 0.0)
                        base_gru = float(baseline_row.get("GRUScore", 0.0) or 0.0)
                        base_reliability = float(baseline_row.get("ReliabilityScore", 70.0) or 70.0)
                        
                        # 1. Technical indicators calculations
                        df_rsi = compute_rsi(df_hist, period=14)
                        rsi_val = float(df_rsi.iloc[-1]["RSI"]) if not df_rsi.empty and "RSI" in df_rsi.columns else 50.0
                        
                        df_ema = compute_ema(df_hist, fast_period=9, slow_period=21)
                        ema_fast = float(df_ema.iloc[-1]["EMA_Fast"]) if not df_ema.empty and "EMA_Fast" in df_ema.columns else 1.0
                        ema_slow = float(df_ema.iloc[-1]["EMA_Slow"]) if not df_ema.empty and "EMA_Slow" in df_ema.columns else 1.0
                        
                        df_macd = compute_macd(df_hist, fast=12, slow=26, signal=9)
                        macd_val = float(df_macd.iloc[-1]["MACD"]) if not df_macd.empty and "MACD" in df_macd.columns else 0.0
                        macd_sig = float(df_macd.iloc[-1]["MACD_Signal"]) if not df_macd.empty and "MACD_Signal" in df_macd.columns else 0.0
                        
                        df_bb = compute_bollinger(df_hist, period=20, num_std=2.0)
                        bb_mid = float(df_bb.iloc[-1]["BB_Mid"]) if not df_bb.empty and "BB_Mid" in df_bb.columns else 1.0
                        bb_upper = float(df_bb.iloc[-1]["BB_Upper"]) if not df_bb.empty and "BB_Upper" in df_bb.columns else 1.0
                        bb_lower = float(df_bb.iloc[-1]["BB_Lower"]) if not df_bb.empty and "BB_Lower" in df_bb.columns else 1.0
                        
                        # Calculate Technical Score components
                        ema_signal = 1.0 if ema_fast > ema_slow else -1.0
                        macd_signal = 1.0 if macd_val > macd_sig else -1.0
                        rsi_signal = (rsi_val - 50.0) / 20.0
                        bb_signal = (quote.get("CurrentPrice", bb_mid) - bb_mid) / (bb_upper - bb_lower) * 4.0 if bb_upper > bb_lower else 0.0
                        
                        calculated_tech = (ema_signal * 30.0) + (macd_signal * 20.0) + (rsi_signal * 15.0) + (bb_signal * 15.0)
                        new_tech = round(max(min(calculated_tech * 0.7 + base_tech * 0.3, 100.0), -100.0), 2)
                        
                        # 2. ML Score calculations (using 5-day return and volume MA ratio)
                        close_series = df_hist["Close"]
                        ret_5 = (close_series.iloc[-1] - close_series.iloc[-6]) / close_series.iloc[-6] * 100.0 if len(close_series) >= 6 else 0.0
                        vol_series = df_hist["Volume"]
                        vol_ma_10 = vol_series.iloc[-10:].mean() if len(vol_series) >= 10 else 1.0
                        vol_ratio = (vol_series.iloc[-1] / vol_ma_10) if vol_ma_10 > 0 else 1.0
                        
                        calculated_ml = (ret_5 * 2.5) + (vol_ratio - 1.0) * 5.0
                        new_ml = round(max(min(calculated_ml * 0.7 + base_ml * 0.3, 50.0), -50.0), 2)
                        
                        # 3. GRU Score calculations (sequential returns momentum)
                        returns_15 = close_series.pct_change().iloc[-15:] * 100.0
                        decay_weights = np.array([0.9 ** (15 - i) for i in range(len(returns_15))])
                        weighted_ret = np.sum(returns_15.values * decay_weights) / np.sum(decay_weights) if len(returns_15) > 0 else 0.0
                        calculated_gru = weighted_ret * 15.0
                        new_gru = round(max(min(calculated_gru * 0.7 + base_gru * 0.3, 50.0), -50.0), 2)
                        
                        new_reliability = base_reliability
                        
                        # 4. Composite Score calculations
                        new_composite = round(new_tech * 0.40 + new_ml * 0.35 + new_gru * 0.15 + new_reliability * 0.10, 2)
                        
                        # 5. Confidence calculation based on sub-scores direction agreement
                        agree_count = max(
                            sum(1 for x in [new_tech, new_ml, new_gru] if x > 0),
                            sum(1 for x in [new_tech, new_ml, new_gru] if x < 0)
                        )
                        consensus_boost = 15.0 if agree_count == 3 else (5.0 if agree_count == 2 else -10.0)
                        new_confidence = round(max(min(baseline_row.get("Confidence", 75.0) + consensus_boost, 100.0), 40.0), 2)
                        
                        # 6. Final Rating threshold check
                        if new_composite >= 35.0:
                            new_rating = "STRONG BUY"
                        elif new_composite >= 15.0:
                            new_rating = "BUY"
                        elif new_composite >= -15.0:
                            new_rating = "HOLD"
                        elif new_composite >= -35.0:
                            new_rating = "SELL"
                        else:
                            new_rating = "STRONG SELL"
                        
                        # Update in-memory data_loader DataFrame
                        df.at[idx[0], "TechnicalScore"] = new_tech
                        df.at[idx[0], "MLScore"] = new_ml
                        df.at[idx[0], "GRUScore"] = new_gru
                        df.at[idx[0], "Confidence"] = new_confidence
                        df.at[idx[0], "CompositeScoreV2"] = new_composite
                        df.at[idx[0], "FinalRating"] = new_rating
                        df.at[idx[0], "PortfolioEligible"] = new_rating in ("STRONG BUY", "BUY")
                        df.at[idx[0], "ConvictionLevel"] = "High Conviction" if new_confidence >= 80 else ("Medium Conviction" if new_confidence >= 60 else "Low Conviction")
                        
                        # Update active SQLite snapshot database tables
                        from app.services import db as db_service
                        conn = db_service.get_db_connection()
                        try:
                            latest_snap = db_service.get_latest_snapshot()
                            if latest_snap:
                                snapshot_id = latest_snap["snapshot_id"]
                                
                                # Update snapshot_stock table
                                portfolio_eligible = 1 if new_rating in ("STRONG BUY", "BUY") else 0
                                conviction_level = "High Conviction" if new_confidence >= 80 else ("Medium Conviction" if new_confidence >= 60 else "Low Conviction")
                                
                                update_stock_query = """
                                UPDATE snapshot_stock
                                SET open = ?, high = ?, low = ?, close = ?, volume = ?,
                                    prev_close = ?, daily_chg_pct = ?, daily_chg_amt = ?,
                                    technical_score = ?, ml_score = ?, gru_score = ?,
                                    risk_score = ?, momentum_score = ?, trend_score = ?,
                                    confidence = ?, composite_score = ?, reliability_score = ?,
                                    final_rating = ?, portfolio_eligible = ?, conviction_level = ?
                                WHERE snapshot_id = ? AND symbol = ?
                                """
                                conn.execute(
                                    update_stock_query,
                                    (
                                        quote.get("Open"), quote.get("High"), quote.get("Low"), quote.get("CurrentPrice"), quote.get("Volume"),
                                        quote.get("PreviousClose"), quote.get("DailyChangePct"), quote.get("DailyChangeAmount"),
                                        new_tech, new_ml, new_gru,
                                        100.0 - new_confidence, round(new_tech * 0.8 + new_ml * 0.2, 2), round(new_gru * 0.6 + new_tech * 0.4, 2),
                                        new_confidence, new_composite, new_reliability,
                                        new_rating, portfolio_eligible, conviction_level,
                                        snapshot_id, canonical_symbol
                                    )
                                )
                                
                                # Update snapshot_score table
                                update_score_query = """
                                UPDATE snapshot_score
                                SET trend_component = ?, momentum_component = ?, lgbm_signal = ?
                                WHERE snapshot_id = ? AND symbol = ?
                                """
                                conn.execute(
                                    update_score_query,
                                    (
                                        round((new_gru * 0.6 + new_tech * 0.4) * 0.5, 2),
                                        round((new_tech * 0.8 + new_ml * 0.2) * 0.5, 2),
                                        new_ml,
                                        snapshot_id, canonical_symbol
                                    )
                                )
                                conn.commit()
                        except Exception as dberr:
                            logger.error(f"Failed to update database snapshot with recalculated scores for {canonical_symbol}: {dberr}")
                        finally:
                            conn.close()
    except Exception as e:
        logger.warning(f"Live quote refresh during analysis failed for {canonical_symbol}: {e}")

    # 2. Get stock details
    stock = stock_service.get_stock(canonical_symbol)
    if stock is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve stock scores")
        
    # 3. Log the analysis run in SQLite
    analysis_id = analysis_history_service.record_analysis(
        symbol=stock.Symbol,
        rating=stock.FinalRating,
        confidence=stock.Confidence,
        composite_score=stock.CompositeScoreV2
    )
    
    # 4. Inject current timestamp as the analysis run time
    import pytz
    from datetime import datetime
    ist = pytz.timezone("Asia/Kolkata")
    now_str = datetime.now(ist).strftime("%d-%b-%Y %I:%M %p IST")
    
    stock.LastScannerRun = now_str
    
    return AnalyzeResponse(
        analysis_id=analysis_id,
        symbol=canonical_symbol,
        status="completed",
        analysis_timestamp=now_str,
        result=stock
    )
