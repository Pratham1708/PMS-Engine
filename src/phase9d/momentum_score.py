def momentum_score(row):

    score = 0

    if row["RSI14"] > 60:
        score += 20

    elif row["RSI14"] < 40:
        score -= 20

    if row["MACD"] > 0:
        score += 40
    else:
        score -= 40

    if row["MACD_HIST"] > 0:
        score += 20
    else:
        score -= 20

    return score