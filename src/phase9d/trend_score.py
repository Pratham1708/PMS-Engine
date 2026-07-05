def trend_score(row):

    score = 0

    if row["Price_vs_EMA20"] > 1:
        score += 25
    else:
        score -= 25

    if row["Price_vs_EMA50"] > 1:
        score += 25
    else:
        score -= 25

    if row["Price_vs_EMA200"] > 1:
        score += 30
    else:
        score -= 30

    if row["EMA20_vs_EMA50"] > 1:
        score += 10
    else:
        score -= 10

    if row["EMA50_vs_EMA200"] > 1:
        score += 10
    else:
        score -= 10

    return score