"""
lab_extensions.py — API Router for extended Quantitative Research Laboratory capabilities.
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

# Core Lab Imports
from app.lab.cross_indicator import rank_indicator_combinations
from app.lab.ensemble_researcher import compare_ensemble_methods
from app.lab.hyperopt_lab import optimize_ml_thresholds, optimize_risk_thresholds, optimize_position_sizing
from app.lab.monte_carlo import run_monte_carlo_simulation
from app.lab.stress_tester import run_stress_test
from app.lab.position_sizer import simulate_position_sizing
from app.lab.portfolio_construction import optimize_portfolio_construction
from app.lab.correlation_lab import run_correlation_research
from app.lab.market_breadth import calculate_market_breadth
from app.lab.liquidity_research import evaluate_stock_liquidity
from app.lab.drift_monitor import check_score_drift, get_drift_alerts

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/lab", tags=["lab-extensions"])

# ── REQUEST MODELS ──

class CrossIndicatorRequest(BaseModel):
    symbol: str = Field("RELIANCE.NS", examples=["RELIANCE.NS"])
    period: str = Field("3Y", examples=["3Y"])
    target_metric: str = Field("sharpe", examples=["sharpe"])

class EnsembleRequest(BaseModel):
    period: str = Field("3Y", examples=["3Y"])
    initial_capital: float = Field(100000.0, examples=[100000.0])

class HyperoptRequest(BaseModel):
    target: str = Field("ml_model", description="ml_model | risk_thresholds | position_sizing", examples=["ml_model"])
    symbol: str = Field("^NSEI", examples=["^NSEI"])
    period: str = Field("3Y", examples=["3Y"])
    target_metric: str = Field("sharpe_ratio", examples=["sharpe_ratio"])

class MonteCarloRequest(BaseModel):
    symbol: str = Field("^NSEI", examples=["^NSEI"])
    period: str = Field("3Y", examples=["3Y"])
    n_simulations: int = Field(250, ge=10, le=1000, examples=[250])
    horizon_days: int = Field(252, ge=20, le=500, examples=[252])

class StressTestRequest(BaseModel):
    symbol: str = Field("^NSEI", examples=["^NSEI"])

class PositionSizingRequest(BaseModel):
    symbol: str = Field("RELIANCE.NS", examples=["RELIANCE.NS"])
    period: str = Field("3Y", examples=["3Y"])
    risk_pct: float = Field(2.0, ge=0.1, le=10.0, examples=[2.0])

class PortfolioConstructionRequest(BaseModel):
    symbols: List[str] = Field(default_factory=list, examples=[["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS"]])
    period: str = Field("3Y", examples=["3Y"])

# ── ROUTE ENDPOINTS ──

@router.post("/cross-indicator/run")
async def run_cross_indicator(req: CrossIndicatorRequest):
    """Backtest and rank all single, dual, and triple indicator combinations."""
    try:
        return rank_indicator_combinations(req.symbol, period=req.period, target_metric=req.target_metric)
    except Exception as e:
        logger.error(f"Error in cross-indicator research: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ensemble/run")
async def run_ensemble(req: EnsembleRequest):
    """Compare performance of Weighted/Majority/Rank voting ensemble strategies."""
    try:
        return compare_ensemble_methods(period=req.period, initial_capital=req.initial_capital)
    except Exception as e:
        logger.error(f"Error in ensemble research: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/hyperopt/run")
async def run_hyperopt(req: HyperoptRequest):
    """Run parameter grid search optimizer for ML, risk cuts, or sizing parameters."""
    try:
        if req.target == "ml_model":
            return optimize_ml_thresholds(req.symbol, period=req.period, target_metric=req.target_metric)
        elif req.target == "risk_thresholds":
            return optimize_risk_thresholds(req.symbol, period=req.period, target_metric=req.target_metric)
        else:
            return optimize_position_sizing(req.symbol, period=req.period, target_metric=req.target_metric)
    except Exception as e:
        logger.error(f"Error in hyperopt research: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/monte-carlo/run")
async def run_monte_carlo(req: MonteCarloRequest):
    """Simulate asset/portfolio returns using bootstrap Monte Carlo resampling."""
    try:
        return run_monte_carlo_simulation(
            symbol=req.symbol,
            period=req.period,
            n_simulations=req.n_simulations,
            horizon_days=req.horizon_days
        )
    except Exception as e:
        logger.error(f"Error in Monte Carlo research: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stress-test/run")
async def run_stress(req: StressTestRequest):
    """Evaluate strategy returns and drawdowns during key historical crises."""
    try:
        return run_stress_test(symbol=req.symbol)
    except Exception as e:
        logger.error(f"Error in stress test: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/position-sizing/run")
async def run_position_sizing(req: PositionSizingRequest):
    """Compare portfolio value growth across Fixed, Kelly, Fractional, and Volatility sizing."""
    try:
        # Load trades from standard indicator backtest to drive sizer
        from app.lab.backtester import load_ohlcv, generate_signals, run_backtest
        df = load_ohlcv(req.symbol, req.period)
        if df is None or df.empty:
            raise ValueError("No price history for position sizing simulation")
        sig = generate_signals(df, "rsi", {"period": 14})
        bt = run_backtest(sig)
        return simulate_position_sizing(bt["trade_log"], risk_pct=req.risk_pct)
    except Exception as e:
        logger.error(f"Error in position sizing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/portfolio-construction/run")
async def run_portfolio_construction(req: PortfolioConstructionRequest):
    """Plot efficient frontier scatter and calculate optimized weights."""
    try:
        return optimize_portfolio_construction(req.symbols, period=req.period)
    except Exception as e:
        logger.error(f"Error in portfolio construction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/correlation/run")
async def get_correlation_lab(
    symbol: str = Query("RELIANCE.NS"),
    period: str = Query("3Y")
):
    """Retrieve rolling and indicator correlation analysis."""
    try:
        return run_correlation_research(symbol, period)
    except Exception as e:
        logger.error(f"Error in correlation research: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/breadth/run")
async def get_market_breadth(period: str = Query("6M")):
    """Compute timeline of market breadth and Advance-Decline metrics."""
    try:
        return calculate_market_breadth(period)
    except Exception as e:
        logger.error(f"Error in breadth research: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/liquidity/run")
async def get_liquidity_research(symbol: str = Query("RELIANCE.NS")):
    """Check ticker liquidity and gap frequency for suitability."""
    try:
        return evaluate_stock_liquidity(symbol)
    except Exception as e:
        logger.error(f"Error in liquidity research: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/drift/run")
async def get_drift_monitor():
    """Trigger drift check and calculate deviation scores."""
    try:
        return check_score_drift()
    except Exception as e:
        logger.error(f"Error in drift monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/drift/alerts")
async def get_logged_drift_alerts():
    """Retrieve recently logged drift alerts from SQLite."""
    try:
        return get_drift_alerts()
    except Exception as e:
        logger.error(f"Error reading drift alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))
# End of file

