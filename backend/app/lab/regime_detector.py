"""
regime_detector.py — Market regime classification for the Quant Research Laboratory.

Classifies each trading day into a regime using only OHLCV data and derived indicators.
No external data required. All derived from pandas operations.

Primary regimes (mutually exclusive):
  Bull, Bear, Correction, Recovery, Sideways

Overlay regimes (can co-exist with primary):
  High Volatility, Low Volatility, Trending, Range Bound

Special event windows (hardcoded for Indian market):
  Covid Crash, Post-Covid Rally, Rate Hike Cycle, etc.
"""

import logging
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# KNOWN MACRO EVENT WINDOWS (Indian Market)
# ─────────────────────────────────────────────────────────────────────────────

MACRO_EVENTS = [
    {"label": "Covid Crash",         "start": "2020-03-01", "end": "2020-03-31"},
    {"label": "Post-Covid Rally",    "start": "2020-04-01", "end": "2021-01-01"},
    {"label": "Rate Hike Cycle",     "start": "2022-04-01", "end": "2023-06-01"},
    {"label": "Pre-Election Rally",  "start": "2024-01-01", "end": "2024-04-30"},
    {"label": "GFC Recovery",        "start": "2009-03-01", "end": "2010-12-31"},
    {"label": "Demonetisation Shock","start": "2016-11-08", "end": "2016-12-31"},
    {"label": "IL&FS Crisis",        "start": "2018-09-01", "end": "2018-12-31"},
]


# ─────────────────────────────────────────────────────────────────────────────
# REGIME DETECTION
# ─────────────────────────────────────────────────────────────────────────────

def detect_regimes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Classify each trading day into a primary regime and overlay regime.

    Input: OHLCV DataFrame with Date, Open, High, Low, Close, Volume
    Output: DataFrame with added columns: 'primary_regime', 'overlay_regime', 'regime'
    """
    if df is None or len(df) < 50:
        logger.warning("detect_regimes: insufficient data (< 50 bars)")
        if df is not None:
            df = df.copy()
            df["regime"] = "Insufficient Data"
        return df

    out = df.copy().reset_index(drop=True)
    close = out["Close"]
    high  = out["High"]
    low   = out["Low"]

    # ── Trend indicators ──────────────────────────────────
    sma50  = close.rolling(min(50, len(close) // 2)).mean()
    sma200 = close.rolling(min(200, len(close) // 2)).mean()

    # 30-day rolling return
    ret30 = close.pct_change(min(30, len(close) // 4))

    # Peak / trough from 52-week rolling window
    window_52w = min(252, len(close) - 1)
    peak  = close.rolling(window_52w).max()
    trough = close.rolling(window_52w).min()

    # ── Volatility indicators ─────────────────────────────
    # ATR (14-day)
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low  - prev_close).abs()
    ], axis=1).max(axis=1)
    atr14 = tr.rolling(14).mean()
    atr_ratio = (atr14 / close.replace(0, np.nan)) * 100  # % of price

    atr_75th = atr_ratio.quantile(0.75)
    atr_25th = atr_ratio.quantile(0.25)

    # ── ADX ───────────────────────────────────────────────
    def _compute_adx(h, l, c, period=14):
        tr_ = pd.concat([
            h - l,
            (h - c.shift(1)).abs(),
            (l - c.shift(1)).abs()
        ], axis=1).max(axis=1)
        dm_plus  = (h - h.shift(1)).clip(lower=0)
        dm_minus = (l.shift(1) - l).clip(lower=0)
        dm_plus  = dm_plus.where(dm_plus > dm_minus, 0)
        dm_minus = dm_minus.where(dm_minus > dm_plus, 0)
        alpha = 1.0 / period
        atr_ = tr_.ewm(alpha=alpha, min_periods=period, adjust=False).mean()
        di_p = 100 * dm_plus.ewm(alpha=alpha, min_periods=period, adjust=False).mean() / atr_.replace(0, np.nan)
        di_m = 100 * dm_minus.ewm(alpha=alpha, min_periods=period, adjust=False).mean() / atr_.replace(0, np.nan)
        dx = 100 * (di_p - di_m).abs() / (di_p + di_m).replace(0, np.nan)
        adx_ = dx.ewm(alpha=alpha, min_periods=period, adjust=False).mean()
        return adx_

    adx = _compute_adx(high, low, close)

    # ── Primary regime classification ─────────────────────
    primary = pd.Series("Sideways", index=out.index)

    # Bull: 50D SMA above 200D SMA AND price above 50D SMA AND 30D return > 5%
    bull_mask = (sma50 > sma200) & (close > sma50) & (ret30 > 0.05)
    primary[bull_mask] = "Bull"

    # Bear: 50D SMA below 200D SMA AND 30D return < -10%
    bear_mask = (sma50 < sma200) & (ret30 < -0.10)
    primary[bear_mask] = "Bear"

    # Correction: -10% to -20% from 52W peak
    corr_mask = (close < peak * 0.90) & (close > peak * 0.80) & (primary != "Bear")
    primary[corr_mask] = "Correction"

    # Recovery: +10% from 52W trough AND still below 52W peak
    recov_mask = (close > trough * 1.10) & (close < peak * 0.95) & (primary == "Sideways")
    primary[recov_mask] = "Recovery"

    # ── Overlay regime ────────────────────────────────────
    overlay = pd.Series("Normal", index=out.index)
    overlay[atr_ratio > atr_75th] = "High Volatility"
    overlay[atr_ratio < atr_25th] = "Low Volatility"
    overlay[adx > 25] = "Trending"
    overlay[adx < 18] = "Range Bound"

    out["primary_regime"] = primary
    out["overlay_regime"]  = overlay
    out["regime"] = primary + " / " + overlay

    # ── Macro event overlay ───────────────────────────────
    if "Date" in out.columns:
        date_series = pd.to_datetime(out["Date"], errors="coerce")
        for event in MACRO_EVENTS:
            start = pd.Timestamp(event["start"])
            end   = pd.Timestamp(event["end"])
            mask  = (date_series >= start) & (date_series <= end)
            if mask.any():
                out.loc[mask, "regime"] = event["label"]

    return out


# ─────────────────────────────────────────────────────────────────────────────
# REGIME PERFORMANCE SUMMARY
# ─────────────────────────────────────────────────────────────────────────────

def regime_performance_summary(signals_df: pd.DataFrame, regimes_df: pd.DataFrame) -> Dict:
    """
    Per-regime performance stats from signal-tagged OHLCV data.
    Computes: trade_count, win_rate, avg_return, sharpe, best, worst, days
    """
    if "Date" not in signals_df.columns or "regime" not in regimes_df.columns:
        return {}

    merged = signals_df.merge(regimes_df[["Date", "regime"]], on="Date", how="left")
    merged["regime"] = merged["regime"].fillna("Unknown")

    results = {}
    for regime, group in merged.groupby("regime"):
        days = len(group)
        if days < 5:
            continue

        # Daily returns in this regime
        group_returns = group["Close"].pct_change().dropna() * 100

        # Trade returns: rows where signal == 1 followed by -1
        buy_returns = []
        in_trade = False
        entry = None
        for _, row in group.iterrows():
            sig = int(row.get("Signal", 0))
            price = float(row.get("Close", 0))
            if not in_trade and sig == 1:
                entry = price
                in_trade = True
            elif in_trade and sig == -1 and entry:
                ret = (price - entry) / entry * 100
                buy_returns.append(ret)
                in_trade = False

        wins = [r for r in buy_returns if r > 0]
        losses = [r for r in buy_returns if r <= 0]
        win_rate = len(wins) / len(buy_returns) * 100 if buy_returns else 0.0

        # Regime sharpe (daily returns basis)
        if len(group_returns) > 1:
            sr = group_returns.mean() / group_returns.std() * np.sqrt(252) if group_returns.std() > 0 else 0.0
        else:
            sr = 0.0

        results[regime] = {
            "days": days,
            "trade_count": len(buy_returns),
            "win_rate": round(win_rate, 2),
            "avg_return": round(float(np.mean(buy_returns)), 2) if buy_returns else 0.0,
            "sharpe": round(float(sr), 4),
            "best": round(float(max(buy_returns)), 2) if buy_returns else 0.0,
            "worst": round(float(min(buy_returns)), 2) if buy_returns else 0.0,
        }

    return results


# ─────────────────────────────────────────────────────────────────────────────
# REGIME TIMELINE (for frontend chart)
# ─────────────────────────────────────────────────────────────────────────────

def regime_timeline(regimes_df: pd.DataFrame) -> List[Dict]:
    """Return regime label per date for the timeline area chart."""
    if "Date" not in regimes_df.columns:
        return []

    result = []
    regime_map = {
        "Bull": 5, "Recovery": 4, "Sideways": 3, "Correction": 2, "Bear": 1,
    }

    for _, row in regimes_df.iterrows():
        primary = str(row.get("primary_regime", "Sideways"))
        overlay = str(row.get("overlay_regime", "Normal"))
        regime  = str(row.get("regime", "Sideways"))
        result.append({
            "date": str(row["Date"]),
            "primary_regime": primary,
            "overlay_regime": overlay,
            "regime": regime,
            "regime_score": regime_map.get(primary, 3),
            "close": float(row["Close"]) if not pd.isna(row.get("Close", None)) else None,
        })
    return result
