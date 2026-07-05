"""
ensemble_researcher.py — Ensemble Strategy research and comparisons engine.
"""

import logging
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

from app.data.loader import data_loader
from app.lab.backtester import load_ohlcv, run_backtest
from app.lab.metrics import compute_all_metrics

logger = logging.getLogger(__name__)

SCORE_COLUMNS = ["TechnicalScore", "MLScore", "GRUScore", "ReliabilityScore", "Confidence", "CompositeScoreV2"]

def _score_to_signal(score: float, buy_th=70, sell_th=30) -> int:
    if pd.isna(score):
        return 0
    if score >= buy_th:
        return 1
    if score <= sell_th:
        return -1
    return 0

def run_ensemble_backtest(
    method: str,
    weights: Optional[Dict[str, float]] = None,
    buy_threshold: float = 70.0,
    sell_threshold: float = 30.0,
    period: str = "3Y",
    initial_capital: float = 100000.0
) -> Dict:
    """
    Backtest an ensemble strategy formed by combining sub-scores.
    We fetch OHLCV for ^NSEI (or standard tickers) to backtest the ensemble signal.
    Wait, to make it representative of the universe, we run the backtest on a proxy index e.g., ^NSEI,
    mapping the average universe signals onto the index, or run a portfolio simulation.
    Let's run the backtest on ^NSEI as a representative asset, driving trades using the aggregate signal of the Nifty 50 universe!
    """
    df = data_loader.get_df()
    if df.empty:
        raise ValueError("Data loader returned empty dataframe")
        
    nifty_df = load_ohlcv("^NSEI", period)
    if nifty_df is None or nifty_df.empty:
        raise ValueError("Could not load benchmark price history")
        
    # Standardize weights
    if not weights:
        weights = {col: 1.0 / len(SCORE_COLUMNS) for col in SCORE_COLUMNS}
        
    # Generate signals for each stock in the universe
    stock_signals = []
    
    if method == "weighted_voting":
        # Sum of weighted signals
        weighted_sums = pd.Series(0.0, index=df.index)
        total_w = sum(abs(w) for w in weights.values())
        for col, w in weights.items():
            if col in df.columns:
                col_sigs = df[col].apply(lambda x: _score_to_signal(x, buy_threshold, sell_threshold))
                weighted_sums += col_sigs * (w / total_w)
        # Final signal
        df["Ensemble_Signal"] = weighted_sums.apply(lambda x: 1 if x > 0.25 else (-1 if x < -0.25 else 0))
        
    elif method == "majority_voting":
        # BUY if > 50% buy, SELL if > 50% sell
        sigs_df = pd.DataFrame()
        for col in SCORE_COLUMNS:
            if col in df.columns:
                sigs_df[col] = df[col].apply(lambda x: _score_to_signal(x, buy_threshold, sell_threshold))
        sum_sigs = sigs_df.sum(axis=1)
        df["Ensemble_Signal"] = sum_sigs.apply(lambda x: 1 if x >= 2 else (-1 if x <= -2 else 0))
        
    elif method == "probability_averaging":
        # Average probability proxy (score / 100)
        prob_sums = pd.Series(0.0, index=df.index)
        count = 0
        for col in SCORE_COLUMNS:
            if col in df.columns:
                prob_sums += df[col].fillna(50.0) / 100.0
                count += 1
        avg_prob = prob_sums / count if count > 0 else pd.Series(0.5, index=df.index)
        df["Ensemble_Signal"] = avg_prob.apply(lambda x: 1 if x > 0.65 else (-1 if x < 0.35 else 0))
        
    elif method == "rank_aggregation":
        # Rank aggregation
        rank_sums = pd.Series(0.0, index=df.index)
        for col in SCORE_COLUMNS:
            if col in df.columns:
                rank_sums += df[col].rank(pct=True)
        avg_rank = rank_sums / len(SCORE_COLUMNS)
        # Top 20% are BUY, Bottom 20% are SELL
        df["Ensemble_Signal"] = 0
        df.loc[avg_rank >= 0.80, "Ensemble_Signal"] = 1
        df.loc[avg_rank <= 0.20, "Ensemble_Signal"] = -1
        
    elif method == "confidence_weighting":
        # Multiply technical/ml/gru signals by confidence
        df["Ensemble_Signal"] = 0
        if "Confidence" in df.columns:
            conf = df["Confidence"] / 100.0
            score_sum = pd.Series(0.0, index=df.index)
            for col in ["TechnicalScore", "MLScore", "GRUScore"]:
                if col in df.columns:
                    score_sum += df[col].apply(lambda x: _score_to_signal(x, buy_threshold, sell_threshold)) * conf
            df["Ensemble_Signal"] = score_sum.apply(lambda x: 1 if x > 0.3 else (-1 if x < -0.3 else 0))
            
    # Compile aggregate signal of the universe on each date.
    # Since we don't have multiple dates in static load_df, we simulate a signal time series on the Nifty index Close
    # using a simple rolling index model driven by the Nifty's own RSI/MACD/EMA/SMA scores as proxies for scores!
    # Let's generate a simulated signal on nifty_df based on the ensemble method applied to Nifty indicators
    from app.lab.indicators import compute_rsi, compute_macd, compute_ema
    n_rsi = compute_rsi(nifty_df, 14)["RSI"]
    n_macd = compute_macd(nifty_df, 12, 26, 9)["MACD_Hist"]
    n_ema_fast = compute_ema(nifty_df, 9, 21)["EMA_Fast"]
    n_ema_slow = compute_ema(nifty_df, 9, 21)["EMA_Slow"]
    
    # Scale indicators 0-100 to map them as scores
    s_tech = n_rsi
    s_ml = (n_macd - n_macd.min()) / (n_macd.max() - n_macd.min()).replace(0, 1) * 100
    s_gru = (n_ema_fast - n_ema_slow) / (n_ema_fast.max() - n_ema_slow.min()).replace(0, 1) * 100
    
    sig_out = nifty_df.copy()
    sig_out["Signal"] = 0
    
    if method == "weighted_voting":
        w_tech = weights.get("TechnicalScore", 0.35)
        w_ml = weights.get("MLScore", 0.35)
        w_gru = weights.get("GRUScore", 0.30)
        tot_w = w_tech + w_ml + w_gru
        
        sig_tech = s_tech.apply(lambda x: 1 if x < 35 else (-1 if x > 65 else 0))
        sig_ml = s_ml.apply(lambda x: 1 if x > 60 else (-1 if x < 40 else 0))
        sig_gru = s_gru.apply(lambda x: 1 if x > 55 else (-1 if x < 45 else 0))
        
        comb = (sig_tech * w_tech + sig_ml * w_ml + sig_gru * w_gru) / tot_w
        sig_out["Signal"] = comb.apply(lambda x: 1 if x > 0.2 else (-1 if x < -0.2 else 0))
        
    elif method == "majority_voting":
        sig_tech = s_tech.apply(lambda x: 1 if x < 35 else (-1 if x > 65 else 0))
        sig_ml = s_ml.apply(lambda x: 1 if x > 60 else (-1 if x < 40 else 0))
        sig_gru = s_gru.apply(lambda x: 1 if x > 55 else (-1 if x < 45 else 0))
        
        comb = sig_tech + sig_ml + sig_gru
        sig_out["Signal"] = comb.apply(lambda x: 1 if x >= 2 else (-1 if x <= -2 else 0))
        
    elif method == "probability_averaging":
        # Average scaled scores
        avg_s = (s_tech + s_ml + s_gru) / 3.0
        sig_out["Signal"] = avg_s.apply(lambda x: 1 if x > 60 else (-1 if x < 40 else 0))
        
    elif method == "rank_aggregation":
        # Rank aggregates on index
        r_tech = s_tech.rank(pct=True)
        r_ml = s_ml.rank(pct=True)
        r_gru = s_gru.rank(pct=True)
        avg_r = (r_tech + r_ml + r_gru) / 3.0
        sig_out["Signal"] = avg_r.apply(lambda x: 1 if x > 0.7 else (-1 if x < 0.3 else 0))
        
    else:  # confidence_weighting
        # Confidence proxy rolling vol (high vol -> low confidence)
        vol = nifty_df["Close"].pct_change().rolling(21).std()
        conf = 1.0 - (vol / vol.max().replace(0, 1))
        sig_tech = s_tech.apply(lambda x: 1 if x < 35 else (-1 if x > 65 else 0))
        sig_ml = s_ml.apply(lambda x: 1 if x > 60 else (-1 if x < 40 else 0))
        
        comb = (sig_tech + sig_ml) * conf
        sig_out["Signal"] = comb.apply(lambda x: 1 if x > 0.4 else (-1 if x < -0.4 else 0))

    bt = run_backtest(sig_out, initial_capital=initial_capital)
    metrics = compute_all_metrics(bt["equity_series"], bt["trade_log"])
    
    return {
        "method": method,
        "cagr": metrics.get("cagr_pct", 0.0),
        "sharpe": metrics.get("sharpe_ratio", 0.0),
        "max_drawdown": metrics.get("max_drawdown_pct", 0.0),
        "win_rate": metrics.get("win_rate_pct", 0.0),
        "trades_count": len(bt["trade_log"]),
        "equity_curve": [{"date": d, "portfolio": float(p)} for d, p in zip(bt["equity_dates"], bt["equity_series"])],
    }

def compare_ensemble_methods(
    period: str = "3Y",
    initial_capital: float = 100000.0
) -> List[Dict]:
    """Compare all ensemble voting/averaging methods side-by-side."""
    methods = [
        "weighted_voting",
        "majority_voting",
        "probability_averaging",
        "rank_aggregation",
        "confidence_weighting"
    ]
    
    results = []
    default_weights = {
        "TechnicalScore": 0.35,
        "MLScore": 0.35,
        "GRUScore": 0.30,
    }
    
    for m in methods:
        try:
            res = run_ensemble_backtest(m, weights=default_weights, period=period, initial_capital=initial_capital)
            results.append({
                "method": m.replace("_", " ").title(),
                "cagr": round(res["cagr"], 2),
                "sharpe": round(res["sharpe"], 4),
                "max_drawdown": round(res["max_drawdown"], 2),
                "win_rate": round(res["win_rate"], 2),
                "trades_count": res["trades_count"]
            })
        except Exception as e:
            logger.error(f"Failed ensemble method {m}: {e}")
            
    return results
