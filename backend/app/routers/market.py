"""
Market Router — Endpoints for stock quotes, price history, and market overview.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from app.services.market_data_service import market_data_service
from app.data.loader import data_loader

router = APIRouter(tags=["market"])


@router.get("/market/quote/{symbol}")
async def get_market_quote(symbol: str):
    """Return live quote details for a single symbol from yfinance."""
    quote = market_data_service.get_live_quote(symbol)
    if not quote:
        # Check if symbol exists in data loader, if it does but fetch failed, return from memory
        df = data_loader.get_df()
        clean_sym = symbol.upper().replace(".NS", "").strip()
        match = df[df["Symbol"].str.upper().str.replace(".NS", "") == clean_sym]
        if not match.empty:
            row = match.iloc[0]
            return {
                "symbol": row["Symbol"],
                "current_price": row.get("CurrentPrice"),
                "open": row.get("Open"),
                "high": row.get("High"),
                "low": row.get("Low"),
                "volume": int(row.get("Volume")) if row.get("Volume") is not None else None,
                "previous_close": row.get("PreviousClose"),
                "daily_change_pct": row.get("DailyChangePct"),
                "daily_change_amount": row.get("DailyChangeAmount"),
                "last_updated": data_loader.last_market_update or "N/A"
            }
        raise HTTPException(
            status_code=404, detail=f"Stock quote not found for symbol: {symbol}"
        )
    
    # Format field names to camelCase or standard keys matching requirement
    return {
        "symbol": quote["Symbol"],
        "current_price": quote["CurrentPrice"],
        "open": quote["Open"],
        "high": quote["High"],
        "low": quote["Low"],
        "volume": quote["Volume"],
        "previous_close": quote["PreviousClose"],
        "daily_change_pct": quote["DailyChangePct"],
        "daily_change_amount": quote["DailyChangeAmount"],
        "last_updated": datetime_now_string()
    }


@router.get("/market/history/{symbol}")
async def get_market_history(
    symbol: str,
    period: str = Query("1Y", regex="^(1M|3M|6M|1Y|3Y|5Y)$")
):
    """Return historical stock prices for a symbol. Cached locally for 24h."""
    # Check if stock symbol exists in scanner first (validate)
    df = data_loader.get_df()
    clean_sym = symbol.upper().replace(".NS", "").strip()
    match = df[df["Symbol"].str.upper().str.replace(".NS", "") == clean_sym]
    if match.empty:
        raise HTTPException(
            status_code=404, detail=f"Symbol {symbol} is not covered in Nifty 50 universe"
        )
    
    # Fetch from historical data service
    # We standardise the symbol casing
    standardized_symbol = match.iloc[0]["Symbol"]
    history_df = market_data_service.get_historical_data(standardized_symbol, period)
    if history_df is None or history_df.empty:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve history series for {symbol}"
        )
    
    # Return as list of dictionaries
    return history_df.to_dict(orient="records")


@router.get("/market/overview")
async def get_market_overview():
    """Return aggregated market overview statistics for Nifty 50 universe."""
    df = data_loader.get_df()
    if df.empty:
        raise HTTPException(status_code=503, detail="Scanner cache is empty")
    
    # Calculate averages from live quote columns in cache
    import pandas as pd
    import numpy as np

    avg_change_pct = 0.0
    if "DailyChangePct" in df.columns:
        mean_val = df["DailyChangePct"].mean()
        if pd.notna(mean_val) and not np.isnan(mean_val):
            avg_change_pct = float(mean_val)

    total_volume = 0
    if "Volume" in df.columns:
        sum_val = df["Volume"].sum()
        if pd.notna(sum_val) and not np.isnan(sum_val):
            total_volume = int(sum_val)
    
    # Top gainers (sorted by DailyChangePct desc)
    gainers = []
    if "DailyChangePct" in df.columns:
        gainers_df = df.dropna(subset=["DailyChangePct", "CurrentPrice"])
        if not gainers_df.empty:
            gainers_df = gainers_df.sort_values(by="DailyChangePct", ascending=False).head(5)
            for _, row in gainers_df.iterrows():
                gainers.append({
                    "symbol": row["Symbol"],
                    "current_price": float(row["CurrentPrice"]),
                    "daily_change_pct": float(row["DailyChangePct"]),
                })
            
    # Top losers (sorted by DailyChangePct asc)
    losers = []
    if "DailyChangePct" in df.columns:
        losers_df = df.dropna(subset=["DailyChangePct", "CurrentPrice"])
        if not losers_df.empty:
            losers_df = losers_df.sort_values(by="DailyChangePct", ascending=True).head(5)
            for _, row in losers_df.iterrows():
                losers.append({
                    "symbol": row["Symbol"],
                    "current_price": float(row["CurrentPrice"]),
                    "daily_change_pct": float(row["DailyChangePct"]),
                })
            
    return {
        "average_daily_change_pct": round(avg_change_pct, 2),
        "total_volume": total_volume,
        "top_gainers": gainers,
        "top_losers": losers,
        "last_market_update": data_loader.last_market_update or "N/A",
        "last_scanner_run": data_loader.last_scanner_run or "N/A",
    }


def datetime_now_string() -> str:
    """Helper to get ISO formatted IST timestamp string."""
    import pytz
    from datetime import datetime
    ist = pytz.timezone("Asia/Kolkata")
    return datetime.now(ist).isoformat()
