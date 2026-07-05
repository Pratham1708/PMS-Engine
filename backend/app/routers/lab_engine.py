"""
lab_engine.py — API Router for validating the full PMS Engine scoring pipelines and sub-scores.
"""

import logging
from typing import Dict, Optional, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field

from app.lab.db_lab import (
    create_experiment,
    get_experiment,
)
from app.lab.background_runner import run_experiment_task
from app.lab.pms_score_validator import (
    full_engine_validation,
    score_distribution,
    SCORE_COLUMNS,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/lab/engine", tags=["lab-engine"])


class EngineValidationRequest(BaseModel):
    horizon: str = Field("1M", description="Forward return horizon (1M, 3M, 6M)", example="1M")


def _run_engine_validation_sync(horizon: str) -> Dict[str, Any]:
    """Synchronous core runner for background engine validation."""
    # Runs the full scoring pipeline validation
    validation_results = full_engine_validation(horizon=horizon)
    
    # Format metrics for SQLite saving
    metrics = {}
    for col, res in validation_results["score_validations"].items():
        if col == "FinalRating" or "error" in res:
            continue
        metrics[f"{col}_ic"] = res.get("ic")
        metrics[f"{col}_hit_rate"] = res.get("hit_rate")
        metrics[f"{col}_t_stat"] = res.get("t_stat")
        metrics[f"{col}_significant"] = 1 if res.get("significant") else 0
        metrics[f"{col}_spread"] = res.get("quartile_spread")

    # Stringify rating validation details for saving
    import json
    rating_data = validation_results["score_validations"].get("FinalRating", {})
    metrics["final_rating_monotonicity"] = 1 if rating_data.get("monotonicity") else 0
    metrics["final_rating_details_json"] = json.dumps(rating_data)
    
    # Charts represent histograms of score distribution & rating monotonicity bar
    charts = {}
    for col, dist in validation_results["score_distributions"].items():
        charts[f"{col}_dist"] = dist.get("histogram", [])

    # Monotonicity bar chart: rating vs avg return
    rating_bars = []
    if "per_rating" in rating_data:
        for rname, rstats in rating_data["per_rating"].items():
            rating_bars.append({
                "rating": rname,
                "avg_return": rstats.get("avg_return"),
                "n": rstats.get("n"),
            })
    charts["rating_monotonicity"] = rating_bars

    return {
        "metrics": metrics,
        "charts": charts,
    }


@router.post("/validate")
async def start_engine_validation(req: EngineValidationRequest, background_tasks: BackgroundTasks):
    """Start an async PMS Engine score validation run. Returns the experiment ID."""
    params_info = {
        "horizon": req.horizon,
    }
    
    try:
        exp_id = create_experiment(
            module="engine_validation",
            name=f"PMS Engine Validation (Horizon: {req.horizon})",
            params=params_info,
        )
        
        background_tasks.add_task(
            run_experiment_task,
            experiment_id=exp_id,
            runner_fn=_run_engine_validation_sync,
            horizon=req.horizon,
        )
        
        return {"experiment_id": exp_id, "status": "pending"}
    except Exception as e:
        logger.error(f"Error starting engine validation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/result/{exp_id}")
async def get_engine_validation_result(exp_id: str):
    """Retrieve the results of a completed scoring engine validation experiment."""
    exp = get_experiment(exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    if exp["status"] == "failed":
        raise HTTPException(
            status_code=400,
            detail=f"Validation failed: {exp['error_msg']}"
        )
    if exp["status"] != "complete":
        return {
            "experiment_id": exp_id,
            "status": exp["status"],
            "message": "Validation is still running."
        }

    # Reconstruct the validation response structure
    import json
    metrics = exp.get("metrics", {})
    charts = exp.get("charts", {})
    
    score_validations = {}
    for col in SCORE_COLUMNS:
        score_validations[col] = {
            "score_column": col,
            "horizon": exp["params"].get("horizon", "1M"),
            "ic": metrics.get(f"{col}_ic"),
            "hit_rate": metrics.get(f"{col}_hit_rate"),
            "t_stat": metrics.get(f"{col}_t_stat"),
            "significant": metrics.get(f"{col}_significant") == 1,
            "quartile_spread": metrics.get(f"{col}_spread"),
        }

    # Reconstruct FinalRating monotonicity data
    final_rating_details = {}
    fr_str = metrics.get("final_rating_details_json")
    if fr_str:
        try:
            final_rating_details = json.loads(fr_str)
        except Exception:
            pass

    score_validations["FinalRating"] = final_rating_details

    # Reconstruct distributions
    score_distributions = {}
    for col in SCORE_COLUMNS:
        score_distributions[col] = {
            "score_column": col,
            "histogram": charts.get(f"{col}_dist", []),
        }

    return {
        "experiment_id": exp_id,
        "status": exp["status"],
        "params": exp["params"],
        "score_validations": score_validations,
        "score_distributions": score_distributions,
        "rating_monotonicity_chart": charts.get("rating_monotonicity", []),
        "started_at": exp["started_at"],
        "completed_at": exp["completed_at"],
    }


@router.get("/score-distribution")
async def get_score_distribution(score_column: str = Query(..., description="The score column to run distribution for")):
    """Get the current histogram distribution of any score column across the universe (synchronous)."""
    if score_column not in SCORE_COLUMNS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid score column. Must be one of: {', '.join(SCORE_COLUMNS)}"
        )
    try:
        return score_distribution(score_column)
    except Exception as e:
        logger.error(f"Error calculating score distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

