"""
benchmark_comparator.py — Benchmark comparison for the Quant Research Laboratory.

Indian Market Benchmarks (downloaded via yfinance-compatible tickers):
  NIFTY50     → ^NSEI
  SENSEX      → ^BSESN
  NIFTY MIDCAP → NIFTY_MIDCAP100.NS (proxy)
  NIFTY SMALL → NIFTY_SMLCAP100.NS (proxy)
  GOLD        → GLD or XAUUSD (proxy)

Compares any experiment equity curve vs benchmark using full metrics suite.
"""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from app.services.historical_data_service import historical_data_service
from app.lab.metrics import compute_all_metrics
from app.lab.chart_builder import equity_curve, drawdown_curve

logger = logging.getLogger(__name__)

BENCHMARK_TICKERS = {
    "NIFTY50":     {"ticker": "^NSEI",                 "label": "Nifty 50"},
    "SENSEX":      {"ticker": "^BSESN",                "label": "BSE Sensex"},
    "MIDCAP150":   {"ticker": "NIFTYMIDCAP150.NS",     "label": "Nifty Midcap 150"},
    "SMALLCAP250": {"ticker": "NIFTYSMLCAP250.NS",     "label": "Nifty Smallcap 250"},
    "NIFTY_IT":    {"ticker": "^CNXIT",                "label": "Nifty IT"},
    "NIFTY_BANK":  {"ticker": "^NSEBANK",              "label": "Nifty Bank"},
    "GOLD_ETF":    {"ticker": "GOLDBEES.NS",           "label": "Gold BeES ETF"},
}

DEFAULT_BENCHMARK = "NIFTY50"
DEFAULT_PERIOD    = "3Y"


# ─────────────────────────────────────────────────────────────────────────────
# BENCHMARK PRICE FETCHER
# ─────────────────────────────────────────────────────────────────────────────

def fetch_benchmark(benchmark_key: str = DEFAULT_BENCHMARK,
                    period: str = DEFAULT_PERIOD) -> Optional[pd.Series]:
    """Fetch benchmark Close series using historical_data_service."""
    meta = BENCHMARK_TICKERS.get(benchmark_key)
    if not meta:
        logger.warning(f"Unknown benchmark: {benchmark_key}")
        return None

    ticker = meta["ticker"]
    try:
        hist = historical_data_service.get_stock_history(ticker, period)
        if hist is None or hist.empty:
            return None
        hist = hist.copy()
        hist["Date"] = pd.to_datetime(hist["Date"], errors="coerce")
        hist["Close"] = pd.to_numeric(hist["Close"], errors="coerce")
        hist = hist.dropna(subset=["Date", "Close"]).sort_values("Date")
        return hist.set_index("Date")["Close"]
    except Exception as e:
        logger.error(f"fetch_benchmark {ticker}: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# BENCHMARK STATISTICS
# ─────────────────────────────────────────────────────────────────────────────

def benchmark_stats(benchmark_key: str = DEFAULT_BENCHMARK,
                    period: str = DEFAULT_PERIOD) -> Dict:
    """Return standalone statistics for a benchmark."""
    series = fetch_benchmark(benchmark_key, period)
    if series is None:
        return {"error": f"No data for benchmark {benchmark_key}"}

    metrics = compute_all_metrics(series, [], dates=[str(d.date()) for d in series.index])
    return {
        "benchmark": benchmark_key,
        "label": BENCHMARK_TICKERS.get(benchmark_key, {}).get("label", benchmark_key),
        "period": period,
        "n_bars": len(series),
        "metrics": metrics,
    }


# ─────────────────────────────────────────────────────────────────────────────
# PORTFOLIO vs BENCHMARK
# ─────────────────────────────────────────────────────────────────────────────

def compare_to_benchmark(
    portfolio_equity: pd.Series,
    portfolio_dates: List[str],
    portfolio_trade_log: Optional[List] = None,
    benchmark_key: str = DEFAULT_BENCHMARK,
    period: str = DEFAULT_PERIOD,
) -> Dict:
    """
    Compare portfolio equity curve vs benchmark.
    Returns combined metrics, alpha, beta, tracking error, information ratio.
    """
    benchmark_series = fetch_benchmark(benchmark_key, period)
    if benchmark_series is None:
        benchmark_series = None

    # Align lengths
    if benchmark_series is not None:
        min_len = min(len(portfolio_equity), len(benchmark_series))
        portfolio_aligned = portfolio_equity.iloc[:min_len]
        benchmark_aligned = benchmark_series.iloc[:min_len]
    else:
        portfolio_aligned = portfolio_equity
        benchmark_aligned = None

    portfolio_metrics = compute_all_metrics(
        portfolio_aligned,
        portfolio_trade_log or [],
        benchmark_aligned,
        equity_dates=portfolio_dates[:min_len] if benchmark_series is not None else portfolio_dates,
    )

    # Chart data with benchmark overlay
    chart_dates = portfolio_dates[:len(portfolio_aligned)]
    charts = {}
    try:
        charts["equity_curve"] = equity_curve(portfolio_aligned, chart_dates, benchmark_aligned)
    except Exception:
        charts["equity_curve"] = []
    try:
        charts["drawdown"] = drawdown_curve(portfolio_aligned, chart_dates)
        if benchmark_aligned is not None:
            charts["benchmark_drawdown"] = drawdown_curve(benchmark_aligned, chart_dates)
    except Exception:
        pass

    return {
        "portfolio_metrics": portfolio_metrics,
        "benchmark_key": benchmark_key,
        "benchmark_label": BENCHMARK_TICKERS.get(benchmark_key, {}).get("label", benchmark_key),
        "alpha": portfolio_metrics.get("alpha_pct"),
        "beta": portfolio_metrics.get("beta"),
        "tracking_error": portfolio_metrics.get("tracking_error_pct"),
        "information_ratio": portfolio_metrics.get("information_ratio"),
        "upside_capture": portfolio_metrics.get("upside_capture"),
        "downside_capture": portfolio_metrics.get("downside_capture"),
        "charts": charts,
    }


# ─────────────────────────────────────────────────────────────────────────────
# MULTI-BENCHMARK COMPARISON
# ─────────────────────────────────────────────────────────────────────────────

def multi_benchmark_stats(period: str = DEFAULT_PERIOD) -> Dict:
    """Return stats for all benchmarks side-by-side."""
    results = {}
    for key in BENCHMARK_TICKERS.keys():
        try:
            results[key] = benchmark_stats(key, period)
        except Exception as e:
            results[key] = {"error": str(e)}

    # Build comparison table
    metric_names = [
        "total_return_pct", "cagr_pct", "sharpe_ratio",
        "max_drawdown_pct", "annualized_volatility_pct",
    ]
    table = []
    for metric in metric_names:
        row = {"metric": metric}
        for key, data in results.items():
            val = data.get("metrics", {}).get(metric)
            row[key] = round(float(val), 2) if val is not None else None
        table.append(row)

    return {
        "benchmarks": results,
        "comparison_table": table,
        "period": period,
    }


# ─────────────────────────────────────────────────────────────────────────────
# CORRELATION OF UNIVERSE vs BENCHMARK
# ─────────────────────────────────────────────────────────────────────────────

def universe_benchmark_correlation(
    symbols: List[str],
    benchmark_key: str = DEFAULT_BENCHMARK,
    period: str = "1Y",
) -> List[Dict]:
    """
    Return per-symbol beta and correlation to benchmark.
    Useful for portfolio construction and risk management.
    """
    bench = fetch_benchmark(benchmark_key, period)
    if bench is None or bench.empty:
        return []

    bench_ret = bench.pct_change().dropna()
    result = []

    for symbol in symbols:
        try:
            hist = historical_data_service.get_stock_history(symbol, period)
            if hist is None or hist.empty:
                continue
            hist = hist.copy()
            hist["Date"] = pd.to_datetime(hist["Date"], errors="coerce")
            hist["Close"] = pd.to_numeric(hist["Close"], errors="coerce")
            hist = hist.dropna(subset=["Date", "Close"]).set_index("Date")["Close"]
            stock_ret = hist.pct_change().dropna()

            # Align
            common = stock_ret.index.intersection(bench_ret.index)
            if len(common) < 10:
                continue
            sr = stock_ret.loc[common]
            br = bench_ret.loc[common]

            corr = float(sr.corr(br))
            cov = np.cov(sr, br)[0, 1]
            var_b = float(np.var(br))
            beta = float(cov / var_b) if var_b > 0 else 1.0

            result.append({
                "symbol": symbol,
                "beta": round(beta, 4),
                "correlation": round(corr, 4) if not pd.isna(corr) else None,
                "n_days": len(common),
            })
        except Exception as e:
            logger.debug(f"universe_benchmark_correlation {symbol}: {e}")

    result.sort(key=lambda x: abs(x.get("beta", 1) - 1))
    return result
