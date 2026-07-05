import numpy as np

def create_five_class_labels(
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

    strong_buy = mean + 2*std

    buy = mean + std

    sell = mean - std

    strong_sell = mean - 2*std

    conditions = [

        df["FutureReturn"] >= strong_buy,

        df["FutureReturn"] >= buy,

        df["FutureReturn"] > sell,

        df["FutureReturn"] > strong_sell
    ]

    choices = [

        "STRONG_BUY",

        "BUY",

        "HOLD",

        "SELL"
    ]

    df["Signal5"] = np.select(

        conditions,

        choices,

        default="STRONG_SELL"
    )

    return df