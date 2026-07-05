import pandas as pd


def create_return_target(
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

    return df


def prepare_regression_dataset(
    df,
    features,
    target="FutureReturn"
):

    dataset = df[
        features + [target]
    ].dropna()

    X = dataset[
        features
    ]

    y = dataset[
        target
    ]

    return X, y