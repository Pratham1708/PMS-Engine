import pandas as pd


def create_future_returns(
    df,
    horizon=5
):

    df = df.copy()

    df["FutureClose"] = (
        df["Close"]
        .shift(-horizon)
    )

    df["FutureReturn"] = (
        (df["FutureClose"] - df["Close"])
        /
        df["Close"]
    )

    return df