"""
backtest_report_generator.py — Generate JSON, HTML, and PDF reports for backtest runs.

Saves files to data/reports/backtest/{run_id}.[json|html|pdf].
"""

import json
import logging
import os

logger = logging.getLogger(__name__)

REPORTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "reports", "backtest"
)
os.makedirs(REPORTS_DIR, exist_ok=True)


def save_json_report(run_id: str, result: dict) -> str:
    """Save the full backtest response dict to a JSON file."""
    fpath = os.path.join(REPORTS_DIR, f"{run_id}.json")
    try:
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        logger.info("[ReportGenerator] Saved JSON report: %s", fpath)
        return fpath
    except Exception as e:
        logger.error("[ReportGenerator] Failed to save JSON report: %s", e)
        return ""


def generate_html_report(run_id: str, result: dict) -> str:
    """Generate a self-contained HTML report with responsive styling."""
    fpath = os.path.join(REPORTS_DIR, f"{run_id}.html")
    try:
        # Simple standalone HTML compilation with modern design matching the platform
        summary = result.get("summary", {})
        cm = result.get("custom_metrics", {})
        pm = result.get("pms_default_metrics", {})
        bm = result.get("benchmark_metrics", {})

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Backtest Report — {result.get("strategy_name")}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: #0f172a;
            color: #f1f5f9;
            margin: 0;
            padding: 40px;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: #1e293b;
            padding: 30px;
            border-radius: 16px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }}
        h1 {{
            color: #6366f1;
            margin-top: 0;
        }}
        .meta {{
            color: #94a3b8;
            font-size: 0.9rem;
            margin-bottom: 24px;
            border-bottom: 1px solid #334155;
            padding-bottom: 12px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
            gap: 16px;
            margin-bottom: 30px;
        }}
        .card {{
            background: #0f172a;
            padding: 16px;
            border-radius: 12px;
            border: 1px solid #334155;
        }}
        .card-label {{
            font-size: 0.78rem;
            color: #64748b;
            text-transform: uppercase;
        }}
        .card-value {{
            font-size: 1.4rem;
            font-weight: 700;
            color: #f1f5f9;
            margin-top: 6px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #334155;
        }}
        th {{
            color: #94a3b8;
            font-weight: 600;
            font-size: 0.85rem;
        }}
        .pos {{ color: #10b981; }}
        .neg {{ color: #ef4444; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Backtest Report — {result.get("strategy_name")}</h1>
        <div class="meta">
            Strategy ID: {result.get("strategy_id")} &middot; 
            Period: {result.get("start_date")} to {result.get("end_date")} &middot; 
            Rebalance: {result.get("rebalance_freq")} &middot; 
            Benchmark: {result.get("benchmark")}
        </div>

        <div class="grid">
            <div class="card">
                <div class="card-label">Total Return (Custom)</div>
                <div class="card-value pos">{summary.get("total_return_pct", 0.0):.2f}%</div>
            </div>
            <div class="card">
                <div class="card-label">CAGR (Custom)</div>
                <div class="card-value pos">{summary.get("cagr_pct", 0.0):.2f}%</div>
            </div>
            <div class="card">
                <div class="card-label">Sharpe Ratio (Custom)</div>
                <div class="card-value">{summary.get("sharpe_ratio", 0.0):.2f}x</div>
            </div>
            <div class="card">
                <div class="card-label">Max Drawdown (Custom)</div>
                <div class="card-value neg">{summary.get("max_drawdown_pct", 0.0):.2f}%</div>
            </div>
        </div>

        <h2>Performance vs Baselines</h2>
        <table>
            <thead>
                <tr>
                    <th>Metric</th>
                    <th>Custom Strategy</th>
                    <th>PMS Default</th>
                    <th>Benchmark</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Total Return</td>
                    <td class="pos">{summary.get("total_return_pct", 0.0):.2f}%</td>
                    <td>{summary.get("pms_total_return_pct", 0.0):.2f}%</td>
                    <td>{summary.get("benchmark_total_return_pct", 0.0):.2f}%</td>
                </tr>
                <tr>
                    <td>CAGR</td>
                    <td>{summary.get("cagr_pct", 0.0):.2f}%</td>
                    <td>{summary.get("pms_cagr_pct", 0.0):.2f}%</td>
                    <td>{summary.get("benchmark_cagr_pct", 0.0):.2f}%</td>
                </tr>
                <tr>
                    <td>Sharpe Ratio</td>
                    <td>{summary.get("sharpe_ratio", 0.0):.2f}x</td>
                    <td>{summary.get("pms_sharpe_ratio", 0.0):.2f}x</td>
                    <td>{summary.get("benchmark_sharpe_ratio", 0.0):.2f}x</td>
                </tr>
                <tr>
                    <td>Max Drawdown</td>
                    <td class="neg">{summary.get("max_drawdown_pct", 0.0):.2f}%</td>
                    <td class="neg">{summary.get("pms_max_drawdown_pct", 0.0):.2f}%</td>
                    <td class="neg">{summary.get("benchmark_max_drawdown_pct", 0.0):.2f}%</td>
                </tr>
            </tbody>
        </table>

        <h2>Closed Trades Log Summary ({len(result.get("trade_log", []))} total trades)</h2>
        <table>
            <thead>
                <tr>
                    <th>Symbol</th>
                    <th>Entry Date</th>
                    <th>Exit Date</th>
                    <th>Holding Days</th>
                    <th>Return %</th>
                </tr>
            </thead>
            <tbody>
                {"".join([
                    f"<tr>"
                    f"<td><strong>{t.get('symbol')}</strong><br><span style='font-size:0.75rem;color:#64748b'>{t.get('company_name')}</span></td>"
                    f"<td>{t.get('entry_date')}</td>"
                    f"<td>{t.get('exit_date')}</td>"
                    f"<td>{t.get('holding_days')}d</td>"
                    f"<td class='{'pos' if t.get('return_pct', 0) >= 0 else 'neg'}'>{t.get('return_pct', 0.0):.2f}%</td>"
                    f"</tr>"
                    for t in result.get("trade_log", [])[:10]
                ])}
            </tbody>
        </table>
        {f"<p style='color:#64748b;font-style:italic;'>Showing first 10 of {len(result.get('trade_log', []))} closed positions.</p>" if len(result.get("trade_log", [])) > 10 else ""}
    </div>
</body>
</html>
"""
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(html)
        logger.info("[ReportGenerator] Saved HTML report: %s", fpath)
        return fpath
    except Exception as e:
        logger.error("[ReportGenerator] Failed to save HTML report: %s", e)
        return ""


def generate_pdf_report(run_id: str, result: dict) -> str:
    """Generate PDF report using xhtml2pdf."""
    fpath = os.path.join(REPORTS_DIR, f"{run_id}.pdf")
    try:
        from xhtml2pdf import pisa
        html_path = generate_html_report(run_id, result)
        if not html_path or not os.path.exists(html_path):
            return ""

        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        with open(fpath, "wb") as f_pdf:
            pisa_status = pisa.CreatePDF(html_content, dest=f_pdf, encoding="utf-8")

        if pisa_status.err:
            logger.warning("[ReportGenerator] xhtml2pdf reported %d errors", pisa_status.err)

        logger.info("[ReportGenerator] Saved PDF report: %s", fpath)
        return fpath
    except Exception as e:
        logger.error("[ReportGenerator] Failed to generate PDF report: %s", e)
        return ""
