"""
indicators.py — Pure-Pandas technical indicator library for the Quant Research Laboratory.

All indicators accept a pandas DataFrame with at minimum columns:
  Open, High, Low, Close, Volume

Each indicator function returns a pd.DataFrame with the original OHLCV columns
plus one or more indicator-specific columns and a 'Signal' column:
  BUY  = +1
  HOLD =  0
  SELL = -1

The INDICATOR_REGISTRY maps indicator names to their function and parameter definitions
so the API and frontend can discover and render param inputs dynamically.
"""

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# HELPER UTILITIES
# ─────────────────────────────────────────────────────────────────────────────

def _rma(series: pd.Series, period: int) -> pd.Series:
    """Wilder's smoothed moving average (RMA)."""
    alpha = 1.0 / period
    return series.ewm(alpha=alpha, min_periods=period, adjust=False).mean()


def _true_range(df: pd.DataFrame) -> pd.Series:
    high, low, prev_close = df["High"], df["Low"], df["Close"].shift(1)
    return pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    ).max(axis=1)


# ─────────────────────────────────────────────────────────────────────────────
# INDICATOR FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def compute_rsi(df: pd.DataFrame, period: int = 14,
                buy_threshold: float = 30.0,
                sell_threshold: float = 70.0) -> pd.DataFrame:
    close = df["Close"]
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = _rma(gain, period)
    avg_loss = _rma(loss, period)
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    out = df.copy()
    out["RSI"] = rsi
    out["Signal"] = 0
    out.loc[rsi < buy_threshold, "Signal"] = 1
    out.loc[rsi > sell_threshold, "Signal"] = -1
    return out


def compute_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26,
                 signal: int = 9) -> pd.DataFrame:
    close = df["Close"]
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    hist = macd - signal_line
    out = df.copy()
    out["MACD"] = macd
    out["MACD_Signal"] = signal_line
    out["MACD_Hist"] = hist
    out["Signal"] = 0
    # Buy: MACD crosses above signal
    out.loc[(macd > signal_line) & (macd.shift(1) <= signal_line.shift(1)), "Signal"] = 1
    # Sell: MACD crosses below signal
    out.loc[(macd < signal_line) & (macd.shift(1) >= signal_line.shift(1)), "Signal"] = -1
    return out


def compute_ema(df: pd.DataFrame, fast_period: int = 9,
                slow_period: int = 21) -> pd.DataFrame:
    close = df["Close"]
    ema_fast = close.ewm(span=fast_period, adjust=False).mean()
    ema_slow = close.ewm(span=slow_period, adjust=False).mean()
    out = df.copy()
    out["EMA_Fast"] = ema_fast
    out["EMA_Slow"] = ema_slow
    out["Signal"] = 0
    out.loc[(ema_fast > ema_slow) & (ema_fast.shift(1) <= ema_slow.shift(1)), "Signal"] = 1
    out.loc[(ema_fast < ema_slow) & (ema_fast.shift(1) >= ema_slow.shift(1)), "Signal"] = -1
    return out


def compute_sma(df: pd.DataFrame, fast_period: int = 50,
                slow_period: int = 200) -> pd.DataFrame:
    close = df["Close"]
    sma_fast = close.rolling(fast_period).mean()
    sma_slow = close.rolling(slow_period).mean()
    out = df.copy()
    out["SMA_Fast"] = sma_fast
    out["SMA_Slow"] = sma_slow
    out["Signal"] = 0
    out.loc[(sma_fast > sma_slow) & (sma_fast.shift(1) <= sma_slow.shift(1)), "Signal"] = 1
    out.loc[(sma_fast < sma_slow) & (sma_fast.shift(1) >= sma_slow.shift(1)), "Signal"] = -1
    return out


def compute_bollinger(df: pd.DataFrame, period: int = 20,
                      num_std: float = 2.0) -> pd.DataFrame:
    close = df["Close"]
    mid = close.rolling(period).mean()
    std = close.rolling(period).std()
    upper = mid + num_std * std
    lower = mid - num_std * std
    out = df.copy()
    out["BB_Upper"] = upper
    out["BB_Mid"] = mid
    out["BB_Lower"] = lower
    out["Signal"] = 0
    out.loc[close < lower, "Signal"] = 1
    out.loc[close > upper, "Signal"] = -1
    return out


def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    tr = _true_range(df)
    atr = _rma(tr, period)
    close = df["Close"]
    # Buy when close > previous close + ATR (breakout), sell on reverse
    out = df.copy()
    out["ATR"] = atr
    out["Signal"] = 0
    # Simple signal: price crossing 1-ATR breakout
    upper_band = close.shift(1) + atr.shift(1)
    lower_band = close.shift(1) - atr.shift(1)
    out.loc[close > upper_band, "Signal"] = 1
    out.loc[close < lower_band, "Signal"] = -1
    return out


def compute_adx(df: pd.DataFrame, period: int = 14,
                threshold: float = 25.0) -> pd.DataFrame:
    high, low, close = df["High"], df["Low"], df["Close"]
    tr = _true_range(df)
    dm_plus = (high - high.shift(1)).clip(lower=0)
    dm_minus = (low.shift(1) - low).clip(lower=0)
    dm_plus = dm_plus.where(dm_plus > dm_minus, 0)
    dm_minus = dm_minus.where(dm_minus > dm_plus, 0)
    atr = _rma(tr, period)
    di_plus = 100 * _rma(dm_plus, period) / atr.replace(0, np.nan)
    di_minus = 100 * _rma(dm_minus, period) / atr.replace(0, np.nan)
    dx = 100 * (di_plus - di_minus).abs() / (di_plus + di_minus).replace(0, np.nan)
    adx = _rma(dx, period)
    out = df.copy()
    out["ADX"] = adx
    out["DI_Plus"] = di_plus
    out["DI_Minus"] = di_minus
    out["Signal"] = 0
    out.loc[(adx > threshold) & (di_plus > di_minus), "Signal"] = 1
    out.loc[(adx > threshold) & (di_minus > di_plus), "Signal"] = -1
    return out


def compute_stoch_rsi(df: pd.DataFrame, rsi_period: int = 14,
                      stoch_period: int = 14,
                      smooth_k: int = 3, smooth_d: int = 3) -> pd.DataFrame:
    close = df["Close"]
    delta = close.diff()
    gain = _rma(delta.clip(lower=0), rsi_period)
    loss = _rma((-delta).clip(lower=0), rsi_period)
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - 100 / (1 + rs)
    rsi_min = rsi.rolling(stoch_period).min()
    rsi_max = rsi.rolling(stoch_period).max()
    stoch_k_raw = (rsi - rsi_min) / (rsi_max - rsi_min).replace(0, np.nan) * 100
    k = stoch_k_raw.rolling(smooth_k).mean()
    d = k.rolling(smooth_d).mean()
    out = df.copy()
    out["StochRSI_K"] = k
    out["StochRSI_D"] = d
    out["Signal"] = 0
    out.loc[(k < 20) & (k > d), "Signal"] = 1
    out.loc[(k > 80) & (k < d), "Signal"] = -1
    return out


def compute_cci(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
    typical = (df["High"] + df["Low"] + df["Close"]) / 3
    mean_tp = typical.rolling(period).mean()
    mean_dev = typical.rolling(period).apply(lambda x: np.mean(np.abs(x - x.mean())), raw=True)
    cci = (typical - mean_tp) / (0.015 * mean_dev.replace(0, np.nan))
    out = df.copy()
    out["CCI"] = cci
    out["Signal"] = 0
    out.loc[cci < -100, "Signal"] = 1
    out.loc[cci > 100, "Signal"] = -1
    return out


def compute_mfi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    typical = (df["High"] + df["Low"] + df["Close"]) / 3
    money_flow = typical * df["Volume"]
    pos_flow = money_flow.where(typical > typical.shift(1), 0).rolling(period).sum()
    neg_flow = money_flow.where(typical <= typical.shift(1), 0).rolling(period).sum()
    mfr = pos_flow / neg_flow.replace(0, np.nan)
    mfi = 100 - (100 / (1 + mfr))
    out = df.copy()
    out["MFI"] = mfi
    out["Signal"] = 0
    out.loc[mfi < 20, "Signal"] = 1
    out.loc[mfi > 80, "Signal"] = -1
    return out


def compute_obv(df: pd.DataFrame) -> pd.DataFrame:
    close = df["Close"]
    direction = np.sign(close.diff()).fillna(0)
    obv = (direction * df["Volume"]).cumsum()
    obv_sma = obv.rolling(20).mean()
    out = df.copy()
    out["OBV"] = obv
    out["OBV_SMA"] = obv_sma
    out["Signal"] = 0
    out.loc[(obv > obv_sma) & (obv.shift(1) <= obv_sma.shift(1)), "Signal"] = 1
    out.loc[(obv < obv_sma) & (obv.shift(1) >= obv_sma.shift(1)), "Signal"] = -1
    return out


def compute_williams_r(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    hh = df["High"].rolling(period).max()
    ll = df["Low"].rolling(period).min()
    wr = -100 * (hh - df["Close"]) / (hh - ll).replace(0, np.nan)
    out = df.copy()
    out["WilliamsR"] = wr
    out["Signal"] = 0
    out.loc[wr < -80, "Signal"] = 1
    out.loc[wr > -20, "Signal"] = -1
    return out


def compute_roc(df: pd.DataFrame, period: int = 12) -> pd.DataFrame:
    close = df["Close"]
    roc = (close - close.shift(period)) / close.shift(period).replace(0, np.nan) * 100
    out = df.copy()
    out["ROC"] = roc
    out["Signal"] = 0
    out.loc[(roc > 0) & (roc.shift(1) <= 0), "Signal"] = 1
    out.loc[(roc < 0) & (roc.shift(1) >= 0), "Signal"] = -1
    return out


def compute_aroon(df: pd.DataFrame, period: int = 25) -> pd.DataFrame:
    aroon_up = df["High"].rolling(period + 1).apply(
        lambda x: (np.argmax(x) / period) * 100, raw=True
    )
    aroon_down = df["Low"].rolling(period + 1).apply(
        lambda x: (np.argmin(x) / period) * 100, raw=True
    )
    aroon_osc = aroon_up - aroon_down
    out = df.copy()
    out["Aroon_Up"] = aroon_up
    out["Aroon_Down"] = aroon_down
    out["Aroon_Osc"] = aroon_osc
    out["Signal"] = 0
    out.loc[aroon_osc > 50, "Signal"] = 1
    out.loc[aroon_osc < -50, "Signal"] = -1
    return out


def compute_donchian(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
    upper = df["High"].rolling(period).max()
    lower = df["Low"].rolling(period).min()
    mid = (upper + lower) / 2
    out = df.copy()
    out["Donchian_Upper"] = upper
    out["Donchian_Lower"] = lower
    out["Donchian_Mid"] = mid
    out["Signal"] = 0
    close = df["Close"]
    out.loc[close >= upper, "Signal"] = 1
    out.loc[close <= lower, "Signal"] = -1
    return out


def compute_keltner(df: pd.DataFrame, period: int = 20,
                    atr_mult: float = 2.0) -> pd.DataFrame:
    close = df["Close"]
    mid = close.ewm(span=period, adjust=False).mean()
    atr = _rma(_true_range(df), period)
    upper = mid + atr_mult * atr
    lower = mid - atr_mult * atr
    out = df.copy()
    out["KC_Upper"] = upper
    out["KC_Mid"] = mid
    out["KC_Lower"] = lower
    out["Signal"] = 0
    out.loc[close < lower, "Signal"] = 1
    out.loc[close > upper, "Signal"] = -1
    return out


def compute_supertrend(df: pd.DataFrame, period: int = 10,
                       multiplier: float = 3.0) -> pd.DataFrame:
    atr = _rma(_true_range(df), period)
    hl2 = (df["High"] + df["Low"]) / 2
    upper_band = hl2 + multiplier * atr
    lower_band = hl2 - multiplier * atr
    close = df["Close"]
    n = len(df)
    supertrend = pd.Series(index=df.index, dtype=float)
    direction = pd.Series(index=df.index, dtype=int)
    for i in range(1, n):
        if close.iloc[i] > upper_band.iloc[i - 1]:
            direction.iloc[i] = 1
        elif close.iloc[i] < lower_band.iloc[i - 1]:
            direction.iloc[i] = -1
        else:
            direction.iloc[i] = direction.iloc[i - 1] if i > 0 else 0
        supertrend.iloc[i] = lower_band.iloc[i] if direction.iloc[i] == 1 else upper_band.iloc[i]
    out = df.copy()
    out["Supertrend"] = supertrend
    out["Signal"] = direction.astype(int)
    return out


def compute_vwap(df: pd.DataFrame) -> pd.DataFrame:
    typical = (df["High"] + df["Low"] + df["Close"]) / 3
    cum_vol = df["Volume"].cumsum()
    cum_tp_vol = (typical * df["Volume"]).cumsum()
    vwap = cum_tp_vol / cum_vol.replace(0, np.nan)
    close = df["Close"]
    out = df.copy()
    out["VWAP"] = vwap
    out["Signal"] = 0
    out.loc[(close > vwap) & (close.shift(1) <= vwap.shift(1)), "Signal"] = 1
    out.loc[(close < vwap) & (close.shift(1) >= vwap.shift(1)), "Signal"] = -1
    return out


def compute_parabolic_sar(df: pd.DataFrame, af_start: float = 0.02,
                          af_max: float = 0.20) -> pd.DataFrame:
    high, low = df["High"].values, df["Low"].values
    n = len(df)
    sar = np.zeros(n)
    trend = np.ones(n, dtype=int)
    ep = low[0]
    af = af_start
    sar[0] = high[0]
    for i in range(1, n):
        sar[i] = sar[i - 1] + af * (ep - sar[i - 1])
        if trend[i - 1] == 1:
            if low[i] < sar[i]:
                trend[i] = -1
                sar[i] = ep
                ep = low[i]
                af = af_start
            else:
                trend[i] = 1
                if high[i] > ep:
                    ep = high[i]
                    af = min(af + af_start, af_max)
        else:
            if high[i] > sar[i]:
                trend[i] = 1
                sar[i] = ep
                ep = high[i]
                af = af_start
            else:
                trend[i] = -1
                if low[i] < ep:
                    ep = low[i]
                    af = min(af + af_start, af_max)
    out = df.copy()
    out["SAR"] = sar
    out["Signal"] = trend
    return out


def compute_cmf(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
    close, high, low, volume = df["Close"], df["High"], df["Low"], df["Volume"]
    clv = ((close - low) - (high - close)) / (high - low).replace(0, np.nan)
    cmf = (clv * volume).rolling(period).sum() / volume.rolling(period).sum().replace(0, np.nan)
    out = df.copy()
    out["CMF"] = cmf
    out["Signal"] = 0
    out.loc[(cmf > 0) & (cmf.shift(1) <= 0), "Signal"] = 1
    out.loc[(cmf < 0) & (cmf.shift(1) >= 0), "Signal"] = -1
    return out


def compute_force_index(df: pd.DataFrame, period: int = 13) -> pd.DataFrame:
    fi = df["Close"].diff() * df["Volume"]
    fi_ema = fi.ewm(span=period, adjust=False).mean()
    out = df.copy()
    out["ForceIndex"] = fi_ema
    out["Signal"] = 0
    out.loc[(fi_ema > 0) & (fi_ema.shift(1) <= 0), "Signal"] = 1
    out.loc[(fi_ema < 0) & (fi_ema.shift(1) >= 0), "Signal"] = -1
    return out


def compute_trix(df: pd.DataFrame, period: int = 15) -> pd.DataFrame:
    close = df["Close"]
    ema1 = close.ewm(span=period, adjust=False).mean()
    ema2 = ema1.ewm(span=period, adjust=False).mean()
    ema3 = ema2.ewm(span=period, adjust=False).mean()
    trix = ema3.pct_change() * 100
    signal_line = trix.rolling(9).mean()
    out = df.copy()
    out["TRIX"] = trix
    out["TRIX_Signal"] = signal_line
    out["Signal"] = 0
    out.loc[(trix > signal_line) & (trix.shift(1) <= signal_line.shift(1)), "Signal"] = 1
    out.loc[(trix < signal_line) & (trix.shift(1) >= signal_line.shift(1)), "Signal"] = -1
    return out


def compute_dpo(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
    close = df["Close"]
    shift = period // 2 + 1
    sma = close.rolling(period).mean()
    dpo = close - sma.shift(shift)
    out = df.copy()
    out["DPO"] = dpo
    out["Signal"] = 0
    out.loc[(dpo > 0) & (dpo.shift(1) <= 0), "Signal"] = 1
    out.loc[(dpo < 0) & (dpo.shift(1) >= 0), "Signal"] = -1
    return out


def compute_ultimate_oscillator(df: pd.DataFrame, p1: int = 7,
                                 p2: int = 14, p3: int = 28) -> pd.DataFrame:
    close, high, low = df["Close"], df["High"], df["Low"]
    prev_close = close.shift(1)
    bp = close - pd.concat([low, prev_close], axis=1).min(axis=1)
    tr = pd.concat([high, prev_close], axis=1).max(axis=1) - pd.concat([low, prev_close], axis=1).min(axis=1)

    def _avg(period):
        return bp.rolling(period).sum() / tr.rolling(period).sum().replace(0, np.nan)

    uo = 100 * (4 * _avg(p1) + 2 * _avg(p2) + _avg(p3)) / 7
    out = df.copy()
    out["UO"] = uo
    out["Signal"] = 0
    out.loc[uo < 30, "Signal"] = 1
    out.loc[uo > 70, "Signal"] = -1
    return out


# ─────────────────────────────────────────────────────────────────────────────
# INDICATOR REGISTRY
# ─────────────────────────────────────────────────────────────────────────────

INDICATOR_REGISTRY = {
    "rsi": {
        "fn": compute_rsi,
        "label": "Relative Strength Index (RSI)",
        "category": "Momentum",
        "params": {
            "period":         {"type": "int",   "min": 5,  "max": 50,  "default": 14, "step": 1},
            "buy_threshold":  {"type": "float", "min": 10, "max": 45,  "default": 30, "step": 5},
            "sell_threshold": {"type": "float", "min": 55, "max": 90,  "default": 70, "step": 5},
        },
    },
    "macd": {
        "fn": compute_macd,
        "label": "MACD (Moving Average Convergence Divergence)",
        "category": "Trend",
        "params": {
            "fast":   {"type": "int", "min": 5,  "max": 20,  "default": 12, "step": 1},
            "slow":   {"type": "int", "min": 15, "max": 50,  "default": 26, "step": 1},
            "signal": {"type": "int", "min": 5,  "max": 15,  "default": 9,  "step": 1},
        },
    },
    "ema": {
        "fn": compute_ema,
        "label": "Exponential Moving Average Crossover",
        "category": "Trend",
        "params": {
            "fast_period": {"type": "int", "min": 5,  "max": 30,  "default": 9,  "step": 1},
            "slow_period": {"type": "int", "min": 10, "max": 100, "default": 21, "step": 1},
        },
    },
    "sma": {
        "fn": compute_sma,
        "label": "Simple Moving Average Golden/Death Cross",
        "category": "Trend",
        "params": {
            "fast_period": {"type": "int", "min": 10, "max": 100,  "default": 50,  "step": 5},
            "slow_period": {"type": "int", "min": 50, "max": 500,  "default": 200, "step": 10},
        },
    },
    "bollinger": {
        "fn": compute_bollinger,
        "label": "Bollinger Bands",
        "category": "Volatility",
        "params": {
            "period":  {"type": "int",   "min": 10, "max": 50, "default": 20, "step": 1},
            "num_std": {"type": "float", "min": 1,  "max": 4,  "default": 2,  "step": 0.5},
        },
    },
    "atr": {
        "fn": compute_atr,
        "label": "Average True Range Breakout",
        "category": "Volatility",
        "params": {
            "period": {"type": "int", "min": 5, "max": 30, "default": 14, "step": 1},
        },
    },
    "adx": {
        "fn": compute_adx,
        "label": "Average Directional Index (ADX)",
        "category": "Trend",
        "params": {
            "period":    {"type": "int",   "min": 5,  "max": 30, "default": 14, "step": 1},
            "threshold": {"type": "float", "min": 15, "max": 40, "default": 25, "step": 5},
        },
    },
    "stoch_rsi": {
        "fn": compute_stoch_rsi,
        "label": "Stochastic RSI",
        "category": "Momentum",
        "params": {
            "rsi_period":   {"type": "int", "min": 5,  "max": 30, "default": 14, "step": 1},
            "stoch_period": {"type": "int", "min": 5,  "max": 30, "default": 14, "step": 1},
            "smooth_k":     {"type": "int", "min": 1,  "max": 10, "default": 3,  "step": 1},
            "smooth_d":     {"type": "int", "min": 1,  "max": 10, "default": 3,  "step": 1},
        },
    },
    "cci": {
        "fn": compute_cci,
        "label": "Commodity Channel Index (CCI)",
        "category": "Momentum",
        "params": {
            "period": {"type": "int", "min": 10, "max": 50, "default": 20, "step": 1},
        },
    },
    "mfi": {
        "fn": compute_mfi,
        "label": "Money Flow Index (MFI)",
        "category": "Volume",
        "params": {
            "period": {"type": "int", "min": 5, "max": 30, "default": 14, "step": 1},
        },
    },
    "obv": {
        "fn": compute_obv,
        "label": "On-Balance Volume (OBV)",
        "category": "Volume",
        "params": {},
    },
    "williams_r": {
        "fn": compute_williams_r,
        "label": "Williams %R",
        "category": "Momentum",
        "params": {
            "period": {"type": "int", "min": 5, "max": 30, "default": 14, "step": 1},
        },
    },
    "roc": {
        "fn": compute_roc,
        "label": "Rate of Change (ROC)",
        "category": "Momentum",
        "params": {
            "period": {"type": "int", "min": 5, "max": 50, "default": 12, "step": 1},
        },
    },
    "aroon": {
        "fn": compute_aroon,
        "label": "Aroon Oscillator",
        "category": "Trend",
        "params": {
            "period": {"type": "int", "min": 10, "max": 50, "default": 25, "step": 1},
        },
    },
    "donchian": {
        "fn": compute_donchian,
        "label": "Donchian Channel Breakout",
        "category": "Trend",
        "params": {
            "period": {"type": "int", "min": 10, "max": 60, "default": 20, "step": 1},
        },
    },
    "keltner": {
        "fn": compute_keltner,
        "label": "Keltner Channel",
        "category": "Volatility",
        "params": {
            "period":   {"type": "int",   "min": 10, "max": 50, "default": 20, "step": 1},
            "atr_mult": {"type": "float", "min": 1,  "max": 4,  "default": 2,  "step": 0.5},
        },
    },
    "supertrend": {
        "fn": compute_supertrend,
        "label": "Supertrend",
        "category": "Trend",
        "params": {
            "period":     {"type": "int",   "min": 5,  "max": 30, "default": 10, "step": 1},
            "multiplier": {"type": "float", "min": 1,  "max": 6,  "default": 3,  "step": 0.5},
        },
    },
    "vwap": {
        "fn": compute_vwap,
        "label": "Volume Weighted Average Price (VWAP) Crossover",
        "category": "Volume",
        "params": {},
    },
    "parabolic_sar": {
        "fn": compute_parabolic_sar,
        "label": "Parabolic SAR",
        "category": "Trend",
        "params": {
            "af_start": {"type": "float", "min": 0.01, "max": 0.10, "default": 0.02, "step": 0.01},
            "af_max":   {"type": "float", "min": 0.10, "max": 0.50, "default": 0.20, "step": 0.05},
        },
    },
    "cmf": {
        "fn": compute_cmf,
        "label": "Chaikin Money Flow (CMF)",
        "category": "Volume",
        "params": {
            "period": {"type": "int", "min": 10, "max": 30, "default": 20, "step": 1},
        },
    },
    "force_index": {
        "fn": compute_force_index,
        "label": "Force Index",
        "category": "Volume",
        "params": {
            "period": {"type": "int", "min": 5, "max": 30, "default": 13, "step": 1},
        },
    },
    "trix": {
        "fn": compute_trix,
        "label": "TRIX Oscillator",
        "category": "Momentum",
        "params": {
            "period": {"type": "int", "min": 5, "max": 30, "default": 15, "step": 1},
        },
    },
    "dpo": {
        "fn": compute_dpo,
        "label": "Detrended Price Oscillator (DPO)",
        "category": "Momentum",
        "params": {
            "period": {"type": "int", "min": 10, "max": 50, "default": 20, "step": 1},
        },
    },
    "ultimate_oscillator": {
        "fn": compute_ultimate_oscillator,
        "label": "Ultimate Oscillator",
        "category": "Momentum",
        "params": {
            "p1": {"type": "int", "min": 3,  "max": 14, "default": 7,  "step": 1},
            "p2": {"type": "int", "min": 7,  "max": 21, "default": 14, "step": 1},
            "p3": {"type": "int", "min": 14, "max": 56, "default": 28, "step": 1},
        },
    },
}


def get_indicator_list() -> list:
    """Return list of indicator metadata (excluding the fn reference) for the API."""
    return [
        {
            "name": name,
            "label": meta["label"],
            "category": meta["category"],
            "params": meta["params"],
        }
        for name, meta in INDICATOR_REGISTRY.items()
    ]


def compute_indicator(df: pd.DataFrame, name: str, params: dict) -> pd.DataFrame:
    """Compute a named indicator with given params. Raises KeyError if unknown."""
    if name not in INDICATOR_REGISTRY:
        raise KeyError(f"Unknown indicator: {name}")
    fn = INDICATOR_REGISTRY[name]["fn"]
    # Filter params to only those the function accepts
    import inspect
    sig = inspect.signature(fn)
    valid_keys = set(sig.parameters.keys()) - {"df"}
    filtered = {k: v for k, v in params.items() if k in valid_keys}
    return fn(df, **filtered)
