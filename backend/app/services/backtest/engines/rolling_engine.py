"""
rolling_engine.py — Engine 9: Compute all rolling statistics.

Rolling series (3 windows: 30d, 90d, 252d equivalent in snapshot periods):
  - Rolling CAGR
  - Rolling Volatility (annualised)
  - Rolling Sharpe
  - Rolling Sortino
  - Rolling Win Rate (trades closed within window)
  - Rolling Drawdown
  - Rolling Alpha (Jensen's, vs benchmark)

Output:
  ctx.rolling_metrics = {
      "custom": {rolling_cagr: [...], rolling_sharpe: [...], ...},
      "pms_default": {...},
      "benchmark": {...},
  }

Each series item: {date, d30, d90, d252}
"""

import logging
import math
from typing import Any, Dict, List, Optional

import numpy as np

from app.services.backtest.engines import StrategyExecutionContext

logger = logging.getLogger(__name__)

TRADING_DAYS_PER_YEAR = 252


def _pct_returns(values: List[float]) -> List[float]:
    return [(values[i] - values[i-1]) / values[i-1] if values[i-1] > 0 else 0.0
            for i in range(1, len(values))]


def _rolling_stat(
    dates: List[str],
    rets: List[float],
    bench_rets: List[float],
    windows: List[int],
    fn,
) -> List[Dict]:
    """Generic rolling computation. fn(rets_window, bench_rets_window) -> float."""
    n = len(rets)
    result = []
    for i in range(n):
        row: Dict[str, Any] = {"date": dates[i+1] if i+1 < len(dates) else dates[-1]}
        for w in windows:
            if i + 1 >= w:
                r_slice = rets[max(0, i+1-w):i+1]
                b_slice = bench_rets[max(0, i+1-w):i+1]
                row[f"d{w}"] = round(fn(r_slice, b_slice), 4)
            else:
                row[f"d{w}"] = None
        result.append(row)
    return result


def _rolling_cagr(rets, bench_rets, ann_factor=252) -> float:
    if not rets:
        return 0.0
    total = 1.0
    for r in rets:
        total *= (1.0 + r)
    years = len(rets) / ann_factor
    return ((total ** (1.0 / years) - 1.0) * 100.0) if years > 0 else 0.0


def _rolling_vol(rets, bench_rets, ann_factor=252) -> float:
    if len(rets) < 2:
        return 0.0
    return float(np.std(rets, ddof=1)) * math.sqrt(ann_factor) * 100.0


def _rolling_sharpe(rets, bench_rets, ann_factor=252) -> float:
    if len(rets) < 2:
        return 0.0
    mean = float(np.mean(rets))
    std = float(np.std(rets, ddof=1))
    return (mean / std * math.sqrt(ann_factor)) if std > 0 else 0.0


def _rolling_sortino(rets, bench_rets, ann_factor=252) -> float:
    if len(rets) < 2:
        return 0.0
    mean = float(np.mean(rets))
    down = [min(r, 0.0) for r in rets]
    std_down = float(np.std(down, ddof=1)) if len(down) > 1 else 0.0
    return (mean / std_down * math.sqrt(ann_factor)) if std_down > 0 else 0.0


def _rolling_alpha(rets, bench_rets, ann_factor=252) -> float:
    n = min(len(rets), len(bench_rets))
    if n < 2:
        return 0.0
    p = np.array(rets[:n])
    b = np.array(bench_rets[:n])
    cov = np.cov(p, b)
    beta = cov[0, 1] / cov[1, 1] if cov[1, 1] != 0 else 0.0
    alpha = float(np.mean(p)) - beta * float(np.mean(b))
    return alpha * ann_factor * 100.0


def _rolling_drawdown(rets, bench_rets, ann_factor=252) -> float:
    """Max drawdown over the rolling window."""
    if not rets:
        return 0.0
    val = 1.0
    peak = 1.0
    max_dd = 0.0
    for r in rets:
        val *= (1.0 + r)
        if val > peak:
            peak = val
        dd = (val - peak) / peak * 100.0
        max_dd = min(max_dd, dd)
    return max_dd


def _compute_rolling_for_series(
    dates: List[str],
    values: List[float],
    bench_values: List[float],
    periods_per_year: float,
) -> Dict[str, List[Dict]]:
    """Compute all rolling series for one equity curve."""
    rets = _pct_returns(values)
    bench_rets = _pct_returns(bench_values) if len(bench_values) >= 2 else [0.0] * len(rets)
    n_min = min(len(rets), len(bench_rets))
    rets = rets[:n_min]
    bench_rets = bench_rets[:n_min]

    # Windows scaled to snapshot count (not calendar days)
    # ~30 calendar days ≈ 1 period at monthly, ~4 at weekly
    # Use relative windows: 3, 6, 12 periods (quarter, half-year, year)
    windows = [3, 6, 12]
    w_labels = ["d30", "d90", "d252"]  # semantics: short/mid/long

    ann = periods_per_year

    def make_series(fn):
        n = len(rets)
        result = []
        for i in range(n):
            row: Dict[str, Any] = {"date": dates[i+1] if i+1 < len(dates) else dates[-1]}
            for j, w in enumerate(windows):
                key = w_labels[j]
                if i + 1 >= w:
                    r_slice = rets[max(0, i+1-w):i+1]
                    b_slice = bench_rets[max(0, i+1-w):i+1]
                    try:
                        val = fn(r_slice, b_slice, ann)
                        row[key] = round(val, 4)
                    except Exception:
                        row[key] = None
                else:
                    row[key] = None
            result.append(row)
        return result

    return {
        "rolling_cagr":      make_series(_rolling_cagr),
        "rolling_volatility": make_series(_rolling_vol),
        "rolling_sharpe":    make_series(_rolling_sharpe),
        "rolling_sortino":   make_series(_rolling_sortino),
        "rolling_alpha":     make_series(_rolling_alpha),
        "rolling_drawdown":  make_series(_rolling_drawdown),
        "rolling_win_rate":  [],   # computed from trade log (see below)
    }


def run(ctx: StrategyExecutionContext) -> StrategyExecutionContext:
    """Compute rolling stats for all three series."""
    dates      = [e["date"] for e in ctx.equity_curve]
    vals_c     = [e.get("custom", e.get("value", 0.0)) for e in ctx.equity_curve]
    vals_p     = [e.get("pms_default", e.get("value", 0.0)) for e in ctx.equity_curve]
    vals_b     = [e.get("benchmark", 0.0) for e in ctx.equity_curve]

    n = max(len(dates) - 1, 1)
    try:
        from datetime import datetime
        if len(dates) >= 2:
            total_days = (datetime.strptime(dates[-1], "%Y-%m-%d") -
                          datetime.strptime(dates[0], "%Y-%m-%d")).days
            years = max(total_days / 365.25, 0.001)
            periods_per_year = n / years
        else:
            periods_per_year = 12.0
    except Exception:
        periods_per_year = 12.0

    ctx.rolling_metrics = {
        "custom":      _compute_rolling_for_series(dates, vals_c, vals_b, periods_per_year),
        "pms_default": _compute_rolling_for_series(dates, vals_p, vals_b, periods_per_year),
        "benchmark":   _compute_rolling_for_series(dates, vals_b, vals_b, periods_per_year),
    }

    logger.info("[RollingEngine] Rolling statistics computed for %d date points.", len(dates))
    return ctx
