import numpy as np


def create_ema_signals(df):

    df = df.copy()

    df["EMA_SIGNAL"] = np.where(
        df["EMA20"] > df["EMA50"],
        1,
        -1
    )

    return df