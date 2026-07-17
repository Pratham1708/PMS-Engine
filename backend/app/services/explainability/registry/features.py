# app/services/explainability/registry/features.py

METADATA_REGISTRY = {
    # --- Technical Indicators ---
    # Trend
    "ema20": {
        "display_name": "EMA 20 Alignment",
        "category": "Trend",
        "data_source": "Technical Indicator",
        "description": "Measures price alignment relative to the short-term 20-period Exponential Moving Average."
    },
    "ema50": {
        "display_name": "EMA 50 Alignment",
        "category": "Trend",
        "data_source": "Technical Indicator",
        "description": "Measures price alignment relative to the medium-term 50-period Exponential Moving Average."
    },
    "ema200": {
        "display_name": "EMA 200 Alignment",
        "category": "Trend",
        "data_source": "Technical Indicator",
        "description": "Measures price alignment relative to the long-term 200-period Exponential Moving Average."
    },
    "adx": {
        "display_name": "ADX Trend Strength",
        "category": "Trend",
        "data_source": "Technical Indicator",
        "description": "Average Directional Index measures the overall strength or velocity of the current trend (regardless of direction)."
    },
    "supertrend": {
        "display_name": "Supertrend Crossover",
        "category": "Trend",
        "data_source": "Technical Indicator",
        "description": "Trend-following overlay combining ATR and median price to detect structural support and resistance flips."
    },
    # Momentum
    "rsi": {
        "display_name": "RSI Relative Strength",
        "category": "Momentum",
        "data_source": "Technical Indicator",
        "description": "Relative Strength Index measures the speed and change of price movements to identify overbought or oversold cycles."
    },
    "macd": {
        "display_name": "MACD Divergence",
        "category": "Momentum",
        "data_source": "Technical Indicator",
        "description": "Moving Average Convergence Divergence line measures short-term trend velocity shift relative to the signal line."
    },
    "macd_signal": {
        "display_name": "MACD Signal Crossover",
        "category": "Momentum",
        "data_source": "Technical Indicator",
        "description": "MACD signal line crossover tracking direction of short-term momentum acceleration."
    },
    "stoch_k": {
        "display_name": "Stochastic %K Oscillator",
        "category": "Momentum",
        "data_source": "Technical Indicator",
        "description": "Stochastic %K Oscillator compares close price to high-low range over 14 sessions to track cyclical pivot points."
    },
    "cci": {
        "display_name": "Commodity Channel Index (CCI)",
        "category": "Momentum",
        "data_source": "Technical Indicator",
        "description": "Measures the current price level relative to an average price level over a given time interval."
    },
    "roc": {
        "display_name": "Rate of Change (ROC)",
        "category": "Momentum",
        "data_source": "Technical Indicator",
        "description": "Rate of Change measures percentage velocity shifts between current close and close N-periods ago."
    },
    "williams_r": {
        "display_name": "Williams %R Oscillator",
        "category": "Momentum",
        "data_source": "Technical Indicator",
        "description": "Williams %R oscillator measures price relative to the highest high of the lookback period."
    },
    # Volume
    "obv": {
        "display_name": "On-Balance Volume (OBV)",
        "category": "Volume",
        "data_source": "Technical Indicator",
        "description": "On-Balance Volume acts as a cumulative momentum index matching volume shifts directly to price direction."
    },
    "mfi": {
        "display_name": "Money Flow Index (MFI)",
        "category": "Volume",
        "data_source": "Technical Indicator",
        "description": "Volume-weighted Relative Strength Index tracking flow of money into and out of the security."
    },
    "volume_ma": {
        "display_name": "Volume Moving Average Ratio",
        "category": "Volume",
        "data_source": "Technical Indicator",
        "description": "Compares today's volume to its 20-period moving average to verify institutional participation."
    },
    "cmf": {
        "display_name": "Chaikin Money Flow (CMF)",
        "category": "Volume",
        "data_source": "Technical Indicator",
        "description": "Measures accumulation and distribution volume pressure over a 20-period baseline."
    },
    "volume_breakout": {
        "display_name": "Volume Breakout Index",
        "category": "Volume",
        "data_source": "Technical Indicator",
        "description": "Detects high-liquidity breakouts exceeding standard deviations to confirm buyer commitment."
    },
    # Volatility
    "atr": {
        "display_name": "Average True Range (ATR)",
        "category": "Volatility",
        "data_source": "Technical Indicator",
        "description": "Average True Range measures market volatility by decomposing the entire range of an asset for that period."
    },
    "hist_vol": {
        "display_name": "Historical Volatility (20-day)",
        "category": "Volatility",
        "data_source": "Technical Indicator",
        "description": "Standard deviation of daily log returns over a rolling window representing asset price swings."
    },
    "bb_width": {
        "display_name": "Bollinger Band Width",
        "category": "Volatility",
        "data_source": "Technical Indicator",
        "description": "Measures the difference between upper and lower Bollinger bands to track volatility compression and expansion cycles."
    },
    "atr_percentile": {
        "display_name": "ATR Volatility Percentile",
        "category": "Volatility",
        "data_source": "Technical Indicator",
        "description": "Normalized ATR value relative to historical volatility ranges to flag consolidation vs breakout regimes."
    },
    # Breakout
    "resistance_break": {
        "display_name": "Resistance Breakout Check",
        "category": "Breakout",
        "data_source": "Technical Indicator",
        "description": "Detects if price has crossed above its rolling 20-period high boundary."
    },
    "support_holding": {
        "display_name": "Support Level Validation",
        "category": "Breakout",
        "data_source": "Technical Indicator",
        "description": "Detects if price is maintaining above its major rolling support channels."
    },
    "donchian_breakout": {
        "display_name": "Donchian Channel Breakout",
        "category": "Breakout",
        "data_source": "Technical Indicator",
        "description": "Tracks crossovers of Upper and Lower Donchian channels to identify momentum breakouts."
    },
    "volume_confirmation": {
        "display_name": "Breakout Volume Confirmation",
        "category": "Breakout",
        "data_source": "Technical Indicator",
        "description": "Verifies that breakout movements are accompanied by high-liquidity volume expansions."
    },
    
    # --- Ensemble Models ---
    "rf": {
        "display_name": "Random Forest Classifier",
        "category": "Ensemble Models",
        "data_source": "ML Model",
        "description": "Bootstrap aggregated (bagged) decision tree model predicting return probabilities based on tabular indicators."
    },
    "xgb": {
        "display_name": "XGBoost Classifier",
        "category": "Ensemble Models",
        "data_source": "ML Model",
        "description": "Extreme Gradient Boosting decision trees trained on sequential residuals to predict pricing direction."
    },
    "lgb": {
        "display_name": "LightGBM Classifier",
        "category": "Ensemble Models",
        "data_source": "ML Model",
        "description": "Leaf-wise histogram optimized gradient boosting classifier specializing in multi-class return categories."
    },
    
    # --- GRU Patterns ---
    "p_long": {
        "display_name": "GRU Long Continuation Probability",
        "category": "GRU Neural Components",
        "data_source": "Neural Network",
        "description": "Recurrent neural network probability projecting positive sequence continuation."
    },
    "p_hold": {
        "display_name": "GRU Hold Consolidation Probability",
        "category": "GRU Neural Components",
        "data_source": "Neural Network",
        "description": "Recurrent neural network probability projecting sideways sequence consolidation."
    },
    "p_short": {
        "display_name": "GRU Short Reversal Probability",
        "category": "GRU Neural Components",
        "data_source": "Neural Network",
        "description": "Recurrent neural network probability projecting negative sequence continuation."
    },
    "higher_highs": {
        "display_name": "Higher Highs Pattern Detection",
        "category": "Temporal Patterns",
        "data_source": "Neural Network",
        "description": "GRU neural network sequence activation matching rolling peaks pattern accumulation."
    },
    "higher_lows": {
        "display_name": "Higher Lows Pattern Detection",
        "category": "Temporal Patterns",
        "data_source": "Neural Network",
        "description": "GRU neural network sequence activation matching rolling troughs pattern support."
    },
    "volume_expansion": {
        "display_name": "Volume Accumulation Sequence",
        "category": "Temporal Patterns",
        "data_source": "Neural Network",
        "description": "GRU neural network sequence activation matching volume growth during positive bars."
    },
    "volatility_compression": {
        "display_name": "Volatility Squeeze Pattern",
        "category": "Temporal Patterns",
        "data_source": "Neural Network",
        "description": "GRU neural network sequence activation matching volatility squeeze patterns preceding breakouts."
    },
    "trend_persistence": {
        "display_name": "Trend Persistence Lookback",
        "category": "Temporal Patterns",
        "data_source": "Neural Network",
        "description": "GRU neural network sequence activation matching long-term macro trend stability parameters."
    },
    
    # --- Risk ---
    "beta": {
        "display_name": "Systematic Beta Factor",
        "category": "Systematic Volatility",
        "data_source": "Fundamental / Risk",
        "description": "Covariance of asset returns relative to the benchmark Nifty 50 Index."
    },
    "sharpe": {
        "display_name": "Sharpe Ratio (Risk-Adjusted Return)",
        "category": "Systematic Volatility",
        "data_source": "Risk Metric",
        "description": "Asset return in excess of risk-free rate per unit of asset standard deviation."
    },
    "volatility": {
        "display_name": "Asset Realized Volatility",
        "category": "Systematic Volatility",
        "data_source": "Risk Metric",
        "description": "Annualized standard deviation of daily log returns."
    },
    "drawdown": {
        "display_name": "Maximum Historical Drawdown",
        "category": "Drawdown Risk",
        "data_source": "Risk Metric",
        "description": "Largest peak-to-trough drop in price history."
    },
    "downside_dev": {
        "display_name": "Downside Deviation (Sortino)",
        "category": "Drawdown Risk",
        "data_source": "Risk Metric",
        "description": "Standard deviation of negative asset returns, ignoring positive returns."
    },
    "var": {
        "display_name": "Value at Risk (95% VaR)",
        "category": "Drawdown Risk",
        "data_source": "Risk Metric",
        "description": "Maximum expected portfolio loss at a 95% confidence level over a 1-day horizon."
    },
    "cvar": {
        "display_name": "Conditional Value at Risk (CVaR)",
        "category": "Drawdown Risk",
        "data_source": "Risk Metric",
        "description": "Average expected loss in the worst 5% of return distributions."
    },
    "confidence_inverse": {
        "display_name": "Model Disagreement / Uncertainty",
        "category": "Model Uncertainty",
        "data_source": "Telemetry",
        "description": "Inverse of system rating Confidence, mapping uncertainty into risk."
    },
    
    # --- Reliability ---
    "accuracy": {
        "display_name": "Historical Hit Rate",
        "category": "Model Performance",
        "data_source": "Telemetry",
        "description": "Historical predictive accuracy (win rate) of scoring models."
    },
    "agreement": {
        "display_name": "Scoring Model Consensus",
        "category": "Model Performance",
        "data_source": "Telemetry",
        "description": "Classifier concordance/agreement rating across technical, ML, and GRU engines."
    },
    "completeness": {
        "display_name": "Data Feed Integrity",
        "category": "Data & Telemetry",
        "data_source": "Telemetry",
        "description": "Checks for missing values, stale quotes, or corporate actions in inputs."
    },
    "similarity": {
        "display_name": "Regime Similarity Index",
        "category": "Data & Telemetry",
        "data_source": "Telemetry",
        "description": "Statistical similarity between current macro-market volatility context and model training baseline."
    },
    
    # --- Confidence ---
    "baseline": {
        "display_name": "Historical Classifier Baseline",
        "category": "Model Conviction",
        "data_source": "Telemetry",
        "description": "Baseline statistical model confidence rating based on out-of-sample performance."
    },
    "consensus_boost": {
        "display_name": "Consensus Alignment Boost",
        "category": "Model Conviction",
        "data_source": "Telemetry",
        "description": "Boost (+15.0) or penalty (-10.0) based on directional agreement of underlying score signals."
    },
    
    # --- Parent Rollups (Trend, Momentum, Composite) ---
    "technical_score": {
        "display_name": "Technical Score Component",
        "category": "Rollup Core Engines",
        "data_source": "Scoring Engine",
        "description": "Combined technical trend and momentum oscillator overlay score."
    },
    "ml_score": {
        "display_name": "Ensemble ML Score Component",
        "category": "Rollup Core Engines",
        "data_source": "Scoring Engine",
        "description": "Tree ensemble prediction consensus score."
    },
    "gru_score": {
        "display_name": "GRU Deep Neural Component",
        "category": "Rollup Core Engines",
        "data_source": "Scoring Engine",
        "description": "Neural temporal sequence trend prediction score."
    },
    "reliability_score": {
        "display_name": "Model Scoring Reliability Component",
        "category": "Rollup Core Engines",
        "data_source": "Scoring Engine",
        "description": "Data completeness and regime concordance reliability rating."
    }
}
