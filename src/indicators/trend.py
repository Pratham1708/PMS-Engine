import ta


def add_trend_indicators(df):

    df["EMA20"] = ta.trend.ema_indicator(
        df["Close"],
        window=20
    )

    df["EMA50"] = ta.trend.ema_indicator(
        df["Close"],
        window=50
    )

    df["EMA200"] = ta.trend.ema_indicator(
        df["Close"],
        window=200
    )

    return df