"""
lab_reports.py — API Router for generating and serving Quant Research Lab reports.
"""

import os
import logging
from typing import Dict, Optional, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field

from app.lab.db_lab import (
    list_lab_reports,
    get_lab_report,
)
from app.lab.lab_report_generator import generate_lab_report

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/lab/reports", tags=["lab-reports"])


class ReportGenerateRequest(BaseModel):
    experiment_id: Optional[str] = Field(
        None,
        description="Experiment ID to generate report for. Optional for recommendation validation report.",
        example="287807d4-09ea-4dfd-9304-20b151fb789d",
    )
    report_type: str = Field(
        ...,
        description="Type of report: 'indicator', 'model', 'portfolio', 'validation', 'engine'",
        example="indicator",
    )


def _generate_report_task(experiment_id: Optional[str], report_type: str):
    """Synchronous core runner wrapper for background report generation."""
    logger.info(f"Generating report of type '{report_type}' in background...")
    try:
        generate_lab_report(experiment_id=experiment_id, report_type=report_type)
    except Exception as e:
        logger.error(f"Error generating report in background: {e}")


@router.get("")
async def list_reports():
    """List all generated lab reports ordered by generation date descending."""
    try:
        return list_lab_reports()
    except Exception as e:
        logger.error(f"Error listing lab reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate")
async def generate_report(req: ReportGenerateRequest, background_tasks: BackgroundTasks):
    """Trigger an async task to generate a research report. Returns a success message."""
    try:
        background_tasks.add_task(
            _generate_report_task,
            experiment_id=req.experiment_id,
            report_type=req.report_type,
        )
        return {"status": "started", "message": f"Report generation of type '{req.report_type}' started."}
    except Exception as e:
        logger.error(f"Error starting report generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{report_id}/html")
async def serve_html(report_id: str):
    """Serve the raw HTML report file for download or rendering."""
    report = get_lab_report(report_id)
    if not report or not report.get("html_path"):
        raise HTTPException(status_code=404, detail="Report HTML not found")
    
    path = report["html_path"]
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Report HTML file does not exist on disk")
        
    return FileResponse(
        path,
        media_type="text/html",
        filename=f"report_{report_id}.html"
    )


@router.get("/{report_id}/pdf")
async def serve_pdf(report_id: str):
    """Serve the generated PDF report file."""
    report = get_lab_report(report_id)
    if not report or not report.get("pdf_path"):
        raise HTTPException(status_code=404, detail="Report PDF not found")
    
    path = report["pdf_path"]
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Report PDF file does not exist on disk")
        
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=f"report_{report_id}.pdf"
    )


@router.get("/{report_id}/preview", response_class=HTMLResponse)
async def serve_preview(report_id: str):
    """Serve the HTML report content inline as an HTMLResponse (for previews in iframe)."""
    report = get_lab_report(report_id)
    if not report or not report.get("html_path"):
        raise HTTPException(status_code=404, detail="Report HTML not found")
    
    path = report["html_path"]
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Report HTML file does not exist on disk")
        
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content, status_code=200)
    except Exception as e:
        logger.error(f"Error reading HTML preview for report {report_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to read report preview")

