import ta


def add_momentum_indicators(df):

    df["RSI14"] = ta.momentum.rsi(
        df["Close"],
        window=14
    )

    macd = ta.trend.MACD(df["Close"])

    df["MACD"] = macd.macd()

    df["MACD_SIGNAL"] = macd.macd_signal()

    df["MACD_HIST"] = macd.macd_diff()

    df["ROC14"] = ta.momentum.roc(
        df["Close"],
        window=14
    )

    return df