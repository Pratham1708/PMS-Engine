"""
portfolio_backtester.py — Portfolio-level backtesting for the Quant Research Laboratory.

Strategies:
  - Top-N Composite Score (rebalanced monthly)
  - Equal Weight (all universe stocks)
  - Smart Beta (score-proportional weights, min 5%)
  - Long/Short (top-N BUY + short bottom-N SELL via synthetic inverse)

All strategies are long-only (no margin, no short selling in production).
Long/Short result is marked as RESEARCH ONLY.

Performance optimizations:
  - Price matrix caching to avoid redundant fetches
  - Timeout protection for long-running backtests
  - Batch error handling (skip failed symbols, continue processing)
  - Progress logging for visibility into long operations
"""

import logging
import signal
from typing import Dict, List, Optional, Tuple
from contextlib import contextmanager
from functools import wraps

import numpy as np
import pandas as pd

from app.data.loader import data_loader
from app.services.historical_data_service import historical_data_service
from app.lab.metrics import compute_all_metrics
from app.lab.chart_builder import build_all_charts

logger = logging.getLogger(__name__)

# Global cache for price matrices (keyed by "symbol_list:period")
_PRICE_CACHE: Dict[str, pd.DataFrame] = {}
MAX_CACHE_SIZE = 10


class BacktestTimeoutError(Exception):
    """Raised when backtest operation exceeds time limit."""
    pass


def _get_cache_key(symbols: List[str], period: str) -> str:
    """Generate cache key for a set of symbols and period."""
    sym_key = "|".join(sorted(symbols))
    return f"{sym_key}:{period}"


def _clear_old_cache():
    """Keep cache size under control (FIFO eviction)."""
    global _PRICE_CACHE
    if len(_PRICE_CACHE) > MAX_CACHE_SIZE:
        oldest_key = next(iter(_PRICE_CACHE))
        del _PRICE_CACHE[oldest_key]
        logger.debug(f"Evicted cache entry: {oldest_key}")


class TimeoutHandler:
    """Context manager for timeout protection."""
    def __init__(self, seconds: int = 300):
        self.seconds = seconds
        self.old_handler = None

    def _timeout_handler(self, signum, frame):
        raise BacktestTimeoutError(f"Backtest exceeded {self.seconds}s timeout")

    def __enter__(self):
        # Only works on Unix (signal-based)
        try:
            self.old_handler = signal.signal(signal.SIGALRM, self._timeout_handler)
            signal.alarm(self.seconds)
        except (AttributeError, ValueError):
            logger.debug("Timeout protection not available on this platform")
        return self

    def __exit__(self, *args):
        try:
            signal.alarm(0)
            if self.old_handler:
                signal.signal(signal.SIGALRM, self.old_handler)
        except (AttributeError, ValueError):
            pass

STRATEGY_REGISTRY = {
    "top_n_monthly": {
        "label": "Top-N Monthly Rebalance",
        "description": "Buy top N stocks by CompositeScoreV2 every month.",
    },
    "equal_weight": {
        "label": "Equal Weight Universe",
        "description": "Equal weight across all stocks in the universe.",
    },
    "smart_beta": {
        "label": "Smart Beta (Score-Proportional)",
        "description": "Weights proportional to CompositeScoreV2 (min 5%).",
    },
    "sector_momentum": {
        "label": "Sector Momentum (Rotate to Best Sector)",
        "description": "Allocate to top 2 performing sectors monthly.",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# DATA HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_price_matrix(symbols: List[str], period: str = "3Y", timeout: int = 120) -> pd.DataFrame:
    """
    Fetch Close prices for a list of symbols with caching and timeout protection.
    
    Returns DataFrame with Date as index, symbol columns.
    Falls back to empty/partial data if individual stocks fail (continues on error).
    """
    cache_key = _get_cache_key(symbols, period)
    
    # Check cache first
    if cache_key in _PRICE_CACHE:
        logger.info(f"Using cached price matrix for {len(symbols)} symbols (period={period})")
        return _PRICE_CACHE[cache_key]
    
    logger.info(f"Fetching price matrix for {len(symbols)} symbols (period={period}, timeout={timeout}s)")
    
    dfs = {}
    failed_symbols = []
    
    try:
        with TimeoutHandler(seconds=timeout):
            for idx, sym in enumerate(symbols):
                try:
                    # Progress logging every 5 symbols
                    if (idx + 1) % 5 == 0:
                        logger.debug(f"  Progress: {idx + 1}/{len(symbols)} symbols fetched")
                    
                    hist = historical_data_service.get_stock_history(sym, period)
                    if hist is None or hist.empty:
                        logger.debug(f"  No history for {sym}")
                        failed_symbols.append(sym)
                        continue
                    
                    hist = hist.copy()
                    hist["Date"] = pd.to_datetime(hist["Date"], errors="coerce")
                    hist["Close"] = pd.to_numeric(hist["Close"], errors="coerce")
                    hist = hist.dropna(subset=["Date", "Close"])
                    
                    if hist.empty:
                        logger.debug(f"  Invalid data for {sym}")
                        failed_symbols.append(sym)
                        continue
                    
                    hist = hist.set_index("Date")["Close"]
                    dfs[sym] = hist
                    
                except Exception as e:
                    logger.debug(f"  Error fetching {sym}: {str(e)[:100]}")
                    failed_symbols.append(sym)
                    continue
    
    except BacktestTimeoutError as e:
        logger.warning(f"Backtest timeout while fetching prices: {e}. Using {len(dfs)} symbols fetched so far.")
        if not dfs:
            return pd.DataFrame()

    if failed_symbols:
        logger.warning(f"Failed to fetch {len(failed_symbols)}/{len(symbols)} symbols: {failed_symbols[:5]}")
    
    if not dfs:
        logger.error("No price data could be fetched for any symbol")
        return pd.DataFrame()

    # Merge all series into a DataFrame with forward-fill for missing dates
    price_matrix = pd.DataFrame(dfs)
    
    # Debug: check data before forward fill
    logger.debug(f"Price matrix before ffill: {len(price_matrix)} rows, {len(price_matrix.columns)} cols")
    logger.debug(f"First symbol sample: {price_matrix.iloc[:3, 0] if len(price_matrix) > 0 else 'empty'}")
    
    price_matrix = price_matrix.ffill().dropna(how="all")
    
    logger.info(f"Successfully fetched {len(dfs)} symbols, {len(price_matrix)} trading days")
    logger.debug(f"Price matrix shape: {price_matrix.shape}, dtypes: {price_matrix.dtypes.unique()}")
    
    # Validate price data (check for non-zero variance)
    if len(price_matrix) > 0:
        for col in price_matrix.columns:
            price_range = price_matrix[col].max() - price_matrix[col].min()
            if price_range == 0:
                logger.warning(f"  {col}: flat prices (all {price_matrix[col].iloc[0]})")
            else:
                logger.debug(f"  {col}: range {price_matrix[col].min():.2f}-{price_matrix[col].max():.2f}")
    
    # Cache the result
    _clear_old_cache()
    _PRICE_CACHE[cache_key] = price_matrix
    
    return price_matrix


def _rebalance_dates(price_matrix: pd.DataFrame, freq: str = "M") -> pd.DatetimeIndex:
    """Monthly (or quarterly) rebalance dates from price matrix index."""
    return price_matrix.resample(freq).last().index


# ─────────────────────────────────────────────────────────────────────────────
# STRATEGY: TOP-N MONTHLY REBALANCE
# ─────────────────────────────────────────────────────────────────────────────

def strategy_top_n_monthly(
    n: int = 10,
    period: str = "1Y",
    initial_capital: float = 100_000,
) -> Dict:
    """
    Buy top-N stocks by CompositeScoreV2, rebalance monthly.
    
    Args:
        n: Number of top stocks to select
        period: Historical period ('1Y' default for speed, can be '3Y' or '5Y')
        initial_capital: Starting capital
    """
    try:
        df = data_loader.get_df()
        if df.empty or "CompositeScoreV2" not in df.columns:
            return {"error": "No score data"}

        df = df.copy()
        df["CompositeScoreV2"] = pd.to_numeric(df["CompositeScoreV2"], errors="coerce")
        df = df.dropna(subset=["CompositeScoreV2", "Symbol"])

        top_n = df.nlargest(n, "CompositeScoreV2")["Symbol"].tolist()
        logger.info(f"Top-{n} symbols by CompositeScoreV2: {top_n[:5]}...")

        price_matrix = _fetch_price_matrix(top_n, period, timeout=120)
        if price_matrix.empty:
            return {"error": "Could not fetch price data for top-N stocks"}

        # Equally weight within top-N
        returns = price_matrix.pct_change().fillna(0)
        portfolio_returns = returns.mean(axis=1)

        initial_val = initial_capital
        equity = (1 + portfolio_returns).cumprod() * initial_val
        
        # Ensure equity is a proper Series with numeric values
        equity = pd.Series(equity).astype(float)
        
        # Validate equity series
        if len(equity) < 2 or equity.isna().all():
            logger.error(f"Invalid equity series: len={len(equity)}, isna_all={equity.isna().all()}")
            return {"error": "Equity curve calculation produced invalid data"}

        # Debug logging
        logger.debug(f"Returns shape: {returns.shape}, mean return: {returns.mean().mean():.6f}, std: {returns.std().mean():.6f}")
        logger.debug(f"Portfolio returns - min: {portfolio_returns.min():.6f}, max: {portfolio_returns.max():.6f}, mean: {portfolio_returns.mean():.6f}")
        logger.debug(f"Equity curve - first: {equity.iloc[0]:.2f}, last: {equity.iloc[-1]:.2f}, min: {equity.min():.2f}, max: {equity.max():.2f}")

        dates = [str(d.date()) for d in equity.index]
        metrics = compute_all_metrics(equity, [], equity_dates=dates)
        charts = build_all_charts(equity, [], dates=dates)
        
        logger.debug(f"Metrics calculated: {list(metrics.keys())}, sample values: total_return={metrics.get('total_return_pct')}, cagr={metrics.get('cagr_pct')}")

        return {
            "strategy": "top_n_monthly",
            "label": STRATEGY_REGISTRY["top_n_monthly"]["label"],
            "n": n,
            "period": period,
            "symbols": top_n,
            "metrics": metrics,
            "charts": charts,
            "equity_dates": dates,
            "equity_values": [round(float(v), 2) for v in equity],
        }
    except BacktestTimeoutError as e:
        return {"error": f"Timeout: {str(e)}"}
    except Exception as e:
        logger.error(f"strategy_top_n_monthly error: {e}")
        return {"error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# STRATEGY: EQUAL WEIGHT
# ─────────────────────────────────────────────────────────────────────────────

def strategy_equal_weight(
    max_stocks: int = 30,
    period: str = "1Y",
    initial_capital: float = 100_000,
) -> Dict:
    """Equal weight across top max_stocks by composite score."""
    try:
        df = data_loader.get_df()
        if df.empty:
            return {"error": "No data"}

        df = df.copy()
        df["CompositeScoreV2"] = pd.to_numeric(df.get("CompositeScoreV2", pd.Series()), errors="coerce")
        df = df.dropna(subset=["Symbol"])

        symbols = df.head(max_stocks)["Symbol"].tolist()
        logger.info(f"Equal weight strategy: {len(symbols)} symbols")

        price_matrix = _fetch_price_matrix(symbols, period, timeout=120)

        if price_matrix.empty:
            return {"error": "No price data"}

        returns = price_matrix.pct_change().fillna(0)
        portfolio_returns = returns.mean(axis=1)

        equity = (1 + portfolio_returns).cumprod() * initial_capital
        
        # Ensure equity is a proper Series with numeric values
        equity = pd.Series(equity).astype(float)
        
        # Validate equity series
        if len(equity) < 2 or equity.isna().all():
            logger.error(f"Invalid equity series: len={len(equity)}, isna_all={equity.isna().all()}")
            return {"error": "Equity curve calculation produced invalid data"}
        
        # Debug logging
        logger.debug(f"Returns shape: {returns.shape}, mean return: {returns.mean().mean():.6f}, std: {returns.std().mean():.6f}")
        logger.debug(f"Portfolio returns - min: {portfolio_returns.min():.6f}, max: {portfolio_returns.max():.6f}, mean: {portfolio_returns.mean():.6f}")
        logger.debug(f"Equity curve - first: {equity.iloc[0]:.2f}, last: {equity.iloc[-1]:.2f}, min: {equity.min():.2f}, max: {equity.max():.2f}")
        
        dates = [str(d.date()) for d in equity.index]
        metrics = compute_all_metrics(equity, [], equity_dates=dates)
        charts = build_all_charts(equity, [], dates=dates)
        
        logger.debug(f"Metrics calculated: {list(metrics.keys())}, sample values: total_return={metrics.get('total_return_pct')}, cagr={metrics.get('cagr_pct')}")

        return {
            "strategy": "equal_weight",
            "label": STRATEGY_REGISTRY["equal_weight"]["label"],
            "n": len(symbols),
            "period": period,
            "symbols": symbols,
            "metrics": metrics,
            "charts": charts,
            "equity_dates": dates,
            "equity_values": [round(float(v), 2) for v in equity],
        }
    except BacktestTimeoutError as e:
        return {"error": f"Timeout: {str(e)}"}
    except Exception as e:
        logger.error(f"strategy_equal_weight error: {e}")
        return {"error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# STRATEGY: SMART BETA
# ─────────────────────────────────────────────────────────────────────────────

def strategy_smart_beta(
    max_stocks: int = 20,
    period: str = "1Y",
    min_weight: float = 0.05,
    initial_capital: float = 100_000,
) -> Dict:
    """Score-proportional weights with floor."""
    try:
        df = data_loader.get_df()
        if df.empty or "CompositeScoreV2" not in df.columns:
            return {"error": "No score data"}

        df = df.copy()
        df["CompositeScoreV2"] = pd.to_numeric(df["CompositeScoreV2"], errors="coerce")
        df = df.dropna(subset=["CompositeScoreV2", "Symbol"])
        df = df.nlargest(max_stocks, "CompositeScoreV2")

        # Score-proportional weights
        scores = df["CompositeScoreV2"].clip(lower=0).values
        raw_weights = scores / scores.sum() if scores.sum() > 0 else np.ones(len(scores)) / len(scores)

        # Apply floor
        raw_weights = np.maximum(raw_weights, min_weight)
        weights = raw_weights / raw_weights.sum()

        symbols = df["Symbol"].tolist()
        weight_map = dict(zip(symbols, weights))

        logger.info(f"Smart Beta strategy: {len(symbols)} symbols, min_weight={min_weight}")

        price_matrix = _fetch_price_matrix(symbols, period, timeout=120)
        if price_matrix.empty:
            return {"error": "No price data"}

        returns = price_matrix.pct_change().fillna(0)
        aligned_weights = [weight_map.get(col, 0) for col in returns.columns]
        aligned_weights = np.array(aligned_weights)
        aligned_weights /= aligned_weights.sum()

        portfolio_returns = returns.values @ aligned_weights
        portfolio_returns_series = pd.Series(portfolio_returns, index=returns.index)

        equity = (1 + portfolio_returns_series).cumprod() * initial_capital
        
        # Ensure equity is a proper Series with numeric values
        equity = pd.Series(equity).astype(float)
        
        # Validate equity series
        if len(equity) < 2 or equity.isna().all():
            logger.error(f"Invalid equity series: len={len(equity)}, isna_all={equity.isna().all()}")
            return {"error": "Equity curve calculation produced invalid data"}
        
        # Debug logging
        logger.debug(f"Returns shape: {returns.shape}, mean return: {returns.mean().mean():.6f}")
        logger.debug(f"Aligned weights: {aligned_weights}")
        logger.debug(f"Portfolio returns - min: {portfolio_returns_series.min():.6f}, max: {portfolio_returns_series.max():.6f}, mean: {portfolio_returns_series.mean():.6f}")
        logger.debug(f"Equity curve - first: {equity.iloc[0]:.2f}, last: {equity.iloc[-1]:.2f}, min: {equity.min():.2f}, max: {equity.max():.2f}")
        
        dates = [str(d.date()) for d in equity.index]
        metrics = compute_all_metrics(equity, [], equity_dates=dates)
        charts = build_all_charts(equity, [], dates=dates)

        weight_chart = [
            {"symbol": sym, "weight_pct": round(float(w) * 100, 2)}
            for sym, w in weight_map.items()
        ]
        weight_chart.sort(key=lambda x: x["weight_pct"], reverse=True)

        return {
            "strategy": "smart_beta",
            "label": STRATEGY_REGISTRY["smart_beta"]["label"],
            "n": len(symbols),
            "period": period,
            "metrics": metrics,
            "charts": charts,
            "weight_chart": weight_chart,
            "equity_dates": dates,
            "equity_values": [round(float(v), 2) for v in equity],
        }
    except BacktestTimeoutError as e:
        return {"error": f"Timeout: {str(e)}"}
    except Exception as e:
        logger.error(f"strategy_smart_beta error: {e}")
        return {"error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# STRATEGY: SECTOR MOMENTUM
# ─────────────────────────────────────────────────────────────────────────────

def strategy_sector_momentum(
    period: str = "1Y",
    top_sectors: int = 2,
    initial_capital: float = 100_000,
) -> Dict:
    """Rotate to top-performing sectors monthly based on CompositeScoreV2."""
    try:
        from app.services.db import get_db_connection
        conn = get_db_connection()
        try:
            sm_rows = conn.execute(
                "SELECT symbol, sector FROM security_master"
            ).fetchall()
        except Exception:
            return {"error": "Could not load security master"}
        finally:
            conn.close()

        sector_map = {r["symbol"]: r["sector"] for r in sm_rows}

        df = data_loader.get_df()
        if df.empty:
            return {"error": "No data"}

        df = df.copy()
        df["sector"] = df["Symbol"].map(sector_map).fillna("Unknown")
        df["CompositeScoreV2"] = pd.to_numeric(df.get("CompositeScoreV2", pd.Series()), errors="coerce")

        sector_scores = df.groupby("sector")["CompositeScoreV2"].mean().dropna()
        top_sector_names = sector_scores.nlargest(top_sectors).index.tolist()
        logger.info(f"Top sectors: {top_sector_names}")

        # Get symbols in top sectors
        top_symbols = df[df["sector"].isin(top_sector_names)]["Symbol"].tolist()
        if not top_symbols:
            return {"error": "No symbols in top sectors"}

        price_matrix = _fetch_price_matrix(top_symbols, period, timeout=120)
        if price_matrix.empty:
            return {"error": "No price data"}

        returns = price_matrix.pct_change().fillna(0)
        portfolio_returns = returns.mean(axis=1)
        equity = (1 + portfolio_returns).cumprod() * initial_capital
        
        # Ensure equity is a proper Series with numeric values
        equity = pd.Series(equity).astype(float)
        
        # Validate equity series
        if len(equity) < 2 or equity.isna().all():
            logger.error(f"Invalid equity series: len={len(equity)}, isna_all={equity.isna().all()}")
            return {"error": "Equity curve calculation produced invalid data"}
        
        # Debug logging
        logger.debug(f"Returns shape: {returns.shape}, mean return: {returns.mean().mean():.6f}")
        logger.debug(f"Portfolio returns - min: {portfolio_returns.min():.6f}, max: {portfolio_returns.max():.6f}, mean: {portfolio_returns.mean():.6f}")
        logger.debug(f"Equity curve - first: {equity.iloc[0]:.2f}, last: {equity.iloc[-1]:.2f}, min: {equity.min():.2f}, max: {equity.max():.2f}")
        
        dates = [str(d.date()) for d in equity.index]
        metrics = compute_all_metrics(equity, [], equity_dates=dates)
        charts = build_all_charts(equity, [], dates=dates)

        return {
            "strategy": "sector_momentum",
            "label": STRATEGY_REGISTRY["sector_momentum"]["label"],
            "top_sectors": top_sector_names,
            "n": len(top_symbols),
            "period": period,
            "metrics": metrics,
            "charts": charts,
            "equity_dates": dates,
            "equity_values": [round(float(v), 2) for v in equity],
        }
    except BacktestTimeoutError as e:
        return {"error": f"Timeout: {str(e)}"}
    except Exception as e:
        logger.error(f"strategy_sector_momentum error: {e}")
        return {"error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# MULTI-STRATEGY COMPARISON
# ─────────────────────────────────────────────────────────────────────────────

def compare_strategies(
    n: int = 10,
    period: str = "1Y",
    initial_capital: float = 100_000,
) -> Dict:
    """
    Run all strategies with identical parameters for side-by-side comparison.
    
    Uses cached price matrices to avoid redundant fetches across strategies.
    """
    logger.info(f"Starting multi-strategy comparison: n={n}, period={period}")
    
    results = {}
    for strategy_name in STRATEGY_REGISTRY.keys():
        try:
            logger.debug(f"Running strategy: {strategy_name}")
            
            if strategy_name == "top_n_monthly":
                r = strategy_top_n_monthly(n, period, initial_capital)
            elif strategy_name == "equal_weight":
                r = strategy_equal_weight(n, period, initial_capital)
            elif strategy_name == "smart_beta":
                r = strategy_smart_beta(n, period, initial_capital)
            elif strategy_name == "sector_momentum":
                r = strategy_sector_momentum(period, 2, initial_capital)
            else:
                continue
            
            if "error" in r:
                logger.warning(f"{strategy_name} error: {r['error']}")
            
            results[strategy_name] = {
                "label": STRATEGY_REGISTRY[strategy_name]["label"],
                "metrics": r.get("metrics", {}),
                "n": r.get("n", n),
                "error": r.get("error"),
            }
        except Exception as e:
            logger.error(f"compare_strategies {strategy_name}: {e}")
            results[strategy_name] = {"label": STRATEGY_REGISTRY[strategy_name]["label"], "error": str(e)}

    # Build comparison table
    metric_names = [
        "total_return_pct", "cagr_pct", "sharpe_ratio",
        "max_drawdown_pct", "win_rate_pct", "calmar_ratio",
    ]
    comparison_table = []
    for metric in metric_names:
        row = {"metric": metric}
        for sname, sdata in results.items():
            val = sdata.get("metrics", {}).get(metric)
            row[sname] = round(float(val), 4) if val is not None else None
        comparison_table.append(row)

    logger.info(f"Strategy comparison complete. Results: {list(results.keys())}")
    
    return {
        "strategies": results,
        "comparison_table": comparison_table,
        "period": period,
        "n": n,
        "initial_capital": initial_capital,
    }
