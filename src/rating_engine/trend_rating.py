def trend_score(row):

    score = 0

    if row["Close"] > row["EMA20"]:
        score += 10
    else:
        score -= 10

    if row["Close"] > row["EMA50"]:
        score += 20
    else:
        score -= 20

    if row["Close"] > row["EMA200"]:
        score += 30
    else:
        score -= 30

    if row["EMA20"] > row["EMA50"]:
        score += 20
    else:
        score -= 20

    if row["EMA50"] > row["EMA200"]:
        score += 20
    else:
        score -= 20

    return score