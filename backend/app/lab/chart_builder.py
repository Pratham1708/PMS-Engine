"""
chart_builder.py — Recharts-compatible JSON serializers for all lab chart types.

All functions return list[dict] that can be directly passed to Recharts components.
"""

import logging
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def _safe_float(v) -> Optional[float]:
    try:
        f = float(v)
        return None if (np.isnan(f) or np.isinf(f)) else round(f, 4)
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# EQUITY & DRAWDOWN
# ─────────────────────────────────────────────────────────────────────────────

def equity_curve(equity_series: pd.Series, dates: Optional[List[str]] = None,
                 benchmark_series: Optional[pd.Series] = None,
                 initial_capital: float = 100_000) -> List[Dict]:
    """Equity curve normalised to 100 (index-style). Optionally includes benchmark."""
    base = equity_series.iloc[0] if equity_series.iloc[0] != 0 else initial_capital
    norm = (equity_series / base) * 100

    result = []
    for i, v in enumerate(norm):
        d = dates[i] if dates and i < len(dates) else str(i)
        row = {"date": d, "portfolio": _safe_float(v)}
        if benchmark_series is not None and i < len(benchmark_series):
            b_base = benchmark_series.iloc[0]
            b_norm = (benchmark_series.iloc[i] / b_base) * 100 if b_base else None
            row["benchmark"] = _safe_float(b_norm)
        result.append(row)
    return result


def drawdown_curve(equity_series: pd.Series, dates: Optional[List[str]] = None) -> List[Dict]:
    """Drawdown as negative percentage from peak."""
    cummax = equity_series.cummax()
    dd = ((equity_series - cummax) / cummax.replace(0, np.nan)) * 100
    result = []
    for i, v in enumerate(dd):
        d = dates[i] if dates and i < len(dates) else str(i)
        result.append({"date": d, "drawdown_pct": _safe_float(v)})
    return result


def underwater_plot(equity_series: pd.Series, dates: Optional[List[str]] = None) -> List[Dict]:
    """Underwater plot (filled area below zero). Same as drawdown but zero-filled for area charts."""
    return drawdown_curve(equity_series, dates)


# ─────────────────────────────────────────────────────────────────────────────
# ROLLING CHARTS
# ─────────────────────────────────────────────────────────────────────────────

def rolling_sharpe_chart(equity_series: pd.Series, dates: Optional[List[str]] = None,
                         window: int = 30, rf_rate: float = 0.065) -> List[Dict]:
    from app.lab.metrics import rolling_sharpe
    return rolling_sharpe(equity_series, dates, window, rf_rate)


def rolling_cagr_chart(equity_series: pd.Series, dates: Optional[List[str]] = None,
                       window: int = 90) -> List[Dict]:
    from app.lab.metrics import rolling_cagr
    return rolling_cagr(equity_series, dates, window)


def rolling_vol_chart(equity_series: pd.Series, dates: Optional[List[str]] = None,
                      window: int = 30) -> List[Dict]:
    from app.lab.metrics import rolling_volatility
    return rolling_volatility(equity_series, dates, window)


# ─────────────────────────────────────────────────────────────────────────────
# HEATMAPS
# ─────────────────────────────────────────────────────────────────────────────

def monthly_heatmap(equity_series: pd.Series, dates: Optional[List[str]] = None) -> List[Dict]:
    from app.lab.metrics import monthly_returns
    return monthly_returns(equity_series, dates)


def yearly_heatmap(equity_series: pd.Series, dates: Optional[List[str]] = None) -> List[Dict]:
    from app.lab.metrics import yearly_returns
    return yearly_returns(equity_series, dates)


# ─────────────────────────────────────────────────────────────────────────────
# TRADE CHARTS
# ─────────────────────────────────────────────────────────────────────────────

def trade_scatter(trade_log: List[Dict]) -> List[Dict]:
    """Scatter: return_pct vs holding_days per trade, coloured by win/loss."""
    return [
        {
            "entry_date": t.get("entry_date"),
            "exit_date":  t.get("exit_date"),
            "return_pct": _safe_float(t.get("return_pct", 0)),
            "holding_days": t.get("holding_days", 1),
            "outcome": t.get("outcome", "loss"),
            "pnl": _safe_float(t.get("pnl", 0)),
        }
        for t in trade_log
    ]


def return_distribution(trade_log: List[Dict], bins: int = 20) -> List[Dict]:
    """Histogram of trade returns."""
    if not trade_log:
        return []
    returns = np.array([t.get("return_pct", 0) for t in trade_log])
    counts, edges = np.histogram(returns, bins=bins)
    result = []
    for i in range(len(counts)):
        bucket_label = f"{edges[i]:.1f}% to {edges[i+1]:.1f}%"
        result.append({
            "bucket": bucket_label,
            "min": round(float(edges[i]), 2),
            "max": round(float(edges[i + 1]), 2),
            "count": int(counts[i]),
        })
    return result


# ─────────────────────────────────────────────────────────────────────────────
# OPTIMIZATION CHARTS
# ─────────────────────────────────────────────────────────────────────────────

def param_heatmap(opt_results: List[Dict], param1: str, param2: str,
                  metric: str) -> List[Dict]:
    """2D heatmap: param1 × param2 → metric value."""
    result = []
    for r in opt_results:
        p = r.get("params", {})
        v = r.get(metric)
        if p.get(param1) is not None and p.get(param2) is not None and v is not None:
            result.append({
                "p1_label": param1,
                "p2_label": param2,
                param1: _safe_float(p[param1]),
                param2: _safe_float(p[param2]),
                metric: _safe_float(v),
            })
    return result


def sensitivity_chart(opt_results: List[Dict], param: str,
                      metric: str) -> List[Dict]:
    """How does metric change as a single param varies (others at default)?"""
    # Group by param value, average the metric
    grouped: Dict[float, List[float]] = {}
    for r in opt_results:
        pv = r.get("params", {}).get(param)
        mv = r.get(metric)
        if pv is not None and mv is not None:
            grouped.setdefault(float(pv), []).append(float(mv))

    result = []
    for pv in sorted(grouped.keys()):
        vals = grouped[pv]
        result.append({
            "param_value": round(pv, 4),
            "metric_avg": round(float(np.mean(vals)), 4),
            "metric_best": round(float(np.max(vals)), 4),
        })
    return result


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE CHARTS
# ─────────────────────────────────────────────────────────────────────────────

def feature_importance_bar(importance: Dict[str, float]) -> List[Dict]:
    """Horizontal bar chart data — sorted descending."""
    items = [(k, v) for k, v in importance.items() if v is not None]
    items.sort(key=lambda x: abs(x[1]), reverse=True)
    return [{"feature": k, "importance": round(float(v), 4)} for k, v in items]


def correlation_matrix_chart(corr_df: pd.DataFrame) -> List[Dict]:
    """Flat list of {feature_a, feature_b, correlation} for heatmap rendering."""
    result = []
    for col in corr_df.columns:
        for idx in corr_df.index:
            v = corr_df.loc[idx, col]
            result.append({
                "feature_a": str(idx),
                "feature_b": str(col),
                "correlation": _safe_float(v),
            })
    return result


# ─────────────────────────────────────────────────────────────────────────────
# MODEL CHARTS
# ─────────────────────────────────────────────────────────────────────────────

def calibration_curve(prob_bins: List[float], actual_freqs: List[float]) -> List[Dict]:
    """Reliability diagram: predicted probability vs actual frequency."""
    result = []
    for p, a in zip(prob_bins, actual_freqs):
        result.append({
            "predicted_prob": round(float(p), 4),
            "actual_freq": round(float(a), 4),
            "perfect": round(float(p), 4),   # diagonal reference line
        })
    return result


# ─────────────────────────────────────────────────────────────────────────────
# SECTOR / REGIME CHARTS
# ─────────────────────────────────────────────────────────────────────────────

def sector_performance_chart(sector_data: Dict) -> List[Dict]:
    """Bar chart: sector → return_pct."""
    result = []
    for sector, stats in sector_data.items():
        result.append({
            "sector": sector,
            "return_pct": _safe_float(stats.get("return_pct")),
            "sharpe": _safe_float(stats.get("sharpe")),
            "avg_composite": _safe_float(stats.get("avg_composite")),
        })
    return sorted(result, key=lambda x: (x.get("return_pct") or -999), reverse=True)


def regime_bar_chart(regime_perf: Dict) -> List[Dict]:
    """Bar chart: regime → win_rate, avg_return."""
    result = []
    for regime, stats in regime_perf.items():
        result.append({
            "regime": regime,
            "win_rate": _safe_float(stats.get("win_rate")),
            "avg_return": _safe_float(stats.get("avg_return")),
            "sharpe": _safe_float(stats.get("sharpe")),
            "trade_count": stats.get("trade_count"),
        })
    return result


# ─────────────────────────────────────────────────────────────────────────────
# COMPOSITE BUILDER — wraps all chart types for a backtest result
# ─────────────────────────────────────────────────────────────────────────────

def build_all_charts(equity_series: pd.Series, trade_log: List[Dict],
                     dates: Optional[List[str]] = None,
                     benchmark_series: Optional[pd.Series] = None) -> Dict[str, List]:
    """Build all standard charts for an indicator backtest experiment."""
    charts = {}

    try:
        charts["equity_curve"] = equity_curve(
            equity_series, dates, benchmark_series
        )
    except Exception as e:
        logger.warning(f"equity_curve error: {e}")
        charts["equity_curve"] = []

    try:
        charts["drawdown"] = drawdown_curve(equity_series, dates)
    except Exception as e:
        logger.warning(f"drawdown error: {e}")
        charts["drawdown"] = []

    try:
        charts["underwater"] = underwater_plot(equity_series, dates)
    except Exception as e:
        charts["underwater"] = []

    try:
        charts["rolling_sharpe"] = rolling_sharpe_chart(equity_series, dates)
    except Exception as e:
        charts["rolling_sharpe"] = []

    try:
        charts["rolling_cagr"] = rolling_cagr_chart(equity_series, dates)
    except Exception as e:
        charts["rolling_cagr"] = []

    try:
        charts["rolling_vol"] = rolling_vol_chart(equity_series, dates)
    except Exception as e:
        charts["rolling_vol"] = []

    try:
        charts["monthly_heatmap"] = monthly_heatmap(equity_series, dates)
    except Exception as e:
        charts["monthly_heatmap"] = []

    try:
        charts["yearly_heatmap"] = yearly_heatmap(equity_series, dates)
    except Exception as e:
        charts["yearly_heatmap"] = []

    try:
        charts["trade_scatter"] = trade_scatter(trade_log)
    except Exception as e:
        charts["trade_scatter"] = []

    try:
        charts["return_distribution"] = return_distribution(trade_log)
    except Exception as e:
        charts["return_distribution"] = []

    return charts
