"""
Reports Router — API endpoints for research report generation and retrieval.
Supports Stock, Workspace, and Market report generation with PDF/HTML export.
"""

import os
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

from app.services import report_generator

router = APIRouter(tags=["reports"])


# ── STOCK REPORT DIRECT EXPORTS ──

@router.get("/reports/stock/{symbol}/pdf")
async def export_stock_report_pdf(symbol: str):
    """Generate and directly export a stock research report in PDF format."""
    result = report_generator.generate_stock_report(symbol)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Stock '{symbol}' not found in scanner universe.")
    pdf_path = result.get("pdf_path")
    if pdf_path is None or not os.path.exists(pdf_path):
        raise HTTPException(status_code=500, detail="Failed to generate PDF report.")
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"Research_Report_{symbol.upper()}.pdf"
    )


@router.get("/reports/stock/{symbol}/html")
async def export_stock_report_html(symbol: str):
    """Generate and directly export a stock research report in HTML format."""
    result = report_generator.generate_stock_report(symbol)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Stock '{symbol}' not found in scanner universe.")
    html_path = result.get("html_path")
    if html_path is None or not os.path.exists(html_path):
        raise HTTPException(status_code=500, detail="Failed to generate HTML report.")
    return FileResponse(
        path=html_path,
        media_type="text/html",
        filename=f"Research_Report_{symbol.upper()}.html"
    )


@router.get("/reports/stock/{symbol}")
async def generate_stock_report(symbol: str):
    """Generate an institutional stock research report."""
    result = report_generator.generate_stock_report(symbol)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Stock '{symbol}' not found in scanner universe.")
    return result


# ── WORKSPACE REPORT DIRECT EXPORTS ──

@router.get("/reports/workspace/pdf")
async def export_workspace_report_pdf():
    """Generate and directly export a research workspace report in PDF format."""
    result = report_generator.generate_workspace_report()
    pdf_path = result.get("pdf_path")
    if pdf_path is None or not os.path.exists(pdf_path):
        raise HTTPException(status_code=500, detail="Failed to generate PDF workspace report.")
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename="Research_Workspace_Report.pdf"
    )


@router.get("/reports/workspace/html")
async def export_workspace_report_html():
    """Generate and directly export a research workspace report in HTML format."""
    result = report_generator.generate_workspace_report()
    html_path = result.get("html_path")
    if html_path is None or not os.path.exists(html_path):
        raise HTTPException(status_code=500, detail="Failed to generate HTML workspace report.")
    return FileResponse(
        path=html_path,
        media_type="text/html",
        filename="Research_Workspace_Report.html"
    )


@router.get("/reports/workspace")
async def generate_workspace_report():
    """Generate a research workspace report."""
    result = report_generator.generate_workspace_report()
    return result


# ── MARKET REPORT DIRECT EXPORTS ──

@router.get("/reports/market/pdf")
async def export_market_report_pdf():
    """Generate and directly export a market overview report in PDF format."""
    result = report_generator.generate_market_report()
    pdf_path = result.get("pdf_path")
    if pdf_path is None or not os.path.exists(pdf_path):
        raise HTTPException(status_code=500, detail="Failed to generate PDF market report.")
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename="Market_Overview_Report.pdf"
    )


@router.get("/reports/market/html")
async def export_market_report_html():
    """Generate and directly export a market overview report in HTML format."""
    result = report_generator.generate_market_report()
    html_path = result.get("html_path")
    if html_path is None or not os.path.exists(html_path):
        raise HTTPException(status_code=500, detail="Failed to generate HTML market report.")
    return FileResponse(
        path=html_path,
        media_type="text/html",
        filename="Market_Overview_Report.html"
    )


@router.get("/reports/market")
async def generate_market_report():
    """Generate a market overview research report."""
    result = report_generator.generate_market_report()
    return result


# ── UTILITIES & LISTING ──

@router.get("/reports/download/{report_id}")
async def download_report(
    report_id: str,
    format: str = Query("pdf", regex="^(pdf|html)$", description="Download format: pdf or html"),
):
    """Download a generated report by ID in PDF or HTML format."""
    path = report_generator.get_report_path(report_id, fmt=format)
    if path is None:
        raise HTTPException(
            status_code=404,
            detail=f"Report '{report_id}' not found in '{format}' format.",
        )

    media_type = "application/pdf" if format == "pdf" else "text/html"
    filename = f"{report_id}.{format}"
    return FileResponse(
        path=path,
        media_type=media_type,
        filename=filename,
    )


@router.get("/reports/preview/{report_id}", response_class=HTMLResponse)
async def preview_report(report_id: str):
    """Return the raw HTML of a generated report for iframe preview."""
    path = report_generator.get_report_path(report_id, fmt="html")
    if path is None:
        raise HTTPException(
            status_code=404,
            detail=f"Report '{report_id}' HTML not found.",
        )
    with open(path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@router.get("/reports/list")
async def list_reports():
    """List all previously generated reports."""
    return report_generator.list_all_reports()
