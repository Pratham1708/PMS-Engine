"""
lab_models.py — API Router for model research and evaluation laboratory.
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field

from app.lab.db_lab import (
    create_experiment,
    get_experiment,
)
from app.lab.background_runner import run_experiment_task
from app.lab.model_researcher import (
    MODEL_REGISTRY,
    compare_all_models,
    model_calibration,
    model_stability,
    model_regime_performance,
    feature_importance_from_scores,
)
from app.lab.backtester import load_ohlcv
from app.lab.regime_detector import detect_regimes

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/lab/models", tags=["lab-models"])


class ModelCompareRequest(BaseModel):
    horizon_bars: int = Field(21, description="Horizon in trading bars (default 21 for 1 month)", example=21)


def _run_model_comparison_sync(horizon_bars: int) -> Dict[str, Any]:
    """Synchronous core runner for model comparison background task."""
    logger.info(f"Running model comparison backtest for {horizon_bars} bars...")
    
    # 1. Base comparisons
    comparison = compare_all_models(horizon_bars=horizon_bars)
    importance = feature_importance_from_scores()
    
    # 2. Get NIFTY regimes
    regimes_df = None
    try:
        nifty_df = load_ohlcv("^NSEI", "3Y")
        if nifty_df is not None:
            regimes_df = detect_regimes(nifty_df)
    except Exception as e:
        logger.warning(f"Failed to load NIFTY regimes for model comparison: {e}")

    # 3. Compile stats and charts
    metrics = {}
    charts = {}

    # Store base comparison metrics
    import json
    for mname, mres in comparison["models"].items():
        if "error" in mres:
            continue
        metrics[f"{mname}_ic"] = mres.get("ic")
        metrics[f"{mname}_hit_rate"] = mres.get("hit_rate")
        metrics[f"{mname}_t_stat"] = mres.get("t_stat")
        metrics[f"{mname}_significant"] = 1 if mres.get("significant") else 0
        metrics[f"{mname}_mean"] = mres.get("score_mean")
        metrics[f"{mname}_std"] = mres.get("score_std")

    # Store permutation feature importances in metrics
    imp_dict = importance.get("importance", {})
    metrics["feature_importance_json"] = json.dumps(imp_dict)
    
    # Render importance as a chart
    from app.lab.chart_builder import feature_importance_bar
    charts["feature_importance"] = feature_importance_bar(imp_dict)

    # For each model, run calibration, stability, and regime performance
    for mname in MODEL_REGISTRY.keys():
        cal = model_calibration(mname)
        stab = model_stability(mname)
        reg = model_regime_performance(mname, regimes_df) if regimes_df is not None else {"regimes": {}}

        # Store stringified JSONs
        metrics[f"{mname}_calibration_json"] = json.dumps(cal)
        metrics[f"{mname}_stability_json"] = json.dumps(stab)
        metrics[f"{mname}_regime_perf_json"] = json.dumps(reg)

        # Map to charts
        # Calibration curve format: predicted_prob vs actual_freq
        cal_data = []
        for b in cal.get("bins", []):
            cal_data.append({
                "predicted_prob": b["bin_mid"],
                "actual_freq": b["positive_rate"],
                "perfect": b["bin_mid"],
            })
        charts[f"{mname}_calibration"] = cal_data

        # Stability format: month vs ic
        charts[f"{mname}_stability"] = stab.get("trend", [])

        # Regime performance format: regime vs ic
        reg_bars = []
        for rname, rstats in reg.get("regimes", {}).items():
            reg_bars.append({
                "regime": rname,
                "ic": rstats.get("ic"),
                "hit_rate": rstats.get("hit_rate"),
                "n": rstats.get("n"),
            })
        charts[f"{mname}_regime_performance"] = reg_bars

    return {
        "metrics": metrics,
        "charts": charts,
    }


@router.get("/list")
async def list_models():
    """List all registered models under model research registry."""
    model_list = []
    for k, v in MODEL_REGISTRY.items():
        model_list.append({
            "name": k,
            "label": v["label"],
            "category": v["category"],
            "description": v["description"],
            "score_col": v["score_col"],
        })
    return model_list


@router.post("/compare")
async def start_model_comparison(req: ModelCompareRequest, background_tasks: BackgroundTasks):
    """Start side-by-side comparison for all ML models. Returns experiment ID."""
    params_info = {
        "horizon_bars": req.horizon_bars,
    }
    
    try:
        exp_id = create_experiment(
            module="model_comparison",
            name=f"ML Model Side-by-Side Comparison (Horizon: {req.horizon_bars} bars)",
            params=params_info,
        )
        
        background_tasks.add_task(
            run_experiment_task,
            experiment_id=exp_id,
            runner_fn=_run_model_comparison_sync,
            horizon_bars=req.horizon_bars,
        )
        
        return {"experiment_id": exp_id, "status": "pending"}
    except Exception as e:
        logger.error(f"Error starting model comparison: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/result/{exp_id}")
async def get_model_comparison_result(exp_id: str):
    """Retrieve full results of a completed model comparison experiment."""
    exp = get_experiment(exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    if exp["status"] == "failed":
        raise HTTPException(
            status_code=400,
            detail=f"Comparison failed: {exp['error_msg']}"
        )
    if exp["status"] != "complete":
        return {
            "experiment_id": exp_id,
            "status": exp["status"],
            "message": "Comparison is still running."
        }

    # Format the final response
    import json
    metrics = exp.get("metrics", {})
    charts = exp.get("charts", {})

    # Reconstruct the comparison table
    models_comparison = {}
    for mname in MODEL_REGISTRY.keys():
        models_comparison[mname] = {
            "model": mname,
            "label": MODEL_REGISTRY[mname]["label"],
            "category": MODEL_REGISTRY[mname]["category"],
            "n": metrics.get(f"{mname}_ic"),  # dummy placeholder or grab from JSON if needed
            "ic": metrics.get(f"{mname}_ic"),
            "hit_rate": metrics.get(f"{mname}_hit_rate"),
            "t_stat": metrics.get(f"{mname}_t_stat"),
            "significant": metrics.get(f"{mname}_significant") == 1,
            "score_mean": metrics.get(f"{mname}_mean"),
            "score_std": metrics.get(f"{mname}_std"),
        }

    # Feature importance
    feature_importance = {}
    fi_str = metrics.get("feature_importance_json")
    if fi_str:
        try:
            feature_importance = json.loads(fi_str)
        except Exception:
            pass

    # Model specific details
    model_details = {}
    for mname in MODEL_REGISTRY.keys():
        cal, stab, reg = {}, {}, {}
        
        c_str = metrics.get(f"{mname}_calibration_json")
        s_str = metrics.get(f"{mname}_stability_json")
        r_str = metrics.get(f"{mname}_regime_perf_json")
        
        try:
            if c_str: cal = json.loads(c_str)
            if s_str: stab = json.loads(s_str)
            if r_str: reg = json.loads(r_str)
        except Exception:
            pass

        model_details[mname] = {
            "calibration": cal,
            "stability": stab,
            "regime_performance": reg,
            "charts": {
                "calibration": charts.get(f"{mname}_calibration", []),
                "stability": charts.get(f"{mname}_stability", []),
                "regime_performance": charts.get(f"{mname}_regime_performance", []),
            }
        }

    return {
        "experiment_id": exp_id,
        "status": exp["status"],
        "params": exp["params"],
        "comparison": {
            "models": models_comparison,
            "horizon_bars": exp["params"].get("horizon_bars", 21),
        },
        "feature_importance": feature_importance,
        "feature_importance_chart": charts.get("feature_importance", []),
        "details": model_details,
        "started_at": exp["started_at"],
        "completed_at": exp["completed_at"],
    }


@router.get("/calibration/{model}")
async def get_single_model_calibration(model: str):
    """Retrieve calibration curve data for a single model (synchronous)."""
    if model not in MODEL_REGISTRY:
        raise HTTPException(status_code=404, detail="Model not found")
    try:
        return model_calibration(model)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stability/{model}")
async def get_single_model_stability(model: str):
    """Retrieve rolling IC stability over time for a single model (synchronous)."""
    if model not in MODEL_REGISTRY:
        raise HTTPException(status_code=404, detail="Model not found")
    try:
        return model_stability(model)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feature-importance")
async def get_permutation_importance():
    """Retrieve permutation feature importance across pre-computed scores (synchronous)."""
    try:
        return feature_importance_from_scores()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/regime-performance/{model}")
async def get_single_model_regime_perf(model: str):
    """Retrieve performance of a single model across market regimes (synchronous)."""
    if model not in MODEL_REGISTRY:
        raise HTTPException(status_code=404, detail="Model not found")
    try:
        # Load NIFTY regimes as benchmark
        regimes_df = None
        nifty_df = load_ohlcv("^NSEI", "3Y")
        if nifty_df is not None:
            regimes_df = detect_regimes(nifty_df)
        
        return model_regime_performance(model, regimes_df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

