import pandas as pd


def build_portfolio(
    buy_df,
    top_n=5
):

    portfolio = (

        buy_df

        .head(top_n)

        .copy()

        .reset_index(drop=True)

    )

    return portfolio