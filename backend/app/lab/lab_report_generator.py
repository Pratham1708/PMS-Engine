"""
lab_report_generator.py — Report generation engine for the Quant Research Laboratory.

Generates HTML and PDF versions of research reports for completed experiments,
incorporating metrics, heatmaps, parameter optimization results, and audit statistics.
"""

import os
import io
import uuid
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa

from app.lab.db_lab import (
    get_experiment,
    save_lab_report,
    get_rec_audit_dashboard,
)

logger = logging.getLogger(__name__)

# Resolve Paths
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "templates")
LAB_REPORTS_DIR = os.path.join(BACKEND_DIR, "data", "reports", "lab")

# Ensure lab reports folder exists
os.makedirs(LAB_REPORTS_DIR, exist_ok=True)

# Initialize Jinja2 Env for lab templates
jinja_env = Environment(
    loader=FileSystemLoader(os.path.abspath(TEMPLATES_DIR)),
    autoescape=False,
)

# Add custom formatting filters to Jinja environment
def filter_pct(val: Any) -> str:
    try:
        if val is None or val == "":
            return "N/A"
        f = float(val)
        return f"{f * 100:.2f}%" if abs(f) < 1.0 else f"{f:.2f}%"
    except Exception:
        return str(val)

def filter_decimal(val: Any, precision: int = 2) -> str:
    try:
        if val is None or val == "":
            return "N/A"
        f = float(val)
        return f"{f:.{precision}f}"
    except Exception:
        return str(val)

jinja_env.filters["pct"] = filter_pct
jinja_env.filters["decimal"] = filter_decimal


def _html_to_pdf(html_content: str) -> bytes:
    """Convert HTML string to PDF bytes using xhtml2pdf."""
    result = io.BytesIO()
    pisa_status = pisa.CreatePDF(
        src=html_content,
        dest=result,
        encoding="utf-8",
    )
    if pisa_status.err:
        logger.warning(f"xhtml2pdf reported {pisa_status.err} errors during lab report conversion")
    return result.getvalue()


def generate_lab_report(experiment_id: str, report_type: str) -> Dict[str, Any]:
    """
    Generate a lab report (HTML and PDF) for the given experiment.
    
    Supported report_type values:
      - 'indicator': For indicator backtest + optimization runs
      - 'model': For ML model comparison runs
      - 'portfolio': For portfolio backtesting
      - 'validation': For recommendation audit reports (can be generated without experiment_id)
      - 'engine': For complete PMS Engine validation reports
    """
    report_id = str(uuid.uuid4())
    logger.info(f"Generating lab report {report_id} of type '{report_type}' for experiment {experiment_id}...")

    # Fetch experiment if present
    exp = None
    if experiment_id:
        exp = get_experiment(experiment_id)
        if not exp:
            raise ValueError(f"Experiment {experiment_id} not found in database.")
    
    # Prepare template context
    context: Dict[str, Any] = {
        "report_id": report_id,
        "generated_at": datetime.now().strftime("%d-%b-%Y %I:%M %p"),
        "experiment": exp,
    }

    # Resolve template name and custom context additions
    if report_type == "indicator":
        template_name = "lab_indicator_report.html"
    elif report_type == "model":
        template_name = "lab_model_report.html"
    elif report_type == "portfolio":
        template_name = "lab_portfolio_report.html"
    elif report_type == "engine":
        template_name = "lab_engine_report.html"
    elif report_type == "validation":
        template_name = "lab_validation_report.html"
        # Always inject the latest validation dashboard data for validation audits
        context["audit_dashboard"] = get_rec_audit_dashboard()
    else:
        raise ValueError(f"Unsupported lab report type: {report_type}")

    try:
        # Load and render template
        template = jinja_env.get_template(template_name)
        html_content = template.render(**context)
    except Exception as e:
        logger.error(f"Template rendering failed for {template_name}: {e}")
        raise

    # Define file paths
    html_path = os.path.join(LAB_REPORTS_DIR, f"{report_id}.html")
    pdf_path = os.path.join(LAB_REPORTS_DIR, f"{report_id}.pdf")

    # Save HTML to disk
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # Convert and save PDF to disk
    pdf_success = False
    try:
        pdf_bytes = _html_to_pdf(html_content)
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)
        pdf_success = True
    except Exception as e:
        logger.error(f"PDF generation failed for lab report {report_id}: {e}")
        pdf_path = None

    # Record in SQLite database
    try:
        save_lab_report(
            report_id=report_id,
            experiment_id=experiment_id if experiment_id else None,
            report_type=report_type,
            html_path=html_path,
            pdf_path=pdf_path if pdf_success else None
        )
    except Exception as ex:
        logger.error(f"Failed to save lab report {report_id} to SQLite: {ex}")

    return {
        "report_id": report_id,
        "report_type": report_type,
        "experiment_id": experiment_id,
        "html_path": html_path,
        "pdf_path": pdf_path if pdf_success else None,
        "generated_at": context["generated_at"]
    }

