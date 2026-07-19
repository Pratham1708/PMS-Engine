"""
routers/backtest.py — FastAPI endpoints for Phase 14C Backtesting Engine.

Endpoints:
  POST   /api/backtest/run              — launch a backtest run
  GET    /api/backtest/{run_id}         — get full backtest result
  GET    /api/backtest/history          — list all runs (optional ?strategy_id=)
  DELETE /api/backtest/{run_id}         — delete a run + reports
  POST   /api/backtest/validate         — run strategy validation only (no simulation)
  GET    /api/backtest/{run_id}/report  — download report (?format=json|html|pdf)
"""

import json
import logging
import os
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse

from app.models.schemas import BacktestRunRequest
from app.services import db
from app.services.backtest.backtest_orchestrator import run_backtest
from app.services.backtest.strategy_validation_service import run_validation

router = APIRouter(prefix="/api/backtest", tags=["backtest"])
logger = logging.getLogger(__name__)

REPORTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "reports", "backtest"
)
os.makedirs(REPORTS_DIR, exist_ok=True)


# ── POST /api/backtest/run ────────────────────────────────────────────────────

@router.post("/run")
def launch_backtest(request: BacktestRunRequest):
    """Launch a full backtest simulation. Runs synchronously; returns complete results."""
    try:
        result = run_backtest(request)
        if result.get("status") == "failed":
            raise HTTPException(status_code=422, detail=result.get("error", "Backtest failed."))
        return JSONResponse(content=result)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("[BacktestRouter] /run error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ── GET /api/backtest/{run_id} ────────────────────────────────────────────────

@router.get("/{run_id}")
def get_backtest_result(run_id: str):
    """Return the full backtest result for a completed run."""
    session = db.get_db_session()
    try:
        from app.models.orm import StrategyBacktestRun
        rec = session.query(StrategyBacktestRun).filter(
            StrategyBacktestRun.run_id == run_id
        ).first()
        if not rec:
            raise HTTPException(status_code=404, detail=f"Backtest run '{run_id}' not found.")

        response = {
            "run_id": rec.run_id,
            "strategy_id": rec.strategy_id,
            "strategy_version": rec.strategy_version,
            "status": rec.status,
            "start_date": rec.start_date,
            "end_date": rec.end_date,
            "benchmark": rec.benchmark,
            "rebalance_freq": rec.rebalance_freq,
            "weighting_scheme": rec.weighting_scheme,
            "initial_capital": rec.initial_capital,
            "execution_time_sec": rec.execution_time_sec,
            "created_at": rec.created_at,
            "error_msg": rec.error_msg,
            "versioning": {
                "engine_version": rec.engine_version,
                "strategy_version_tag": rec.strategy_version_tag,
                "snapshot_version_tag": rec.snapshot_version_tag,
                "feature_registry_ver": rec.feature_registry_ver,
                "model_version_tag": rec.model_version_tag,
            },
        }

        # Parse stored JSON blobs
        if rec.summary_json:
            try:
                response["summary"] = json.loads(rec.summary_json)
            except Exception:
                response["summary"] = {}

        if rec.metrics_json:
            try:
                response.update(json.loads(rec.metrics_json))
            except Exception:
                pass

        if rec.execution_log_json:
            try:
                response["execution_log"] = json.loads(rec.execution_log_json)
            except Exception:
                response["execution_log"] = []

        return JSONResponse(content=response)
    finally:
        session.close()


# ── GET /api/backtest/history ─────────────────────────────────────────────────

@router.get("/history")
def list_backtest_history(strategy_id: Optional[str] = Query(None)):
    """List all backtest runs, optionally filtered by strategy_id."""
    session = db.get_db_session()
    try:
        from app.models.orm import StrategyBacktestRun, StrategyMaster
        query = session.query(StrategyBacktestRun)
        if strategy_id:
            query = query.filter(StrategyBacktestRun.strategy_id == strategy_id)
        runs = query.order_by(StrategyBacktestRun.created_at.desc()).limit(100).all()

        result = []
        for rec in runs:
            summary = {}
            if rec.summary_json:
                try:
                    summary = json.loads(rec.summary_json)
                except Exception:
                    pass

            # Fetch strategy name
            strat = session.query(StrategyMaster).filter(
                StrategyMaster.strategy_id == rec.strategy_id
            ).first()

            result.append({
                "run_id": rec.run_id,
                "strategy_id": rec.strategy_id,
                "strategy_name": strat.strategy_name if strat else "Unknown",
                "status": rec.status,
                "start_date": rec.start_date,
                "end_date": rec.end_date,
                "benchmark": rec.benchmark,
                "rebalance_freq": rec.rebalance_freq,
                "weighting_scheme": rec.weighting_scheme,
                "created_at": rec.created_at,
                "execution_time_sec": rec.execution_time_sec,
                "summary": summary,
            })
        return result
    finally:
        session.close()


# ── DELETE /api/backtest/{run_id} ─────────────────────────────────────────────

@router.delete("/{run_id}")
def delete_backtest_run(run_id: str):
    """Delete a backtest run and its associated report files."""
    session = db.get_db_session()
    try:
        from app.models.orm import StrategyBacktestRun
        rec = session.query(StrategyBacktestRun).filter(
            StrategyBacktestRun.run_id == run_id
        ).first()
        if not rec:
            raise HTTPException(status_code=404, detail=f"Backtest run '{run_id}' not found.")
        session.delete(rec)
        session.commit()

        # Remove report files
        for ext in ("json", "html", "pdf"):
            fpath = os.path.join(REPORTS_DIR, f"{run_id}.{ext}")
            if os.path.exists(fpath):
                try:
                    os.remove(fpath)
                except Exception:
                    pass

        return {"message": f"Backtest run {run_id} deleted.", "run_id": run_id}
    finally:
        session.close()


# ── POST /api/backtest/validate ───────────────────────────────────────────────

@router.post("/validate")
def validate_strategy(payload: dict):
    """
    Run strategy validation only (no simulation).
    Payload: {strategy_id, definition, strategy_name?, strategy_version?}
    """
    strategy_id = payload.get("strategy_id", "")
    definition = payload.get("definition", {})
    strategy_name = payload.get("strategy_name", "")
    strategy_version = payload.get("strategy_version", "1.0.0")

    if not strategy_id:
        raise HTTPException(status_code=422, detail="strategy_id is required.")
    if not definition:
        # Load from DB
        session = db.get_db_session()
        try:
            from app.models.orm import StrategyMaster
            rec = session.query(StrategyMaster).filter(
                StrategyMaster.strategy_id == strategy_id
            ).first()
            if not rec:
                raise HTTPException(status_code=404, detail=f"Strategy '{strategy_id}' not found.")
            strategy_name = rec.strategy_name
            strategy_version = rec.version or "1.0.0"
            try:
                definition = json.loads(rec.strategy_definition or "{}")
            except Exception:
                definition = {}
        finally:
            session.close()

    try:
        report = run_validation(
            strategy_id=strategy_id,
            definition=definition,
            strategy_name=strategy_name,
            strategy_version=strategy_version,
            persist=True,
        )
        return report
    except Exception as e:
        logger.exception("[BacktestRouter] /validate error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ── GET /api/backtest/{run_id}/report ─────────────────────────────────────────

@router.get("/{run_id}/report")
def download_report(run_id: str, format: str = Query("json", description="json | html | pdf")):
    """Download the backtest report in the requested format."""
    if format not in ("json", "html", "pdf"):
        raise HTTPException(status_code=422, detail="format must be one of: json, html, pdf")

    fpath = os.path.join(REPORTS_DIR, f"{run_id}.{format}")
    if not os.path.exists(fpath):
        # For JSON, fall back to returning the stored DB result
        if format == "json":
            return get_backtest_result(run_id)
        raise HTTPException(
            status_code=404,
            detail=f"Report file not found for run {run_id}. "
                   "Generate a report first via POST /api/backtest/{run_id}/generate-report."
        )

    media_types = {
        "json": "application/json",
        "html": "text/html",
        "pdf": "application/pdf",
    }
    return FileResponse(
        path=fpath,
        media_type=media_types[format],
        filename=f"backtest_{run_id}.{format}",
    )
