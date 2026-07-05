import numpy as np


def calculate_technical_score(row):

    score = 0

    # ==========================================
    # TREND
    # ==========================================

    p20 = (row["Price_vs_EMA20"] - 1) * 100
    p50 = (row["Price_vs_EMA50"] - 1) * 100
    p200 = (row["Price_vs_EMA200"] - 1) * 100

    score += np.clip(
        p20 * 2,
        -15,
        15
    )

    score += np.clip(
        p50 * 2,
        -25,
        25
    )

    score += np.clip(
        p200 * 2,
        -35,
        35
    )

    # ==========================================
    # EMA ALIGNMENT
    # ==========================================

    ema20_50 = (
        row["EMA20_vs_EMA50"] - 1
    ) * 100

    ema50_200 = (
        row["EMA50_vs_EMA200"] - 1
    ) * 100

    score += np.clip(
        ema20_50 * 2,
        -10,
        10
    )

    score += np.clip(
        ema50_200 * 2,
        -15,
        15
    )

    # ==========================================
    # RSI
    # ==========================================

    rsi = row["RSI14"]

    if rsi > 70:

        score += 10

    elif rsi > 60:

        score += 7

    elif rsi > 50:

        score += 4

    elif rsi < 30:

        score -= 10

    elif rsi < 40:

        score -= 7

    elif rsi < 50:

        score -= 4

    # ==========================================
    # MACD
    # ==========================================

    macd = row["MACD"]

    score += np.clip(
        macd * 5,
        -15,
        15
    )

    # ==========================================
    # MACD HIST
    # ==========================================

    hist = row["MACD_HIST"]

    score += np.clip(
        hist * 10,
        -10,
        10
    )

    # ==========================================
    # NORMALIZE
    # ==========================================

    score = np.clip(
        score,
        -100,
        100
    )

    return round(
        score,
        2
    )