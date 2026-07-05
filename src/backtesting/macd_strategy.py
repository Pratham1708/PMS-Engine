import numpy as np


def create_macd_signals(df):

    df = df.copy()

    df["MACD_SIGNAL_STRAT"] = np.where(
        df["MACD"] > df["MACD_SIGNAL"],
        1,
        -1
    )

    return df