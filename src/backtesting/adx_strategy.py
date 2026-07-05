import numpy as np


def create_adx_signals(df):

    df = df.copy()

    df["ADX_FILTER"] = np.where(
        df["ADX14"] > 25,
        1,
        0
    )

    return df