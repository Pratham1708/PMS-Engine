"""
snapshot.py — Snapshot API Router for Phase 13.

Provides 30+ endpoints for:
  - Pipeline control (trigger, monitor)
  - Latest snapshot data (summary, stocks, breadth, sectors, watchlists, changes)
  - Historical archive (dates, per-date data)
  - Comparison (two-date diffs)
  - Data quality and validation
  - Report generation links
"""

import asyncio
import logging
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from app.models.schemas import (
    CompareSnapshotResponse,
    DataQualityResponse,
    MarketBreadthResponse,
    PipelineStatusResponse,
    RecommendationChange,
    SectorSnapshotRecord,
    SnapshotMeta,
    SnapshotStatusResponse,
    SnapshotStockRecord,
    SnapshotSummary,
    ValidationResult,
    WatchlistEntry,
    WatchlistResponse,
)
from app.services import db
from app.services.pipeline_monitor import get_monitor
from app.services.snapshot_pipeline import (
    WATCHLIST_DEFINITIONS,
    run_pipeline,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["snapshot"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _meta_from_db(row: dict) -> SnapshotMeta:
    return SnapshotMeta(
        snapshot_id=row["snapshot_id"],
        pipeline_run_id=row.get("pipeline_run_id"),
        snapshot_date=row["snapshot_date"],
        market_date=row["market_date"],
        generated_at=row["generated_at"],
        is_official=bool(row.get("is_official", 1)),
        status=row.get("status", "unknown"),
        stocks_processed=row.get("stocks_processed", 0),
        stocks_failed=row.get("stocks_failed", 0),
        universe_version=row.get("universe_version"),
        engine_version=row.get("engine_version"),
        indicator_version=row.get("indicator_version"),
        scoring_version=row.get("scoring_version"),
        ml_model_version=row.get("ml_model_version"),
        feature_version=row.get("feature_version"),
        software_build=row.get("software_build"),
        pipeline_started_at=row.get("pipeline_started_at"),
        pipeline_ended_at=row.get("pipeline_ended_at"),
        pipeline_duration_sec=row.get("pipeline_duration_sec"),
        validation_passed=bool(row.get("validation_passed", 0)),
        validation_score=row.get("validation_score"),
        published_at=row.get("published_at"),
        notes=row.get("notes"),
    )


def _stock_from_db(row: dict) -> SnapshotStockRecord:
    return SnapshotStockRecord(**{
        k: row.get(k) for k in SnapshotStockRecord.model_fields
    })


def _breadth_from_db(row: dict) -> MarketBreadthResponse:
    return MarketBreadthResponse(**{
        k: row.get(k) for k in MarketBreadthResponse.model_fields
    })


def _sector_from_db(row: dict) -> SectorSnapshotRecord:
    return SectorSnapshotRecord(**{
        k: row.get(k) for k in SectorSnapshotRecord.model_fields
    })


def _require_latest() -> dict:
    snap = db.get_latest_snapshot()
    if not snap:
        raise HTTPException(
            status_code=404,
            detail="No official snapshot available. Use POST /api/snapshot/generate to create one."
        )
    return snap


def _require_by_date(date: str) -> dict:
    snap = db.get_snapshot_by_date(date)
    if not snap:
        raise HTTPException(status_code=404, detail=f"No snapshot found for date '{date}'")
    return snap


def _compute_freshness(snapshot_date: str) -> str:
    """Compute data freshness label from snapshot_date."""
    import pytz
    from datetime import datetime, timedelta
    try:
        today = datetime.now(pytz.timezone("Asia/Kolkata")).date()
        snap_date = datetime.strptime(snapshot_date, "%Y-%m-%d").date()
        days_old = (today - snap_date).days
        if days_old == 0:
            return "fresh"
        elif days_old == 1:
            return "recent"
        elif days_old <= 3:
            return "aging"
        else:
            return "stale"
    except Exception:
        return "unknown"


def _watchlist_with_meta(wl_name: str, entries: List[dict]) -> WatchlistResponse:
    wl_def = WATCHLIST_DEFINITIONS.get(wl_name, {})
    return WatchlistResponse(
        watchlist_name=wl_name,
        display_name=wl_def.get("display_name", wl_name.replace("_", " ").title()),
        description=wl_def.get("description", ""),
        stocks=[
            WatchlistEntry(
                symbol=e["symbol"],
                rank_in_list=e["rank_in_list"],
                score_used=e.get("score_used"),
                reason=e.get("reason"),
            )
            for e in entries
        ],
    )


# ── Pipeline Control ──────────────────────────────────────────────────────────

@router.post("/snapshot/generate")
async def generate_snapshot(
    background_tasks: BackgroundTasks,
    date: Optional[str] = Query(None, description="Target date in YYYY-MM-DD format")
):
    """
    Trigger the official daily snapshot pipeline.
    Runs asynchronously in the background.
    Poll GET /snapshot/pipeline/status for progress.
    """
    monitor = get_monitor()
    if monitor.status == "running":
        raise HTTPException(
            status_code=409,
            detail=f"Pipeline is already running. Monitor at GET /api/snapshot/pipeline/status. "
                   f"Snapshot: {monitor.snapshot_id}"
        )

    def _run():
        try:
            run_pipeline(is_official=True, snapshot_date=date)
        except Exception as e:
            logger.error(f"[SnapshotAPI] Pipeline raised exception: {e}", exc_info=True)

    background_tasks.add_task(_run)
    return {
        "status": "started",
        "message": f"Official snapshot pipeline started in background for date {date or 'today'}. "
                   "Poll GET /api/snapshot/pipeline/status for progress.",
        "monitor_url": "/api/snapshot/pipeline/status",
    }


@router.post("/snapshot/live-analysis")
async def trigger_live_analysis(background_tasks: BackgroundTasks):
    """
    Trigger a non-official live analysis snapshot.
    This never overwrites the official daily snapshot.
    """
    monitor = get_monitor()
    if monitor.status == "running":
        raise HTTPException(
            status_code=409,
            detail="Pipeline is already running. Wait for it to complete before running live analysis."
        )

    def _run():
        try:
            run_pipeline(is_official=False)
        except Exception as e:
            logger.error(f"[SnapshotAPI] Live analysis raised exception: {e}", exc_info=True)

    background_tasks.add_task(_run)
    return {
        "status": "started",
        "message": "Live analysis pipeline started. This will NOT overwrite the official snapshot.",
        "monitor_url": "/api/snapshot/pipeline/status",
    }


@router.get("/snapshot/pipeline/status", response_model=PipelineStatusResponse)
async def get_pipeline_status():
    """Return real-time pipeline monitor state."""
    monitor = get_monitor()
    return PipelineStatusResponse(**monitor.to_dict())


@router.get("/snapshot/pipeline/{snapshot_id}")
async def get_pipeline_timeline(snapshot_id: str):
    """Return stored pipeline stage execution timeline for a specific snapshot."""
    snap = db.get_snapshot_by_id(snapshot_id)
    if not snap:
        raise HTTPException(status_code=404, detail=f"Snapshot '{snapshot_id}' not found")
    stages = db.get_snapshot_pipeline(snapshot_id)
    return {
        "snapshot_id": snapshot_id,
        "snapshot_date": snap["snapshot_date"],
        "status": snap["status"],
        "pipeline_duration_sec": snap.get("pipeline_duration_sec"),
        "stages": stages,
    }


# ── System Status ─────────────────────────────────────────────────────────────

@router.get("/snapshot/status", response_model=SnapshotStatusResponse)
async def get_snapshot_status():
    """Return system-level snapshot status (latest date, count, freshness, pipeline state)."""
    summary = db.get_snapshot_status_summary()
    latest_row = summary.get("latest_snapshot")
    latest_meta = _meta_from_db(latest_row) if latest_row else None
    freshness = _compute_freshness(latest_meta.snapshot_date) if latest_meta else "no_data"
    monitor = get_monitor()
    return SnapshotStatusResponse(
        latest_snapshot=latest_meta,
        total_snapshots=summary.get("total_snapshots", 0),
        in_progress=summary.get("in_progress", 0),
        data_freshness=freshness,
        pipeline_available=(monitor.status != "running"),
    )


@router.get("/snapshot/freshness")
async def get_snapshot_freshness():
    """
    Expose data freshness information (latest trading date, last successful pipeline run, pipeline status)
    so the frontend can display when the data was last updated.
    """
    summary = db.get_snapshot_status_summary()
    latest_row = summary.get("latest_snapshot")
    latest_meta = _meta_from_db(latest_row) if latest_row else None
    
    if not latest_meta:
        return {
            "latest_trading_date": None,
            "last_successful_run": None,
            "pipeline_status": "no_data",
            "data_freshness": "no_data",
        }
        
    return {
        "latest_trading_date": latest_meta.snapshot_date,
        "last_successful_run": latest_meta.published_at or latest_meta.pipeline_ended_at or latest_meta.generated_at,
        "pipeline_status": latest_meta.status,
        "data_freshness": _compute_freshness(latest_meta.snapshot_date),
    }


@router.get("/system/status")
async def get_system_status():
    """
    Return comprehensive system health and dashboard details, including:
      - Database status & connection status (PostgreSQL/SQLite)
      - Scheduler status (cron scheduler running, active jobs)
      - Last successful pipeline run metadata
      - Latest trading date
      - Freshness details
    """
    from app.services.scheduler import _scheduler
    
    # 1. Database Health Check
    db_alive = False
    db_dialect = "SQLite" if not db.DATABASE_URL else "PostgreSQL"
    try:
        conn = db.get_db_connection()
        row = conn.execute("SELECT 1").fetchone()
        if row and row[0] == 1:
            db_alive = True
        conn.close()
    except Exception as e:
        logger.error(f"Database health check failed: {e}")

    # 2. Scheduler Health Check
    sched_running = _scheduler.running if hasattr(_scheduler, "running") else False
    active_jobs = []
    if sched_running:
        for job in _scheduler.get_jobs():
            active_jobs.append({
                "id": job.id,
                "next_run_time": str(job.next_run_time) if job.next_run_time else None
            })

    # 3. Snapshot and Pipeline Freshness
    summary = db.get_snapshot_status_summary()
    latest_row = summary.get("latest_snapshot")
    latest_meta = _meta_from_db(latest_row) if latest_row else None
    
    freshness = _compute_freshness(latest_meta.snapshot_date) if latest_meta else "no_data"
    
    return {
        "database": {
            "status": "healthy" if db_alive else "unhealthy",
            "dialect": db_dialect,
            "connected": db_alive
        },
        "scheduler": {
            "status": "running" if sched_running else "stopped",
            "running": sched_running,
            "active_jobs": active_jobs
        },
        "freshness": {
            "latest_trading_date": latest_meta.snapshot_date if latest_meta else None,
            "last_successful_run": latest_meta.published_at or latest_meta.pipeline_ended_at or latest_meta.generated_at if latest_meta else None,
            "data_freshness": freshness,
            "pipeline_status": latest_meta.status if latest_meta else "no_data",
            "pipeline_duration_sec": latest_meta.pipeline_duration_sec if latest_meta else None,
            "total_stocks": latest_meta.stocks_processed if latest_meta else 0,
            "failed_stocks": latest_meta.stocks_failed if latest_meta else 0,
            "universe_version": latest_meta.universe_version if latest_meta else None,
            "engine_version": latest_meta.engine_version if latest_meta else None,
        }
    }



# ── Latest Snapshot Endpoints ─────────────────────────────────────────────────

@router.get("/snapshot/latest", response_model=SnapshotMeta)
async def get_latest_snapshot():
    """Return the latest official snapshot metadata."""
    snap = _require_latest()
    return _meta_from_db(snap)


@router.get("/snapshot/latest/summary")
async def get_latest_summary():
    """Return a full dashboard summary for the latest snapshot."""
    snap = _require_latest()
    sid = snap["snapshot_id"]
    meta = _meta_from_db(snap)

    breadth_row = db.get_snapshot_market(sid)
    breadth = _breadth_from_db(breadth_row) if breadth_row else None

    sector_rows = db.get_snapshot_sector(sid)
    sectors = [_sector_from_db(r) for r in sector_rows[:5]]

    stock_rows = db.get_snapshot_stocks(sid)
    top_stocks = [_stock_from_db(r) for r in stock_rows if r.get("final_rating") in ("STRONG BUY", "BUY")][:10]

    changes = db.get_snapshot_changes(sid)
    changes_summary = {
        "total": len(changes),
        "upgrades": sum(1 for c in changes if c["change_type"] == "UPGRADE"),
        "downgrades": sum(1 for c in changes if c["change_type"] == "DOWNGRADE"),
        "new_buys": sum(1 for c in changes if c["change_type"] == "NEW_BUY"),
        "new_sells": sum(1 for c in changes if c["change_type"] == "NEW_SELL"),
    }

    validations = db.get_snapshot_validations(sid)
    val_summary = {
        "pass": sum(1 for v in validations if v["status"] == "pass"),
        "warning": sum(1 for v in validations if v["status"] == "warning"),
        "fail": sum(1 for v in validations if v["status"] == "fail"),
        "score": snap.get("validation_score"),
    }

    stages = db.get_snapshot_pipeline(sid)
    pipeline_summary = {
        "total_stages": len(stages),
        "completed": sum(1 for s in stages if s["stage_status"] == "done"),
        "with_warnings": sum(1 for s in stages if s["stage_status"] == "done_with_warnings"),
        "failed": sum(1 for s in stages if s["stage_status"] == "failed"),
        "duration_sec": snap.get("pipeline_duration_sec"),
    }

    return {
        "meta": meta,
        "breadth": breadth,
        "sectors": sectors,
        "top_opportunities": top_stocks,
        "changes_summary": changes_summary,
        "validation_summary": val_summary,
        "pipeline_summary": pipeline_summary,
    }


@router.get("/snapshot/latest/stocks", response_model=List[SnapshotStockRecord])
async def get_latest_stocks():
    """Return all stock records from the latest official snapshot."""
    snap = _require_latest()
    rows = db.get_snapshot_stocks(snap["snapshot_id"])
    return [_stock_from_db(r) for r in rows]


@router.get("/snapshot/latest/stock/{symbol}", response_model=SnapshotStockRecord)
async def get_latest_stock(symbol: str):
    """Return a single stock from the latest official snapshot."""
    snap = _require_latest()
    row = db.get_snapshot_stock(snap["snapshot_id"], symbol)
    if not row:
        raise HTTPException(status_code=404, detail=f"Stock '{symbol}' not in latest snapshot")
    return _stock_from_db(row)


@router.get("/snapshot/latest/breadth", response_model=MarketBreadthResponse)
async def get_latest_breadth():
    """Return market breadth metrics from the latest official snapshot."""
    snap = _require_latest()
    row = db.get_snapshot_market(snap["snapshot_id"])
    if not row:
        raise HTTPException(status_code=404, detail="Market breadth data not available for latest snapshot")
    return _breadth_from_db(row)


@router.get("/snapshot/latest/sectors", response_model=List[SectorSnapshotRecord])
async def get_latest_sectors():
    """Return sector rankings from the latest official snapshot."""
    snap = _require_latest()
    rows = db.get_snapshot_sector(snap["snapshot_id"])
    return [_sector_from_db(r) for r in rows]


@router.get("/snapshot/latest/watchlists", response_model=List[WatchlistResponse])
async def get_latest_watchlists():
    """Return all auto-generated watchlists from the latest official snapshot."""
    snap = _require_latest()
    rows = db.get_snapshot_watchlists(snap["snapshot_id"])
    # Group by watchlist_name
    grouped: dict = {}
    for row in rows:
        wl = row["watchlist_name"]
        grouped.setdefault(wl, []).append(row)
    return [_watchlist_with_meta(name, entries) for name, entries in grouped.items()]


@router.get("/snapshot/latest/watchlist/{watchlist_name}", response_model=WatchlistResponse)
async def get_latest_watchlist(watchlist_name: str):
    """Return a specific watchlist from the latest official snapshot."""
    snap = _require_latest()
    rows = db.get_snapshot_watchlists(snap["snapshot_id"], watchlist_name=watchlist_name)
    return _watchlist_with_meta(watchlist_name, rows)


@router.get("/snapshot/latest/changes", response_model=List[RecommendationChange])
async def get_latest_changes(
    change_type: Optional[str] = Query(None, description="Filter by change_type"),
    significant_only: bool = Query(False, description="Return only significant changes"),
):
    """Return recommendation changes from the latest official snapshot."""
    snap = _require_latest()
    rows = db.get_snapshot_changes(
        snap["snapshot_id"],
        change_type=change_type,
        significant_only=significant_only
    )
    return [RecommendationChange(**{
        k: r.get(k) for k in RecommendationChange.model_fields
    }) for r in rows]


@router.get("/snapshot/latest/validation", response_model=List[ValidationResult])
async def get_latest_validation():
    """Return validation check results for the latest snapshot."""
    snap = _require_latest()
    rows = db.get_snapshot_validations(snap["snapshot_id"])
    return [ValidationResult(**{k: r.get(k) for k in ValidationResult.model_fields}) for r in rows]


@router.get("/snapshot/latest/pipeline")
async def get_latest_pipeline():
    """Return pipeline stage timeline for the latest snapshot."""
    snap = _require_latest()
    stages = db.get_snapshot_pipeline(snap["snapshot_id"])
    return {"snapshot_id": snap["snapshot_id"], "stages": stages}


@router.get("/snapshot/latest/reports")
async def get_latest_reports():
    """Return report links for the latest snapshot."""
    snap = _require_latest()
    return db.get_snapshot_reports(snap["snapshot_id"])


@router.get("/snapshot/latest/data-quality", response_model=DataQualityResponse)
async def get_latest_data_quality():
    """Return data quality summary for the latest official snapshot."""
    snap = _require_latest()
    sid = snap["snapshot_id"]
    stocks = db.get_snapshot_stocks(sid)
    validations = db.get_snapshot_validations(sid)

    total = len(stocks)
    failed = [s for s in stocks if s.get("download_status") == "failed"]
    cached = [s for s in stocks if s.get("data_source") == "mock"]
    live = [s for s in stocks if s.get("data_source") == "yfinance"]
    coverage = (total - len(failed)) / max(total, 1) * 100

    val_pass = sum(1 for v in validations if v["status"] == "pass")
    val_warn = sum(1 for v in validations if v["status"] == "warning")
    val_fail = sum(1 for v in validations if v["status"] == "fail")

    health_score = snap.get("validation_score") or 0.0
    if health_score >= 85:
        status = "healthy"
    elif health_score >= 60:
        status = "degraded"
    else:
        status = "critical"

    # Freshness in hours
    import pytz
    from datetime import datetime
    try:
        gen_time = datetime.fromisoformat(snap["generated_at"])
        if gen_time.tzinfo is None:
            gen_time = pytz.timezone("Asia/Kolkata").localize(gen_time)
        freshness_hours = (datetime.now(pytz.timezone("Asia/Kolkata")) - gen_time).total_seconds() / 3600
    except Exception:
        freshness_hours = None

    return DataQualityResponse(
        snapshot_id=sid,
        snapshot_date=snap["snapshot_date"],
        health_score=health_score,
        coverage_pct=round(coverage, 1),
        universe_size=total,
        downloaded_count=total - len(failed),
        failed_count=len(failed),
        cached_count=len(cached),
        live_count=len(live),
        mock_count=len(cached),
        freshness_hours=round(freshness_hours, 1) if freshness_hours is not None else None,
        validation_checks=[
            ValidationResult(**{k: v.get(k) for k in ValidationResult.model_fields})
            for v in validations
        ],
        validation_pass_count=val_pass,
        validation_warn_count=val_warn,
        validation_fail_count=val_fail,
        failed_symbols=[s["symbol"] for s in failed],
        status=status,
    )


# ── Comparison ────────────────────────────────────────────────────────────────

@router.get("/snapshot/compare", response_model=CompareSnapshotResponse)
async def compare_snapshots(
    date1: str = Query(..., description="First date, UUID, or keyword ('latest', 'previous')"),
    date2: str = Query(..., description="Second date, UUID, or keyword ('latest', 'previous')"),
    strategy_id: str = Query("pms_default", description="Strategy ID to compare")
):
    """Compare two snapshots side-by-side."""
    from app.services.comparison_service import ComparisonEngine
    try:
        res = ComparisonEngine.run_comparison(
            snap1_sel=date1,
            snap2_sel=date2,
            strategy_id=strategy_id,
            official_only=True
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in snapshot comparison: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error comparing snapshots: {e}")


@router.get("/snapshot/compare/trend")
async def compare_snapshot_trend(
    symbols: List[str] = Query(..., description="List of stock symbols to trace"),
    limit: int = Query(10, ge=2, le=90, description="Max snapshot dates to trace")
):
    """Trace composite score trajectories over the last N snapshots for a list of stocks."""
    from app.services.comparison_service import HistoricalTrendEngine
    try:
        res = HistoricalTrendEngine.get_trajectory_history(symbols, limit=limit)
        return res
    except Exception as e:
        logger.error(f"Error in comparison trend: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/snapshot/compare/stock")
async def compare_stock_across_dates(
    symbol: str = Query(...),
    limit: int = Query(90, ge=1, le=365),
):
    """Return a stock's historical data across multiple snapshots."""
    history = db.get_stock_history_across_snapshots(symbol, limit=limit)
    if not history:
        raise HTTPException(status_code=404, detail=f"No snapshot history found for '{symbol}'")
    return {"symbol": symbol, "history": history, "count": len(history)}


# ── Historical Archive ────────────────────────────────────────────────────────

@router.get("/snapshot/dates")
async def list_snapshot_dates(limit: int = Query(365, ge=1, le=1000)):
    """List all available official snapshot dates (newest first)."""
    dates = db.list_snapshot_dates(official_only=True, limit=limit)
    return {"dates": dates, "total": len(dates)}


@router.get("/snapshot/{date}", response_model=SnapshotMeta)
async def get_snapshot_by_date(date: str):
    """Return snapshot metadata for a specific market date (YYYY-MM-DD)."""
    snap = _require_by_date(date)
    return _meta_from_db(snap)


@router.get("/snapshot/{date}/stocks", response_model=List[SnapshotStockRecord])
async def get_snapshot_stocks_by_date(date: str):
    """Return all stock records for a historical snapshot date."""
    snap = _require_by_date(date)
    rows = db.get_snapshot_stocks(snap["snapshot_id"])
    return [_stock_from_db(r) for r in rows]


@router.get("/snapshot/{date}/breadth", response_model=MarketBreadthResponse)
async def get_snapshot_breadth_by_date(date: str):
    """Return market breadth for a historical snapshot date."""
    snap = _require_by_date(date)
    row = db.get_snapshot_market(snap["snapshot_id"])
    if not row:
        raise HTTPException(status_code=404, detail=f"No breadth data for date '{date}'")
    return _breadth_from_db(row)


@router.get("/snapshot/{date}/sectors", response_model=List[SectorSnapshotRecord])
async def get_snapshot_sectors_by_date(date: str):
    """Return sector rankings for a historical snapshot date."""
    snap = _require_by_date(date)
    rows = db.get_snapshot_sector(snap["snapshot_id"])
    return [_sector_from_db(r) for r in rows]


@router.get("/snapshot/{date}/changes", response_model=List[RecommendationChange])
async def get_snapshot_changes_by_date(date: str):
    """Return recommendation changes for a historical snapshot date."""
    snap = _require_by_date(date)
    rows = db.get_snapshot_changes(snap["snapshot_id"])
    return [RecommendationChange(**{k: r.get(k) for k in RecommendationChange.model_fields}) for r in rows]


@router.get("/snapshot/{date}/validation", response_model=List[ValidationResult])
async def get_snapshot_validation_by_date(date: str):
    """Return validation results for a historical snapshot date."""
    snap = _require_by_date(date)
    rows = db.get_snapshot_validations(snap["snapshot_id"])
    return [ValidationResult(**{k: r.get(k) for k in ValidationResult.model_fields}) for r in rows]


@router.get("/snapshot/{date}/pipeline")
async def get_snapshot_pipeline_by_date(date: str):
    """Return pipeline stage timeline for a historical snapshot date."""
    snap = _require_by_date(date)
    stages = db.get_snapshot_pipeline(snap["snapshot_id"])
    return {"snapshot_id": snap["snapshot_id"], "snapshot_date": date, "stages": stages}


@router.get("/snapshot/{date}/reports")
async def get_snapshot_reports_by_date(date: str):
    """Return report links for a historical snapshot date."""
    snap = _require_by_date(date)
    return db.get_snapshot_reports(snap["snapshot_id"])


# ── Fallback Changes Helper ──────────────────────────────────────────────────

def _get_snapshot_changes_with_fallback(
    snapshot_id: str,
    change_type: Optional[str] = None,
    significant_only: bool = False
) -> List[dict]:
    rows = db.get_snapshot_changes(
        snapshot_id,
        change_type=change_type,
        significant_only=significant_only
    )
    if not rows:
        try:
            from app.services.comparison_service import ComparisonEngine
            prev = db.get_previous_official_snapshot(snapshot_id)
            if prev:
                res = ComparisonEngine.run_comparison(
                    snap1_sel=prev["snapshot_id"],
                    snap2_sel=snapshot_id
                )
                for sd in res["stock_deltas"]:
                    if sd["transition_type"] == "UNCHANGED":
                        continue
                    is_sig = abs(sd["score_changes"].get("composite_score", {}).get("delta", 0.0)) > 5.0 or sd["transition_type"] in ("UPGRADE", "DOWNGRADE")
                    if significant_only and not is_sig:
                        continue
                    if change_type and change_type != "ALL" and sd["transition_type"] != change_type:
                        continue
                    
                    primary = sd["drivers"][0]["feature"] + " change (" + sd["drivers"][0]["change"] + ")" if sd["drivers"] else "No major change"
                    secondary = sd["drivers"][1]["feature"] + " change (" + sd["drivers"][1]["change"] + ")" if len(sd["drivers"]) > 1 else None
                    
                    rows.append({
                        "symbol": sd["symbol"],
                        "change_type": sd["transition_type"],
                        "prev_rating": sd["prev_rating"],
                        "new_rating": sd["new_rating"],
                        "composite_diff": sd["score_changes"].get("composite_score", {}).get("delta"),
                        "confidence_diff": sd["score_changes"].get("confidence_score", {}).get("delta"),
                        "technical_diff": sd["score_changes"].get("technical_score", {}).get("delta"),
                        "ml_diff": sd["score_changes"].get("ensemble_score", {}).get("delta"),
                        "momentum_diff": sd["score_changes"].get("momentum_score", {}).get("delta"),
                        "trend_diff": sd["score_changes"].get("trend_score", {}).get("delta"),
                        "risk_diff": sd["score_changes"].get("risk_score", {}).get("delta"),
                        "primary_driver": primary,
                        "secondary_driver": secondary,
                        "is_significant": 1 if is_sig else 0,
                        "prev_snapshot_id": prev["snapshot_id"]
                    })
        except Exception as e:
            logger.error(f"Fallback changes calculation failed for {snapshot_id}: {e}")
    return rows


@router.get("/snapshot/latest/changes", response_model=List[RecommendationChange])
async def get_latest_changes(
    change_type: Optional[str] = Query(None, description="Filter by change_type"),
    significant_only: bool = Query(False, description="Return only significant changes"),
):
    """Return recommendation changes from the latest official snapshot."""
    snap = _require_latest()
    rows = _get_snapshot_changes_with_fallback(
        snap["snapshot_id"],
        change_type=change_type,
        significant_only=significant_only
    )
    return [RecommendationChange(**{
        k: r.get(k) for k in RecommendationChange.model_fields
    }) for r in rows]


@router.get("/snapshot/{date}/changes", response_model=List[RecommendationChange])
async def get_snapshot_changes_by_date(date: str):
    """Return recommendation changes for a historical snapshot date."""
    snap = _require_by_date(date)
    rows = _get_snapshot_changes_with_fallback(snap["snapshot_id"])
    return [RecommendationChange(**{k: r.get(k) for k in RecommendationChange.model_fields}) for r in rows]


# ── Snapshot Diagnostics Endpoints ───────────────────────────────────────────

@router.get("/snapshot/diagnostics/list")
def get_snapshot_diagnostics(limit: int = Query(100, ge=1, le=1000)):
    """Return list of all snapshots, draft and failures, with record counts."""
    conn = db.get_db_connection()
    try:
        rows = conn.execute(
            f"SELECT * FROM snapshots ORDER BY snapshot_date DESC, generated_at DESC LIMIT {limit}"
        ).fetchall()
        
        diagnostics = []
        for r in rows:
            sid = r["snapshot_id"]
            # Count records in all cascading tables
            stock_cnt = conn.execute("SELECT COUNT(*) FROM snapshot_stock WHERE snapshot_id = ?", (sid,)).fetchone()[0]
            ind_cnt = conn.execute("SELECT COUNT(*) FROM snapshot_indicator WHERE snapshot_id = ?", (sid,)).fetchone()[0]
            score_cnt = conn.execute("SELECT COUNT(*) FROM snapshot_score WHERE snapshot_id = ?", (sid,)).fetchone()[0]
            
            # Find failing validation checks
            failures = conn.execute(
                "SELECT check_name, detail FROM snapshot_validation WHERE snapshot_id = ? AND status = 'fail'",
                (sid,)
            ).fetchall()
            failure_reason = "; ".join([f"{f['check_name']}: {f['detail']}" for f in failures]) if failures else r.get("notes")
            
            diagnostics.append({
                "snapshot_id": sid,
                "snapshot_date": r["snapshot_date"],
                "market_date": r["market_date"],
                "generated_at": r["generated_at"],
                "is_official": bool(r["is_official"]),
                "status": r["status"],
                "stocks_count": stock_cnt,
                "indicators_count": ind_cnt,
                "scores_count": score_cnt,
                "validation_passed": bool(r["validation_passed"]),
                "validation_score": r["validation_score"],
                "failure_reason": failure_reason or "None",
            })
        return diagnostics
    finally:
        conn.close()


@router.delete("/snapshot/{snapshot_id}")
def delete_snapshot(snapshot_id: str):
    """Cascading delete a snapshot and all its metadata from database."""
    conn = db.get_db_connection()
    try:
        # Check if exists
        snap = conn.execute("SELECT * FROM snapshots WHERE snapshot_id = ?", (snapshot_id,)).fetchone()
        if not snap:
            raise HTTPException(status_code=404, detail="Snapshot not found")
        
        # Cascade deletes — all tables that reference snapshot_id directly
        tables = [
            "snapshot_stock", "snapshot_indicator", "snapshot_score", "snapshot_validation",
            "snapshot_metadata", "snapshot_watchlist", "snapshot_change", "snapshot_market",
            "snapshot_sector", "snapshot_report", "explainability_snapshot", "feature_snapshot",
            "indicator_snapshot", "score_snapshot",
        ]
        for tbl in tables:
            try:
                conn.execute(f"DELETE FROM {tbl} WHERE snapshot_id = ?", (snapshot_id,))
            except Exception as e:
                logger.warning(f"Failed to delete cascade from {tbl}: {e}")

        # snapshot_comparisons uses snapshot_id_1/snapshot_id_2 instead of snapshot_id
        try:
            conn.execute(
                "DELETE FROM snapshot_comparisons WHERE snapshot_id_1 = ? OR snapshot_id_2 = ?",
                (snapshot_id, snapshot_id)
            )
        except Exception as e:
            logger.warning(f"Failed to delete cascade from snapshot_comparisons: {e}")

        conn.execute("DELETE FROM snapshots WHERE snapshot_id = ?", (snapshot_id,))
        conn.commit()
        return {"status": "success", "message": f"Snapshot {snapshot_id} deleted successfully."}
    finally:
        conn.close()


@router.post("/snapshot/{snapshot_id}/validate")
def validate_snapshot_endpoint(snapshot_id: str):
    """Force run validation checks on a snapshot date and update status."""
    from app.services.snapshot_validator import run_validation as run_snap_val
    try:
        status, score, checks = run_snap_val(snapshot_id)
        # Update snapshot status
        conn = db.get_db_connection()
        conn.execute(
            "UPDATE snapshots SET status = ?, validation_passed = ?, validation_score = ? WHERE snapshot_id = ?",
            (status, 1 if status in ("completed", "completed_with_warnings") else 0, score, snapshot_id)
        )
        conn.commit()
        conn.close()
        return {"status": status, "score": score, "checks": checks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))







