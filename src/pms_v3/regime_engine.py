def detect_regime(row):

    close = row["Close"]

    ema200 = row["EMA200"]

    adx = row["ADX14"]

    if close > ema200 and adx > 25:

        return "Bull Market"

    elif close < ema200 and adx > 25:

        return "Bear Market"

    elif close < ema200 and adx < 25:

        return "Bearish Recovery"

    else:

        return "Sideways"