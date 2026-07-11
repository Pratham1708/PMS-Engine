"""
PMS Engine — FastAPI Application Entry Point.
Production-ready API server for institutional stock analytics.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.services.json_response import SafeJSONResponse
from app.routers import health, stocks, dashboard, portfolio, market, reports, user_stocks, explain
from app.routers import snapshot as snapshot_router
from app.routers import (
    lab_indicators,
    lab_engine,
    lab_models,
    lab_features,
    lab_composite,
    lab_validation,
    lab_portfolio,
    lab_market,
    lab_experiments,
    lab_reports,
    lab_extensions,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# Create application
app = FastAPI(
    title="PMS Engine API",
    description="Institutional AI-Powered Portfolio Management & Stock Rating System",
    version=settings.app_version,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    default_response_class=SafeJSONResponse,
)

# CORS — allow all origins in development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers under /api prefix
app.include_router(health.router, prefix="/api")
app.include_router(stocks.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(portfolio.router, prefix="/api")
app.include_router(market.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(user_stocks.router, prefix="/api")
app.include_router(snapshot_router.router, prefix="/api")  # Phase 13 snapshot publishing
app.include_router(explain.router, prefix="/api")

# Register Quant Research Laboratory routers (prefixes are built-in)
app.include_router(lab_indicators.router)
app.include_router(lab_engine.router)
app.include_router(lab_models.router)
app.include_router(lab_features.router)
app.include_router(lab_composite.router)
app.include_router(lab_validation.router)
app.include_router(lab_portfolio.router)
app.include_router(lab_market.router)
app.include_router(lab_experiments.router)
app.include_router(lab_reports.router)
app.include_router(lab_extensions.router)

# Globally override standard JSONResponse routes with SafeJSONResponse to handle NaN/Infinity
from fastapi.routing import APIRoute
from fastapi.responses import JSONResponse
for route in app.routes:
    if isinstance(route, APIRoute):
        if route.response_class == JSONResponse:
            route.response_class = SafeJSONResponse



@app.on_event("startup")
async def startup_event():
    """Log startup info and start automated refresh worker."""
    import os
    import asyncio
    from app.data.loader import data_loader
    from app.services.scheduler import start_scheduler
    from app.services.db import init_db
    from app.services.company_service import CACHE_DIR

    # Initialize SQLite database
    init_db()

    # Ensure company profile cache folder exists
    os.makedirs(CACHE_DIR, exist_ok=True)

    logger.info(f"PMS Engine v{settings.app_version} starting")
    logger.info(f"CSV source: {settings.csv_path}")
    logger.info(f"Stocks loaded: {data_loader.stocks_loaded}")
    logger.info(f"API docs: http://{settings.api_host}:{settings.api_port}/api/docs")

    # Start background scheduler
    asyncio.create_task(start_scheduler())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
