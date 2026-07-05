"""
backtester.py — Vectorized backtesting engine for the Quant Research Laboratory.

Reuses:
  - historical_data_service.get_stock_history() for OHLCV data
  - indicators.compute_indicator() for signal generation

All operations are vectorized (pandas/numpy). No row-by-row Python loops
except where unavoidable (e.g. Parabolic SAR — handled in indicators.py).
"""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from app.services.historical_data_service import historical_data_service
from app.lab.indicators import compute_indicator

logger = logging.getLogger(__name__)

DEFAULT_COMMISSION = 0.001   # 0.1% per trade (round-trip = 0.2%)
DEFAULT_SLIPPAGE   = 0.0005  # 0.05% slippage per trade
DEFAULT_CAPITAL    = 100_000.0


# ─────────────────────────────────────────────────────────────────────────────
# OHLCV LOADER (reuses existing service)
# ─────────────────────────────────────────────────────────────────────────────

def load_ohlcv(symbol: str, period: str) -> Optional[pd.DataFrame]:
    """
    Fetch OHLCV from historical_data_service.
    Returns cleaned DataFrame with DatetimeIndex and columns:
    Date, Open, High, Low, Close, Volume.
    Returns None if no data.
    """
    df = historical_data_service.get_stock_history(symbol, period)
    if df is None or df.empty:
        logger.warning(f"No OHLCV data for {symbol} ({period})")
        return None

    df = df.copy()
    # Ensure Date column
    if "Date" not in df.columns and df.index.name == "Date":
        df = df.reset_index()

    # Clean numeric columns
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["Close"]).reset_index(drop=True)
    if df.empty:
        return None

    return df


# ─────────────────────────────────────────────────────────────────────────────
# SIGNAL GENERATION
# ─────────────────────────────────────────────────────────────────────────────

def generate_signals(df: pd.DataFrame, indicator_name: str,
                     params: Dict) -> pd.DataFrame:
    """
    Apply indicator to OHLCV DataFrame and return with Signal column.
    Signal: +1 = BUY, 0 = HOLD, -1 = SELL
    """
    return compute_indicator(df, indicator_name, params)


# ─────────────────────────────────────────────────────────────────────────────
# CORE BACKTEST ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def run_backtest(
    signals_df: pd.DataFrame,
    initial_capital: float = DEFAULT_CAPITAL,
    commission: float = DEFAULT_COMMISSION,
    slippage: float = DEFAULT_SLIPPAGE,
) -> Dict:
    """
    Simulate a long-only strategy on a signals DataFrame.

    Entry: Next day's open after BUY signal.
    Exit: Next day's open after SELL signal.

    Returns dict with:
      - trade_log: list[dict] — one entry per completed trade
      - equity_series: pd.Series — daily portfolio value
      - signals_df: the input df (for chart overlays)
    """
    df = signals_df.copy().reset_index(drop=True)

    # Ensure Open column for next-day entry/exit price
    if "Open" not in df.columns:
        df["Open"] = df["Close"]

    cash = initial_capital
    position = 0.0      # number of shares held
    entry_price = 0.0
    entry_date = None
    in_trade = False

    trade_log = []
    equity = []

    for i in range(len(df)):
        row = df.iloc[i]
        price = float(row["Open"]) if not pd.isna(row["Open"]) else float(row["Close"])
        close = float(row["Close"]) if not pd.isna(row["Close"]) else price
        date = str(row["Date"]) if "Date" in row else str(i)

        # Entry on BUY signal (use next bar's open — already offset by the vectorized shift)
        if not in_trade and i > 0:
            prev_signal = int(df.iloc[i - 1].get("Signal", 0))
            if prev_signal == 1:
                # Apply slippage
                exec_price = price * (1 + slippage)
                cost_factor = 1 + commission
                position = cash / (exec_price * cost_factor)
                cash = 0.0
                entry_price = exec_price
                entry_date = date
                in_trade = True

        # Exit on SELL signal
        if in_trade and i > 0:
            prev_signal = int(df.iloc[i - 1].get("Signal", 0))
            if prev_signal == -1:
                exec_price = price * (1 - slippage)
                proceeds = position * exec_price * (1 - commission)
                pnl = proceeds - (position * entry_price * (1 + commission))
                ret_pct = (exec_price / (entry_price * (1 + commission)) - 1) * 100

                # Count holding days
                holding_days = i - (
                    df.index[df["Date"].astype(str) == entry_date].tolist()[0]
                    if entry_date and "Date" in df.columns
                    else 0
                ) if entry_date else 1

                trade_log.append({
                    "entry_date": entry_date,
                    "exit_date": date,
                    "entry_price": round(entry_price, 2),
                    "exit_price": round(exec_price, 2),
                    "return_pct": round(ret_pct, 2),
                    "pnl": round(pnl, 2),
                    "holding_days": holding_days,
                    "outcome": "win" if pnl > 0 else "loss",
                })
                cash = proceeds
                position = 0.0
                entry_price = 0.0
                entry_date = None
                in_trade = False

        # Daily portfolio value
        portfolio_val = cash + (position * close)
        equity.append({"date": date, "value": round(portfolio_val, 2)})

    # Force close any open position at last price
    if in_trade and position > 0:
        last_close = float(df.iloc[-1]["Close"])
        proceeds = position * last_close * (1 - commission)
        cash = proceeds
        position = 0.0

    equity_series = pd.Series(
        [e["value"] for e in equity],
        index=pd.RangeIndex(len(equity)),
        name="equity",
    )

    return {
        "trade_log": trade_log,
        "equity_series": equity_series,
        "equity_dates": [e["date"] for e in equity],
        "initial_capital": initial_capital,
        "final_capital": float(cash),
    }


# ─────────────────────────────────────────────────────────────────────────────
# WALK-FORWARD VALIDATION
# ─────────────────────────────────────────────────────────────────────────────

def run_walk_forward(
    df: pd.DataFrame,
    indicator_name: str,
    params: Dict,
    n_splits: int = 5,
    train_ratio: float = 0.7,
) -> List[Dict]:
    """
    Walk-forward validation: split data into n_splits equal folds.
    For each fold: use first train_ratio rows as in-sample, remainder as OOS test.
    Returns list of per-fold OOS metrics.
    """
    from app.lab.metrics import compute_all_metrics

    n = len(df)
    fold_size = n // n_splits
    results = []

    for i in range(n_splits):
        fold_start = i * fold_size
        fold_end = min((i + 1) * fold_size, n)
        fold_df = df.iloc[fold_start:fold_end].copy().reset_index(drop=True)

        if len(fold_df) < 30:
            continue

        split_idx = int(len(fold_df) * train_ratio)
        oos_df = fold_df.iloc[split_idx:].copy().reset_index(drop=True)

        if len(oos_df) < 10:
            continue

        try:
            sig_df = generate_signals(oos_df, indicator_name, params)
            bt = run_backtest(sig_df)
            metrics = compute_all_metrics(bt["equity_series"], bt["trade_log"])

            results.append({
                "fold": i + 1,
                "oos_start": str(oos_df.iloc[0]["Date"]) if "Date" in oos_df.columns else str(split_idx),
                "oos_end": str(oos_df.iloc[-1]["Date"]) if "Date" in oos_df.columns else str(len(oos_df)),
                "oos_bars": len(oos_df),
                "sharpe": metrics.get("sharpe_ratio"),
                "cagr": metrics.get("cagr_pct"),
                "max_drawdown": metrics.get("max_drawdown_pct"),
                "win_rate": metrics.get("win_rate_pct"),
                "trade_count": metrics.get("trade_count"),
            })
        except Exception as e:
            logger.warning(f"Walk-forward fold {i + 1} failed: {e}")

    return results


# ─────────────────────────────────────────────────────────────────────────────
# EXPANDING WINDOW VALIDATION
# ─────────────────────────────────────────────────────────────────────────────

def run_expanding_window(
    df: pd.DataFrame,
    indicator_name: str,
    params: Dict,
    min_periods: int = 120,
    step_days: int = 30,
) -> List[Dict]:
    """
    Expanding window: grow training set by step_days each iteration.
    Each step tests on the next step_days block (OOS).
    """
    from app.lab.metrics import compute_all_metrics

    n = len(df)
    results = []
    cursor = min_periods

    while cursor + step_days <= n:
        oos_df = df.iloc[cursor: cursor + step_days].copy().reset_index(drop=True)
        cursor += step_days

        if len(oos_df) < 5:
            continue

        try:
            sig_df = generate_signals(oos_df, indicator_name, params)
            bt = run_backtest(sig_df)
            metrics = compute_all_metrics(bt["equity_series"], bt["trade_log"])
            results.append({
                "window_end_bar": cursor,
                "oos_bars": len(oos_df),
                "sharpe": metrics.get("sharpe_ratio"),
                "cagr": metrics.get("cagr_pct"),
                "win_rate": metrics.get("win_rate_pct"),
                "max_drawdown": metrics.get("max_drawdown_pct"),
            })
        except Exception as e:
            logger.warning(f"Expanding window step failed: {e}")

    return results


# ─────────────────────────────────────────────────────────────────────────────
# REGIME-SPLIT BACKTEST
# ─────────────────────────────────────────────────────────────────────────────

def run_regime_split_backtest(
    df: pd.DataFrame,
    regimes_df: pd.DataFrame,
    indicator_name: str,
    params: Dict,
) -> Dict[str, Dict]:
    """
    Run separate backtests for each market regime.
    regimes_df must have 'Date' and 'regime' columns.
    """
    from app.lab.metrics import compute_all_metrics

    merged = df.copy()
    if "Date" in merged.columns and "Date" in regimes_df.columns:
        merged = merged.merge(
            regimes_df[["Date", "regime"]], on="Date", how="left"
        )
        merged["regime"] = merged["regime"].fillna("Unknown")
    else:
        merged["regime"] = "Unknown"

    regime_results = {}
    for regime, group in merged.groupby("regime"):
        if len(group) < 20:
            continue
        try:
            group_reset = group.drop(columns=["regime"]).reset_index(drop=True)
            sig_df = generate_signals(group_reset, indicator_name, params)
            bt = run_backtest(sig_df)
            metrics = compute_all_metrics(bt["equity_series"], bt["trade_log"])
            regime_results[regime] = {
                "bars": len(group),
                "sharpe": metrics.get("sharpe_ratio"),
                "win_rate": metrics.get("win_rate_pct"),
                "cagr": metrics.get("cagr_pct"),
                "max_drawdown": metrics.get("max_drawdown_pct"),
                "trade_count": metrics.get("trade_count"),
            }
        except Exception as e:
            logger.warning(f"Regime backtest failed for '{regime}': {e}")

    return regime_results
