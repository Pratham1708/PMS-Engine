import ta


def build_features(df):

    df = df.copy()

    # EMA

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

    # RSI

    df["RSI14"] = ta.momentum.rsi(
        df["Close"],
        window=14
    )

    # MACD

    macd = ta.trend.MACD(
        df["Close"]
    )

    df["MACD"] = macd.macd()

    df["MACD_SIGNAL"] = macd.macd_signal()

    df["MACD_HIST"] = macd.macd_diff()

    # ATR

    df["ATR14"] = ta.volatility.average_true_range(

        df["High"],
        df["Low"],
        df["Close"],

        window=14
    )

    # ADX

    adx = ta.trend.ADXIndicator(

        df["High"],
        df["Low"],
        df["Close"],

        window=14
    )

    df["ADX14"] = adx.adx()

    # ROC

    df["ROC14"] = ta.momentum.roc(

        df["Close"],

        window=14
    )

    # Volume Ratio

    df["VolumeRatio"] = (

        df["Volume"]

        /

        df["Volume"]
        .rolling(20)
        .mean()
    )

    return df

def add_relative_features(df):

    df["Price_vs_EMA20"] = (
        df["Close"] /
        df["EMA20"]
    )

    df["Price_vs_EMA50"] = (
        df["Close"] /
        df["EMA50"]
    )

    df["Price_vs_EMA200"] = (
        df["Close"] /
        df["EMA200"]
    )

    df["EMA20_vs_EMA50"] = (
        df["EMA20"] /
        df["EMA50"]
    )

    df["EMA50_vs_EMA200"] = (
        df["EMA50"] /
        df["EMA200"]
    )

    return df