import numpy as np


def create_quantile_labels(
    df,
    long_pct=80,
    short_pct=20
):

    df = df.copy()

    upper = np.percentile(
        df["FutureReturn"].dropna(),
        long_pct
    )

    lower = np.percentile(
        df["FutureReturn"].dropna(),
        short_pct
    )

    conditions = [
        df["FutureReturn"] >= upper,
        df["FutureReturn"] <= lower
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

    return df, upper, lower