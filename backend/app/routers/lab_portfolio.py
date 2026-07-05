"""
lab_portfolio.py — API Router for portfolio-level backtesting.
"""

import logging
import json
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field

from app.lab.db_lab import (
    create_experiment,
    get_experiment,
)
from app.lab.background_runner import run_experiment_task
from app.lab.portfolio_backtester import (
    STRATEGY_REGISTRY,
    strategy_top_n_monthly,
    strategy_equal_weight,
    strategy_smart_beta,
    strategy_sector_momentum,
    compare_strategies,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/lab/portfolio", tags=["lab-portfolio"])


class PortfolioBacktestRequest(BaseModel):
    strategy: str = Field("top_n_monthly", examples=["top_n_monthly"])
    n: int = Field(10, ge=1, le=50, examples=[10])
    period: str = Field("1Y", examples=["1Y"])  # 1Y (fast), 3Y, 5Y (slower)
    initial_capital: float = Field(100000.0, ge=1000.0, examples=[100000.0])


def _run_portfolio_backtest_sync(
    strategy: str,
    n: int,
    period: str,
    initial_capital: float,
) -> Dict[str, Any]:
    """
    Synchronous core runner for portfolio backtest background task.
    
    Supports periods: 1Y (fast, ~30s), 3Y (slower, ~90s), 5Y (slowest, ~120s+)
    """
    logger.info(f"Running portfolio backtest sync: strategy={strategy}, n={n}, period={period}, capital={initial_capital}")
    
    try:
        if strategy == "top_n_monthly":
            res = strategy_top_n_monthly(n=n, period=period, initial_capital=initial_capital)
        elif strategy == "equal_weight":
            res = strategy_equal_weight(max_stocks=n, period=period, initial_capital=initial_capital)
        elif strategy == "smart_beta":
            res = strategy_smart_beta(max_stocks=n, period=period, initial_capital=initial_capital)
        elif strategy == "sector_momentum":
            res = strategy_sector_momentum(period=period, top_sectors=2, initial_capital=initial_capital)
        else:
            raise ValueError(f"Unknown portfolio strategy: {strategy}")

        if "error" in res:
            logger.error(f"Strategy error: {res['error']}")
            raise ValueError(res["error"])

        # Prepare metrics & charts for saving
        metrics = res.get("metrics", {})
        charts = res.get("charts", {})
        
        # Save the custom variables inside metrics
        metrics["strategy_type"] = res.get("strategy")
        metrics["symbols_json"] = json.dumps(res.get("symbols", []))
        
        # Map frontend and test script expected keys
        if "cagr_pct" in metrics:
            metrics["cagr"] = metrics["cagr_pct"]
        if "sharpe_ratio" in metrics:
            metrics["sharpe"] = metrics["sharpe_ratio"]
        if "max_drawdown_pct" in metrics:
            metrics["max_drawdown"] = metrics["max_drawdown_pct"]
        
        if "weight_chart" in res:
            mapped_weights = []
            for w in res["weight_chart"]:
                weight_pct = w.get("weight_pct", 0.0)
                mapped_weights.append({
                    "symbol": w.get("symbol"),
                    "weight_pct": weight_pct,
                    "weight": weight_pct / 100.0
                })
            charts["smart_beta_weights"] = mapped_weights
            
        # Map charts for frontend compatibility
        if "equity_curve" in charts:
            charts["equity"] = charts["equity_curve"]
        if "drawdown" in charts:
            charts["drawdown"] = [
                {**d, "drawdown": d.get("drawdown_pct")} for d in charts["drawdown"]
            ]
            
        if "top_sectors" in res:
            metrics["top_sectors_json"] = json.dumps(res["top_sectors"])
        
        logger.info(f"Portfolio backtest completed successfully")
        
        return {
            "metrics": metrics,
            "charts": charts,
        }
    except Exception as e:
        logger.error(f"Portfolio backtest failed: {str(e)[:200]}")
        raise


@router.get("/strategies")
async def list_strategies():
    """List all registered portfolio strategies and descriptions."""
    s_list = []
    for k, v in STRATEGY_REGISTRY.items():
        s_list.append({
            "name": k,
            "label": v["label"],
            "description": v["description"],
        })
    return s_list


@router.post("/backtest")
async def start_portfolio_backtest(req: PortfolioBacktestRequest, background_tasks: BackgroundTasks):
    """Start an async portfolio-level backtest. Returns the experiment ID."""
    params_info = {
        "strategy": req.strategy,
        "n": req.n,
        "period": req.period,
        "initial_capital": req.initial_capital,
    }
    
    try:
        exp_id = create_experiment(
            module="portfolio_backtest",
            name=f"Portfolio Backtest: {STRATEGY_REGISTRY.get(req.strategy, {}).get('label', req.strategy.upper())}",
            symbol="PORTFOLIO",
            params=params_info,
        )
        
        background_tasks.add_task(
            run_experiment_task,
            experiment_id=exp_id,
            runner_fn=_run_portfolio_backtest_sync,
            strategy=req.strategy,
            n=req.n,
            period=req.period,
            initial_capital=req.initial_capital,
        )
        
        return {"experiment_id": exp_id, "status": "pending"}
    except Exception as e:
        logger.error(f"Error starting portfolio backtest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/result/{exp_id}")
async def get_portfolio_result(exp_id: str):
    """Retrieve results (metrics and charts) for a completed portfolio backtest experiment."""
    exp = get_experiment(exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    if exp["status"] == "failed":
        raise HTTPException(
            status_code=400,
            detail=f"Backtest failed: {exp['error_msg']}"
        )
    if exp["status"] != "complete":
        return {
            "experiment_id": exp_id,
            "status": exp["status"],
            "message": "Backtest is still running."
        }

    # Format the response
    metrics = exp.get("metrics", {})
    charts = exp.get("charts", {})
    params = exp.get("params", {})
    
    # Map frontend and test script expected keys to avoid null values
    if "cagr" not in metrics and "cagr_pct" in metrics:
        metrics["cagr"] = metrics["cagr_pct"]
    if "sharpe" not in metrics and "sharpe_ratio" in metrics:
        metrics["sharpe"] = metrics["sharpe_ratio"]
    if "max_drawdown" not in metrics and "max_drawdown_pct" in metrics:
        metrics["max_drawdown"] = metrics["max_drawdown_pct"]
        
    # Map charts for frontend compatibility (supports existing runs)
    if "equity_curve" in charts and "equity" not in charts:
        charts["equity"] = charts["equity_curve"]
    if "drawdown" in charts:
        charts["drawdown"] = [
            {**d, "drawdown": d.get("drawdown_pct") if "drawdown" not in d else d.get("drawdown")}
            for d in charts["drawdown"]
        ]
    if "smart_beta_weights" in charts:
        charts["smart_beta_weights"] = [
            {**w, "weight": w.get("weight_pct", 0.0) / 100.0 if "weight" not in w else w.get("weight")}
            for w in charts["smart_beta_weights"]
        ]
    
    symbols = []
    sym_str = metrics.get("symbols_json")
    if sym_str:
        try:
            symbols = json.loads(sym_str)
        except Exception:
            pass

    top_sectors = []
    sec_str = metrics.get("top_sectors_json")
    if sec_str:
        try:
            top_sectors = json.loads(sec_str)
        except Exception:
            pass

    return {
        "experiment_id": exp_id,
        "status": exp["status"],
        "params": params,
        "symbols": symbols,
        "top_sectors": top_sectors,
        "metrics": metrics,
        "charts": charts,
        "started_at": exp["started_at"],
        "completed_at": exp["completed_at"],
    }


@router.get("/compare")
async def compare_portfolio_strategies(ids: str = Query(..., description="Comma-separated list of portfolio experiment IDs to compare")):
    """Compare multiple completed portfolio backtests side-by-side."""
    id_list = [i.strip() for i in ids.split(",") if i.strip()]
    comparison = []
    
    for eid in id_list:
        exp = get_experiment(eid)
        if not exp or exp["status"] != "complete":
            continue
        
        metrics = exp.get("metrics", {})
        # Map frontend and test script expected keys to avoid null values
        if "cagr" not in metrics and "cagr_pct" in metrics:
            metrics["cagr"] = metrics["cagr_pct"]
        if "sharpe" not in metrics and "sharpe_ratio" in metrics:
            metrics["sharpe"] = metrics["sharpe_ratio"]
        if "max_drawdown" not in metrics and "max_drawdown_pct" in metrics:
            metrics["max_drawdown"] = metrics["max_drawdown_pct"]

        params = exp.get("params", {})
        
        comparison.append({
            "experiment_id": eid,
            "strategy": params.get("strategy"),
            "n": params.get("n"),
            "period": params.get("period"),
            "initial_capital": params.get("initial_capital"),
            "metrics": metrics,
        })
        
    return comparison

