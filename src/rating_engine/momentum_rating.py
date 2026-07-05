def momentum_score(row):

    score = 0

    rsi = row["RSI14"]

    # RSI

    if rsi >= 70:
        score += 20

    elif rsi >= 60:
        score += 10

    elif rsi <= 30:
        score -= 20

    elif rsi <= 40:
        score -= 10

    # MACD (Most Important)

    if row["MACD"] > 0:
        score += 50
    else:
        score -= 50

    # Histogram

    if row["MACD_HIST"] > 0:
        score += 10
    else:
        score -= 10

    # ROC

    if row["ROC14"] > 0:
        score += 10
    else:
        score -= 10

    return score