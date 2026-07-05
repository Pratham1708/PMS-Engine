import numpy as np


def create_atr_labels(
    df,
    atr_multiplier=1.0,
    horizon=5
):

    df = df.copy()

    threshold = (
        df["ATR14"]
        /
        df["Close"]
    ) * atr_multiplier

    conditions = [
        df["FutureReturn"] > threshold,
        df["FutureReturn"] < -threshold
    ]

    choices = [
        "LONG",
        "SHORT"
    ]

    df["Signal"] = np.select(
        conditions,
        choices,
        default="HOLD"
    )

    return df