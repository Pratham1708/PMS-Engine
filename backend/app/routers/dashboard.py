"""Dashboard, ratings distribution, scanner summary, and refresh endpoints."""

from fastapi import APIRouter

from app.data.loader import data_loader
from app.models.schemas import (
    DashboardData,
    RatingDistribution,
    ScannerSummary,
    RefreshResponse,
)
from app.services import stock_service

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardData)
async def dashboard():
    """Return aggregated dashboard metrics."""
    return stock_service.get_dashboard()


@router.get("/ratings-distribution", response_model=RatingDistribution)
async def ratings_distribution():
    """Return count of stocks per rating level."""
    return stock_service.get_ratings_distribution()


@router.get("/scanner-summary", response_model=ScannerSummary)
async def scanner_summary():
    """Return universe-wide summary statistics."""
    return stock_service.get_scanner_summary()


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_scanner():
    """Reload the scanner CSV from disk without restarting the server."""
    stocks_loaded = data_loader.refresh()
    return RefreshResponse(
        message="Scanner data refreshed successfully",
        stocks_loaded=stocks_loaded,
    )
