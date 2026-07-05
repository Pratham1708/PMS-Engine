def volatility_score(row):

    score = 0

    if row["ADX14"] > 25:
        score += 30

    elif row["ADX14"] < 15:
        score -= 20

    atr_pct = (

        row["ATR14"]

        /

        row["Close"]

    ) * 100

    if atr_pct > 4:
        score -= 20

    elif atr_pct < 2:
        score += 10

    return score