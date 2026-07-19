"""
metrics_engine.py — Engine 8: Compute all 30+ performance metrics across three parallel series.

Inputs (from ctx):
  ctx.equity_curve        — [{date, value}] — custom strategy equity
  ctx.pms_equity_curve    — [{date, value}] — PMS default equity (Equal-weight on archived ratings)
  ctx.benchmark_prices    — {date: price}
  ctx.benchmark_initial_price
  ctx.trade_log           — enriched trade records
  ctx.portfolio_ledger    — per-date portfolio snapshots

Outputs (populated on ctx):
  ctx.custom_metrics          — full PerformanceMetrics dict for custom strategy
  ctx.pms_default_metrics     — full PerformanceMetrics dict for PMS default
  ctx.benchmark_metrics_dict  — full PerformanceMetrics dict for benchmark
  ctx.equity_curve            — enriched with benchmark column [{date, custom, pms_default, benchmark}]
  ctx.win_loss_histogram
  ctx.sector_allocation_timeline
  ctx.benchmark_comparison_table
"""

import logging
import math
from typing import Any, Dict, List, Optional

import numpy as np

from app.services.backtest.engines import StrategyExecutionContext

logger = logging.getLogger(__name__)

TRADING_DAYS_PER_YEAR = 252
RF_RATE = 0.0  # risk-free rate (assume 0 for simplicity)


# ── Core math helpers ─────────────────────────────────────────────────────────

def _pct_returns(values: List[float]) -> List[float]:
    """Compute period-over-period percentage returns."""
    rets = []
    for i in range(1, len(values)):
        prev = values[i - 1]
        curr = values[i]
        rets.append((curr - prev) / prev if prev > 0 else 0.0)
    return rets


def _cagr(start_val: float, end_val: float, years: float) -> float:
    if start_val <= 0 or years <= 0:
        return 0.0
    return ((end_val / start_val) ** (1.0 / years) - 1.0) * 100.0


def _annualized_vol(returns: List[float], periods_per_year: float) -> float:
    if len(returns) < 2:
        return 0.0
    return float(np.std(returns, ddof=1)) * math.sqrt(periods_per_year) * 100.0


def _max_drawdown(values: List[float]) -> tuple:
    """Returns (max_drawdown_pct, drawdown_series [{date?, dd_pct}])."""
    if not values:
        return 0.0, []
    peak = values[0]
    max_dd = 0.0
    dd_series = []
    recovery_map = []
    for v in values:
        if v > peak:
            peak = v
        dd = (v - peak) / peak * 100.0
        dd_series.append(dd)
        max_dd = min(max_dd, dd)
    return max_dd, dd_series


def _sharpe(returns: List[float], periods_per_year: float) -> float:
    if len(returns) < 2:
        return 0.0
    mean = float(np.mean(returns)) - RF_RATE / periods_per_year
    std = float(np.std(returns, ddof=1))
    return (mean / std * math.sqrt(periods_per_year)) if std > 0 else 0.0


def _sortino(returns: List[float], periods_per_year: float) -> float:
    if len(returns) < 2:
        return 0.0
    mean = float(np.mean(returns))
    downside = [min(r, 0.0) for r in returns]
    downside_std = float(np.std(downside, ddof=1)) if len(downside) > 1 else 0.0
    return (mean / downside_std * math.sqrt(periods_per_year)) if downside_std > 0 else 0.0


def _beta_alpha(port_rets: List[float], bench_rets: List[float], periods_per_year: float):
    n = min(len(port_rets), len(bench_rets))
    if n < 2:
        return 0.0, 0.0
    p = np.array(port_rets[:n])
    b = np.array(bench_rets[:n])
    cov = np.cov(p, b)
    beta = cov[0, 1] / cov[1, 1] if cov[1, 1] != 0 else 0.0
    alpha_period = float(np.mean(p)) - beta * float(np.mean(b))
    alpha_ann = alpha_period * periods_per_year * 100.0
    return float(beta), alpha_ann


def _information_ratio(port_rets: List[float], bench_rets: List[float]) -> float:
    n = min(len(port_rets), len(bench_rets))
    if n < 2:
        return 0.0
    diff = np.array(port_rets[:n]) - np.array(bench_rets[:n])
    mean_diff = float(np.mean(diff))
    std_diff = float(np.std(diff, ddof=1))
    return (mean_diff / std_diff) if std_diff > 0 else 0.0


def _calmar(cagr_pct: float, max_dd_pct: float) -> float:
    return abs(cagr_pct / max_dd_pct) if max_dd_pct != 0 else 0.0


def _treynor(port_rets: List[float], beta: float, periods_per_year: float) -> float:
    if beta == 0:
        return 0.0
    mean_ret_ann = float(np.mean(port_rets)) * periods_per_year
    return (mean_ret_ann - RF_RATE) / beta


def _trade_metrics(trades: List[Dict]) -> Dict[str, float]:
    if not trades:
        return {
            "total_trades": 0, "win_rate_pct": 0.0, "loss_rate_pct": 0.0,
            "avg_win_pct": 0.0, "avg_loss_pct": 0.0, "profit_factor": 0.0,
            "expectancy_pct": 0.0, "avg_holding_days": 0.0,
        }
    rets = [t["return_pct"] for t in trades]
    wins = [r for r in rets if r > 0]
    losses = [r for r in rets if r <= 0]
    n = len(rets)
    win_rate = len(wins) / n if n > 0 else 0.0
    loss_rate = len(losses) / n if n > 0 else 0.0
    avg_win = float(np.mean(wins)) if wins else 0.0
    avg_loss = float(np.mean(losses)) if losses else 0.0
    gross_profit = sum(wins) if wins else 0.0
    gross_loss = abs(sum(losses)) if losses else 0.0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else (1.0 if not losses else 0.0)
    expectancy = win_rate * avg_win + loss_rate * avg_loss
    avg_hold = float(np.mean([t.get("holding_days", 0) for t in trades])) if trades else 0.0
    return {
        "total_trades": n,
        "win_rate_pct": round(win_rate * 100.0, 2),
        "loss_rate_pct": round(loss_rate * 100.0, 2),
        "avg_win_pct": round(avg_win, 4),
        "avg_loss_pct": round(avg_loss, 4),
        "profit_factor": round(profit_factor, 4),
        "expectancy_pct": round(expectancy, 4),
        "avg_holding_days": round(avg_hold, 1),
    }


def _monthly_returns(dates: List[str], values: List[float]) -> List[Dict]:
    monthly: Dict[str, List[float]] = {}
    for i in range(1, min(len(dates), len(values))):
        ym = dates[i][:7]  # YYYY-MM
        r = (values[i] - values[i-1]) / values[i-1] if values[i-1] > 0 else 0.0
        monthly.setdefault(ym, []).append(r)
    result = []
    for ym, rets in sorted(monthly.items()):
        total = 1.0
        for r in rets:
            total *= (1.0 + r)
        total = (total - 1.0) * 100.0
        yr, mn = ym.split("-")
        result.append({"year": int(yr), "month": int(mn), "return_pct": round(total, 4)})
    return result


def _yearly_returns(dates: List[str], values: List[float]) -> List[Dict]:
    yearly: Dict[str, List[float]] = {}
    for i in range(1, min(len(dates), len(values))):
        yr = dates[i][:4]
        r = (values[i] - values[i-1]) / values[i-1] if values[i-1] > 0 else 0.0
        yearly.setdefault(yr, []).append(r)
    result = []
    for yr, rets in sorted(yearly.items()):
        total = 1.0
        for r in rets:
            total *= (1.0 + r)
        result.append({"year": int(yr), "return_pct": round((total - 1.0) * 100.0, 4)})
    return result


def _win_loss_histogram(trades: List[Dict]) -> List[Dict]:
    buckets = [(-100, -30), (-30, -20), (-20, -10), (-10, -5), (-5, 0),
               (0, 5), (5, 10), (10, 20), (20, 30), (30, 100)]
    hist = []
    for lo, hi in buckets:
        count = sum(1 for t in trades if lo <= t["return_pct"] < hi)
        hist.append({"bucket": f"{lo}% to {hi}%", "low": lo, "high": hi, "count": count})
    return hist


def _portfolio_metrics(ctx: StrategyExecutionContext, trades: List[Dict]) -> Dict[str, Any]:
    ledger = ctx.portfolio_ledger
    if not ledger:
        return {}
    avg_score = float(np.mean([e.get("avg_score", 0) for e in ledger])) if ledger else 0.0
    avg_turn = float(np.mean([e.get("turnover_pct", 0) for e in ledger])) if ledger else 0.0
    avg_cash = float(np.mean([e.get("cash_pct", 0) for e in ledger])) if ledger else 0.0
    # Time-averaged sector allocation
    all_sectors: Dict[str, List[float]] = {}
    for e in ledger:
        for sector, w in e.get("sector_allocation", {}).items():
            all_sectors.setdefault(sector, []).append(w)
    sector_alloc = {k: round(float(np.mean(v)), 4) for k, v in all_sectors.items()}
    # Top-5 weight
    top5_weights = []
    for e in ledger:
        sorted_h = sorted(e.get("top_holdings", []), key=lambda x: x.get("weight", 0), reverse=True)
        top5 = sum(h.get("weight", 0) for h in sorted_h[:5])
        top5_weights.append(top5)
    top5_avg = float(np.mean(top5_weights)) * 100.0 if top5_weights else 0.0
    return {
        "avg_portfolio_score": round(avg_score, 2),
        "avg_turnover_pct": round(avg_turn, 2),
        "avg_cash_utilization_pct": round(100.0 - avg_cash, 2),
        "sector_allocation": sector_alloc,
        "avg_position_concentration_pct": 0.0,
        "top5_weight_pct": round(top5_avg, 2),
        "feature_utilization_pct": 0.0,
    }


def _compute_metrics(
    dates: List[str],
    values: List[float],
    bench_values: List[float],
    trades: List[Dict],
    periods_per_year: float,
    ctx: StrategyExecutionContext,
    label: str = "strategy",
) -> Dict[str, Any]:
    """Compute full PerformanceMetrics dict for one equity series."""
    if not values or len(values) < 2:
        return {}

    total_years = (len(values) - 1) / periods_per_year
    total_return = (values[-1] - values[0]) / values[0] * 100.0
    cagr = _cagr(values[0], values[-1], total_years)

    port_rets = _pct_returns(values)
    bench_rets = _pct_returns(bench_values) if len(bench_values) >= 2 else [0.0] * len(port_rets)
    # Align lengths
    n = min(len(port_rets), len(bench_rets))
    port_rets_a = port_rets[:n]
    bench_rets_a = bench_rets[:n]

    vol = _annualized_vol(port_rets_a, periods_per_year)
    sharpe = _sharpe(port_rets_a, periods_per_year)
    sortino = _sortino(port_rets_a, periods_per_year)
    beta, alpha = _beta_alpha(port_rets_a, bench_rets_a, periods_per_year)
    max_dd, dd_series = _max_drawdown(values)
    calmar = _calmar(cagr, max_dd)
    ir = _information_ratio(port_rets_a, bench_rets_a)
    treynor = _treynor(port_rets_a, beta, periods_per_year)

    # Drawdown curve merged with dates
    dd_curve = [{"date": dates[i], "drawdown_pct": round(dd_series[i], 4)} for i in range(len(dd_series))]

    # Recovery days
    max_recovery = 0
    underwater_count = 0
    curr_recovery = 0
    for dd in dd_series:
        if dd < 0:
            curr_recovery += 1
            underwater_count += 1
        else:
            max_recovery = max(max_recovery, curr_recovery)
            curr_recovery = 0
    max_recovery = max(max_recovery, curr_recovery)

    trade_m = _trade_metrics(trades)
    monthly = _monthly_returns(dates, values)
    yearly = _yearly_returns(dates, values)

    # Benchmark relative
    bench_total = (bench_values[-1] - bench_values[0]) / bench_values[0] * 100.0 if bench_values and bench_values[0] > 0 else 0.0
    bench_cagr = _cagr(bench_values[0], bench_values[-1], total_years) if bench_values else 0.0
    bench_max_dd, _ = _max_drawdown(bench_values) if bench_values else (0.0, [])
    excess_ret = total_return - bench_total
    tracking_err = _annualized_vol([p - b for p, b in zip(port_rets_a, bench_rets_a)], periods_per_year)
    rel_sharpe = sharpe - _sharpe(bench_rets_a, periods_per_year)
    rel_cagr = cagr - bench_cagr
    rel_max_dd = max_dd - bench_max_dd

    portfolio_m = _portfolio_metrics(ctx, trades) if label == "strategy" else {}

    return {
        "returns": {
            "total_return_pct": round(total_return, 4),
            "cagr_pct": round(cagr, 4),
            "annualized_return_pct": round(cagr, 4),
            "monthly_returns": monthly,
            "quarterly_returns": [],  # computed from monthly in frontend
            "yearly_returns": yearly,
        },
        "risk": {
            "annualized_volatility_pct": round(vol, 4),
            "beta": round(beta, 4),
            "alpha_pct": round(alpha, 4),
            "sharpe_ratio": round(sharpe, 4),
            "sortino_ratio": round(sortino, 4),
            "calmar_ratio": round(calmar, 4),
            "information_ratio": round(ir, 4),
            "treynor_ratio": round(treynor, 6),
        },
        "drawdown": {
            "max_drawdown_pct": round(max_dd, 4),
            "avg_drawdown_pct": round(float(np.mean([d for d in dd_series if d < 0]) if any(d < 0 for d in dd_series) else 0.0), 4),
            "max_recovery_days": max_recovery,
            "total_underwater_days": underwater_count,
            "drawdown_curve": dd_curve,
        },
        "trades": trade_m,
        "portfolio": portfolio_m,
        "benchmark_relative": {
            "excess_return_pct": round(excess_ret, 4),
            "tracking_error_pct": round(tracking_err, 4),
            "relative_max_drawdown_pct": round(rel_max_dd, 4),
            "relative_sharpe": round(rel_sharpe, 4),
            "relative_cagr_pct": round(rel_cagr, 4),
        },
    }


def _build_benchmark_comparison_table(
    custom: Dict, pms: Dict, bench: Dict
) -> List[Dict]:
    rows = []

    def _row(metric_key: str, label: str, path: List[str], higher_better: bool = True):
        def _get(d, path):
            for k in path:
                if isinstance(d, dict):
                    d = d.get(k, 0.0)
                else:
                    return 0.0
            return d if isinstance(d, (int, float)) else 0.0

        cv = _get(custom, path)
        pv = _get(pms, path)
        bv = _get(bench, path)
        rows.append({
            "metric": metric_key,
            "metric_label": label,
            "strategy_value": round(float(cv), 4),
            "pms_default_value": round(float(pv), 4),
            "benchmark_value": round(float(bv), 4),
            "strategy_vs_default": round(float(cv) - float(pv), 4),
            "strategy_vs_benchmark": round(float(cv) - float(bv), 4),
            "higher_is_better": higher_better,
        })

    _row("total_return", "Total Return (%)", ["returns", "total_return_pct"])
    _row("cagr", "CAGR (%)", ["returns", "cagr_pct"])
    _row("sharpe", "Sharpe Ratio", ["risk", "sharpe_ratio"])
    _row("sortino", "Sortino Ratio", ["risk", "sortino_ratio"])
    _row("calmar", "Calmar Ratio", ["risk", "calmar_ratio"])
    _row("alpha", "Alpha (%)", ["risk", "alpha_pct"])
    _row("beta", "Beta", ["risk", "beta"], higher_better=False)
    _row("volatility", "Annualised Volatility (%)", ["risk", "annualized_volatility_pct"], higher_better=False)
    _row("max_drawdown", "Max Drawdown (%)", ["drawdown", "max_drawdown_pct"], higher_better=False)
    _row("information_ratio", "Information Ratio", ["risk", "information_ratio"])
    _row("win_rate", "Win Rate (%)", ["trades", "win_rate_pct"])
    _row("profit_factor", "Profit Factor", ["trades", "profit_factor"])
    _row("excess_return", "Excess Return vs Benchmark (%)", ["benchmark_relative", "excess_return_pct"])

    return rows


def run(ctx: StrategyExecutionContext) -> StrategyExecutionContext:
    """
    Compute performance metrics for all three series.
    """
    eq_custom  = ctx.equity_curve        # [{date, value}]
    eq_pms     = ctx.pms_equity_curve    # [{date, value}]
    dates      = [e["date"] for e in eq_custom]
    vals_c     = [e["value"] for e in eq_custom]
    vals_p     = [e["value"] for e in eq_pms]

    # Benchmark equity curve (scaled to initial_capital)
    bmark_initial = ctx.benchmark_initial_price
    vals_b = []
    for d in dates:
        price = ctx.benchmark_prices.get(d, 0.0)
        if price > 0 and bmark_initial > 0:
            vals_b.append(ctx.initial_capital * price / bmark_initial)
        else:
            vals_b.append(ctx.initial_capital)

    # Periods per year (approximate from snapshot frequency)
    n_dates = max(len(dates) - 1, 1)
    try:
        from datetime import datetime
        if len(dates) >= 2:
            total_days = (datetime.strptime(dates[-1], "%Y-%m-%d") - datetime.strptime(dates[0], "%Y-%m-%d")).days
            years = max(total_days / 365.25, 0.001)
            periods_per_year = n_dates / years
        else:
            periods_per_year = 12.0
    except Exception:
        periods_per_year = 12.0

    # Compute metrics
    ctx.custom_metrics = _compute_metrics(dates, vals_c, vals_b, ctx.trade_log, periods_per_year, ctx, "strategy")
    ctx.pms_default_metrics = _compute_metrics(dates, vals_p, vals_b, [], periods_per_year, ctx, "pms_default")
    ctx.benchmark_metrics_dict = _compute_metrics(dates, vals_b, vals_b, [], periods_per_year, ctx, "benchmark")

    # Enrich equity_curve with all 3 series
    ctx.equity_curve = [
        {
            "date": dates[i],
            "custom": round(vals_c[i] if i < len(vals_c) else 0.0, 2),
            "pms_default": round(vals_p[i] if i < len(vals_p) else 0.0, 2),
            "benchmark": round(vals_b[i] if i < len(vals_b) else 0.0, 2),
        }
        for i in range(len(dates))
    ]

    # Benchmark comparison table
    ctx.benchmark_comparison_table = _build_benchmark_comparison_table(
        ctx.custom_metrics, ctx.pms_default_metrics, ctx.benchmark_metrics_dict
    )

    # Win/loss histogram
    ctx.win_loss_histogram = _win_loss_histogram(ctx.trade_log)

    # Sector allocation timeline from portfolio_ledger
    ctx.sector_allocation_timeline = [
        {"date": e["date"], **e.get("sector_allocation", {})}
        for e in ctx.portfolio_ledger
    ]

    logger.info("[MetricsEngine] Custom CAGR=%.2f%% Sharpe=%.2f MaxDD=%.2f%%",
                ctx.custom_metrics.get("returns", {}).get("cagr_pct", 0.0),
                ctx.custom_metrics.get("risk", {}).get("sharpe_ratio", 0.0),
                ctx.custom_metrics.get("drawdown", {}).get("max_drawdown_pct", 0.0))
    return ctx
