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
    
    # 1. Fetch live quote
    try:
        quote = fetch_quote_single(canonical_symbol)
        if quote:
            df = data_loader._df
            if df is not None and not df.empty:
                idx = df[df["Symbol"].str.upper() == canonical_symbol.upper()].index
                if not idx.empty:
                    for col in ["CurrentPrice", "Open", "High", "Low", "Volume",
                                "PreviousClose", "DailyChangePct", "DailyChangeAmount"]:
                        if col in quote:
                            df.at[idx[0], col] = quote[col]
                    
                    # Update live market timestamp
                    import pytz
                    from datetime import datetime
                    ist = pytz.timezone("Asia/Kolkata")
                    data_loader.last_market_update = datetime.now(ist).strftime("%d-%b-%Y %I:%M %p IST")
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
