"""
lab_market.py — API Router for market, sector, and benchmark comparisons.
"""

import logging
import json
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field
import pandas as pd

from app.lab.db_lab import (
    create_experiment,
    get_experiment,
)
from app.lab.background_runner import run_experiment_task
from app.lab.backtester import load_ohlcv
from app.lab.regime_detector import (
    detect_regimes,
    regime_timeline,
    regime_performance_summary,
)
from app.lab.sector_researcher import (
    sector_score_analysis,
    sector_return_performance,
    sector_correlation_matrix,
    sector_rotation_signal,
)
from app.lab.benchmark_comparator import (
    compare_to_benchmark,
    multi_benchmark_stats,
    BENCHMARK_TICKERS,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/lab", tags=["lab-market"])


# ─────────────────────────────────────────────────────────────────────────────
# PYDANTIC SCHEMAS
# ─────────────────────────────────────────────────────────────────────────────

class RegimeDetectRequest(BaseModel):
    symbol: str = Field("^NSEI", examples=["^NSEI"])
    period: str = Field("3Y", examples=["3Y"])


class SectorReturnsRequest(BaseModel):
    period: str = Field("1Y", examples=["1Y"])


class BenchmarkCompareRequest(BaseModel):
    strategy_experiment_id: str = Field(..., description="Completed portfolio experiment ID")
    benchmark_key: str = Field("NIFTY50", examples=["NIFTY50"])
    period: str = Field("3Y", examples=["3Y"])


# ─────────────────────────────────────────────────────────────────────────────
# REGIME DETECTION ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

def _run_regime_detection_sync(symbol: str, period: str) -> Dict[str, Any]:
    """Synchronous core runner for regime detection background task."""
    logger.info(f"Running market regime detection for {symbol} ({period})...")
    df = load_ohlcv(symbol, period)
    if df is None or df.empty:
        raise ValueError(f"Could not load price data for {symbol} ({period})")

    # Detect daily regimes
    regimes_df = detect_regimes(df)
    timeline = regime_timeline(regimes_df)

    # Compute descriptive statistics per regime
    # Group by primary_regime and compute simple returns metrics
    df_with_ret = regimes_df.copy()
    df_with_ret["Daily_Return"] = df_with_ret["Close"].pct_change() * 100
    
    regime_stats = []
    for regime_name, group in df_with_ret.groupby("primary_regime"):
        rets = group["Daily_Return"].dropna()
        n_days = len(group)
        avg_ret = float(rets.mean()) if not rets.empty else 0.0
        std_ret = float(rets.std()) if not rets.empty else 0.0
        regime_stats.append({
            "regime": regime_name,
            "days": n_days,
            "pct_time": round(float(n_days / len(df_with_ret) * 100), 2),
            "avg_daily_return": round(avg_ret, 4),
            "volatility_daily": round(std_ret, 4),
        })

    # Prepare metrics & charts
    metrics = {
        "total_days": len(df_with_ret),
        "primary_regimes_found": len(df_with_ret["primary_regime"].unique()),
        "regime_stats_json": json.dumps(regime_stats),
    }

    charts = {
        "regime_timeline": timeline,
        "regime_stats": regime_stats,
    }

    return {
        "metrics": metrics,
        "charts": charts,
    }


@router.post("/regime/detect")
async def detect_market_regime(req: RegimeDetectRequest, background_tasks: BackgroundTasks):
    """Start an async regime detection experiment. Returns experiment ID."""
    params_info = {
        "symbol": req.symbol.upper(),
        "period": req.period,
    }
    
    try:
        exp_id = create_experiment(
            module="regime_detection",
            name=f"Market Regime Detection on {req.symbol.upper()}",
            symbol=req.symbol.upper(),
            params=params_info,
        )
        
        background_tasks.add_task(
            run_experiment_task,
            experiment_id=exp_id,
            runner_fn=_run_regime_detection_sync,
            symbol=req.symbol,
            period=req.period,
        )
        
        return {"experiment_id": exp_id, "status": "pending"}
    except Exception as e:
        logger.error(f"Error starting regime detection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/regime/result/{exp_id}")
async def get_regime_result(exp_id: str):
    """Retrieve timeline data and metrics of a completed regime detection experiment."""
    exp = get_experiment(exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    if exp["status"] == "failed":
        raise HTTPException(
            status_code=400,
            detail=f"Regime detection failed: {exp['error_msg']}"
        )
    if exp["status"] != "complete":
        return {
            "experiment_id": exp_id,
            "status": exp["status"],
            "message": "Regime detection is still running."
        }

    metrics = exp.get("metrics", {})
    charts = exp.get("charts", {})
    
    regime_stats = []
    stats_str = metrics.get("regime_stats_json")
    if stats_str:
        try:
            regime_stats = json.loads(stats_str)
        except Exception:
            pass

    return {
        "experiment_id": exp_id,
        "status": exp["status"],
        "params": exp["params"],
        "total_days": metrics.get("total_days"),
        "primary_regimes_found": metrics.get("primary_regimes_found"),
        "regime_stats": regime_stats,
        "regime_timeline": charts.get("regime_timeline", []),
        "started_at": exp["started_at"],
        "completed_at": exp["completed_at"],
    }


# ─────────────────────────────────────────────────────────────────────────────
# SECTOR RESEARCH ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/sector/analysis")
async def get_sector_analysis():
    """Get static sub-score groupings and pick summaries for sectors (synchronous)."""
    try:
        return sector_score_analysis()
    except Exception as e:
        logger.error(f"Error running sector score analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _run_sector_returns_sync(period: str) -> Dict[str, Any]:
    """Synchronous core runner for sector performance evaluation."""
    logger.info(f"Running sector performance analysis for period {period}...")
    
    # 1. Performance ranks
    perf = sector_return_performance(period=period)
    
    # 2. Correlation matrix
    corr = sector_correlation_matrix(period=period)
    
    # 3. Momentum rotation signals
    rot = sector_rotation_signal()
    
    metrics = {
        "period": period,
        "sector_performance_json": json.dumps(perf.get("sector_returns", [])),
        "sector_rotation_json": json.dumps(rot),
    }

    charts = {
        "sector_returns": perf.get("sector_returns", []),
        "sector_correlation": corr.get("correlation", []),
        "sector_rotation": rot,
    }

    return {
        "metrics": metrics,
        "charts": charts,
    }


@router.post("/sector/returns")
async def start_sector_returns(req: SectorReturnsRequest, background_tasks: BackgroundTasks):
    """Start an async sector performance analysis run. Returns experiment ID."""
    params_info = {
        "period": req.period,
    }
    
    try:
        exp_id = create_experiment(
            module="sector_performance",
            name=f"Sector Returns & Rotation Research (Period: {req.period})",
            params=params_info,
        )
        
        background_tasks.add_task(
            run_experiment_task,
            experiment_id=exp_id,
            runner_fn=_run_sector_returns_sync,
            period=req.period,
        )
        
        return {"experiment_id": exp_id, "status": "pending"}
    except Exception as e:
        logger.error(f"Error starting sector analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sector/result/{exp_id}")
async def get_sector_result(exp_id: str):
    """Retrieve results of a completed sector performance experiment."""
    exp = get_experiment(exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    if exp["status"] == "failed":
        raise HTTPException(
            status_code=400,
            detail=f"Sector analysis failed: {exp['error_msg']}"
        )
    if exp["status"] != "complete":
        return {
            "experiment_id": exp_id,
            "status": exp["status"],
            "message": "Sector analysis is still running."
        }

    metrics = exp.get("metrics", {})
    charts = exp.get("charts", {})
    
    sector_returns = []
    ret_str = metrics.get("sector_performance_json")
    if ret_str:
        try:
            sector_returns = json.loads(ret_str)
        except Exception:
            pass

    sector_rotation = []
    rot_str = metrics.get("sector_rotation_json")
    if rot_str:
        try:
            sector_rotation = json.loads(rot_str)
        except Exception:
            pass

    return {
        "experiment_id": exp_id,
        "status": exp["status"],
        "params": exp["params"],
        "sector_returns": sector_returns,
        "sector_rotation": sector_rotation,
        "sector_correlation": charts.get("sector_correlation", []),
        "started_at": exp["started_at"],
        "completed_at": exp["completed_at"],
    }


# ─────────────────────────────────────────────────────────────────────────────
# BENCHMARK COMPARISON ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

def _run_benchmark_comparison_sync(
    strategy_experiment_id: str,
    benchmark_key: str,
    period: str,
) -> Dict[str, Any]:
    """Synchronous core runner for benchmark comparisons."""
    logger.info(f"Comparing strategy {strategy_experiment_id} vs benchmark {benchmark_key}...")
    
    # 1. Fetch completed strategy experiment
    strat_exp = get_experiment(strategy_experiment_id)
    if not strat_exp or strat_exp["status"] != "complete":
        raise ValueError(f"Strategy experiment {strategy_experiment_id} not found or not completed.")

    # 2. Extract daily equity curve data
    charts_data = strat_exp.get("charts", {})
    eq_curve = charts_data.get("equity_curve", [])
    if not eq_curve:
        raise ValueError(f"No equity curve data found in strategy experiment {strategy_experiment_id}")

    # Reconstruct equity series and dates
    portfolio_equity = pd.Series([item["portfolio"] for item in eq_curve])
    portfolio_dates = [item["date"] for item in eq_curve]
    
    # 3. Compare to benchmark
    comparison = compare_to_benchmark(
        portfolio_equity=portfolio_equity,
        portfolio_dates=portfolio_dates,
        portfolio_trade_log=[],
        benchmark_key=benchmark_key,
        period=period,
    )
    
    # Re-normalize comparative metrics for saving
    metrics = comparison["portfolio_metrics"]
    metrics["alpha_vs_bench"] = comparison["alpha"]
    metrics["beta_vs_bench"] = comparison["beta"]
    metrics["tracking_error_vs_bench"] = comparison["tracking_error"]
    metrics["information_ratio_vs_bench"] = comparison["information_ratio"]
    metrics["upside_capture_vs_bench"] = comparison["upside_capture"]
    metrics["downside_capture_vs_bench"] = comparison["downside_capture"]
    metrics["benchmark_key"] = comparison["benchmark_key"]
    metrics["benchmark_label"] = comparison["benchmark_label"]
    
    # Extract charts
    charts = comparison.get("charts", {})
    
    # Map charts for frontend compatibility
    if "equity_curve" in charts:
        charts["equity"] = charts["equity_curve"]
    if "drawdown" in charts:
        portfolio_dd = charts.get("drawdown", [])
        benchmark_dd = charts.get("benchmark_drawdown", [])
        combined_dd = []
        for i in range(len(portfolio_dd)):
            p_item = portfolio_dd[i]
            b_item = benchmark_dd[i] if i < len(benchmark_dd) else {}
            combined_dd.append({
                "date": p_item.get("date"),
                "drawdown_portfolio": p_item.get("drawdown_pct"),
                "drawdown_benchmark": b_item.get("drawdown_pct") if b_item else None
            })
        charts["drawdown"] = combined_dd
    
    return {
        "metrics": metrics,
        "charts": charts,
    }


@router.post("/benchmark/compare")
async def compare_strategy_benchmark(req: BenchmarkCompareRequest, background_tasks: BackgroundTasks):
    """Start an async benchmark comparison backtest. Returns experiment ID."""
    params_info = {
        "strategy_experiment_id": req.strategy_experiment_id,
        "benchmark_key": req.benchmark_key,
        "period": req.period,
    }
    
    try:
        exp_id = create_experiment(
            module="benchmark_comparison",
            name=f"Benchmark Comparison ({req.benchmark_key})",
            params=params_info,
        )
        
        background_tasks.add_task(
            run_experiment_task,
            experiment_id=exp_id,
            runner_fn=_run_benchmark_comparison_sync,
            strategy_experiment_id=req.strategy_experiment_id,
            benchmark_key=req.benchmark_key,
            period=req.period,
        )
        
        return {"experiment_id": exp_id, "status": "pending"}
    except Exception as e:
        logger.error(f"Error starting benchmark comparison: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/benchmark/result/{exp_id}")
async def get_benchmark_result(exp_id: str):
    """Retrieve comparison metrics and charts of a completed benchmark experiment."""
    exp = get_experiment(exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    if exp["status"] == "failed":
        raise HTTPException(
            status_code=400,
            detail=f"Benchmark comparison failed: {exp['error_msg']}"
        )
    if exp["status"] != "complete":
        return {
            "experiment_id": exp_id,
            "status": exp["status"],
            "message": "Benchmark comparison is still running."
        }

    metrics = exp.get("metrics", {})
    charts = exp.get("charts", {})

    # Map charts for frontend compatibility (supports existing runs)
    if "equity_curve" in charts and "equity" not in charts:
        charts["equity"] = charts["equity_curve"]
    if "drawdown" in charts:
        first_item = charts["drawdown"][0] if charts["drawdown"] else {}
        if first_item and "drawdown_portfolio" not in first_item:
            portfolio_dd = charts.get("drawdown", [])
            benchmark_dd = charts.get("benchmark_drawdown", [])
            combined_dd = []
            for i in range(len(portfolio_dd)):
                p_item = portfolio_dd[i]
                b_item = benchmark_dd[i] if i < len(benchmark_dd) else {}
                combined_dd.append({
                    "date": p_item.get("date"),
                    "drawdown_portfolio": p_item.get("drawdown_pct"),
                    "drawdown_benchmark": b_item.get("drawdown_pct") if b_item else None
                })
            charts["drawdown"] = combined_dd

    return {
        "experiment_id": exp_id,
        "status": exp["status"],
        "params": exp["params"],
        "benchmark_key": metrics.get("benchmark_key"),
        "benchmark_label": metrics.get("benchmark_label"),
        "alpha": metrics.get("alpha_vs_bench"),
        "beta": metrics.get("beta_vs_bench"),
        "tracking_error": metrics.get("tracking_error_vs_bench"),
        "information_ratio": metrics.get("information_ratio_vs_bench"),
        "upside_capture": metrics.get("upside_capture_vs_bench"),
        "downside_capture": metrics.get("downside_capture_vs_bench"),
        "metrics": metrics,
        "charts": charts,
        "started_at": exp["started_at"],
        "completed_at": exp["completed_at"],
    }

