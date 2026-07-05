import pandas as pd


def rolling_performance(
    portfolio_df,
    window=252
):

    rolling_return = (

        portfolio_df[
            "PortfolioReturn"
        ]

        .rolling(window)

        .mean()

    )

    rolling_volatility = (

        portfolio_df[
            "PortfolioReturn"
        ]

        .rolling(window)

        .std()

    )

    output = portfolio_df.copy()

    output[
        "RollingReturn"
    ] = rolling_return

    output[
        "RollingVolatility"
    ] = rolling_volatility

    return output