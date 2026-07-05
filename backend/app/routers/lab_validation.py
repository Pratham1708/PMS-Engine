"""
lab_validation.py — API Router for recommendation validation and audit lab.
"""

import logging
from typing import Dict, List, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field

from app.lab.recommendation_auditor import (
    populate_audit_queue,
    process_pending_validations,
    get_accuracy_dashboard,
    get_symbol_validation,
    accuracy_trend,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/lab/validation", tags=["lab-validation"])


class ProcessValidationRequest(BaseModel):
    batch_size: int = Field(50, ge=1, le=500, description="Number of pending rows to process", examples=[50])


def _process_validations_task(batch_size: int):
    """Synchronous core runner wrapper for background process validations."""
    logger.info(f"Processing validations in background with batch size {batch_size}...")
    try:
        process_pending_validations(batch_size=batch_size)
    except Exception as e:
        logger.error(f"Error in background validation processing: {e}")


@router.post("/populate")
async def populate_queue():
    """Scan all records in analysis_history and populate the audit queue for all horizons."""
    try:
        return populate_audit_queue()
    except Exception as e:
        logger.error(f"Error populating audit queue: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process")
async def process_queue(req: ProcessValidationRequest, background_tasks: BackgroundTasks):
    """Start an async task to validate pending recommendations whose horizons have passed."""
    try:
        background_tasks.add_task(
            _process_validations_task,
            batch_size=req.batch_size,
        )
        return {"status": "started", "batch_size": req.batch_size}
    except Exception as e:
        logger.error(f"Error starting validation process: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
async def get_dashboard():
    """Retrieve the validation audit dashboard containing accuracy by rating and horizon."""
    try:
        return get_accuracy_dashboard()
    except Exception as e:
        logger.error(f"Error loading validation dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/symbol/{symbol}")
async def get_symbol_audit(symbol: str):
    """Retrieve all recommendation audit records for a single symbol."""
    try:
        return get_symbol_validation(symbol)
    except Exception as e:
        logger.error(f"Error loading symbol audit records: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trend")
async def get_trend():
    """Retrieve monthly recommendation accuracy trends."""
    try:
        return accuracy_trend()
    except Exception as e:
        logger.error(f"Error loading accuracy trend: {e}")
        raise HTTPException(status_code=500, detail=str(e))

