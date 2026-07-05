"""
metrics.py — Institutional metrics suite for the Quant Research Laboratory.

All computations are pure pandas/numpy. No external libraries (no pyfolio, etc.).

Input:
  - equity_series: pd.Series of daily portfolio values
  - trade_log: list[dict] from backtester.run_backtest()
  - benchmark_series: optional pd.Series of benchmark daily values
  - rf_rate: annual risk-free rate (default 6.5% for Indian market)
"""

import logging
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

TRADING_DAYS_PER_YEAR = 252
DEFAULT_RF_RATE = 0.065   # 6.5% — approximate Indian 10Y government bond yield


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def compute_all_metrics(
    equity_series: pd.Series,
    trade_log: List[Dict],
    benchmark_series: Optional[pd.Series] = None,
    rf_rate: float = DEFAULT_RF_RATE,
    equity_dates: Optional[List[str]] = None,
) -> Dict:
    """Compute all institutional metrics. Returns a flat dict."""
    if equity_series is None or len(equity_series) < 2:
        return _empty_metrics()

    try:
        returns = equity_series.pct_change().dropna()
        metrics = {}

        # ── Returns ──────────────────────────────────────────
        metrics["total_return_pct"]      = _total_return(equity_series)
        metrics["cagr_pct"]              = _cagr(equity_series)
        metrics["annualized_return_pct"] = metrics["cagr_pct"]

        # ── Risk ─────────────────────────────────────────────
        metrics["annualized_volatility_pct"] = _annualized_vol(returns)
        metrics["downside_deviation_pct"]    = _downside_deviation(returns, rf_rate)
        metrics["var_95_pct"]                = _var(returns, 0.95)
        metrics["var_99_pct"]                = _var(returns, 0.99)
        metrics["cvar_95_pct"]               = _cvar(returns, 0.95)

        # ── Risk-Adjusted ─────────────────────────────────────
        metrics["sharpe_ratio"]  = _sharpe(returns, rf_rate)
        metrics["sortino_ratio"] = _sortino(returns, rf_rate)
        metrics["calmar_ratio"]  = _calmar(equity_series)
        metrics["omega_ratio"]   = _omega(returns, rf_rate)
        metrics["mar_ratio"]     = _mar(equity_series)

        # ── Drawdown ──────────────────────────────────────────
        dd = _drawdown_series(equity_series)
        metrics["max_drawdown_pct"]    = float(dd.min() * 100)
        metrics["avg_drawdown_pct"]    = float(dd[dd < 0].mean() * 100) if (dd < 0).any() else 0.0
        metrics["ulcer_index"]         = _ulcer_index(dd)
        metrics["recovery_factor"]     = _recovery_factor(equity_series, dd)
        metrics["time_underwater_pct"] = float((dd < 0).mean() * 100)

        # ── Trade Statistics ──────────────────────────────────
        trade_stats = _trade_stats(trade_log)
        metrics.update(trade_stats)

        # ── Distribution ─────────────────────────────────────
        metrics["skewness"]  = float(returns.skew()) if len(returns) > 3 else 0.0
        metrics["kurtosis"]  = float(returns.kurt()) if len(returns) > 3 else 0.0

        # ── vs Benchmark ──────────────────────────────────────
        if benchmark_series is not None and len(benchmark_series) >= len(equity_series):
            bench_ret = benchmark_series.pct_change().dropna().iloc[:len(returns)].reset_index(drop=True)
            returns_aligned = returns.reset_index(drop=True)
            metrics["beta"]              = _beta(returns_aligned, bench_ret)
            metrics["alpha_pct"]         = _alpha(returns_aligned, bench_ret, rf_rate, metrics["beta"])
            metrics["tracking_error_pct"]= _tracking_error(returns_aligned, bench_ret)
            metrics["information_ratio"] = _information_ratio(returns_aligned, bench_ret)
            metrics["upside_capture"]    = _upside_capture(returns_aligned, bench_ret)
            metrics["downside_capture"]  = _downside_capture(returns_aligned, bench_ret)
        else:
            for k in ["beta", "alpha_pct", "tracking_error_pct",
                      "information_ratio", "upside_capture", "downside_capture"]:
                metrics[k] = None

        # Round all float metrics to 4 decimal places
        for k, v in metrics.items():
            if isinstance(v, float):
                metrics[k] = round(v, 4)

        return metrics

    except Exception as e:
        logger.error(f"compute_all_metrics error: {e}", exc_info=True)
        return _empty_metrics()


# ─────────────────────────────────────────────────────────────────────────────
# RETURN METRICS
# ─────────────────────────────────────────────────────────────────────────────

def _total_return(equity: pd.Series) -> float:
    if equity.iloc[0] == 0:
        return 0.0
    return float((equity.iloc[-1] / equity.iloc[0] - 1) * 100)


def _cagr(equity: pd.Series) -> float:
    n = len(equity)
    if n < 2 or equity.iloc[0] == 0:
        return 0.0
    years = n / TRADING_DAYS_PER_YEAR
    ratio = equity.iloc[-1] / equity.iloc[0]
    if ratio <= 0:
        return -100.0
    return float((ratio ** (1 / years) - 1) * 100)


# ─────────────────────────────────────────────────────────────────────────────
# RISK METRICS
# ─────────────────────────────────────────────────────────────────────────────

def _annualized_vol(returns: pd.Series) -> float:
    if len(returns) < 2:
        return 0.0
    return float(returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR) * 100)


def _downside_deviation(returns: pd.Series, rf_rate: float) -> float:
    daily_rf = rf_rate / TRADING_DAYS_PER_YEAR
    downside = returns[returns < daily_rf]
    if downside.empty:
        return 0.0
    return float(downside.std() * np.sqrt(TRADING_DAYS_PER_YEAR) * 100)


def _var(returns: pd.Series, confidence: float) -> float:
    if returns.empty:
        return 0.0
    return float(np.percentile(returns, (1 - confidence) * 100) * 100)


def _cvar(returns: pd.Series, confidence: float) -> float:
    if returns.empty:
        return 0.0
    threshold = np.percentile(returns, (1 - confidence) * 100)
    tail = returns[returns <= threshold]
    return float(tail.mean() * 100) if not tail.empty else 0.0


# ─────────────────────────────────────────────────────────────────────────────
# RISK-ADJUSTED METRICS
# ─────────────────────────────────────────────────────────────────────────────

def _sharpe(returns: pd.Series, rf_rate: float) -> float:
    if len(returns) < 2:
        return 0.0
    daily_rf = rf_rate / TRADING_DAYS_PER_YEAR
    excess = returns - daily_rf
    vol = excess.std()
    if vol < 1e-6:
        return 0.0
    return float(excess.mean() / vol * np.sqrt(TRADING_DAYS_PER_YEAR))


def _sortino(returns: pd.Series, rf_rate: float) -> float:
    daily_rf = rf_rate / TRADING_DAYS_PER_YEAR
    excess = returns - daily_rf
    downside = excess[excess < 0]
    if downside.empty:
        return float(excess.mean() * TRADING_DAYS_PER_YEAR)  # effectively infinite
    dd_vol = downside.std() * np.sqrt(TRADING_DAYS_PER_YEAR)
    if dd_vol < 1e-6:
        return 0.0
    return float(excess.mean() * TRADING_DAYS_PER_YEAR / dd_vol)


def _calmar(equity: pd.Series) -> float:
    cagr = _cagr(equity)
    dd = _drawdown_series(equity)
    max_dd = abs(dd.min() * 100)
    if max_dd == 0:
        return 0.0
    return float(cagr / max_dd)


def _omega(returns: pd.Series, rf_rate: float) -> float:
    daily_rf = rf_rate / TRADING_DAYS_PER_YEAR
    gains = (returns - daily_rf).clip(lower=0).sum()
    losses = (daily_rf - returns).clip(lower=0).sum()
    if losses == 0:
        return float("inf")
    return float(gains / losses)


def _mar(equity: pd.Series) -> float:
    """MAR Ratio = CAGR / Max Drawdown (same as Calmar but historical full period)."""
    return _calmar(equity)


# ─────────────────────────────────────────────────────────────────────────────
# DRAWDOWN
# ─────────────────────────────────────────────────────────────────────────────

def _drawdown_series(equity: pd.Series) -> pd.Series:
    """Return fractional drawdown series (negative values are drawdowns)."""
    cummax = equity.cummax()
    return (equity - cummax) / cummax.replace(0, np.nan)


def _ulcer_index(dd: pd.Series) -> float:
    """Ulcer Index = sqrt(mean of squared % drawdowns)."""
    dd_pct = dd * 100
    return float(np.sqrt((dd_pct ** 2).mean()))


def _recovery_factor(equity: pd.Series, dd: pd.Series) -> float:
    total_ret = _total_return(equity)
    max_dd = abs(dd.min() * 100)
    if max_dd == 0:
        return 0.0
    return float(total_ret / max_dd)


# ─────────────────────────────────────────────────────────────────────────────
# TRADE STATISTICS
# ─────────────────────────────────────────────────────────────────────────────

def _trade_stats(trade_log: List[Dict]) -> Dict:
    if not trade_log:
        return {
            "trade_count": 0,
            "win_count": 0,
            "loss_count": 0,
            "win_rate_pct": 0.0,
            "profit_factor": 0.0,
            "expectancy_pct": 0.0,
            "kelly_criterion": 0.0,
            "avg_win_pct": 0.0,
            "avg_loss_pct": 0.0,
            "best_trade_pct": 0.0,
            "worst_trade_pct": 0.0,
            "avg_holding_days": 0.0,
        }

    returns = [t["return_pct"] for t in trade_log]
    wins  = [r for r in returns if r > 0]
    losses = [r for r in returns if r <= 0]

    n = len(returns)
    n_win = len(wins)
    n_loss = len(losses)
    win_rate = n_win / n if n > 0 else 0.0

    avg_win  = np.mean(wins)  if wins  else 0.0
    avg_loss = np.mean(losses) if losses else 0.0  # negative

    gross_win  = sum(wins) if wins else 0.0
    gross_loss = abs(sum(losses)) if losses else 0.0
    profit_factor = gross_win / gross_loss if gross_loss > 0 else float("inf")

    # Expectancy: avg return per trade
    expectancy = np.mean(returns) if returns else 0.0

    # Kelly Criterion: W/R - (1-W)/R where R = |avg_win/avg_loss|
    kelly = 0.0
    if avg_loss != 0 and avg_win != 0:
        r_ratio = abs(avg_win / avg_loss)
        kelly = max(0.0, win_rate - (1 - win_rate) / r_ratio)

    holding_days = [t.get("holding_days", 1) for t in trade_log]
    avg_hold = np.mean(holding_days) if holding_days else 0.0

    return {
        "trade_count":     n,
        "win_count":       n_win,
        "loss_count":      n_loss,
        "win_rate_pct":    round(win_rate * 100, 2),
        "profit_factor":   round(profit_factor, 4),
        "expectancy_pct":  round(expectancy, 4),
        "kelly_criterion": round(kelly, 4),
        "avg_win_pct":     round(avg_win, 4),
        "avg_loss_pct":    round(avg_loss, 4),
        "best_trade_pct":  round(max(returns), 4),
        "worst_trade_pct": round(min(returns), 4),
        "avg_holding_days": round(avg_hold, 1),
    }


# ─────────────────────────────────────────────────────────────────────────────
# BENCHMARK METRICS
# ─────────────────────────────────────────────────────────────────────────────

def _beta(portfolio_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    min_len = min(len(portfolio_returns), len(benchmark_returns))
    p = portfolio_returns.iloc[:min_len]
    b = benchmark_returns.iloc[:min_len]
    cov = np.cov(p, b)
    var_b = float(np.var(b))
    if var_b == 0:
        return 1.0
    return float(cov[0, 1] / var_b)


def _alpha(portfolio_returns: pd.Series, benchmark_returns: pd.Series,
           rf_rate: float, beta: float) -> float:
    daily_rf = rf_rate / TRADING_DAYS_PER_YEAR
    p_ann = float(portfolio_returns.mean() * TRADING_DAYS_PER_YEAR)
    b_ann = float(benchmark_returns.mean() * TRADING_DAYS_PER_YEAR)
    return float((p_ann - rf_rate - beta * (b_ann - rf_rate)) * 100)


def _tracking_error(portfolio_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    min_len = min(len(portfolio_returns), len(benchmark_returns))
    active = portfolio_returns.iloc[:min_len] - benchmark_returns.iloc[:min_len]
    return float(active.std() * np.sqrt(TRADING_DAYS_PER_YEAR) * 100)


def _information_ratio(portfolio_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    min_len = min(len(portfolio_returns), len(benchmark_returns))
    active = portfolio_returns.iloc[:min_len] - benchmark_returns.iloc[:min_len]
    te = active.std() * np.sqrt(TRADING_DAYS_PER_YEAR)
    if te == 0:
        return 0.0
    return float(active.mean() * TRADING_DAYS_PER_YEAR / te)


def _upside_capture(portfolio_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    min_len = min(len(portfolio_returns), len(benchmark_returns))
    p = portfolio_returns.iloc[:min_len]
    b = benchmark_returns.iloc[:min_len]
    up_days = b > 0
    if not up_days.any():
        return 0.0
    p_up = (1 + p[up_days]).prod() ** (TRADING_DAYS_PER_YEAR / up_days.sum()) - 1
    b_up = (1 + b[up_days]).prod() ** (TRADING_DAYS_PER_YEAR / up_days.sum()) - 1
    if b_up == 0:
        return 0.0
    return float(p_up / b_up * 100)


def _downside_capture(portfolio_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    min_len = min(len(portfolio_returns), len(benchmark_returns))
    p = portfolio_returns.iloc[:min_len]
    b = benchmark_returns.iloc[:min_len]
    down_days = b < 0
    if not down_days.any():
        return 0.0
    p_down = (1 + p[down_days]).prod() ** (TRADING_DAYS_PER_YEAR / down_days.sum()) - 1
    b_down = (1 + b[down_days]).prod() ** (TRADING_DAYS_PER_YEAR / down_days.sum()) - 1
    if b_down == 0:
        return 0.0
    return float(p_down / b_down * 100)


# ─────────────────────────────────────────────────────────────────────────────
# ROLLING METRICS (for chart_builder)
# ─────────────────────────────────────────────────────────────────────────────

def rolling_sharpe(equity_series: pd.Series,
                   dates: Optional[List[str]] = None,
                   window: int = 30,
                   rf_rate: float = DEFAULT_RF_RATE) -> List[Dict]:
    returns = equity_series.pct_change().dropna()
    daily_rf = rf_rate / TRADING_DAYS_PER_YEAR
    rolling_mean = (returns - daily_rf).rolling(window).mean()
    rolling_std  = (returns - daily_rf).rolling(window).std()
    sharpe = (rolling_mean / rolling_std.replace(0, np.nan)) * np.sqrt(TRADING_DAYS_PER_YEAR)
    result = []
    for i, v in enumerate(sharpe):
        if pd.notna(v):
            d = dates[i] if dates and i < len(dates) else str(i)
            result.append({"date": d, "rolling_sharpe": round(float(v), 4)})
    return result


def rolling_cagr(equity_series: pd.Series,
                 dates: Optional[List[str]] = None,
                 window: int = 90) -> List[Dict]:
    result = []
    for i in range(window, len(equity_series)):
        window_equity = equity_series.iloc[i - window: i + 1]
        if window_equity.iloc[0] <= 0:
            continue
        years = window / TRADING_DAYS_PER_YEAR
        r = float((window_equity.iloc[-1] / window_equity.iloc[0]) ** (1 / years) - 1) * 100
        d = dates[i] if dates and i < len(dates) else str(i)
        result.append({"date": d, "rolling_cagr": round(r, 4)})
    return result


def rolling_volatility(equity_series: pd.Series,
                       dates: Optional[List[str]] = None,
                       window: int = 30) -> List[Dict]:
    returns = equity_series.pct_change().dropna()
    rvol = returns.rolling(window).std() * np.sqrt(TRADING_DAYS_PER_YEAR) * 100
    result = []
    for i, v in enumerate(rvol):
        if pd.notna(v):
            d = dates[i] if dates and i < len(dates) else str(i)
            result.append({"date": d, "rolling_vol": round(float(v), 4)})
    return result


def monthly_returns(equity_series: pd.Series,
                    dates: Optional[List[str]] = None) -> List[Dict]:
    """Return list of {year, month, return_pct} for monthly heatmap."""
    if dates is None or len(dates) != len(equity_series):
        return []
    try:
        s = pd.Series(equity_series.values, index=pd.to_datetime(dates, errors="coerce"))
        s = s.dropna()
        if s.empty:
            return []
        monthly = s.resample("M").last().pct_change().dropna()
        result = []
        for dt, val in monthly.items():
            result.append({
                "year": int(dt.year),
                "month": int(dt.month),
                "return_pct": round(float(val) * 100, 2),
            })
        return result
    except Exception as e:
        logger.warning(f"monthly_returns error: {e}")
        return []


def yearly_returns(equity_series: pd.Series,
                   dates: Optional[List[str]] = None) -> List[Dict]:
    """Return list of {year, return_pct} for yearly heatmap."""
    if dates is None or len(dates) != len(equity_series):
        return []
    try:
        s = pd.Series(equity_series.values, index=pd.to_datetime(dates, errors="coerce"))
        s = s.dropna()
        if s.empty:
            return []
        yearly = s.resample("Y").last().pct_change().dropna()
        result = []
        for dt, val in yearly.items():
            result.append({
                "year": int(dt.year),
                "return_pct": round(float(val) * 100, 2),
            })
        return result
    except Exception as e:
        logger.warning(f"yearly_returns error: {e}")
        return []


# ─────────────────────────────────────────────────────────────────────────────
# EMPTY METRICS FALLBACK
# ─────────────────────────────────────────────────────────────────────────────

def _empty_metrics() -> Dict:
    return {
        "total_return_pct": 0.0,
        "cagr_pct": 0.0,
        "annualized_return_pct": 0.0,
        "annualized_volatility_pct": 0.0,
        "sharpe_ratio": 0.0,
        "sortino_ratio": 0.0,
        "calmar_ratio": 0.0,
        "omega_ratio": 0.0,
        "mar_ratio": 0.0,
        "max_drawdown_pct": 0.0,
        "avg_drawdown_pct": 0.0,
        "ulcer_index": 0.0,
        "recovery_factor": 0.0,
        "time_underwater_pct": 0.0,
        "trade_count": 0,
        "win_count": 0,
        "loss_count": 0,
        "win_rate_pct": 0.0,
        "profit_factor": 0.0,
        "expectancy_pct": 0.0,
        "kelly_criterion": 0.0,
        "avg_win_pct": 0.0,
        "avg_loss_pct": 0.0,
        "best_trade_pct": 0.0,
        "worst_trade_pct": 0.0,
        "avg_holding_days": 0.0,
        "var_95_pct": 0.0,
        "var_99_pct": 0.0,
        "cvar_95_pct": 0.0,
        "downside_deviation_pct": 0.0,
        "skewness": 0.0,
        "kurtosis": 0.0,
        "beta": None,
        "alpha_pct": None,
        "tracking_error_pct": None,
        "information_ratio": None,
        "upside_capture": None,
        "downside_capture": None,
    }
