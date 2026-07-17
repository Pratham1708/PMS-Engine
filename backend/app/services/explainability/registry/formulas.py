# app/services/explainability/registry/formulas.py

FORMULA_REGISTRY = {
    # Trend
    "ema20": {
        "plain_formula": "Close > EMA(20)",
        "latex_formula": "C_t > \\text{EMA}(C, 20)_t"
    },
    "ema50": {
        "plain_formula": "Close > EMA(50)",
        "latex_formula": "C_t > \\text{EMA}(C, 50)_t"
    },
    "ema200": {
        "plain_formula": "Close > EMA(200)",
        "latex_formula": "C_t > \\text{EMA}(C, 200)_t"
    },
    "adx": {
        "plain_formula": "ADX(14) > 25",
        "latex_formula": "\\text{ADX}_{14} > 25"
    },
    "supertrend": {
        "plain_formula": "Close > Supertrend(10, 3)",
        "latex_formula": "C_t > \\text{Supertrend}(10, 3)_t"
    },
    # Momentum
    "rsi": {
        "plain_formula": "100 - (100 / (1 + RS))",
        "latex_formula": "\\text{RSI}_{14} = 100 - \\frac{100}{1 + \\frac{\\text{EMA}(U, 14)}{\\text{EMA}(D, 14)}}"
    },
    "macd": {
        "plain_formula": "EMA(12) - EMA(26)",
        "latex_formula": "\\text{MACD} = \\text{EMA}(C, 12) - \\text{EMA}(C, 26)"
    },
    "macd_signal": {
        "plain_formula": "EMA(MACD, 9)",
        "latex_formula": "\\text{Signal} = \\text{EMA}(\\text{MACD}, 9)"
    },
    "stoch_k": {
        "plain_formula": "(Close - Low14) / (High14 - Low14) * 100",
        "latex_formula": "\\%K = \\frac{C_t - L_{14}}{H_{14} - L_{14}} \\times 100"
    },
    "cci": {
        "plain_formula": "(Price - SMA) / (0.015 * Mean Deviation)",
        "latex_formula": "\\text{CCI} = \\frac{p_t - \\text{SMA}(p, 20)}{0.015 \\times \\text{MD}(p, 20)}"
    },
    "roc": {
        "plain_formula": "(Close - Close_N) / Close_N * 100",
        "latex_formula": "\\text{ROC} = \\frac{C_t - C_{t-N}}{C_{t-N}} \\times 100"
    },
    "williams_r": {
        "plain_formula": "(High14 - Close) / (High14 - Low14) * -100",
        "latex_formula": "\\%R = \\frac{H_{14} - C_t}{H_{14} - L_{14}} \\times (-100)"
    },
    # Volume
    "obv": {
        "plain_formula": "OBV_prev + (Volume * Sign(Close - Close_prev))",
        "latex_formula": "\\text{OBV}_t = \\text{OBV}_{t-1} + V_t \\cdot \\text{sgn}(C_t - C_{t-1})"
    },
    "mfi": {
        "plain_formula": "100 - (100 / (1 + MFR))",
        "latex_formula": "\\text{MFI} = 100 - \\frac{100}{1 + \\frac{\\text{Positive Money Flow}}{\\text{Negative Money Flow}}}"
    },
    "volume_ma": {
        "plain_formula": "Volume / SMA(Volume, 20)",
        "latex_formula": "\\text{VolRatio} = \\frac{V_t}{\\text{SMA}(V, 20)_t}"
    },
    "cmf": {
        "plain_formula": "Sum(MFV, 20) / Sum(Volume, 20)",
        "latex_formula": "\\text{CMF} = \\frac{\\sum_{i=0}^{19} \\left( \\frac{(C - L) - (H - C)}{H - L} \\times V \\right)_{t-i}}{\\sum_{i=0}^{19} V_{t-i}}"
    },
    "volume_breakout": {
        "plain_formula": "Volume > SMA(Volume, 20) + 1.5 * Std(Volume, 20)",
        "latex_formula": "V_t > \\mu_V + 1.5\\sigma_V"
    },
    # Volatility
    "atr": {
        "plain_formula": "EMA(TrueRange, 14)",
        "latex_formula": "\\text{ATR}_{14} = \\text{EMA}(\\max(H - L, |H - C_{prev}|, |L - C_{prev}|), 14)"
    },
    "hist_vol": {
        "plain_formula": "Std(DailyReturns, 20) * Sqrt(252) * 100",
        "latex_formula": "\\sigma_{ann} = \\text{Std}(\\ln(C_t/C_{t-1}), 20) \\times \\sqrt{252} \\times 100"
    },
    "bb_width": {
        "plain_formula": "(UpperBand - LowerBand) / MiddleBand * 100",
        "latex_formula": "\\text{BBWidth} = \\frac{UB_t - LB_t}{MB_t} \\times 100"
    },
    "atr_percentile": {
        "plain_formula": "Percentile(ATR, 252)",
        "latex_formula": "\\text{ATR}_{pct} = \\text{Rank}_{252}(\\text{ATR}_t)"
    },
    # Breakout
    "resistance_break": {
        "plain_formula": "Close > High(20)",
        "latex_formula": "C_t > \\max_{1 \\le i \\le 20}(H_{t-i})"
    },
    "support_holding": {
        "plain_formula": "Close > Low(20)",
        "latex_formula": "C_t > \\min_{1 \\le i \\le 20}(L_{t-i})"
    },
    "donchian_breakout": {
        "plain_formula": "Close > DonchianUpper(20)",
        "latex_formula": "C_t > DC_{upper, 20}"
    },
    "volume_confirmation": {
        "plain_formula": "Volume Ratio > 1.25",
        "latex_formula": "\\text{VolRatio} > 1.25"
    },
    
    # ML Models
    "rf": {
        "plain_formula": "Softmax(Sum(Tree_i(x)) / N)",
        "latex_formula": "P(y|x) = \\frac{1}{M}\\sum_{m=1}^{M} T_m(x)"
    },
    "xgb": {
        "plain_formula": "Logistic(Sum(f_k(x)))",
        "latex_formula": "P(y|x) = \\sigma\\left(\\sum_{k=1}^{K} f_k(x)\\right)"
    },
    "lgb": {
        "plain_formula": "Softmax(Sum(f_j(x)))",
        "latex_formula": "P(y|x) = \\text{softmax}\\left(\\sum_{j=1}^{J} f_j(x)\\right)"
    },
    
    # GRU
    "p_long": {
        "plain_formula": "GRU_Layer_Outputs -> Softmax[0]",
        "latex_formula": "P(y=\\text{Long}|X_{30}) = \\text{Softmax}(\\mathbf{W}_h \\mathbf{h}_t + \\mathbf{b})"
    },
    "p_hold": {
        "plain_formula": "GRU_Layer_Outputs -> Softmax[1]",
        "latex_formula": "P(y=\\text{Hold}|X_{30}) = \\text{Softmax}(\\mathbf{W}_h \\mathbf{h}_t + \\mathbf{b})"
    },
    "p_short": {
        "plain_formula": "GRU_Layer_Outputs -> Softmax[2]",
        "latex_formula": "P(y=\\text{Short}|X_{30}) = \\text{Softmax}(\\mathbf{W}_h \\mathbf{h}_t + \\mathbf{b})"
    },
    "higher_highs": {
        "plain_formula": "Sum(Close_t > Close_{t-1}) / 30",
        "latex_formula": "\\sum_{i=1}^{30} \\mathbb{I}(C_{t-i} > C_{t-i-1})"
    },
    "higher_lows": {
        "plain_formula": "Sum(Low_t > Low_{t-1}) / 30",
        "latex_formula": "\\sum_{i=1}^{30} \\mathbb{I}(L_{t-i} > L_{t-i-1})"
    },
    "volume_expansion": {
        "plain_formula": "Volume_t > SMA(Volume, 30)",
        "latex_formula": "V_t > \\text{SMA}(V, 30)_t"
    },
    "volatility_compression": {
        "plain_formula": "ATR_t / Price_t",
        "latex_formula": "\\text{Volatility}_{norm} = \\frac{\\text{ATR}(14)_t}{C_t}"
    },
    "trend_persistence": {
        "plain_formula": "LinearSlope(Close, 30)",
        "latex_formula": "\\beta_{slope} = \\frac{\\text{Cov}(t, C_t)}{\\text{Var}(t)}"
    },
    
    # Risk Metrics
    "beta": {
        "plain_formula": "Cov(Asset, Nifty50) / Var(Nifty50)",
        "latex_formula": "\\beta = \\frac{\\text{Cov}(R_a, R_m)}{\\text{Var}(R_m)}"
    },
    "sharpe": {
        "plain_formula": "(Return - RF) / Volatility",
        "latex_formula": "\\text{Sharpe} = \\frac{\\mathbb{E}[R_a - R_f]}{\\sigma_a}"
    },
    "volatility": {
        "plain_formula": "Std(DailyReturns) * Sqrt(252)",
        "latex_formula": "\\sigma_{ann} = \\sqrt{252} \\times \\sqrt{\\frac{1}{N-1}\\sum (R_i - \\mu)^2}"
    },
    "drawdown": {
        "plain_formula": "(Peak - Trough) / Peak * 100",
        "latex_formula": "\\text{MDD} = \\max_{\\tau \\le t} \\left( \\frac{P_\\tau - P_t}{P_\\tau} \\right)"
    },
    "downside_dev": {
        "plain_formula": "Sqrt(Sum(Min(0, Return)^2) / N) * Sqrt(252)",
        "latex_formula": "\\sigma_{down} = \\sqrt{252} \\times \\sqrt{\\frac{1}{N}\\sum \\min(0, R_i)^2}"
    },
    "var": {
        "plain_formula": "Percentile(Returns, 5)",
        "latex_formula": "\\text{VaR}_{95\\%} = F^{-1}(0.05)"
    },
    "cvar": {
        "plain_formula": "Mean(Returns where Returns < VaR)",
        "latex_formula": "\\text{CVaR}_{95\\%} = \\mathbb{E}[R \\mid R \\le \\text{VaR}_{95\\%}]"
    },
    "confidence_inverse": {
        "plain_formula": "100 - Confidence",
        "latex_formula": "\\text{Uncertainty} = 100 - \\text{Confidence}"
    },
    
    # Reliability
    "accuracy": {
        "plain_formula": "Wins / Total Predictions",
        "latex_formula": "\\text{Accuracy} = \\frac{\\sum \\mathbb{I}(\\text{sign}(\\text{pred}) == \\text{sign}(\\text{real}))}{N}"
    },
    "agreement": {
        "plain_formula": "Agreeing Sign Count / Total Models",
        "latex_formula": "\\text{Concordance} = \\frac{1}{M}\\sum \\mathbb{I}(\\text{sign}(S_i) == \\text{sign}(S_{blended}))"
    },
    "completeness": {
        "plain_formula": "Valid Inputs / Expected Inputs",
        "latex_formula": "\\text{Integrity} = 1.0 - \\frac{N_{missing}}{N_{total}}"
    },
    "similarity": {
        "plain_formula": "CosineSimilarity(Current_Regime, History)",
        "latex_formula": "\\text{Similarity} = \\frac{\\mathbf{A} \\cdot \\mathbf{B}}{\\|\\mathbf{A}\\| \\|\\mathbf{B}\\|}"
    },
    
    # Confidence
    "baseline": {
        "plain_formula": "Out-of-Sample F1-Score",
        "latex_formula": "\\text{Baseline} = 2 \\times \\frac{\\text{Precision} \\times \\text{Recall}}{\\text{Precision} + \\text{Recall}}"
    },
    "consensus_boost": {
        "plain_formula": "Agreement Boost Adjustment",
        "latex_formula": "\\text{Boost} = \\begin{cases} +15 & \\text{if } 3/3 \\text{ models agree} \\\\ +5 & \\text{if } 2/3 \\text{ models agree} \\\\ -10 & \\text{otherwise} \\end{cases}"
    },
    "technical_score": {
        "plain_formula": "Trend + Momentum + Volatility Indicators blend",
        "latex_formula": "\\text{Technical Score} = \\text{blend}(\\text{Indicators})"
    },
    "ml_score": {
        "plain_formula": "Random Forest + XGBoost + LightGBM Ensemble",
        "latex_formula": "\\text{ML Score} = \\text{ensemble}(RF, XGB, LGB)"
    },
    "gru_score": {
        "plain_formula": "GRU Probability Spread",
        "latex_formula": "\\text{GRU Score} = (P_{long} - P_{short}) \\times 100"
    },
    "reliability_score": {
        "plain_formula": "Consensus + Accuracy + Telemetry + Similarity Blend",
        "latex_formula": "\\text{Reliability Score} = \\text{blend}(\\text{Telemetry})"
    }
}
