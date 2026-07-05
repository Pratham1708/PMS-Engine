# risk_engine.py

def risk_score(row):

    atr_pct = (
        row["ATR14"]
        /
        row["Close"]
    ) * 100

    if atr_pct < 2:
        return 90

    elif atr_pct < 4:
        return 70

    elif atr_pct < 6:
        return 50

    else:
        return 30