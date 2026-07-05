"""
lab_indicators.py — API Router for technical indicator research and backtesting.
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field

from app.lab.indicators import get_indicator_list
from app.lab.db_lab import (
    create_experiment,
    get_experiment,
    list_experiments,
)
from app.lab.background_runner import run_experiment_task
from app.lab.backtester import load_ohlcv, generate_signals, run_backtest
from app.lab.metrics import compute_all_metrics
from app.lab.chart_builder import build_all_charts
from app.lab.optimizer import grid_search

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/lab", tags=["lab-indicators"])


# ─────────────────────────────────────────────────────────────────────────────
# PYDANTIC SCHEMAS
# ─────────────────────────────────────────────────────────────────────────────

class BacktestRequest(BaseModel):
    symbol: str = Field(..., examples=["RELIANCE.NS"])
    indicator: str = Field(..., examples=["rsi"])
    params: Dict[str, Any] = Field(default_factory=dict, examples=[{"period": 14}])
    period: str = Field("3Y", examples=["3Y"])  # 1M, 3M, 6M, 1Y, 3Y, 5Y


class OptimizeRequest(BaseModel):
    symbol: str = Field(..., examples=["RELIANCE.NS"])
    indicator: str = Field(..., examples=["rsi"])
    param_grid: Optional[Dict[str, Dict[str, float]]] = Field(
        None,
        description="Optional overrides in format: {param_name: {min: float, max: float, step: float}}",
    )
    target_metric: str = Field("sharpe_ratio", examples=["sharpe_ratio"])
    period: str = Field("3Y", examples=["3Y"])
    n_splits: int = Field(3, ge=2, le=10)


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/indicators")
async def list_indicators():
    """List all registered technical indicators and their parameter specifications."""
    try:
        return get_indicator_list()
    except Exception as e:
        logger.error(f"Error listing indicators: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _run_backtest_sync(symbol: str, indicator_name: str, params: Dict, period: str) -> Dict:
    """Synchronous core for indicator backtest background execution."""
    df = load_ohlcv(symbol, period)
    if df is None or df.empty:
        raise ValueError(f"Could not load OHLCV data for {symbol} ({period})")

    # Generate signals
    sig_df = generate_signals(df, indicator_name, params)
    
    # Run backtest simulation
    bt = run_backtest(sig_df)
    
    # Compute metrics
    metrics = compute_all_metrics(bt["equity_series"], bt["trade_log"])
    
    # Build charts
    charts = build_all_charts(
        equity_series=bt["equity_series"],
        trade_log=bt["trade_log"],
        dates=bt["equity_dates"]
    )
    
    return {
        "metrics": metrics,
        "charts": charts,
    }


@router.post("/indicator/run")
async def start_backtest(req: BacktestRequest, background_tasks: BackgroundTasks):
    """Start an async indicator backtest task. Returns the experiment ID."""
    params_info = {
        "symbol": req.symbol.upper(),
        "indicator": req.indicator,
        "params": req.params,
        "period": req.period,
    }
    
    try:
        # Create a pending experiment record
        exp_id = create_experiment(
            module="indicator",
            name=f"{req.indicator.upper()} Backtest on {req.symbol.upper()}",
            symbol=req.symbol.upper(),
            params=params_info,
        )
        
        # Enqueue backtest background task
        background_tasks.add_task(
            run_experiment_task,
            experiment_id=exp_id,
            runner_fn=_run_backtest_sync,
            symbol=req.symbol,
            indicator_name=req.indicator,
            params=req.params,
            period=req.period,
        )
        
        return {"experiment_id": exp_id, "status": "pending"}
    except Exception as e:
        logger.error(f"Error starting backtest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/indicator/status/{exp_id}")
async def get_backtest_status(exp_id: str):
    """Check status of a running or completed indicator experiment."""
    exp = get_experiment(exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return {
        "experiment_id": exp["experiment_id"],
        "status": exp["status"],
        "started_at": exp["started_at"],
        "completed_at": exp["completed_at"],
        "error_msg": exp["error_msg"],
    }


@router.get("/indicator/result/{exp_id}")
async def get_backtest_result(exp_id: str):
    """Retrieve full results (metrics and charts) for a completed experiment."""
    exp = get_experiment(exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    if exp["status"] == "failed":
        raise HTTPException(
            status_code=400,
            detail=f"Experiment failed: {exp['error_msg']}"
        )
    if exp["status"] != "complete":
        return {
            "experiment_id": exp_id,
            "status": exp["status"],
            "message": "Results are not ready yet."
        }
        
    return exp


def _run_optimization_sync(
    symbol: str,
    indicator_name: str,
    param_grid_override: Optional[Dict],
    target_metric: str,
    period: str,
    n_splits: int,
) -> Dict:
    """Synchronous core for indicator optimization background execution."""
    df = load_ohlcv(symbol, period)
    if df is None or df.empty:
        raise ValueError(f"Could not load OHLCV data for {symbol} ({period})")

    # Run parameter grid search optimization
    opt_results = grid_search(
        df=df,
        indicator_name=indicator_name,
        param_grid_override=param_grid_override,
        target_metric=target_metric,
        n_wf_splits=n_splits,
    )

    # Flatten nested metrics for SQLite saving
    metrics = {
        "best_metric_value": opt_results["best_metric_value"],
        "target_metric": opt_results["target_metric"],
        "total_combinations": opt_results["total_combinations"],
    }
    
    # Save best parameters in metrics
    for pk, pv in opt_results["best_params"].items():
        metrics[f"best_param_{pk}"] = pv

    # Save top results in metrics in stringified format
    import json
    metrics["top_results_json"] = json.dumps(opt_results["top_results"])

    # Prepare chart payload
    charts = {
        "param_heatmap": opt_results["optimization_surface"],
    }
    for pname, sensitivity_data in opt_results["sensitivity"].items():
        charts[f"sensitivity_{pname}"] = sensitivity_data

    return {
        "metrics": metrics,
        "charts": charts,
    }


@router.post("/indicator/optimize")
async def start_optimization(req: OptimizeRequest, background_tasks: BackgroundTasks):
    """Start an async parameter optimization grid search. Returns the experiment ID."""
    params_info = {
        "symbol": req.symbol.upper(),
        "indicator": req.indicator,
        "target_metric": req.target_metric,
        "period": req.period,
        "n_splits": req.n_splits,
        "grid_overrides": req.param_grid,
    }
    
    try:
        exp_id = create_experiment(
            module="indicator_optimize",
            name=f"{req.indicator.upper()} Optimization on {req.symbol.upper()}",
            symbol=req.symbol.upper(),
            params=params_info,
        )
        
        background_tasks.add_task(
            run_experiment_task,
            experiment_id=exp_id,
            runner_fn=_run_optimization_sync,
            symbol=req.symbol,
            indicator_name=req.indicator,
            param_grid_override=req.param_grid,
            target_metric=req.target_metric,
            period=req.period,
            n_splits=req.n_splits,
        )
        
        return {"experiment_id": exp_id, "status": "pending"}
    except Exception as e:
        logger.error(f"Error starting optimization: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/indicator/optimize/result/{exp_id}")
async def get_optimization_result(exp_id: str):
    """Retrieve full results of a completed parameter optimization grid search."""
    exp = get_experiment(exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    if exp["status"] == "failed":
        raise HTTPException(
            status_code=400,
            detail=f"Optimization failed: {exp['error_msg']}"
        )
    if exp["status"] != "complete":
        return {
            "experiment_id": exp_id,
            "status": exp["status"],
            "message": "Optimization is still running."
        }

    # Reconstruct top_results and best_params
    import json
    metrics = exp.get("metrics", {})
    charts = exp.get("charts", {})
    
    best_params = {}
    for k, v in metrics.items():
        if k.startswith("best_param_"):
            pname = k.replace("best_param_", "")
            best_params[pname] = v

    top_results = []
    top_results_str = metrics.get("top_results_json")
    if top_results_str:
        try:
            top_results = json.loads(top_results_str)
        except Exception:
            pass

    # Extract sensitivity charts
    sensitivity = {}
    for chart_type, data in charts.items():
        if chart_type.startswith("sensitivity_"):
            pname = chart_type.replace("sensitivity_", "")
            sensitivity[pname] = data

    return {
        "experiment_id": exp_id,
        "symbol": exp["symbol"],
        "status": exp["status"],
        "params": exp["params"],
        "best_params": best_params,
        "best_metric_value": metrics.get("best_metric_value"),
        "target_metric": metrics.get("target_metric"),
        "total_combinations": metrics.get("total_combinations"),
        "top_results": top_results,
        "optimization_surface": charts.get("param_heatmap", []),
        "sensitivity": sensitivity,
        "started_at": exp["started_at"],
        "completed_at": exp["completed_at"],
    }


@router.get("/indicator/compare")
async def compare_indicators(ids: str = Query(..., description="Comma-separated list of experiment IDs to compare")):
    """Compare multiple completed indicator backtest experiments side-by-side."""
    id_list = [i.strip() for i in ids.split(",") if i.strip()]
    comparison = []
    
    for eid in id_list:
        exp = get_experiment(eid)
        if not exp or exp["status"] != "complete":
            continue
        
        metrics = exp.get("metrics", {})
        params = exp.get("params", {})
        
        comparison.append({
            "experiment_id": eid,
            "symbol": exp["symbol"],
            "name": exp["name"],
            "indicator": params.get("indicator"),
            "params": params.get("params"),
            "period": params.get("period"),
            "metrics": metrics,
        })
        
    return comparison

