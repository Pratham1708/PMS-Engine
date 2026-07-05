import pandas as pd
import numpy as np


def build_historical_portfolio(
    master_df,
    min_signal="BUY"
):

    signal_order = {

        "STRONG BUY": 5,
        "BUY": 4,
        "HOLD": 3,
        "SELL": 2,
        "STRONG SELL": 1

    }

    threshold = signal_order[min_signal]

    portfolio_returns = []

    unique_dates = sorted(
        master_df["Date"].unique()
    )

    for dt in unique_dates:

        day_df = master_df[
            master_df["Date"] == dt
        ].copy()

        day_df = day_df[

            day_df["HistoricalSignal"]

            .map(signal_order)

            >=

            threshold

        ]

        if len(day_df) == 0:

            continue

        portfolio_return = (

            day_df["FutureReturn"]

            .mean()

        )

        portfolio_returns.append(

            [

                dt,

                portfolio_return

            ]

        )

    portfolio_df = pd.DataFrame(

        portfolio_returns,

        columns=[
            "Date",
            "PortfolioReturn"
        ]

    )

    return portfolio_df