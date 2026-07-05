import pandas as pd


def performance_attribution(
    portfolio
):

    return (

        portfolio

        .groupby(
            "Symbol"
        )

        ["ForwardReturn"]

        .mean()

        .reset_index()
    )