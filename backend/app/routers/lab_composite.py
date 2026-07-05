"""
lab_composite.py — API Router for composite score weighting research.
"""

import logging
import json
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field

from app.lab.db_lab import (
    create_experiment,
    get_experiment,
    list_weight_snapshots,
)
from app.lab.background_runner import run_experiment_task
from app.lab.composite_validator import (
    current_weight_analysis,
    weight_grid_search,
    regime_optimal_weights,
    SCORE_FEATURES,
)
from app.lab.backtester import load_ohlcv
from app.lab.regime_detector import detect_regimes

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/lab/composite", tags=["lab-composite"])


class OptimizeWeightsRequest(BaseModel):
    step: float = Field(0.10, ge=0.01, le=0.5, description="Grid step size (default 0.10)", example=0.10)
    target_metric: str = Field("rank_ic", description="Target metric to optimize (default rank_ic)", example="rank_ic")


def _run_weight_optimization_sync(step: float, target_metric: str, experiment_id: str) -> Dict[str, Any]:
    """Synchronous core runner for weight optimization background task."""
    logger.info(f"Running weight optimization with step={step}, metric={target_metric} for experiment {experiment_id}...")
    
    # Run the grid search
    res = weight_grid_search(
        step=step,
        target_metric=target_metric,
        experiment_id=experiment_id,
    )
    
    # Format metrics for SQLite
    metrics = {
        "best_metric_value": res["best_metric_value"],
        "target_metric": res["target_metric"],
        "total_combinations": res["total_combinations"],
    }
    
    # Add best weights to metrics
    best_w = res.get("best_weights") or {}
    for fk, fv in best_w.items():
        metrics[f"best_weight_{fk}"] = fv

    # Stringify top results
    metrics["top_results_json"] = json.dumps(res.get("top_results", []))
    
    # Save surface chart
    charts = {
        "optimization_surface": res.get("optimization_surface", [])
    }
    
    return {
        "metrics": metrics,
        "charts": charts,
    }


@router.get("/current-analysis")
async def get_current_analysis():
    """Retrieve partial correlation and estimated contribution analysis for current sub-score weights."""
    try:
        return current_weight_analysis()
    except Exception as e:
        logger.error(f"Error calculating current weight analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize-weights")
async def start_weight_optimization(req: OptimizeWeightsRequest, background_tasks: BackgroundTasks):
    """Start an async weight grid search optimization. Returns experiment ID."""
    params_info = {
        "step": req.step,
        "target_metric": req.target_metric,
    }
    
    try:
        exp_id = create_experiment(
            module="composite_optimize",
            name=f"Composite Score Weight Optimization (Step: {req.step})",
            params=params_info,
        )
        
        background_tasks.add_task(
            run_experiment_task,
            experiment_id=exp_id,
            runner_fn=_run_weight_optimization_sync,
            step=req.step,
            target_metric=req.target_metric,
        )
        
        return {"experiment_id": exp_id, "status": "pending"}
    except Exception as e:
        logger.error(f"Error starting weight optimization: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/optimize-result/{exp_id}")
async def get_weight_optimization_result(exp_id: str):
    """Retrieve top weight combinations and surface maps for a completed weight optimization experiment."""
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

    # Format the final response
    metrics = exp.get("metrics", {})
    charts = exp.get("charts", {})
    
    best_weights = {}
    for col in SCORE_FEATURES:
        w_val = metrics.get(f"best_weight_{col}")
        if w_val is not None:
            best_weights[col] = w_val

    top_results = []
    top_results_str = metrics.get("top_results_json")
    if top_results_str:
        try:
            top_results = json.loads(top_results_str)
        except Exception:
            pass

    return {
        "experiment_id": exp_id,
        "status": exp["status"],
        "params": exp["params"],
        "best_weights": best_weights,
        "best_metric_value": metrics.get("best_metric_value"),
        "target_metric": metrics.get("target_metric"),
        "total_combinations": metrics.get("total_combinations"),
        "top_results": top_results,
        "optimization_surface": charts.get("optimization_surface", []),
        "research_note": "⚠️ Research only. Production weights are unchanged.",
    }


@router.get("/regime-weights")
async def get_regime_weights():
    """Retrieve optimal weight configurations per market regime (synchronous)."""
    try:
        # Load NIFTY regimes as benchmark
        regimes_df = None
        nifty_df = load_ohlcv("^NSEI", "3Y")
        if nifty_df is not None:
            regimes_df = detect_regimes(nifty_df)
        
        return regime_optimal_weights(regimes_df)
    except Exception as e:
        logger.error(f"Error calculating regime-optimal weights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/snapshots")
async def get_snapshots(exp_id: str = Query(..., description="Experiment ID to fetch weight snapshots for")):
    """List historical weight snapshots recorded during a grid search."""
    try:
        return list_weight_snapshots(exp_id)
    except Exception as e:
        logger.error(f"Error listing weight snapshots: {e}")
        raise HTTPException(status_code=500, detail=str(e))

