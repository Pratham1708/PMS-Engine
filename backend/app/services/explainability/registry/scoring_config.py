# app/services/explainability/registry/scoring_config.py

# Weights for composite score rollup
COMPOSITE_WEIGHTS = {
    "technical": 0.40,
    "ml": 0.35,
    "gru": 0.15,
    "reliability": 0.10
}

# Weights for technical score components
TECHNICAL_WEIGHTS = {
    "trend": 0.30,
    "momentum": 0.20,
    "rsi": 0.15,
    "volatility": 0.15,
    "historical": 0.20
}

# Subweights within Technical Trend Category
TECHNICAL_TREND_WEIGHTS = {
    "ema20": 0.08,
    "ema50": 0.06,
    "ema200": 0.06,
    "adx": 0.05,
    "supertrend": 0.05
}

# Subweights within Technical Momentum Category
TECHNICAL_MOMENTUM_WEIGHTS = {
    "rsi": 0.05,
    "macd": 0.05,
    "stoch_k": 0.05,
    "cci": 0.05,
    "roc": 0.05,
    "williams_r": 0.05
}

# Subweights within Technical Volume Category
TECHNICAL_VOLUME_WEIGHTS = {
    "obv": 0.06,
    "mfi": 0.04,
    "volume_ma": 0.04,
    "cmf": 0.03,
    "volume_breakout": 0.03
}

# Subweights within Technical Volatility Category
TECHNICAL_VOLATILITY_WEIGHTS = {
    "atr": 0.05,
    "hist_vol": 0.04,
    "bb_width": 0.03,
    "atr_percentile": 0.03
}

# Subweights within Technical Breakout Category
TECHNICAL_BREAKOUT_WEIGHTS = {
    "resistance_break": 0.05,
    "support_holding": 0.05,
    "donchian_breakout": 0.05,
    "volume_confirmation": 0.05
}

# Weights for GRU sequence patterns
GRU_WEIGHTS = {
    "p_long": 0.50,
    "p_short": -0.50,
    "p_hold": 0.00
}

GRU_PATTERN_WEIGHTS = {
    "higher_highs": 0.22,
    "higher_lows": 0.18,
    "volume_expansion": 0.12,
    "volatility_compression": 0.09,
    "trend_persistence": 0.39
}

# Weights for ensemble classifiers
ENSEMBLE_WEIGHTS = {
    "rf": 0.35,
    "xgb": 0.35,
    "lgb": 0.30
}

# Weights for trend score rollup
TREND_WEIGHTS = {
    "gru": 0.60,
    "technical": 0.40
}

# Weights for momentum score rollup
MOMENTUM_WEIGHTS = {
    "technical": 0.80,
    "ml": 0.20
}

# Weights for risk score rollup
RISK_WEIGHTS = {
    "consensus": 0.30,
    "drawdown": 0.40,
    "volatility": 0.30
}

# Weights for reliability score rollup
RELIABILITY_WEIGHTS = {
    "accuracy": 0.30,
    "agreement": 0.30,
    "completeness": 0.20,
    "similarity": 0.20
}

# Weights for confidence score rollup
CONFIDENCE_WEIGHTS = {
    "baseline": 1.00,
    "consensus_boost": 1.00
}
