"""
lab_experiments.py — API Router for master experiment registry management.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from app.services.json_response import SafeJSONResponse

from app.lab.db_lab import (
    get_experiment,
    list_experiments,
    get_experiments_summary,
    delete_experiment,
)


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/lab/experiments", tags=["lab-experiments"])


@router.get("")
async def query_experiments(
    module: Optional[str] = Query(None, description="Filter by lab module"),
    status: Optional[str] = Query(None, description="Filter by status (pending, running, complete, failed)"),
    symbol: Optional[str] = Query(None, description="Filter by stock ticker"),
    limit: int = Query(50, ge=1, le=200, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """List experiments with optional filters (module, status, symbol) ordered by start time descending."""
    try:
        return list_experiments(
            module=module,
            status=status,
            symbol=symbol,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        logger.error(f"Error querying experiments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_summary():
    """Get count summaries of all experiments grouped by module and status."""
    try:
        return get_experiments_summary()
    except Exception as e:
        logger.error(f"Error loading experiments summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/running")
async def get_running_experiments():
    """List all currently active (running) experiments."""
    try:
        return list_experiments(status="running", limit=100)
    except Exception as e:
        logger.error(f"Error listing running experiments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{exp_id}")
async def get_detail(exp_id: str):
    """Get full details of a specific experiment (including metrics and charts)."""
    exp = get_experiment(exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return exp


@router.delete("/{exp_id}")
async def delete_exp(exp_id: str):
    """Hard-delete an experiment and all associated metrics, charts, and weight snapshots."""
    success = delete_experiment(exp_id)
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to delete experiment. It may not exist."
        )
    return {"message": f"Experiment {exp_id} successfully deleted."}


@router.get("/{exp_id}/export")
async def export_exp(exp_id: str):
    """Export the full experiment configuration and output variables as a downloadable JSON file."""
    exp = get_experiment(exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    headers = {
        "Content-Disposition": f"attachment; filename=experiment_{exp_id}.json"
    }
    return SafeJSONResponse(content=exp, headers=headers)

