import numpy as np

def create_labels(

    df,

    horizon=5
):

    df = df.copy()

    df["FutureReturn"] = (

        df["Close"]
        .shift(-horizon)

        /
        df["Close"]

        - 1
    )

    mean = df["FutureReturn"].mean()

    std = df["FutureReturn"].std()

    upper = mean + std

    lower = mean - std

    df["Signal"] = np.where(

        df["FutureReturn"] > upper,

        "LONG",

        np.where(

            df["FutureReturn"] < lower,

            "SHORT",

            "HOLD"
        )
    )

    return df