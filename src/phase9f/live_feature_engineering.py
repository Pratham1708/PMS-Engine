import pandas as pd
import ta

def generate_features(
    df
):

    result = []

    for symbol in df["Symbol"].unique():

        stock = df[
            df["Symbol"] == symbol
        ].copy()

        stock["EMA20"] = (
            stock["Close"]
            .ewm(span=20)
            .mean()
        )

        stock["EMA50"] = (
            stock["Close"]
            .ewm(span=50)
            .mean()
        )

        stock["EMA200"] = (
            stock["Close"]
            .ewm(span=200)
            .mean()
        )

        stock["RSI14"] = ta.momentum.RSIIndicator(
            stock["Close"]
        ).rsi()

        macd = ta.trend.MACD(
            stock["Close"]
        )

        stock["MACD"] = macd.macd()

        stock["MACD_HIST"] = (
            macd.macd_diff()
        )

        stock["Price_vs_EMA20"] = (

            stock["Close"]

            /

            stock["EMA20"]
        )

        stock["Price_vs_EMA50"] = (

            stock["Close"]

            /

            stock["EMA50"]
        )

        stock["Price_vs_EMA200"] = (

            stock["Close"]

            /

            stock["EMA200"]
        )

        stock["EMA20_vs_EMA50"] = (

            stock["EMA20"]

            /

            stock["EMA50"]
        )

        stock["EMA50_vs_EMA200"] = (

            stock["EMA50"]

            /

            stock["EMA200"]
        )

        result.append(stock)

    final_df = pd.concat(
        result
    )

    return final_df