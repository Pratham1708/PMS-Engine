"""Stock data endpoints."""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import StockDetail, StockSummary
from app.services import stock_service
from app.services.db import search_security_master, get_security_master_entry
from app.services.market_data_service import market_data_service
from app.services.user_stock_service import get_canonical_symbol

logger = logging.getLogger(__name__)
router = APIRouter(tags=["stocks"])


@router.get("/stocks", response_model=List[StockDetail])
async def list_stocks(
    sort_by: str = Query("CompositeScoreV2", description="Column to sort by"),
    order: str = Query("desc", description="Sort order: asc or desc"),
    rating: Optional[str] = Query(None, description="Filter by FinalRating"),
    search: Optional[str] = Query(None, description="Search symbol substring"),
):
    """Return all stocks with optional sorting, filtering, and search."""
    # Get baseline Nifty 50 stocks from data_loader
    stocks = stock_service.get_all_stocks(
        sort_by=sort_by, order=order, rating=rating, search=search
    )
    
    # If search is specified, merge with matching security master stocks
    if search:
        sm_results = search_security_master(search)
        existing_symbols = {s.Symbol.upper() for s in stocks}
        
        for entry in sm_results:
            sym_upper = entry["symbol"].upper()
            if sym_upper not in existing_symbols:
                # If a rating filter is active, only include if it filters for "Not Analyzed"
                if rating and rating != "Not Analyzed":
                    continue
                stocks.append(
                    StockDetail(
                        Symbol=entry["symbol"],
                        FinalRating="Not Analyzed",
                        Confidence=0.0,
                        CompositeScoreV2=0.0,
                        TechnicalScore=0.0,
                        MLScore=0.0,
                        GRUScore=0.0,
                        ReliabilityScore=0.0,
                        Sector=entry.get("sector") or "—"
                    )
                )
        
        # Sort merged list if sorting by Symbol
        if sort_by == "Symbol":
            reverse = order.lower() == "desc"
            stocks.sort(key=lambda x: x.Symbol.upper(), reverse=reverse)
            
    return stocks


@router.get("/stock/{symbol}", response_model=StockDetail)
async def get_stock(symbol: str):
    """Return detailed data for a single stock, fallback to security master if not in Nifty 50."""
    # 1. Try to fetch analyzed Nifty 50 stock
    stock = stock_service.get_stock(symbol)
    if stock is not None:
        return stock
        
    # 2. Fallback to security master
    canonical = get_canonical_symbol(symbol)
    entry = get_security_master_entry(canonical)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"Stock '{symbol}' not found")
        
    # Fetch live price for non-analyzed stock
    current_price = None
    open_val = None
    high_val = None
    low_val = None
    volume = None
    prev_close = None
    daily_change_pct = None
    daily_change_amount = None
    last_update = None
    
    try:
        quote = market_data_service.get_live_quote(canonical)
        if quote:
            current_price = quote.get("CurrentPrice")
            open_val = quote.get("Open")
            high_val = quote.get("High")
            low_val = quote.get("Low")
            volume = quote.get("Volume")
            prev_close = quote.get("PreviousClose")
            daily_change_pct = quote.get("DailyChangePct")
            daily_change_amount = quote.get("DailyChangeAmount")
            
            import pytz
            from datetime import datetime
            ist = pytz.timezone("Asia/Kolkata")
            last_update = datetime.now(ist).strftime("%d-%b-%Y %I:%M %p IST")
    except Exception as e:
        logger.warning(f"Failed to fetch live quote for {canonical} during get_stock: {e}")
        
    return StockDetail(
        Symbol=entry["symbol"],
        FinalRating="Not Analyzed",
        Confidence=0.0,
        CompositeScoreV2=0.0,
        TechnicalScore=0.0,
        MLScore=0.0,
        GRUScore=0.0,
        ReliabilityScore=0.0,
        Sector=entry.get("sector") or "—",
        CurrentPrice=current_price,
        Open=open_val,
        High=high_val,
        Low=low_val,
        Volume=volume,
        PreviousClose=prev_close,
        DailyChangePct=daily_change_pct,
        DailyChangeAmount=daily_change_amount,
        LastMarketUpdate=last_update
    )


@router.get("/top-buys", response_model=List[StockSummary])
async def top_buys(
    limit: int = Query(10, ge=1, le=50, description="Number of results"),
):
    """Return top STRONG BUY and BUY stocks by CompositeScoreV2."""
    return stock_service.get_top_buys(limit=limit)


@router.get("/top-sells", response_model=List[StockSummary])
async def top_sells(
    limit: int = Query(10, ge=1, le=50, description="Number of results"),
):
    """Return top SELL and STRONG SELL stocks by CompositeScoreV2 (ascending)."""
    return stock_service.get_top_sells(limit=limit)
