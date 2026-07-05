"""Health check router."""

from fastapi import APIRouter
from app.config import settings
from app.data.loader import data_loader
from app.models.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """System health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        stocks_loaded=data_loader.stocks_loaded,
    )
