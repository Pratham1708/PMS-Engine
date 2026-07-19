"""
benchmark_engine.py — Engine 6: Abstract BenchmarkProvider + NIFTY50 implementation.

Architecture:
    BenchmarkProvider (ABC)
        ├── YFinanceBenchmarkProvider  ← pulls ^NSEI / ^CNX500 at runtime
        └── CustomBenchmarkProvider    ← accepts pre-loaded price dict (future stored snapshots)

Future stored-snapshot benchmark plugs in by implementing BenchmarkProvider.
The simulator and metrics_engine are completely unaffected by the choice of provider.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional
from datetime import datetime, timedelta

import pandas as pd

from app.services.backtest.engines import StrategyExecutionContext

logger = logging.getLogger(__name__)

_BENCHMARK_TICKERS = {
    "NIFTY50":  "^NSEI",
    "NIFTY500": "^CNX500",
    "SENSEX":   "^BSESN",
}


# ── Abstract Interface ────────────────────────────────────────────────────────

class BenchmarkProvider(ABC):
    @abstractmethod
    def get_price_series(self, start_date: str, end_date: str) -> pd.Series:
        """Return a date-indexed pd.Series of adjusted close prices."""


# ── YFinance Implementation ───────────────────────────────────────────────────

class YFinanceBenchmarkProvider(BenchmarkProvider):
    def __init__(self, benchmark_name: str = "NIFTY50"):
        self.benchmark_name = benchmark_name
        self.ticker = _BENCHMARK_TICKERS.get(benchmark_name.upper(), "^NSEI")
        self._cache: Optional[pd.Series] = None

    def get_price_series(self, start_date: str, end_date: str) -> pd.Series:
        if self._cache is not None:
            return self._cache

        try:
            import yfinance as yf
            # Extend by 5 days to ensure we capture data at boundaries
            start = (datetime.strptime(start_date, "%Y-%m-%d") - timedelta(days=5)).strftime("%Y-%m-%d")
            end   = (datetime.strptime(end_date,   "%Y-%m-%d") + timedelta(days=5)).strftime("%Y-%m-%d")
            df = yf.download(self.ticker, start=start, end=end, auto_adjust=True, progress=False)
            if df.empty:
                logger.warning("[BenchmarkEngine] yfinance returned empty data for %s", self.ticker)
                return pd.Series(dtype=float)
            series = df["Close"].squeeze()
            if hasattr(series, "columns"):
                series = series.iloc[:, 0]
            series.index = pd.to_datetime(series.index).strftime("%Y-%m-%d")
            self._cache = series
            logger.info("[BenchmarkEngine] Loaded %d price points for %s", len(series), self.ticker)
            return series
        except Exception as e:
            logger.error("[BenchmarkEngine] Failed to fetch %s: %s", self.ticker, e)
            return pd.Series(dtype=float)


# ── Custom / Future Stored Snapshot Implementation ────────────────────────────

class CustomBenchmarkProvider(BenchmarkProvider):
    """
    Accepts a pre-loaded {date_str: price} dict.
    Use this to implement stored-snapshot benchmark without changing any downstream code.
    """
    def __init__(self, prices: Dict[str, float]):
        self._prices = prices

    def get_price_series(self, start_date: str, end_date: str) -> pd.Series:
        filtered = {d: p for d, p in self._prices.items() if start_date <= d <= end_date}
        return pd.Series(filtered).sort_index()


# ── Engine Entry Point ────────────────────────────────────────────────────────

def _get_provider(benchmark_name: str) -> BenchmarkProvider:
    return YFinanceBenchmarkProvider(benchmark_name)


def run(ctx: StrategyExecutionContext) -> StrategyExecutionContext:
    """
    Load benchmark price series and align to simulation snapshot dates.
    Populates ctx.benchmark_prices and ctx.benchmark_initial_price.
    """
    provider = _get_provider(ctx.benchmark)
    series = provider.get_price_series(ctx.start_date, ctx.end_date)

    if series.empty:
        logger.warning("[BenchmarkEngine] No benchmark data; using flat benchmark.")
        ctx.benchmark_prices = {d: ctx.initial_capital for d in ctx.snapshot_dates}
        ctx.benchmark_initial_price = ctx.initial_capital
        return ctx

    # Align to snapshot dates — find nearest prior trading day for each
    prices: Dict[str, float] = {}
    sorted_idx = sorted(series.index.tolist())

    for snap_date in ctx.snapshot_dates:
        # Find the latest benchmark date <= snap_date
        matching = [d for d in sorted_idx if d <= snap_date]
        if matching:
            prices[snap_date] = float(series[matching[-1]])
        elif sorted_idx:
            prices[snap_date] = float(series.iloc[0])

    ctx.benchmark_prices = prices

    # Initial price: use the price at or before ctx.start_date
    init_candidates = [d for d in sorted_idx if d <= ctx.start_date]
    if init_candidates:
        ctx.benchmark_initial_price = float(series[init_candidates[-1]])
    elif prices:
        ctx.benchmark_initial_price = list(prices.values())[0]
    else:
        ctx.benchmark_initial_price = 1.0

    logger.info("[BenchmarkEngine] Benchmark '%s' aligned to %d snapshot dates.",
                ctx.benchmark, len(prices))
    return ctx
