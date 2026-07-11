"""
Chart Service — Static chart image generation for PDF reports.

Produces publication-quality PNG charts from the same ReportContext data
used by the interactive HTML report. These charts are embedded exclusively
in the PDF report template.

Charts produced:
  1. price_action_chart  — OHLC candlestick + EMA20/50/200 + Volume + Support/Resistance + Trend
  2. score_gauge_chart   — Horizontal grouped bar chart of all model scores
  3. score_timeline_chart — 4-point composite score trend line

All charts target 150 DPI, white institutional background, professional typography.
"""

import os
import io
import logging
from typing import Optional, List, Dict, Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ── Chart output directory ───────────────────────────────────────
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHARTS_DIR = os.path.join(BACKEND_DIR, "data", "reports", "charts")

# ── Publication color palette (consistent across all charts) ─────
COLORS = {
    "navy": "#0f172a",
    "blue_dark": "#1e3a8a",
    "blue_mid": "#3b82f6",
    "gold": "#d4a843",
    "green": "#10b981",
    "red": "#ef4444",
    "orange": "#f59e0b",
    "gray_dark": "#334155",
    "gray_mid": "#64748b",
    "gray_light": "#cbd5e1",
    "bg": "#ffffff",
    "bg_alt": "#f8fafc",
    "ema20": "#3b82f6",
    "ema50": "#f59e0b",
    "ema200": "#64748b",
    "trend": "#8b5cf6",
    "support": "#10b981",
    "resistance": "#ef4444",
}

DPI = 150
FIGURE_WIDTH = 10.5   # inches (A4 content width ~170mm)


def _setup_matplotlib():
    """Configure matplotlib for non-interactive, publication-quality rendering."""
    import matplotlib
    matplotlib.use("Agg")  # non-interactive backend — must be set before pyplot import
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
    from matplotlib import rcParams

    rcParams.update({
        "figure.facecolor": COLORS["bg"],
        "axes.facecolor": COLORS["bg"],
        "axes.edgecolor": COLORS["gray_light"],
        "axes.labelcolor": COLORS["gray_dark"],
        "axes.titlecolor": COLORS["navy"],
        "xtick.color": COLORS["gray_mid"],
        "ytick.color": COLORS["gray_mid"],
        "grid.color": "#f1f5f9",
        "grid.linewidth": 0.6,
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.titlesize": 11,
        "axes.labelsize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 8,
        "legend.framealpha": 0.95,
        "legend.edgecolor": COLORS["gray_light"],
        "figure.dpi": DPI,
        "savefig.dpi": DPI,
        "savefig.bbox": "tight",
        "savefig.facecolor": COLORS["bg"],
    })
    return plt, mticker


def _add_figure_caption(fig, caption: str, source: str = "PMS Engine · Yahoo Finance"):
    """Add a standard source/caption line below the figure."""
    import matplotlib
    fig.text(
        0.01, 0.01,
        f"Source: {source}  |  {caption}",
        ha="left", va="bottom",
        fontsize=7,
        color=COLORS["gray_mid"],
        style="italic",
    )


def _ensure_chart_dir(report_id: str) -> str:
    """Ensure per-report chart directory exists and return its path."""
    path = os.path.join(CHARTS_DIR, report_id)
    os.makedirs(path, exist_ok=True)
    return path


# ════════════════════════════════════════════════════════════════
# CHART 1 — PRICE ACTION (Candlestick + EMAs + Volume + Trend)
# ════════════════════════════════════════════════════════════════

def generate_price_action_chart(
    report_id: str,
    symbol: str,
    chart_history: List[Dict],
    support_level: float,
    resistance_level: float,
    current_price: float,
) -> Optional[str]:
    """
    Generate a full-featured institutional price action chart.

    Figure 1 — 1-Year Price Action
    Subtitle: Daily OHLC Candlesticks with EMA20, EMA50, EMA200 overlays
    X-Axis: Date (Trading Days)
    Y-Axis: Price (INR ₹)
    Lower panel: Volume (Shares)
    Price lines: Support (green dashed) | Resistance (red dashed) | Trend line (purple)

    Returns: absolute path to saved PNG, or None on failure.
    """
    if not chart_history:
        logger.warning(f"[ChartService] No chart_history for {symbol}, skipping price chart.")
        return None

    try:
        plt, mticker = _setup_matplotlib()

        df = pd.DataFrame(chart_history)
        df["time"] = pd.to_datetime(df["time"])
        df = df.sort_values("time").reset_index(drop=True)

        n = len(df)
        x = np.arange(n)

        # ── Figure layout: 70% price | 30% volume ─────────────
        fig, (ax_price, ax_vol) = plt.subplots(
            2, 1,
            figsize=(FIGURE_WIDTH, 5.5),
            gridspec_kw={"height_ratios": [3, 1], "hspace": 0.04},
            sharex=True,
        )

        # ── Candlesticks ───────────────────────────────────────
        candle_width = 0.6
        for i in range(n):
            o = df["open"].iloc[i]
            h = df["high"].iloc[i]
            l = df["low"].iloc[i]
            c = df["close"].iloc[i]
            color = COLORS["green"] if c >= o else COLORS["red"]
            # Wick
            ax_price.plot([x[i], x[i]], [l, h], color=color, linewidth=0.5, zorder=2)
            # Body
            ax_price.bar(
                x[i], abs(c - o),
                bottom=min(o, c),
                width=candle_width,
                color=color,
                alpha=0.85,
                zorder=3,
            )

        # ── EMA lines ─────────────────────────────────────────
        if "ema20" in df.columns:
            ax_price.plot(x, df["ema20"], color=COLORS["ema20"], linewidth=1.3, label="EMA 20", zorder=4)
        if "ema50" in df.columns:
            ax_price.plot(x, df["ema50"], color=COLORS["ema50"], linewidth=1.3, label="EMA 50", zorder=4)
        if "ema200" in df.columns:
            ax_price.plot(x, df["ema200"], color=COLORS["ema200"], linewidth=1.5, label="EMA 200", linestyle="--", zorder=4)

        # ── Trend line ─────────────────────────────────────────
        if "trend_line" in df.columns:
            ax_price.plot(x, df["trend_line"], color=COLORS["trend"], linewidth=1.0,
                          linestyle=(0, (4, 2)), label="Trend", alpha=0.8, zorder=4)

        # ── Support & Resistance ───────────────────────────────
        ax_price.axhline(support_level, color=COLORS["support"], linewidth=1.2,
                         linestyle=":", alpha=0.9, label=f"Support ₹{support_level:,.0f}", zorder=5)
        ax_price.axhline(resistance_level, color=COLORS["resistance"], linewidth=1.2,
                         linestyle=":", alpha=0.9, label=f"Resistance ₹{resistance_level:,.0f}", zorder=5)

        # ── Current price marker ───────────────────────────────
        ax_price.axhline(current_price, color=COLORS["navy"], linewidth=1.0,
                         linestyle="-", alpha=0.4, zorder=5)
        ax_price.text(n - 1, current_price, f" ₹{current_price:,.1f}",
                      va="center", ha="left", fontsize=7.5,
                      color=COLORS["navy"], fontweight="bold")

        # ── Price axis formatting ──────────────────────────────
        ax_price.set_ylabel("Price (INR ₹)", fontsize=9, color=COLORS["gray_dark"])
        ax_price.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"₹{v:,.0f}"))
        ax_price.legend(loc="upper left", ncol=3, fontsize=7.5, framealpha=0.9)
        ax_price.grid(True, axis="y", alpha=0.5)
        ax_price.spines["top"].set_visible(False)
        ax_price.spines["right"].set_visible(False)
        ax_price.set_xlim(-1, n)

        # ── Title block ────────────────────────────────────────
        ax_price.set_title(
            f"Figure 1 — 1-Year Price Action: {symbol}",
            fontsize=12, fontweight="bold", color=COLORS["navy"],
            loc="left", pad=8,
        )
        ax_price.text(
            0, 1.01,
            "Daily OHLC Candlesticks with EMA20, EMA50, EMA200 Overlays  |  Support & Resistance  |  Trend Line",
            transform=ax_price.transAxes,
            fontsize=7.5, color=COLORS["gray_mid"], va="bottom",
        )

        # ── Volume bars ────────────────────────────────────────
        if "volume" in df.columns:
            vol_colors = [
                COLORS["green"] if df["close"].iloc[i] >= df["open"].iloc[i]
                else COLORS["red"]
                for i in range(n)
            ]
            ax_vol.bar(x, df["volume"], width=candle_width, color=vol_colors, alpha=0.55)

        ax_vol.set_ylabel("Volume", fontsize=8, color=COLORS["gray_dark"])
        ax_vol.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda v, _: f"{v/1e6:.1f}M" if v >= 1e6 else f"{v/1e3:.0f}K")
        )
        ax_vol.grid(True, axis="y", alpha=0.3)
        ax_vol.spines["top"].set_visible(False)
        ax_vol.spines["right"].set_visible(False)

        # ── X-axis: show month labels from dates ───────────────
        tick_step = max(1, n // 12)
        tick_positions = x[::tick_step]
        tick_labels = [df["time"].iloc[i].strftime("%b '%y") for i in tick_positions]
        ax_vol.set_xticks(tick_positions)
        ax_vol.set_xticklabels(tick_labels, rotation=30, ha="right", fontsize=7.5)
        ax_vol.set_xlabel("Trading Days", fontsize=9, color=COLORS["gray_dark"])

        _add_figure_caption(fig, f"PMS Engine Report ID context for {symbol}")

        # ── Save ───────────────────────────────────────────────
        chart_dir = _ensure_chart_dir(report_id)
        path = os.path.join(chart_dir, "price_action.png")
        fig.savefig(path, dpi=DPI, bbox_inches="tight", facecolor=COLORS["bg"])
        plt.close(fig)

        logger.info(f"[ChartService] Saved price_action chart → {path}")
        return path

    except Exception as e:
        logger.error(f"[ChartService] Failed to generate price action chart: {e}", exc_info=True)
        return None


# ════════════════════════════════════════════════════════════════
# CHART 2 — SCORE GAUGE (Horizontal grouped bars for all scores)
# ════════════════════════════════════════════════════════════════

def generate_score_gauge_chart(
    report_id: str,
    composite_score: float,
    technical_score: float,
    ml_score: float,
    gru_score: float,
    reliability_score: float,
    confidence: float,
) -> Optional[str]:
    """
    Generate a horizontal bar score dashboard chart.

    Figure 2 — Multi-Model Score Summary
    Shows all 6 key scores as labeled horizontal bars (0–100 scale).
    Color-coded by score zone: green >= 65 | orange 40-65 | red < 40.
    Returns: absolute path to saved PNG, or None on failure.
    """
    try:
        plt, mticker = _setup_matplotlib()

        def normalize(v):
            """Normalize score to 0-100 range (technical can be -100..+100)."""
            if v is None:
                return 50.0
            v = float(v)
            if v < 0:
                return max(0.0, (v + 100) / 2.0)
            return min(100.0, v)

        def bar_color(v_norm):
            if v_norm >= 65:
                return COLORS["green"]
            elif v_norm >= 40:
                return COLORS["orange"]
            return COLORS["red"]

        labels = [
            "Composite Score",
            "Technical Score",
            "ML Ensemble",
            "GRU Deep Learning",
            "Reliability Index",
            "Confidence",
        ]
        raw_values = [composite_score, technical_score, ml_score, gru_score, reliability_score, confidence]
        norm_values = [normalize(v) for v in raw_values]
        colors = [bar_color(v) for v in norm_values]

        fig, ax = plt.subplots(figsize=(FIGURE_WIDTH, 3.2))

        y_pos = np.arange(len(labels))
        bars = ax.barh(y_pos, norm_values, color=colors, height=0.55, alpha=0.88, edgecolor="none")

        # Value labels inside/outside bars
        for bar, raw, norm in zip(bars, raw_values, norm_values):
            label_x = norm + 1.5
            ax.text(label_x, bar.get_y() + bar.get_height() / 2,
                    f"{raw:.1f}", va="center", ha="left", fontsize=8.5, fontweight="bold",
                    color=COLORS["navy"])

        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, fontsize=9)
        ax.set_xlim(0, 115)
        ax.set_xlabel("Score (0 – 100 scale)", fontsize=9)
        ax.axvline(65, color=COLORS["green"], linewidth=0.8, linestyle="--", alpha=0.5, label="BUY threshold (65)")
        ax.axvline(40, color=COLORS["red"], linewidth=0.8, linestyle="--", alpha=0.5, label="SELL threshold (40)")
        ax.legend(loc="lower right", fontsize=7.5)
        ax.grid(True, axis="x", alpha=0.35)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)

        ax.set_title("Figure 2 — Multi-Model Score Summary",
                     fontsize=12, fontweight="bold", color=COLORS["navy"], loc="left", pad=8)
        ax.text(0, 1.02,
                "All quantitative model scores normalized to 0–100 scale. Green ≥65 (Buy zone) | Orange 40–65 (Hold) | Red <40 (Sell)",
                transform=ax.transAxes, fontsize=7.5, color=COLORS["gray_mid"], va="bottom")

        _add_figure_caption(fig, "Generated by PMS Engine Composite Scoring Framework")

        chart_dir = _ensure_chart_dir(report_id)
        path = os.path.join(chart_dir, "score_gauges.png")
        fig.savefig(path, dpi=DPI, bbox_inches="tight", facecolor=COLORS["bg"])
        plt.close(fig)

        logger.info(f"[ChartService] Saved score_gauge chart → {path}")
        return path

    except Exception as e:
        logger.error(f"[ChartService] Failed to generate score gauge chart: {e}", exc_info=True)
        return None


# ════════════════════════════════════════════════════════════════
# CHART 3 — SCORE TIMELINE (4-point composite score trend)
# ════════════════════════════════════════════════════════════════

def generate_score_timeline_chart(
    report_id: str,
    score_timeline: Dict,
) -> Optional[str]:
    """
    Generate a 4-point composite score trend chart.

    Figure 3 — Composite Score Evolution
    X-Axis: Time period (30D Ago → 7D Ago → Previous → Today)
    Y-Axis: Composite Score (0–100)
    Returns: absolute path to saved PNG, or None on failure.
    """
    try:
        plt, _ = _setup_matplotlib()

        labels = ["30 Days Ago", "7 Days Ago", "Previous", "Today"]
        values = [
            float(score_timeline.get("days30", 50)),
            float(score_timeline.get("days7", 50)),
            float(score_timeline.get("previous", 50)),
            float(score_timeline.get("current", 50)),
        ]

        x = np.arange(len(labels))
        fig, ax = plt.subplots(figsize=(7.0, 2.8))

        # Filled area under line
        ax.fill_between(x, values, alpha=0.08, color=COLORS["blue_dark"])
        ax.plot(x, values, color=COLORS["blue_dark"], linewidth=2.0, zorder=3)

        # Data point markers
        for i, (xi, v) in enumerate(zip(x, values)):
            color = COLORS["gold"] if i == len(x) - 1 else COLORS["blue_mid"]
            size = 90 if i == len(x) - 1 else 55
            ax.scatter(xi, v, color=color, s=size, zorder=4, edgecolors="white", linewidths=1.5)
            offset = 2.5 if v < 95 else -4
            ax.text(xi, v + offset, f"{v:.1f}", ha="center", va="bottom",
                    fontsize=8.5, fontweight="bold", color=COLORS["navy"])

        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=9)
        ax.set_ylabel("Composite Score", fontsize=9)
        ax.set_ylim(max(0, min(values) - 15), min(100, max(values) + 15))

        # Threshold reference lines
        ax.axhline(65, color=COLORS["green"], linewidth=0.8, linestyle="--", alpha=0.5)
        ax.axhline(40, color=COLORS["red"], linewidth=0.8, linestyle="--", alpha=0.5)
        ax.text(3.05, 65, "BUY", fontsize=7, color=COLORS["green"], va="center")
        ax.text(3.05, 40, "SELL", fontsize=7, color=COLORS["red"], va="center")

        ax.grid(True, axis="y", alpha=0.35)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.set_xlim(-0.3, 3.5)

        ax.set_title("Figure 3 — Composite Score Evolution",
                     fontsize=12, fontweight="bold", color=COLORS["navy"], loc="left", pad=8)
        ax.text(0, 1.04,
                "Composite Score trend over the last 30 trading days  |  Gold dot = Today's reading",
                transform=ax.transAxes, fontsize=7.5, color=COLORS["gray_mid"], va="bottom")

        _add_figure_caption(fig, "Generated by PMS Engine Score Telemetry")

        chart_dir = _ensure_chart_dir(report_id)
        path = os.path.join(chart_dir, "score_timeline.png")
        fig.savefig(path, dpi=DPI, bbox_inches="tight", facecolor=COLORS["bg"])
        plt.close(fig)

        logger.info(f"[ChartService] Saved score_timeline chart → {path}")
        return path

    except Exception as e:
        logger.error(f"[ChartService] Failed to generate score timeline chart: {e}", exc_info=True)
        return None


# ════════════════════════════════════════════════════════════════
# ORCHESTRATOR
# ════════════════════════════════════════════════════════════════

def generate_all_charts(report_id: str, context: Dict) -> Dict[str, Optional[str]]:
    """
    Generate all static charts for a PDF report and return a dict of absolute paths.

    Args:
        report_id: Unique identifier for the report.
        context: The shared ReportContext dict from report_generator.

    Returns:
        dict with keys: 'price_action', 'score_gauges', 'score_timeline'
        Each value is an absolute path string or None if generation failed.
    """
    symbol = context.get("symbol", "UNKNOWN")
    logger.info(f"[ChartService] Generating all charts for {symbol} (report_id={report_id})")

    price_path = generate_price_action_chart(
        report_id=report_id,
        symbol=symbol,
        chart_history=context.get("chart_history", []),
        support_level=context.get("support_level", 0),
        resistance_level=context.get("resistance_level", 0),
        current_price=context.get("current_price", 0),
    )

    gauge_path = generate_score_gauge_chart(
        report_id=report_id,
        composite_score=context.get("composite_score", 50),
        technical_score=context.get("technical_score", 50),
        ml_score=context.get("ml_score", 50),
        gru_score=context.get("gru_score", 50),
        reliability_score=context.get("reliability_score", 50),
        confidence=context.get("confidence", 50),
    )

    timeline_path = generate_score_timeline_chart(
        report_id=report_id,
        score_timeline=context.get("score_timeline", {}),
    )

    chart_paths = {
        "price_action": price_path,
        "score_gauges": gauge_path,
        "score_timeline": timeline_path,
    }

    generated = sum(1 for v in chart_paths.values() if v is not None)
    logger.info(f"[ChartService] Chart generation complete: {generated}/3 charts generated.")
    return chart_paths
