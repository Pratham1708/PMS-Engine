import pandas as pd


def build_ml_features(df):

    df = df.copy()

    df["Price_vs_EMA20"] = (
        (df["Close"] - df["EMA20"])
        /
        df["EMA20"]
    )

    df["Price_vs_EMA50"] = (
        (df["Close"] - df["EMA50"])
        /
        df["EMA50"]
    )

    df["Price_vs_EMA200"] = (
        (df["Close"] - df["EMA200"])
        /
        df["EMA200"]
    )

    df["EMA20_vs_EMA50"] = (
        (df["EMA20"] - df["EMA50"])
        /
        df["EMA50"]
    )

    df["EMA50_vs_EMA200"] = (
        (df["EMA50"] - df["EMA200"])
        /
        df["EMA200"]
    )

    return df