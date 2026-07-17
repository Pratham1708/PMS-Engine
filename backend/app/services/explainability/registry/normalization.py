# app/services/explainability/registry/normalization.py

NORMALIZATION_REGISTRY = {
    # Trend
    "ema20": {
        "method": "Distance-Based Sign",
        "range": "-100 to 100",
        "logic": "+100 if Close > EMA20 else -100"
    },
    "ema50": {
        "method": "Distance-Based Sign",
        "range": "-100 to 100",
        "logic": "+100 if Close > EMA50 else -100"
    },
    "ema200": {
        "method": "Distance-Based Sign",
        "range": "-100 to 100",
        "logic": "+100 if Close > EMA200 else -100"
    },
    "adx": {
        "method": "Step Activation Threshold",
        "range": "-100 to 100",
        "logic": "+100 if ADX > 25 (trending regime) else -100 (rangebound)"
    },
    "supertrend": {
        "method": "Overlay Sign Indicator",
        "range": "-100 to 100",
        "logic": "+100 if Close > Supertrend line else -100"
    },
    
    # Momentum
    "rsi": {
        "method": "Min-Max Standard Scaling",
        "range": "-100 to 100",
        "logic": "Calculates (RSI - 50) * 2 to map neutral 50 as zero index."
    },
    "macd": {
        "method": "Divergence Sign",
        "range": "-100 to 100",
        "logic": "+100 if MACD > MACD Signal else -100"
    },
    "macd_signal": {
        "method": "Divergence Sign",
        "range": "-100 to 100",
        "logic": "+100 if MACD > MACD Signal else -100"
    },
    "stoch_k": {
        "method": "Oscillator Re-scaling",
        "range": "-100 to 100",
        "logic": "Calculates (Stochastic - 50) * 2 to represent speed dynamics."
    },
    "cci": {
        "method": "Standard Score Threshold",
        "range": "-100 to 100",
        "logic": "+100 if CCI > 100, -100 if CCI < -100, else linear scaling."
    },
    "roc": {
        "method": "Linear Re-scaling",
        "range": "-100 to 100",
        "logic": "ROC return percentage clipped and normalized relative to 20-period volatility."
    },
    "williams_r": {
        "method": "Oscillator Re-scaling",
        "range": "-100 to 100",
        "logic": "Calculates (Williams %R + 50) * 2 to align with standard oscillator boundaries."
    },
    
    # Volume
    "obv": {
        "method": "Directional Volume Accumulation",
        "range": "-100 to 100",
        "logic": "+100 if OBV > 20-period OBV average else -100"
    },
    "mfi": {
        "method": "Oscillator Re-scaling",
        "range": "-100 to 100",
        "logic": "Calculates (MFI - 50) * 2 to map money flow momentum."
    },
    "volume_ma": {
        "method": "Ratio Normalization",
        "range": "-100 to 100",
        "logic": "Calculates (Volume / Volume MA - 1.0) * 100 clipped at bounds."
    },
    "cmf": {
        "method": "Multiplier Bounds Scaling",
        "range": "-100 to 100",
        "logic": "CMF value (-1.0 to 1.0) multiplied by 100."
    },
    "volume_breakout": {
        "method": "Std Deviation Threshold",
        "range": "-100 to 100",
        "logic": "+100 if volume exceeds Bollinger upper band boundary, else -100"
    },
    
    # Volatility
    "atr": {
        "method": "Vol Scale Normalization",
        "range": "0 to 100",
        "logic": "ATR divided by asset price to represent volatility ratio percentage."
    },
    "hist_vol": {
        "method": "Annualized Vol Scaling",
        "range": "0 to 100",
        "logic": "Annualized standard deviation of daily log returns."
    },
    "bb_width": {
        "method": "Vol Bandwidth Scaling",
        "range": "0 to 100",
        "logic": "Width between upper/lower Bollinger Bands relative to the middle SMA."
    },
    "atr_percentile": {
        "method": "Rolling Percentile Rank",
        "range": "0 to 100",
        "logic": "Today's ATR ranked against 252-day lookback series."
    },
    
    # Breakout
    "resistance_break": {
        "method": "Binary State Verification",
        "range": "-100 to 100",
        "logic": "+100 if price breaks above 20-day high channel else -100"
    },
    "support_holding": {
        "method": "Binary State Verification",
        "range": "-100 to 100",
        "logic": "+100 if price holds above 20-day low channel else -100"
    },
    "donchian_breakout": {
        "method": "Channel Bounds Check",
        "range": "-100 to 100",
        "logic": "+100 if close matches Donchian upper band boundary else -100"
    },
    "volume_confirmation": {
        "method": "Ratio Normalization",
        "range": "-100 to 100",
        "logic": "+100 if volume exceeds 1.25x rolling average, else -100"
    },
    
    # ML Models
    "rf": {
        "method": "Probability Sigmoid Scaling",
        "range": "-100 to 100",
        "logic": "Random forest prediction signal mapped linearly to model confidence intervals."
    },
    "xgb": {
        "method": "Probability Sigmoid Scaling",
        "range": "-100 to 100",
        "logic": "XGBoost classifier probability logits normalized to score boundaries."
    },
    "lgb": {
        "method": "Probability Sigmoid Scaling",
        "range": "-100 to 100",
        "logic": "LightGBM probability classes normalized using softmax mapping."
    },
    
    # GRU
    "p_long": {
        "method": "Probability Softmax Output",
        "range": "0 to 100",
        "logic": "Percentage probability output from the sequential GRU long node."
    },
    "p_hold": {
        "method": "Probability Softmax Output",
        "range": "0 to 100",
        "logic": "Percentage probability output from the sequential GRU hold node."
    },
    "p_short": {
        "method": "Probability Softmax Output",
        "range": "0 to 100",
        "logic": "Percentage probability output from the sequential GRU short node."
    },
    "higher_highs": {
        "method": "Lookback Fraction Normalization",
        "range": "0 to 100",
        "logic": "Fraction of higher-high sessions inside the rolling 30-day sequence."
    },
    "higher_lows": {
        "method": "Lookback Fraction Normalization",
        "range": "0 to 100",
        "logic": "Fraction of higher-low sessions inside the rolling 30-day sequence."
    },
    "volume_expansion": {
        "method": "Lookback Fraction Normalization",
        "range": "0 to 100",
        "logic": "Fraction of positive volume expansion days inside the sequence."
    },
    "volatility_compression": {
        "method": "Historical Vol Percentile",
        "range": "0 to 100",
        "logic": "Standardized normalization of ATR bandwidth."
    },
    "trend_persistence": {
        "method": "Regression Slope Scaling",
        "range": "-100 to 100",
        "logic": "Normalized slope parameter of log price regression series."
    },
    
    # Risk
    "beta": {
        "method": "Historical Covariance Ratio",
        "range": "0.0 to 3.0+",
        "logic": "Raw coefficient calculated over 252-day daily return series."
    },
    "sharpe": {
        "method": "Risk-Free Excess Ratio",
        "range": "-3.0 to 5.0+",
        "logic": "Excess annualized return divided by annualized realized volatility."
    },
    "volatility": {
        "method": "Realized Annualized Standard Deviation",
        "range": "0% to 100%+",
        "logic": "Standard deviation of daily log returns scaled by 252 trading sessions."
    },
    "drawdown": {
        "method": "Maximum Trough Percentage",
        "range": "-100% to 0%",
        "logic": "Highest peak-to-trough return drawdown value observed."
    },
    "downside_dev": {
        "method": "Downside Deviation Annualized",
        "range": "0% to 100%+",
        "logic": "Annualized volatility computed using only negative return sessions."
    },
    "var": {
        "method": "Historical Empirical Percentile",
        "range": "0% to 50%",
        "logic": "5th percentile value of the daily asset returns distribution."
    },
    "cvar": {
        "method": "Historical Conditional Mean",
        "range": "0% to 50%",
        "logic": "Mean value of the daily returns distribution below the 5th percentile."
    },
    "confidence_inverse": {
        "method": "Uncertainty Linear Map",
        "range": "0 to 100",
        "logic": "Linear inverse function mapping consensus confidence value."
    },
    
    # Reliability
    "accuracy": {
        "method": "Hit Rate Ratio",
        "range": "0% to 100%",
        "logic": "Accuracy ratio of final predictions relative to forward returns."
    },
    "agreement": {
        "method": "Concordance Sign Ratio",
        "range": "0% to 100%",
        "logic": "Ratio of sub-models sharing the same directional polarity."
    },
    "completeness": {
        "method": "Integrity Check Ratio",
        "range": "0% to 100%",
        "logic": "Percentage of clean, uncorrupted, and populated data feed nodes."
    },
    "similarity": {
        "method": "Feature Vector Cosine Similarity",
        "range": "0% to 100%",
        "logic": "Similarity coefficient relative to baseline macro indicators."
    },
    
    # Confidence
    "baseline": {
        "method": "Performance Probability Scaling",
        "range": "0 to 100",
        "logic": "Expected baseline statistical F1 performance metric."
    },
    "consensus_boost": {
        "method": "Consensus Step Boost Mapping",
        "range": "-10 to 15",
        "logic": "+15.0 for 3/3 model concordance, +5.0 for 2/3 model concordance, else -10.0."
    },
    "technical_score": {
        "method": "Direct Score Mapping",
        "range": "-100 to 100",
        "logic": "Calculated indicator blend."
    },
    "ml_score": {
        "method": "Direct Score Mapping",
        "range": "-100 to 100",
        "logic": "Calculated ensemble tree signal blend."
    },
    "gru_score": {
        "method": "Direct Score Mapping",
        "range": "-100 to 100",
        "logic": "Calculated temporal sequence forecast."
    },
    "reliability_score": {
        "method": "Direct Score Mapping",
        "range": "0 to 100",
        "logic": "Calculated telemetry reliability rating."
    }
}
