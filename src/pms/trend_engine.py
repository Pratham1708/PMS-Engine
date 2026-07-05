# trend_engine.py

def trend_score(row):

    score = 0

    if row["Close"] > row["EMA20"]:
        score += 25

    if row["Close"] > row["EMA50"]:
        score += 25

    if row["Close"] > row["EMA200"]:
        score += 50

    return score