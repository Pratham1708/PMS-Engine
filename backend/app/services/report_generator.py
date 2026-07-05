"""
Report Generator Service — Institutional research report generation.
Generates Stock, Workspace, and Market reports in HTML and PDF formats
using Jinja2 templates and xhtml2pdf.
"""

import os
import io
import uuid
import logging
from datetime import datetime
from typing import Optional, List

from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa

from app.data.loader import data_loader
from app.services import stock_service, analysis_history_service, research_workspace_service

logger = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "templates")
REPORTS_DIR = os.path.join(BACKEND_DIR, "data", "reports")

# Ensure report directories exist
for sub in ("stock", "workspace", "market"):
    os.makedirs(os.path.join(REPORTS_DIR, sub), exist_ok=True)

# ── Jinja2 Environment ────────────────────────────────────────
jinja_env = Environment(
    loader=FileSystemLoader(os.path.abspath(TEMPLATES_DIR)),
    autoescape=False,
)


def _generate_report_uuid() -> str:
    """Generate a unique UUID for the report."""
    return str(uuid.uuid4())


def _html_to_pdf(html_content: str) -> bytes:
    """Convert HTML string to PDF bytes using xhtml2pdf."""
    result = io.BytesIO()
    pisa_status = pisa.CreatePDF(
        src=html_content,
        dest=result,
        encoding="utf-8",
    )
    if pisa_status.err:
        logger.warning(f"xhtml2pdf reported {pisa_status.err} errors during conversion")
    return result.getvalue()


def _save_report(
    report_type: str,
    report_id: str,
    html_content: str,
    symbol: Optional[str] = None,
    analysis_id: Optional[str] = None
) -> dict:
    """Save HTML and PDF to disk, record in DB, and return metadata."""
    subdir = os.path.join(REPORTS_DIR, report_type)
    html_path = os.path.join(subdir, f"{report_id}.html")
    pdf_path = os.path.join(subdir, f"{report_id}.pdf")

    # Save HTML
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # Generate and save PDF
    try:
        pdf_bytes = _html_to_pdf(html_content)
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)
        pdf_generated = True
    except Exception as e:
        logger.error(f"PDF generation failed for {report_id}: {e}")
        pdf_generated = False

    generated_at = datetime.now().isoformat()

    # Record in SQLite database
    try:
        from app.services.db import add_report_to_history
        add_report_to_history(
            report_id=report_id,
            report_type=report_type,
            symbol=symbol,
            generated_at=generated_at,
            analysis_id=analysis_id,
            file_path=html_path,
            report_version="1.0"
        )
    except Exception as ex:
        logger.error(f"Failed to record report {report_id} in history database: {ex}")

    return {
        "report_id": report_id,
        "type": report_type,
        "symbol": symbol,
        "html_path": html_path,
        "pdf_path": pdf_path if pdf_generated else None,
        "generated_at": generated_at,
        "analysis_id": analysis_id,
    }


def _get_cached_report(report_type: str, symbol: Optional[str] = None) -> Optional[dict]:
    """
    Check if a report can be reused based on freshness logic:
    - Stock: Reuse if latest report analysis_id matches current stock analysis_id.
    - Market: Reuse if generated in the last 1 hour.
    - Workspace: Reuse if generated in the last 5 minutes.
    """
    try:
        from app.services.db import get_latest_report
        latest = get_latest_report(report_type, symbol)
        if not latest:
            return None

        report_id = latest["report_id"]
        html_path = latest["file_path"]
        pdf_path = html_path.replace(".html", ".pdf")

        # Verify files actually exist on disk
        if not os.path.exists(html_path) or not os.path.exists(pdf_path):
            return None

        # Freshness Check
        if report_type == "stock" and symbol:
            # Check latest analysis run for this stock
            last_run = analysis_history_service.get_last_analysis(symbol)
            if not last_run:
                return None
            # If the analysis IDs match, the report is fresh
            if last_run["analysis_id"] != latest["analysis_id"]:
                return None

        elif report_type == "market":
            # Fresh if created within 1 hour (3600 seconds)
            gen_time = datetime.fromisoformat(latest["generated_at"])
            age = (datetime.now() - gen_time).total_seconds()
            if age > 3600:
                return None

        elif report_type == "workspace":
            # Fresh if created within 5 minutes (300 seconds)
            gen_time = datetime.fromisoformat(latest["generated_at"])
            age = (datetime.now() - gen_time).total_seconds()
            if age > 300:
                return None

        logger.info(f"Reusing cached {report_type} report: {report_id}")
        return {
            "report_id": report_id,
            "type": report_type,
            "symbol": symbol,
            "html_path": html_path,
            "pdf_path": pdf_path,
            "generated_at": latest["generated_at"],
            "analysis_id": latest["analysis_id"],
        }
    except Exception as e:
        logger.warning(f"Error checking cached report for {report_type} {symbol}: {e}")
        return None


# ═══════════════════════════════════════════════════════════════
# STOCK REPORT
# ═══════════════════════════════════════════════════════════════

def generate_stock_report(symbol: str) -> Optional[dict]:
    """Generate a stock research report for a given symbol."""
    # 1. Check cache first
    cached = _get_cached_report("stock", symbol)
    if cached:
        return cached

    # 2. Fetch data
    stock = stock_service.get_stock(symbol)
    if stock is None:
        return None

    # Get the latest analysis_id to associate with the report
    last_run = analysis_history_service.get_last_analysis(symbol)
    analysis_id = last_run["analysis_id"] if last_run else None

    report_id = _generate_report_uuid()
    report_date = datetime.now().strftime("%d %B %Y, %H:%M IST")

    # Build template context
    xai = stock.xai_explanation
    drivers_data = []
    if xai and xai.RatingDrivers:
        for d in xai.RatingDrivers:
            drivers_data.append({
                "name": d.name,
                "value": d.value,
                "contribution": d.contribution,
                "impact": d.impact,
                "description": d.description,
            })

    context = {
        "symbol": stock.Symbol,
        "final_rating": stock.FinalRating,
        "confidence": stock.Confidence,
        "composite_score": stock.CompositeScoreV2,
        "technical_score": stock.TechnicalScore,
        "ml_score": stock.MLScore,
        "gru_score": stock.GRUScore,
        "reliability_score": stock.ReliabilityScore,
        "rank": stock.Rank,
        "percentile": stock.Percentile,
        "universe_position": stock.UniversePosition,
        "portfolio_eligible": stock.PortfolioEligible,
        "conviction_level": stock.ConvictionLevel,
        "gru_long": stock.GRU_LONG,
        "gru_short": stock.GRU_SHORT,
        "gru_hold": stock.GRU_HOLD,
        "return_score": stock.ReturnScore,
        "current_price": stock.CurrentPrice,
        "daily_change_pct": stock.DailyChangePct,
        "volume": stock.Volume,
        "sector": stock.Sector,
        "technical_reason": xai.TechnicalScoreReason if xai else "",
        "ml_reason": xai.MLScoreReason if xai else "",
        "gru_reason": xai.GRUScoreReason if xai else "",
        "return_reason": xai.ReturnScoreReason if xai else "",
        "rating_reason": xai.FinalRatingReason if xai else "",
        "rating_drivers": drivers_data,
        "positive_factors": stock.top_positive_factors or [],
        "negative_factors": stock.top_negative_factors or [],
        "institutional_insight": stock.institutional_insight or "",
        "report_date": report_date,
        "report_id": report_id,
    }

    template = jinja_env.get_template("stock_report.html")
    html_content = template.render(**context)
    return _save_report("stock", report_id, html_content, symbol=symbol, analysis_id=analysis_id)


# ═══════════════════════════════════════════════════════════════
# RESEARCH WORKSPACE REPORT
# ═══════════════════════════════════════════════════════════════

def generate_workspace_report() -> dict:
    """Generate a Research Workspace report compiling tracked stocks and history."""
    # 1. Check cache first
    cached = _get_cached_report("workspace")
    if cached:
        return cached

    # 2. Compile data
    ws_data = research_workspace_service.get_workspace_data()
    my_stocks = ws_data["my_stocks"]
    recent_analysis = ws_data["recent_analysis"]
    universe_stats = ws_data["universe_stats"]

    # Filter my_stocks that have been analyzed (composite score exists)
    analyzed_my_stocks = [s for s in my_stocks if s["last_composite"] is not None]

    # Calculate highlights
    most_bullish_symbol = None
    most_bullish_score = None
    most_bearish_symbol = None
    most_bearish_score = None
    highest_conviction_symbol = None
    highest_conviction_confidence = None

    if analyzed_my_stocks:
        # Sort by composite score
        sorted_by_composite = sorted(analyzed_my_stocks, key=lambda s: s["last_composite"])
        most_bullish = sorted_by_composite[-1]
        most_bullish_symbol = most_bullish["symbol"]
        most_bullish_score = most_bullish["last_composite"]

        most_bearish = sorted_by_composite[0]
        most_bearish_symbol = most_bearish["symbol"]
        most_bearish_score = most_bearish["last_composite"]

        # Sort by confidence
        sorted_by_confidence = sorted(analyzed_my_stocks, key=lambda s: s["last_confidence"] or 0)
        highest_conviction = sorted_by_confidence[-1]
        highest_conviction_symbol = highest_conviction["symbol"]
        highest_conviction_confidence = highest_conviction["last_confidence"]
    elif recent_analysis:
        # Fallback to recent analysis if my_stocks is empty/un-analyzed
        sorted_by_composite = sorted(recent_analysis, key=lambda s: s["composite_score"])
        most_bullish = sorted_by_composite[-1]
        most_bullish_symbol = most_bullish["symbol"]
        most_bullish_score = most_bullish["composite_score"]

        most_bearish = sorted_by_composite[0]
        most_bearish_symbol = most_bearish["symbol"]
        most_bearish_score = most_bearish["composite_score"]

        sorted_by_confidence = sorted(recent_analysis, key=lambda s: s["confidence"])
        highest_conviction = sorted_by_confidence[-1]
        highest_conviction_symbol = highest_conviction["symbol"]
        highest_conviction_confidence = highest_conviction["confidence"]

    # Most recently analyzed
    latest_analyzed_symbol = None
    latest_analyzed_time = None
    if recent_analysis:
        latest_analyzed = recent_analysis[0]  # recent_analysis is sorted by analyzed_at DESC
        latest_analyzed_symbol = latest_analyzed["symbol"]
        latest_analyzed_time = latest_analyzed["analyzed_at"]

    # Calculate coverage ratio
    total_universe = universe_stats["total_universe"]
    tracked_count = len(my_stocks)
    coverage_ratio = (tracked_count / total_universe * 100) if total_universe > 0 else 0.0

    # Calculate averages
    avg_confidence = None
    avg_composite = None
    if analyzed_my_stocks:
        avg_confidence = sum(s["last_confidence"] for s in analyzed_my_stocks) / len(analyzed_my_stocks)
        avg_composite = sum(s["last_composite"] for s in analyzed_my_stocks) / len(analyzed_my_stocks)

    # Generate workspace insight narrative
    analyzed_count = len(analyzed_my_stocks)
    if tracked_count == 0:
        workspace_insight = "Your research workspace is currently empty. Add Indian stocks to your workspace and execute model analyses to begin generating automated intelligence reports."
    else:
        if analyzed_count == 0:
            workspace_insight = f"You are actively tracking {tracked_count} stocks. None of these tracked stocks have been analyzed in the current cycle. Run PMS analysis to populate model breakdowns and generate conviction scores."
        else:
            ratings = [s["last_rating"] for s in analyzed_my_stocks]
            strong_buys = ratings.count("STRONG BUY")
            buys = ratings.count("BUY")
            sells = ratings.count("SELL") + ratings.count("STRONG SELL")
            bullish = strong_buys + buys

            if bullish > sells:
                workspace_insight = f"Your research coverage exhibits a distinct bullish bias, with {bullish} out of {analyzed_count} analyzed stocks carrying BUY or STRONG BUY ratings. Momentum is heavily concentrated in your top-ranked stock, {most_bullish_symbol}."
            elif sells > bullish:
                workspace_insight = f"Your research coverage exhibits a defensive skew, with {sells} out of {analyzed_count} analyzed stocks carrying SELL or STRONG SELL ratings. Review your exposures carefully, paying specific attention to lagging indicators on {most_bearish_symbol}."
            else:
                workspace_insight = f"Your research workspace shows a balanced scoring profile between bullish and defensive signals. Stock selection is paramount in this regime; consider focusing allocations towards high-conviction models like {most_bullish_symbol}."

    report_id = _generate_report_uuid()
    report_date = datetime.now().strftime("%d %B %Y, %H:%M IST")

    context = {
        "tracked_count": tracked_count,
        "total_universe": total_universe,
        "coverage_ratio": coverage_ratio,
        "analyzed_count": analyzed_count,
        "avg_confidence": avg_confidence,
        "avg_composite": avg_composite,
        "most_bullish_symbol": most_bullish_symbol,
        "most_bullish_score": most_bullish_score,
        "most_bearish_symbol": most_bearish_symbol,
        "most_bearish_score": most_bearish_score,
        "highest_conviction_symbol": highest_conviction_symbol,
        "highest_conviction_confidence": highest_conviction_confidence,
        "latest_analyzed_symbol": latest_analyzed_symbol,
        "latest_analyzed_time": latest_analyzed_time,
        "workspace_insight": workspace_insight,
        "my_stocks": my_stocks,
        "recent_analysis": recent_analysis,
        "report_date": report_date,
        "report_id": report_id,
    }

    template = jinja_env.get_template("workspace_report.html")
    html_content = template.render(**context)
    return _save_report("workspace", report_id, html_content)


# ═══════════════════════════════════════════════════════════════
# MARKET REPORT
# ═══════════════════════════════════════════════════════════════

def generate_market_report() -> dict:
    """Generate a market overview report."""
    # 1. Check cache first
    cached = _get_cached_report("market")
    if cached:
        return cached

    # 2. Compile data
    df = data_loader.get_df()
    report_id = _generate_report_uuid()
    report_date = datetime.now().strftime("%d %B %Y, %H:%M IST")

    total_stocks = len(df)
    rating_counts = df["FinalRating"].value_counts()
    strong_buy_count = int(rating_counts.get("STRONG BUY", 0))
    buy_count = int(rating_counts.get("BUY", 0))
    hold_count = int(rating_counts.get("HOLD", 0))
    sell_count = int(rating_counts.get("SELL", 0))
    strong_sell_count = int(rating_counts.get("STRONG SELL", 0))

    bullish_pct = ((strong_buy_count + buy_count) / total_stocks * 100) if total_stocks > 0 else 0
    bearish_pct = ((sell_count + strong_sell_count) / total_stocks * 100) if total_stocks > 0 else 0
    neutral_pct = (hold_count / total_stocks * 100) if total_stocks > 0 else 0

    # Top and bottom decile
    sorted_df = df.sort_values("CompositeScoreV2", ascending=False)
    decile_size = max(1, total_stocks // 10)

    top_decile = []
    for _, row in sorted_df.head(decile_size).iterrows():
        top_decile.append({
            "Symbol": row["Symbol"],
            "FinalRating": row["FinalRating"],
            "CompositeScoreV2": round(float(row["CompositeScoreV2"]), 2),
            "Confidence": round(float(row["Confidence"]), 1),
        })

    bottom_decile = []
    for _, row in sorted_df.tail(decile_size).iterrows():
        bottom_decile.append({
            "Symbol": row["Symbol"],
            "FinalRating": row["FinalRating"],
            "CompositeScoreV2": round(float(row["CompositeScoreV2"]), 2),
            "Confidence": round(float(row["Confidence"]), 1),
        })

    context = {
        "total_stocks": total_stocks,
        "strong_buy_count": strong_buy_count,
        "buy_count": buy_count,
        "hold_count": hold_count,
        "sell_count": sell_count,
        "strong_sell_count": strong_sell_count,
        "avg_confidence": round(float(df["Confidence"].mean()), 1),
        "avg_composite": round(float(df["CompositeScoreV2"].mean()), 2),
        "avg_technical": round(float(df["TechnicalScore"].mean()), 2),
        "avg_ml": round(float(df["MLScore"].mean()), 2),
        "avg_gru": round(float(df["GRUScore"].mean()), 2),
        "top_decile": top_decile,
        "bottom_decile": bottom_decile,
        "bullish_pct": bullish_pct,
        "bearish_pct": bearish_pct,
        "neutral_pct": neutral_pct,
        "report_date": report_date,
        "report_id": report_id,
    }

    template = jinja_env.get_template("market_report.html")
    html_content = template.render(**context)
    return _save_report("market", report_id, html_content)


# ═══════════════════════════════════════════════════════════════
# REPORT LISTING & RETRIEVAL
# ═══════════════════════════════════════════════════════════════

def list_all_reports() -> List[dict]:
    """List all generated reports from SQLite history sorted by newest first."""
    try:
        from app.services.db import list_reports_from_history
        db_reports = list_reports_from_history()
        
        reports = []
        for r in db_reports:
            html_path = r["file_path"]
            pdf_path = html_path.replace(".html", ".pdf")
            
            # Verify that files still exist on disk
            if os.path.exists(html_path):
                reports.append({
                    "report_id": r["report_id"],
                    "type": r["report_type"],
                    "symbol": r["symbol"],
                    "generated_at": r["generated_at"],
                    "analysis_id": r["analysis_id"],
                    "has_pdf": os.path.exists(pdf_path),
                })
        return reports
    except Exception as e:
        logger.error(f"Error fetching report list from database: {e}")
        # Fallback to filesystem scanner if DB fails
        reports = []
        for report_type in ("stock", "workspace", "market"):
            subdir = os.path.join(REPORTS_DIR, report_type)
            if not os.path.isdir(subdir):
                continue
            for filename in os.listdir(subdir):
                if filename.endswith(".html"):
                    report_id = filename[:-5]
                    html_path = os.path.join(subdir, filename)
                    pdf_path = os.path.join(subdir, f"{report_id}.pdf")
                    stat = os.stat(html_path)
                    reports.append({
                        "report_id": report_id,
                        "type": report_type,
                        "symbol": report_id.split("_")[1] if report_type == "stock" else None,
                        "generated_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "has_pdf": os.path.exists(pdf_path),
                    })
        reports.sort(key=lambda r: r["generated_at"], reverse=True)
        return reports


def get_report_path(report_id: str, fmt: str = "pdf") -> Optional[str]:
    """Get the file path for a report by ID and format."""
    ext = "pdf" if fmt == "pdf" else "html"
    for report_type in ("stock", "workspace", "market"):
        path = os.path.join(REPORTS_DIR, report_type, f"{report_id}.{ext}")
        if os.path.exists(path):
            return path
    return None
