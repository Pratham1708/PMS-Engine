import numpy as np


def create_rsi_signals(df):

    df = df.copy()

    df["RSI_SIGNAL"] = np.where(
        df["RSI14"] < 30,
        1,
        np.where(
            df["RSI14"] > 70,
            -1,
            0
        )
    )

    return df