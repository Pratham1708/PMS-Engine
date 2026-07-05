# momentum_engine.py

def momentum_score(row):

    score = 0

    rsi = row["RSI14"]

    if 55 <= rsi <= 70:
        score += 40

    if row["MACD"] > 0:
        score += 30

    if row["ROC14"] > 0:
        score += 30

    return score