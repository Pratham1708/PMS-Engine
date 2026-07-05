import ta


def add_volatility_indicators(df):

    df["ATR14"] = ta.volatility.average_true_range(
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        window=14
    )

    df["ADX14"] = ta.trend.adx(
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        window=14
    )

    return df