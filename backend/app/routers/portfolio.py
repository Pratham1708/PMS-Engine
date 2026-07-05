"""Portfolio construction endpoint."""

from fastapi import APIRouter, Query

from app.models.schemas import PortfolioResponse
from app.services import portfolio_service

router = APIRouter(tags=["portfolio"])


@router.get("/portfolio", response_model=PortfolioResponse)
async def portfolio(
    capital: float = Query(..., gt=0, description="Total investment capital in INR"),
):
    """
    Build a conviction-weighted portfolio from STRONG BUY and BUY stocks.
    Capital is allocated proportionally to CompositeScoreV2.
    """
    return portfolio_service.build_portfolio(capital=capital)
